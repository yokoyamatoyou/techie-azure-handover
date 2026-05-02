"""Forensic-linguistic fingerprint metrics for AI-text detection evasion.

All metrics are computed locally (no LLM calls).  The ``FingerprintAnalyzer``
class aggregates the individual scores into a single ``FingerprintReport``.
When values fall into a "flat zone" (suspiciously uniform), a lightweight
correction hint is emitted.  Callers decide whether to act on it (fail-open).

Design goal: **reduce predictability** to raise humanness.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    from sudachipy import dictionary as sudachi_dictionary
    from sudachipy import tokenizer as sudachi_tokenizer

    SUDACHI_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    sudachi_dictionary = None
    sudachi_tokenizer = None
    SUDACHI_AVAILABLE = False


# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------
_TERMINAL_PUNCT = re.compile(r"[。！？!?]")
_PARAGRAPH_SEP = re.compile(r"\n{2,}")
_HEADING_LINE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
_LIST_LINE = re.compile(r"^\s*(?:[-*+]|\d+[.)]|[・●◦▪])\s+", re.MULTILINE)

_CONJUNCTION_PATTERN = re.compile(
    r"^(まず|次に|さらに|また|そして|しかし|ただ|一方で?|なお|ところで|"
    r"加えて|つまり|したがって|それでは|ちなみに|もっとも|ただし)"
)

_SUBJECT_MARKER = re.compile(
    r"(私|僕|俺|我々|当社|弊社|自分|彼|彼女|あなた|皆さん|読者|"
    r"それ|これ|あれ|ここ|そこ|あそこ|彼ら|私たち|人々|誰|何)"
    r"[はがも]"
)
_INITIAL_SUBJECT_PRONOUN = re.compile(
    r"^(?:私|わたし|僕|俺|我々|私たち|自分|あなた|皆さん|読者|"
    r"当社|弊社|彼|彼女|彼ら|それ|これ|あれ|ここ|そこ|あそこ|人々|誰|何)"
    r"[はが]"
)
_INITIAL_SUBJECT_NOUN = re.compile(
    r"^(?:[一-龯ァ-ヶーA-Za-z0-9]+(?:の[一-龯ァ-ヶーA-Za-z0-9]+){0,2})(?<![でにともへ])[はが]"
)

_PARTICLE_PATTERN = re.compile(r"[はがをにでともへ]")
_TARGET_PARTICLES = list("はがをにでとも")
_TARGET_SUBJECT_PARTICLES = {"は", "が"}

_HIRAGANA = re.compile(r"[ぁ-ん]")
_KATAKANA = re.compile(r"[ァ-ヶー]")
_KANJI = re.compile(r"[一-龯]")

# ---------------------------------------------------------------------------
# Sentence ending category patterns (R9-T01)
# ---------------------------------------------------------------------------
_ENDING_DESU = re.compile(r"です[。！？!?]?$")
_ENDING_MASU = re.compile(r"(?:ます|ました|ません|ましょう)[。！？!?]?$")
_ENDING_QUESTION = re.compile(r"(?:か|でしょうか|ですか|ますか|のか|だろうか|かな)[。？!?]*$")
_ENDING_CONJECTURE = re.compile(
    r"(?:でしょう|だろう|かもしれません|かもしれない|はずです|はずだ|"
    r"に違いない|と思われます|と考えられます|ではないでしょうか|っぽい|らしい|そうだ)[。！？!?]?$"
)
_ENDING_NEGATIVE = re.compile(
    r"(?:ない|ません|ぬ|ず|ありません|いません|できません|しません)[。！？!?]?$"
)
_ENDING_TAIGEN = re.compile(
    r"(?:[一-龯ァ-ヶー]{1,12}|こと|もの|ところ|ほう|わけ|はず|つもり|ばかり|まま|とおり)[。]?$"
)

_ENDING_CATEGORIES = [
    ("question", _ENDING_QUESTION),
    ("conjecture", _ENDING_CONJECTURE),
    ("negative", _ENDING_NEGATIVE),
    ("desu", _ENDING_DESU),
    ("masu", _ENDING_MASU),
    ("taigen", _ENDING_TAIGEN),
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class FingerprintReport:
    """Aggregated fingerprint result."""
    sentence_length_cv: float = 0.0
    paragraph_length_cv: float = 0.0
    conjunction_repetition_rate: float = 0.0
    subject_explicit_rate: float = 0.0
    particle_entropy: float = 0.0
    particle_max_entropy: float = 0.0
    script_ratio_hiragana: float = 0.0
    script_ratio_katakana: float = 0.0
    script_ratio_kanji: float = 0.0
    pos_bigram_monotonicity: float = 0.0
    mtld: float = 0.0
    hd_d: float = 0.0
    nominalization_rate: float = 0.0
    sentence_ending_entropy: float = 0.0
    sentence_ending_fine_entropy: float = 0.0  # R14
    sentence_opening_entropy: float = 0.0  # R14
    comma_position_cv: float = 0.0  # R14
    vocab_repetition_lemmas: List[str] = field(default_factory=list)
    flat_zone_flags: List[str] = field(default_factory=list)
    correction_hints: List[str] = field(default_factory=list)
    overall_unpredictability: float = 0.0
    # Enhanced morphological metrics (kotomegane)
    morphological_ngram_entropy: float = 0.0
    morphological_diversity: Dict[str, float] = field(default_factory=dict)
    syntactic_complexity: Dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Sentence ending classification (R9-T01)
# ---------------------------------------------------------------------------

def classify_sentence_ending(sentence: str) -> str:
    """Classify a sentence into one of 7 ending categories (R9-T01).

    Categories: desu / masu / taigen / question / conjecture / negative / other.
    Order matters: question/conjecture/negative are checked before desu/masu
    because patterns like ``ですか`` should be classified as ``question``.
    """
    s = sentence.strip().rstrip("。！？!?").strip()
    if not s:
        return "other"
    # Check with trailing punctuation stripped for pattern matching
    for cat, pattern in _ENDING_CATEGORIES:
        if pattern.search(s):
            return cat
    return "other"


def classify_endings_distribution(text: str) -> Dict[str, float]:
    """Return the distribution of sentence ending categories for *text* (R9-T01).

    Returns a dict mapping each category to its ratio (0.0-1.0).
    """
    sentences = _split_sentences(text)
    if not sentences:
        return {}
    counts: Counter = Counter()
    for s in sentences:
        counts[classify_sentence_ending(s)] += 1
    total = sum(counts.values())
    if total == 0:
        return {}
    return {cat: round(cnt / total, 4) for cat, cnt in counts.items()}


def _detect_ending_repetition_in_sentences(
    sentences: Sequence[str],
    max_consecutive: int = 2,
) -> List[str]:
    """Detect repeated ending categories within a single local sentence stream."""
    if len(sentences) < 3:
        return []
    categories = [classify_sentence_ending(s) for s in sentences]
    hints: List[str] = []
    run_cat = categories[0]
    run_len = 1
    for cat in categories[1:]:
        if cat == run_cat:
            run_len += 1
        else:
            if run_len > max_consecutive:
                hints.append(
                    f"文末「{run_cat}」が{run_len}回連続（最大{max_consecutive}回推奨）"
                )
            run_cat = cat
            run_len = 1
    if run_len > max_consecutive:
        hints.append(
            f"文末「{run_cat}」が{run_len}回連続（最大{max_consecutive}回推奨）"
        )
    return hints


def detect_ending_repetition(text: str, max_consecutive: int = 2) -> List[str]:
    """Detect runs of 3+ identical endings inside each paragraph (R9-T03).

    Returns correction hints for each violation found. Paragraph boundaries reset
    the streak because cross-paragraph repetition is less user-visible than an
    uninterrupted monotone run inside one paragraph.
    """
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return []
    hints: List[str] = []
    for paragraph in paragraphs:
        hints.extend(
            _detect_ending_repetition_in_sentences(
                _split_sentences(paragraph),
                max_consecutive=max_consecutive,
            )
        )
    return hints


_ABSTRACT_WORDS = {
    "透明性", "包括的", "多層的", "柔軟", "柔軟な", "戦略的", "効果的",
    "持続可能", "革新的", "先進的", "総合的", "体系的", "網羅的",
    "本質的", "根本的", "抜本的", "画期的", "多角的", "横断的",
    "最適化", "高度化", "効率化", "可視化", "標準化", "一元化",
    "推進", "促進", "強化", "向上", "実現", "確保", "構築",
    "重要", "大切", "必要", "不可欠", "喫緊", "急務",
}


def detect_abstract_tautology(text: str, max_repeat: int = 1) -> List[str]:
    """Detect abstract words used more than *max_repeat* times (R9-T12).

    Targets explanation/analysis articles where abstract buzzwords tend to
    cluster without concrete backing. Returns correction hint strings.
    """
    sentences = _split_sentences(text)
    if len(sentences) < 3:
        return []
    counts: Counter = Counter()
    for s in sentences:
        for word in _ABSTRACT_WORDS:
            if word in s:
                counts[word] += 1
    hints: List[str] = []
    for word, cnt in counts.most_common():
        if cnt > max_repeat:
            hints.append(
                f"抽象語「{word}」が{cnt}回出現（具体化または言い換え推奨）"
            )
    return hints[:5]


def detect_comma_overuse(text: str, max_per_sentence: int = 3) -> List[str]:
    """Detect sentences with too many commas (読点「、」) (R9-T08).

    Returns correction hint strings for sentences exceeding *max_per_sentence*.
    Human average: 0-3 commas per sentence. 4+ is AI-like uniform punctuation.
    """
    sentences = _split_sentences(text)
    if len(sentences) < 3:
        return []
    hints: List[str] = []
    for s in sentences:
        comma_count = s.count("、")
        if comma_count > max_per_sentence:
            preview = s[:30] + "…" if len(s) > 30 else s
            hints.append(
                f"読点過多（{comma_count}個）: 「{preview}」"
            )
    return hints


def sentence_ending_entropy(text: str) -> float:
    """Shannon entropy of sentence ending category distribution (R9-T02).

    Human-like target: entropy ≧ 1.5 (7 categories → max ~2.81).
    Low entropy indicates repetitive sentence endings (AI tendency).
    Returns 0.0 for texts with fewer than 4 sentences.
    """
    sentences = _split_sentences(text)
    if len(sentences) < 4:
        return 0.0
    counts: Counter = Counter()
    for s in sentences:
        counts[classify_sentence_ending(s)] += 1
    total = sum(counts.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for cnt in counts.values():
        if cnt > 0:
            p = cnt / total
            entropy -= p * math.log2(p)
    return round(entropy, 4)


# ---------------------------------------------------------------------------
# Core metric functions (stateless, unit-testable)
# ---------------------------------------------------------------------------

def sentence_length_cv(text: str) -> float:
    """Coefficient of variation of sentence lengths (burstiness proxy)."""
    sentences = _split_sentences(text)
    if len(sentences) < 4:
        return 0.0
    lengths = [len(s) for s in sentences]
    mean = sum(lengths) / len(lengths)
    if mean < 1.0:
        return 0.0
    variance = sum((ln - mean) ** 2 for ln in lengths) / len(lengths)
    return (variance ** 0.5) / mean


def paragraph_length_cv(text: str) -> float:
    """Coefficient of variation of paragraph sentence-counts."""
    paragraphs = _split_paragraphs(text)
    if len(paragraphs) < 3:
        return 0.0
    counts = [_count_sentences(p) for p in paragraphs]
    counts = [c for c in counts if c > 0]
    if len(counts) < 3:
        return 0.0
    mean = sum(counts) / len(counts)
    if mean < 0.5:
        return 0.0
    variance = sum((c - mean) ** 2 for c in counts) / len(counts)
    return (variance ** 0.5) / mean


def conjunction_repetition_rate(text: str) -> float:
    """Fraction of paragraphs starting with a conjunction."""
    paragraphs = _split_paragraphs(text)
    if len(paragraphs) < 3:
        return 0.0
    hits = 0
    for p in paragraphs:
        first_line = p.strip().split("\n")[0].strip()
        first_line = re.sub(r"^#{1,6}\s+.*\n?", "", first_line).strip()
        if not first_line:
            continue
        if _CONJUNCTION_PATTERN.match(first_line):
            hits += 1
    return hits / max(1, len(paragraphs))


def subject_explicit_rate(text: str) -> float:
    """Fraction of sentences starting with an explicit grammatical subject/topic.

    User-visible AI感 is driven more by repeated sentence-initial ``Xは/が`` starts
    than by a topic phrase appearing later in the sentence, so the metric only
    counts sentence-initial subjects.
    """
    sentences = _split_sentences(text)
    if len(sentences) < 3:
        return 0.0
    sudachi_hits = _subject_explicit_rate_sudachi(sentences)
    if sudachi_hits is not None:
        return sudachi_hits
    hits = sum(1 for s in sentences if _has_initial_subject_marker(s))
    return hits / len(sentences)


def particle_distribution_entropy(text: str) -> Tuple[float, float]:
    """Shannon entropy of particle distribution (は/が/を/に/で/と/も).

    Returns (entropy, max_possible_entropy).
    """
    body = _strip_headings(text)
    counts = _collect_particle_counts(body)
    total = sum(counts.values())
    if total < 10:
        return (0.0, 0.0)
    max_entropy = math.log2(len(_TARGET_PARTICLES))
    entropy = 0.0
    for particle in _TARGET_PARTICLES:
        freq = counts.get(particle, 0)
        if freq > 0:
            p = freq / total
            entropy -= p * math.log2(p)
    return (round(entropy, 4), round(max_entropy, 4))


def script_ratio(text: str) -> Tuple[float, float, float]:
    """Ratio of hiragana / katakana / kanji characters.

    Returns (hiragana_ratio, katakana_ratio, kanji_ratio).
    """
    body = _strip_headings(text)
    hiragana = len(_HIRAGANA.findall(body))
    katakana = len(_KATAKANA.findall(body))
    kanji = len(_KANJI.findall(body))
    total = hiragana + katakana + kanji
    if total < 20:
        return (0.0, 0.0, 0.0)
    return (
        round(hiragana / total, 4),
        round(katakana / total, 4),
        round(kanji / total, 4),
    )


def pos_bigram_monotonicity(text: str) -> float:
    """POS-bigram monotonicity score.

    Sudachiが利用可能な場合は品詞タグbigramのユニーク率を返す。
    利用不可の場合は文字種遷移ベースの近似値へフォールバックする。
    低い値ほど単調（AIらしい）傾向。
    """
    body = _strip_headings(text)
    if len(body) < 30:
        return 0.0
    sudachi_score = _pos_bigram_monotonicity_sudachi(body)
    if sudachi_score is not None:
        return sudachi_score
    tags: List[str] = []
    for ch in body:
        if _HIRAGANA.match(ch):
            tags.append("H")
        elif _KATAKANA.match(ch):
            tags.append("K")
        elif _KANJI.match(ch):
            tags.append("J")
        elif ch.isascii() and ch.isalpha():
            tags.append("A")
        else:
            tags.append("O")
    if len(tags) < 10:
        return 0.0
    bigrams = [f"{tags[i]}{tags[i+1]}" for i in range(len(tags) - 1)]
    unique = len(set(bigrams))
    possible = min(len(bigrams), 25)  # 5 tag types -> 25 possible bigrams
    return round(unique / possible, 4) if possible > 0 else 0.0


# ---------------------------------------------------------------------------
# Lexical diversity metrics (R5-T07)
# ---------------------------------------------------------------------------

_MTLD_TTR_THRESHOLD = 0.72
_HDD_SAMPLE_SIZE = 42
_CONTENT_POS_PREFIXES = ("名詞", "動詞", "形容詞", "副詞")
_VOCAB_REPEAT_MIN = 3


def _extract_lemmas(text: str) -> List[str]:
    """Extract content-word lemmas using Sudachi, fallback to simple tokens."""
    tokens = _tokenize_sudachi(text)
    if tokens:
        lemmas: List[str] = []
        for m in tokens:
            pos = m.part_of_speech()
            if not pos:
                continue
            if not pos[0].startswith(_CONTENT_POS_PREFIXES):
                continue
            lemma = m.dictionary_form()
            if lemma and len(lemma) >= 2:
                lemmas.append(lemma)
        if lemmas:
            return lemmas
    # Fallback: split by punctuation/spaces, keep tokens >= 2 chars
    raw = re.sub(r"[。！？!?\s、,\n\r\t]+", " ", _strip_headings(text))
    return [t for t in raw.split() if len(t) >= 2]


def compute_mtld(text: str) -> float:
    """Measure of Textual Lexical Diversity (MTLD).

    Computes forward and backward MTLD and returns the harmonic mean.
    Higher values = more diverse vocabulary. Typical human range: 50-120+.
    """
    lemmas = _extract_lemmas(text)
    if len(lemmas) < 10:
        return 0.0
    forward = _mtld_one_direction(lemmas)
    backward = _mtld_one_direction(list(reversed(lemmas)))
    if forward <= 0 and backward <= 0:
        return 0.0
    if forward <= 0:
        return backward
    if backward <= 0:
        return forward
    return round(2.0 * forward * backward / (forward + backward), 2)


def _mtld_one_direction(lemmas: List[str]) -> float:
    """Single-direction MTLD computation."""
    factor_count = 0.0
    factor_start = 0
    types: set = set()
    for i, lemma in enumerate(lemmas):
        types.add(lemma)
        ttr = len(types) / (i - factor_start + 1)
        if ttr <= _MTLD_TTR_THRESHOLD:
            factor_count += 1.0
            factor_start = i + 1
            types = set()
    # Partial factor
    remaining = len(lemmas) - factor_start
    if remaining > 0 and factor_count > 0:
        current_ttr = len(types) / remaining
        if current_ttr < 1.0:
            factor_count += (1.0 - current_ttr) / (1.0 - _MTLD_TTR_THRESHOLD)
    if factor_count <= 0:
        return float(len(lemmas))
    return len(lemmas) / factor_count


def compute_hd_d(text: str, sample_size: int = _HDD_SAMPLE_SIZE) -> float:
    """Hypergeometric Distribution D (HD-D) lexical diversity.

    Text-length robust alternative to TTR. Returns 0.0-1.0.
    Higher = more diverse.
    """
    lemmas = _extract_lemmas(text)
    n = len(lemmas)
    if n < sample_size or n < 10:
        return 0.0
    freq = Counter(lemmas)
    contribution = 0.0
    for lemma, fi in freq.items():
        # P(lemma appears in sample) = 1 - C(n-fi, sample) / C(n, sample)
        # Use log to avoid overflow
        p_not_in = _hypergeom_log_prob(n, fi, sample_size)
        contribution += (1.0 - p_not_in)
    hdd = contribution / sample_size
    return round(min(1.0, max(0.0, hdd)), 4)


def _hypergeom_log_prob(n: int, fi: int, s: int) -> float:
    """P(type NOT in sample) = C(n-fi, s) / C(n, s) using log-space."""
    if fi >= n or s > n - fi:
        return 0.0
    log_p = 0.0
    for j in range(s):
        log_p += math.log(max(1, n - fi - j)) - math.log(max(1, n - j))
    return math.exp(log_p)


def detect_vocab_repetition(text: str, min_count: int = _VOCAB_REPEAT_MIN) -> List[str]:
    """Detect content lemmas repeated >= min_count times (R5-T08)."""
    lemmas = _extract_lemmas(text)
    if len(lemmas) < 10:
        return []
    freq = Counter(lemmas)
    return sorted([lemma for lemma, cnt in freq.items() if cnt >= min_count],
                  key=lambda x: -freq[x])


# ---------------------------------------------------------------------------
# R14: Fine-grained sentence ending entropy (morpheme-level)
# ---------------------------------------------------------------------------

def sentence_ending_fine_entropy(text: str) -> float:
    """Sudachi形態素ベースの文末fine-grainedエントロピー (R14).

    各文の末尾3形態素の表層形を連結してパターン化し、
    そのパターン分布のShannon entropyを返す。
    「です」「のです」「なのです」「ている」「のだ」等を区別する。
    Sudachi不可時は正規表現ベースのフォールバックを使用。
    高い値ほど文末が多様（人間的）。
    """
    sentences = _split_sentences(text)
    if len(sentences) < 4:
        return 0.0

    patterns: List[str] = []
    for s in sentences:
        pattern = _extract_ending_morpheme_pattern(s)
        if pattern:
            patterns.append(pattern)

    if len(patterns) < 4:
        return 0.0

    counts: Counter = Counter(patterns)
    total = sum(counts.values())
    entropy = 0.0
    for cnt in counts.values():
        if cnt > 0:
            p = cnt / total
            entropy -= p * math.log2(p)
    return round(entropy, 4)


def _extract_ending_morpheme_pattern(sentence: str) -> str:
    """文末の形態素パターンを抽出する（Sudachi優先、regexフォールバック）。"""
    s = sentence.strip().rstrip("。！？!?").strip()
    if not s:
        return ""

    # Sudachi available: 末尾3形態素の表層形を連結
    tokens = _tokenize_sudachi(s)
    if tokens:
        # 補助記号・空白を除外した末尾3形態素
        content_tokens = [
            m for m in tokens
            if m.part_of_speech() and m.part_of_speech()[0] not in ("補助記号", "空白")
        ]
        if content_tokens:
            tail = content_tokens[-3:] if len(content_tokens) >= 3 else content_tokens
            return "+".join(m.surface() for m in tail)

    # Regex fallback: 末尾のひらがな/カタカナ/漢字パターンを抽出
    m = re.search(r"([ぁ-んァ-ヶー一-龯]{1,8})$", s)
    return m.group(1) if m else s[-4:]


# ---------------------------------------------------------------------------
# R14: Sentence opening pattern entropy
# ---------------------------------------------------------------------------

def sentence_opening_entropy(text: str) -> float:
    """文頭パターンのShannon entropy (R14).

    各文の冒頭2形態素の品詞パターンを分類し、エントロピーを返す。
    AI文は「名詞+は」の主語開始が均一になりがち。
    高い値ほど文頭が多様（人間的）。
    """
    sentences = _split_sentences(text)
    if len(sentences) < 4:
        return 0.0

    patterns: List[str] = []
    for s in sentences:
        pattern = _extract_opening_pattern(s)
        if pattern:
            patterns.append(pattern)

    if len(patterns) < 4:
        return 0.0

    counts: Counter = Counter(patterns)
    total = sum(counts.values())
    entropy = 0.0
    for cnt in counts.values():
        if cnt > 0:
            p = cnt / total
            entropy -= p * math.log2(p)
    return round(entropy, 4)


def _extract_opening_pattern(sentence: str) -> str:
    """文頭の品詞パターンを抽出する（Sudachi優先、regexフォールバック）。"""
    s = sentence.strip()
    if not s:
        return ""

    # Sudachi available: 冒頭2形態素の品詞大分類を連結
    tokens = _tokenize_sudachi(s)
    if tokens:
        content_tokens = [
            m for m in tokens
            if m.part_of_speech() and m.part_of_speech()[0] not in ("補助記号", "空白")
        ]
        if len(content_tokens) >= 2:
            pos0 = content_tokens[0].part_of_speech()
            pos1 = content_tokens[1].part_of_speech()
            tag0 = f"{pos0[0]}:{pos0[1]}" if len(pos0) > 1 else pos0[0]
            tag1 = f"{pos1[0]}:{pos1[1]}" if len(pos1) > 1 else pos1[0]
            return f"{tag0}>{tag1}"
        elif content_tokens:
            pos0 = content_tokens[0].part_of_speech()
            return f"{pos0[0]}:{pos0[1]}" if len(pos0) > 1 else pos0[0]

    # Regex fallback: 文頭の文字種パターン
    if _CONJUNCTION_PATTERN.match(s):
        return "conjunction"
    if _SUBJECT_MARKER.match(s):
        return "subject+particle"
    if re.match(r"[ァ-ヶー]", s):
        return "katakana_start"
    if re.match(r"[一-龯]", s):
        return "kanji_start"
    if re.match(r"[ぁ-ん]", s):
        return "hiragana_start"
    return "other"


# ---------------------------------------------------------------------------
# R14: Comma position CV (読点位置の変動係数)
# ---------------------------------------------------------------------------

def comma_position_cv(text: str) -> float:
    """各文内の読点の相対位置（0.0〜1.0）の変動係数 (R14).

    人間は読点位置にばらつきがある（CV 0.3〜0.7）。
    AIは均等間隔に打つ傾向がある（CV < 0.2）。
    高い値ほど読点位置が多様（人間的）。
    """
    sentences = _split_sentences(text)
    if len(sentences) < 4:
        return 0.0

    positions: List[float] = []
    for s in sentences:
        s_clean = s.strip()
        if len(s_clean) < 6:
            continue
        for i, ch in enumerate(s_clean):
            if ch == "、":
                # 相対位置 (0.0 = 文頭, 1.0 = 文末)
                positions.append(i / max(1, len(s_clean) - 1))

    if len(positions) < 4:
        return 0.0

    mean = sum(positions) / len(positions)
    if mean < 0.01:
        return 0.0
    variance = sum((p - mean) ** 2 for p in positions) / len(positions)
    cv = (variance ** 0.5) / mean
    return round(cv, 4)


# ---------------------------------------------------------------------------
# Nominalization rate (R5-T10)
# ---------------------------------------------------------------------------

_NOMINALIZATION_SUFFIX_RE = re.compile(r"(?:化|性|こと|もの|ところ)$")
_NOMINALIZATION_PATTERN_RE = re.compile(
    r"(?:の実現|の実施|の推進|の導入|の活用|の改善|の向上|の確保|の促進|における|ことが|ものである)"
)


def compute_nominalization_rate(text: str) -> float:
    """Ratio of nominalization signals to total content tokens (R5-T10).

    Uses Sudachi POS when available (サ変可能名詞 + 形式名詞 + 接尾辞).
    Falls back to regex pattern matching.
    Returns 0.0-1.0. Higher = more nominalized (AI tendency per PNAS 2025).
    """
    body = _strip_headings(text)
    if len(body) < 50:
        return 0.0

    sudachi_rate = _nominalization_rate_sudachi(body)
    if sudachi_rate is not None:
        return sudachi_rate

    # Regex fallback
    sentences = _split_sentences(text)
    if len(sentences) < 3:
        return 0.0
    total_chars = max(1, sum(len(s) for s in sentences))
    suffix_hits = sum(len(_NOMINALIZATION_SUFFIX_RE.findall(s)) for s in sentences)
    pattern_hits = sum(len(_NOMINALIZATION_PATTERN_RE.findall(s)) for s in sentences)
    # Normalize: each hit ~= 2 chars of nominalization signal
    signal_chars = (suffix_hits + pattern_hits) * 2
    return round(min(1.0, signal_chars / total_chars), 4)


def _nominalization_rate_sudachi(text: str) -> Optional[float]:
    """Sudachi-based nominalization rate."""
    tokenizer_obj, _ = _get_sudachi_components()
    if tokenizer_obj is None:
        return None
    tokens = _tokenize_sudachi(text)
    if not tokens or len(tokens) < 10:
        return None
    content_count = 0
    nom_count = 0
    for m in tokens:
        pos = m.part_of_speech()
        if not pos:
            continue
        major = pos[0]
        sub = pos[1] if len(pos) > 1 else ""
        # Count content tokens
        if major in ("名詞", "動詞", "形容詞", "副詞"):
            content_count += 1
        # Nominalization signals
        if major == "名詞" and sub in ("普通名詞",):
            sub2 = pos[2] if len(pos) > 2 else ""
            if sub2 in ("サ変可能", "形状詞可能", "サ変形状詞可能"):
                nom_count += 1
        if major == "名詞" and sub == "形式名詞":
            nom_count += 1
        if major == "接尾辞" and sub in ("名詞的",):
            surface = m.surface()
            if surface in ("化", "性", "的"):
                nom_count += 1
    if content_count < 5:
        return None
    return round(nom_count / content_count, 4)


# ---------------------------------------------------------------------------
# Analyzer class
# ---------------------------------------------------------------------------

# Flat-zone thresholds (empirically tuned for Japanese blog text)
_FLAT_ZONES = {
    "sentence_length_cv": (0.10, "文長の変動が小さすぎる（機械的なリズム）"),
    "paragraph_length_cv": (0.10, "段落長の変動が小さすぎる"),
    "conjunction_repetition_rate_high": (0.50, "段落冒頭接続詞が多すぎる"),
    "subject_explicit_rate_high": (0.55, "主語明示率が高すぎる（英語直訳調）"),
    "particle_entropy_low": (1.8, "助詞分布が偏っている"),
    "pos_bigram_monotonicity_low": (0.40, "文字種パターンが単調"),
    "mtld_low": (40.0, "語彙多様性が低い（同じ語の繰り返し）"),
    "nominalization_rate_high": (0.25, "名詞化率が高い（抽象的・AI的文体）"),
    "sentence_ending_entropy_low": (1.5, "文末パターンが単調（です/ます偏重）"),
    # R14: パープレキシティ3指標
    "sentence_ending_fine_entropy_low": (2.0, "文末形態素パターンが単調（形態素レベルで同じ語尾の繰り返し）"),
    "sentence_opening_entropy_low": (1.5, "文頭パターンが単調（名詞+は の主語開始が均一）"),
    "comma_position_cv_low": (0.25, "読点位置が均一すぎる（AIの等間隔打ち傾向）"),
}


def _get_runtime_fingerprint_thresholds() -> Dict[str, float]:
    """Load active fingerprint thresholds from config; fallback to module defaults."""
    try:
        from core.app_config import get_active_fingerprint_thresholds

        runtime = get_active_fingerprint_thresholds()
    except Exception:
        runtime = {}
    if not isinstance(runtime, dict):
        runtime = {}
    out: Dict[str, float] = {}
    for key in (
        "sentence_length_cv",
        "paragraph_length_cv",
        "conjunction_repetition_rate_high",
        "subject_explicit_rate_high",
        "particle_entropy_low",
        "pos_bigram_monotonicity_low",
        "mtld_low",
        "nominalization_rate_high",
    ):
        default_val = _FLAT_ZONES[key][0]
        try:
            out[key] = float(runtime.get(key, default_val))
        except Exception:
            out[key] = float(default_val)
    return out


def _get_candidate_penalty_weights() -> Tuple[float, float, float]:
    """Return overlap/paragraph/flat penalties for candidate selection."""
    overlap_w = 0.10
    para_w = 0.10
    flat_w = 0.03

    try:
        from core.app_config import get_hlcv2_config, get_fingerprint_threshold_presets

        cfg = get_hlcv2_config()
        presets = get_fingerprint_threshold_presets()
        active = str((presets or {}).get("active_preset", "standard"))
    except Exception:
        cfg = {}
        active = "standard"

    if active in ("strict", "superhuman"):
        overlap_w = 0.14
        para_w = 0.14
        flat_w = 0.035
    if active == "superhuman":
        overlap_w = 0.16
        para_w = 0.18
        flat_w = 0.04

    if isinstance(cfg, dict):
        try:
            overlap_w = float(cfg.get("overlap_penalty_weight", overlap_w))
        except Exception:
            pass
        try:
            para_w = float(cfg.get("paragraph_similarity_penalty_weight", para_w))
        except Exception:
            pass
        try:
            flat_w = float(cfg.get("flat_flag_penalty_weight", flat_w))
        except Exception:
            pass

    return (
        max(0.0, min(0.40, overlap_w)),
        max(0.0, min(0.40, para_w)),
        max(0.0, min(0.15, flat_w)),
    )


class FingerprintAnalyzer:
    """Compute all fingerprint metrics and detect flat zones."""

    def analyze(self, text: str, focus: str = "") -> FingerprintReport:
        """Compute all fingerprint metrics.

        Args:
            text: The text to analyze.
            focus: Writing focus (e.g. 'explanation', 'analysis'). R9-T11 uses
                   this to raise the sentence_length_cv flat-zone threshold.
        """
        if not text or len(text.strip()) < 100:
            return FingerprintReport()

        sl_cv = sentence_length_cv(text)
        pl_cv = paragraph_length_cv(text)
        conj_rate = conjunction_repetition_rate(text)
        subj_rate = subject_explicit_rate(text)
        p_entropy, p_max = particle_distribution_entropy(text)
        h_ratio, k_ratio, j_ratio = script_ratio(text)
        bigram_mono = pos_bigram_monotonicity(text)
        mtld_val = compute_mtld(text)
        hdd_val = compute_hd_d(text)
        nom_rate = compute_nominalization_rate(text)
        se_entropy = sentence_ending_entropy(text)
        # Enhanced morphological fingerprinting (kotomegane)
        morph_ngram_entropy = morphological_ngram_entropy(text)
        morph_diversity = morphological_pattern_diversity(text)
        syntactic_complexity = syntactic_complexity_fingerprint(text)
        
        # R14: パープレキシティ3指標
        se_fine_entropy = sentence_ending_fine_entropy(text)
        so_entropy = sentence_opening_entropy(text)
        comma_cv = comma_position_cv(text)
        vocab_reps = detect_vocab_repetition(text)

        flags: List[str] = []
        hints: List[str] = []

        runtime_thresholds = _get_runtime_fingerprint_thresholds()

        # R9-T11: 解説/分析モードでは sentence_length_cv しきい値を引き上げ
        sl_cv_threshold = runtime_thresholds.get("sentence_length_cv", _FLAT_ZONES["sentence_length_cv"][0])
        if focus in ("explanation", "analysis"):
            sl_cv_threshold = max(0.35, sl_cv_threshold)
        if sl_cv < sl_cv_threshold:
            flags.append("sentence_length_cv_flat")
            hints.append(_FLAT_ZONES["sentence_length_cv"][1])
        if pl_cv < runtime_thresholds.get("paragraph_length_cv", _FLAT_ZONES["paragraph_length_cv"][0]):
            flags.append("paragraph_length_cv_flat")
            hints.append(_FLAT_ZONES["paragraph_length_cv"][1])
        if conj_rate > runtime_thresholds.get(
            "conjunction_repetition_rate_high", _FLAT_ZONES["conjunction_repetition_rate_high"][0]
        ):
            flags.append("conjunction_rate_high")
            hints.append(_FLAT_ZONES["conjunction_repetition_rate_high"][1])
        if subj_rate > runtime_thresholds.get(
            "subject_explicit_rate_high", _FLAT_ZONES["subject_explicit_rate_high"][0]
        ):
            flags.append("subject_explicit_high")
            hints.append(_FLAT_ZONES["subject_explicit_rate_high"][1])
            hints.extend(_detect_initial_subject_repetition(text))
        if p_max > 0 and p_entropy < runtime_thresholds.get("particle_entropy_low", _FLAT_ZONES["particle_entropy_low"][0]):
            flags.append("particle_entropy_low")
            hints.append(_FLAT_ZONES["particle_entropy_low"][1])
        if bigram_mono > 0 and bigram_mono < runtime_thresholds.get(
            "pos_bigram_monotonicity_low", _FLAT_ZONES["pos_bigram_monotonicity_low"][0]
        ):
            flags.append("bigram_mono_low")
            hints.append(_FLAT_ZONES["pos_bigram_monotonicity_low"][1])
        if mtld_val > 0 and mtld_val < runtime_thresholds.get("mtld_low", _FLAT_ZONES["mtld_low"][0]):
            flags.append("mtld_low")
            hints.append(_FLAT_ZONES["mtld_low"][1])
        if vocab_reps:
            flags.append("vocab_repetition")
            hints.append(f"語彙反復: {', '.join(vocab_reps[:5])} が頻出")
        if nom_rate > runtime_thresholds.get("nominalization_rate_high", _FLAT_ZONES["nominalization_rate_high"][0]):
            flags.append("nominalization_rate_high")
            hints.append(_FLAT_ZONES["nominalization_rate_high"][1])
        if se_entropy > 0 and se_entropy < _FLAT_ZONES["sentence_ending_entropy_low"][0]:
            flags.append("sentence_ending_entropy_low")
            hints.append(_FLAT_ZONES["sentence_ending_entropy_low"][1])
        # Enhanced morphological flat zones (kotomegane)
        if morph_ngram_entropy > 0 and morph_ngram_entropy < 2.5:
            flags.append("morphological_ngram_entropy_low")
            hints.append("形態素n-gramパターンが単調（AI的な均一性）")
        if morph_diversity.get("pos_sequence_entropy", 0) < 1.8:
            flags.append("pos_sequence_entropy_low")
            hints.append("品詞系列が単調（構造的予測可能性が高い）")
        if morph_diversity.get("inflection_entropy", 0) < 1.2:
            flags.append("inflection_entropy_low")
            hints.append("活用形パターンが単調（動詞活用の多様性不足）")
        if syntactic_complexity.get("dependency_depth_avg", 0) < 1.5:
            flags.append("syntactic_complexity_low")
            hints.append("統語構造が単純すぎる（依存深度が浅い）")
        
        # R14: パープレキシティ3指標のflat zone検知
        if se_fine_entropy > 0 and se_fine_entropy < _FLAT_ZONES["sentence_ending_fine_entropy_low"][0]:
            flags.append("sentence_ending_fine_entropy_low")
            hints.append(_FLAT_ZONES["sentence_ending_fine_entropy_low"][1])
        if so_entropy > 0 and so_entropy < _FLAT_ZONES["sentence_opening_entropy_low"][0]:
            flags.append("sentence_opening_entropy_low")
            hints.append(_FLAT_ZONES["sentence_opening_entropy_low"][1])
        if comma_cv > 0 and comma_cv < _FLAT_ZONES["comma_position_cv_low"][0]:
            flags.append("comma_position_cv_low")
            hints.append(_FLAT_ZONES["comma_position_cv_low"][1])
        ending_rep_hints = detect_ending_repetition(text)
        if ending_rep_hints:
            flags.append("ending_repetition")
            hints.extend(ending_rep_hints)
        comma_hints = detect_comma_overuse(text)
        if comma_hints:
            flags.append("comma_overuse")
            hints.extend(comma_hints)
        # R9-T12: 解説/分析モードのみ抽象語同義反復を検知
        if focus in ("explanation", "analysis"):
            tautology_hints = detect_abstract_tautology(text)
            if tautology_hints:
                flags.append("abstract_tautology")
                hints.extend(tautology_hints)

        # Overall unpredictability score: 0.0 (fully predictable) .. 1.0 (human-like)
        # Weighted combination of normalized sub-scores (Enhanced with morphological features)
        unpredictability = _compute_unpredictability_enhanced(
            sl_cv, pl_cv, conj_rate, subj_rate, p_entropy, p_max, bigram_mono,
            se_fine_entropy, so_entropy, comma_cv,
            morph_ngram_entropy, morph_diversity, syntactic_complexity,
        )

        return FingerprintReport(
            sentence_length_cv=round(sl_cv, 4),
            paragraph_length_cv=round(pl_cv, 4),
            conjunction_repetition_rate=round(conj_rate, 4),
            subject_explicit_rate=round(subj_rate, 4),
            particle_entropy=p_entropy,
            particle_max_entropy=p_max,
            script_ratio_hiragana=h_ratio,
            script_ratio_katakana=k_ratio,
            script_ratio_kanji=j_ratio,
            pos_bigram_monotonicity=bigram_mono,
            mtld=mtld_val,
            hd_d=hdd_val,
            nominalization_rate=nom_rate,
            sentence_ending_entropy=se_entropy,
            sentence_ending_fine_entropy=se_fine_entropy,
            sentence_opening_entropy=so_entropy,
            comma_position_cv=comma_cv,
            vocab_repetition_lemmas=vocab_reps,
            flat_zone_flags=flags,
            correction_hints=hints,
            overall_unpredictability=round(unpredictability, 4),
            # Enhanced morphological metrics (kotomegane)
            morphological_ngram_entropy=round(morph_ngram_entropy, 4),
            morphological_diversity=morph_diversity,
            syntactic_complexity=syntactic_complexity,
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_sudachi_components():
    if not SUDACHI_AVAILABLE or sudachi_dictionary is None or sudachi_tokenizer is None:
        return None, None
    try:
        tokenizer_obj = sudachi_dictionary.Dictionary().create()
        split_mode = sudachi_tokenizer.Tokenizer.SplitMode.B
        return tokenizer_obj, split_mode
    except Exception:  # pragma: no cover - defensive fallback
        return None, None


def _tokenize_sudachi(text: str):
    tokenizer_obj, split_mode = _get_sudachi_components()
    if tokenizer_obj is None:
        return []
    try:
        return list(tokenizer_obj.tokenize(text or "", split_mode))
    except Exception:  # pragma: no cover - defensive fallback
        return []


def _particle_count_from_sudachi(text: str) -> Counter:
    counts: Counter = Counter()
    for morpheme in _tokenize_sudachi(text):
        pos = morpheme.part_of_speech()
        pos_major = pos[0] if pos else ""
        if pos_major != "助詞":
            continue
        surface = morpheme.surface()
        if surface in _TARGET_PARTICLES:
            counts[surface] += 1
    return counts


def _collect_particle_counts(text: str) -> Counter:
    sudachi_counts = _particle_count_from_sudachi(text)
    if sum(sudachi_counts.values()) > 0:
        return sudachi_counts
    counts = Counter()
    for ch in text:
        if ch in _TARGET_PARTICLES:
            counts[ch] += 1
    return counts


def _is_subject_noun_morpheme(morpheme) -> bool:
    pos = morpheme.part_of_speech()
    if not pos:
        return False
    pos_major = pos[0]
    if pos_major != "名詞":
        return False
    pos_sub = pos[1] if len(pos) > 1 else ""
    if pos_sub in {"非自立可能", "数詞"}:
        return False
    return bool(morpheme.surface().strip())


def _normalize_sentence_for_subject_scan(sentence: str) -> str:
    normalized = re.sub(r"\s+", "", str(sentence or "")).strip()
    return normalized.lstrip("「『（(").strip()


def _has_initial_subject_marker(sentence: str) -> bool:
    normalized = _normalize_sentence_for_subject_scan(sentence)
    if not normalized or _CONJUNCTION_PATTERN.match(normalized):
        return False
    if _INITIAL_SUBJECT_PRONOUN.match(normalized):
        return True
    return bool(_INITIAL_SUBJECT_NOUN.match(normalized))


def _leading_content_morphemes(sentence: str, limit: int = 3) -> List[Any]:
    content: List[Any] = []
    for morpheme in _tokenize_sudachi(sentence):
        pos = morpheme.part_of_speech()
        pos_major = pos[0] if pos else ""
        if pos_major in {"補助記号", "空白"}:
            continue
        content.append(morpheme)
        if len(content) >= limit:
            break
    return content


def _has_initial_subject_marker_sudachi(sentence: str) -> bool:
    content = _leading_content_morphemes(sentence, limit=3)
    if len(content) < 2:
        return False
    first = content[0]
    first_surface = _normalize_sentence_for_subject_scan(first.surface())
    if not first_surface or _CONJUNCTION_PATTERN.match(first_surface):
        return False
    second = content[1]
    second_pos = second.part_of_speech()
    if not second_pos or second_pos[0] != "助詞":
        return False
    return _is_subject_noun_morpheme(first) and second.surface() in _TARGET_SUBJECT_PARTICLES


def _detect_initial_subject_repetition(
    text: str,
    *,
    max_consecutive: int = 2,
) -> List[str]:
    hints: List[str] = []
    for paragraph in _split_paragraphs(text):
        run_len = 0
        for sentence in _split_sentences(paragraph):
            if _has_initial_subject_marker(sentence):
                run_len += 1
            else:
                if run_len > max_consecutive:
                    hints.append(
                        f"文頭主語開始が{run_len}文連続（最大{max_consecutive}文推奨）"
                    )
                run_len = 0
        if run_len > max_consecutive:
            hints.append(
                f"文頭主語開始が{run_len}文連続（最大{max_consecutive}文推奨）"
            )
    return hints


def _subject_explicit_rate_sudachi(sentences: Sequence[str]) -> Optional[float]:
    tokenizer_obj, _ = _get_sudachi_components()
    if tokenizer_obj is None:
        return None
    valid = 0
    hits = 0
    for sentence in sentences:
        tokens = _tokenize_sudachi(sentence)
        if not tokens:
            continue
        valid += 1
        if _has_initial_subject_marker_sudachi(sentence):
            hits += 1
    if valid < 3:
        return None
    return hits / valid


def _pos_bigram_monotonicity_sudachi(text: str) -> Optional[float]:
    tokenizer_obj, _ = _get_sudachi_components()
    if tokenizer_obj is None:
        return None
    pos_tags: List[str] = []
    for morpheme in _tokenize_sudachi(text):
        pos = morpheme.part_of_speech()
        if not pos:
            continue
        pos_major = pos[0]
        if pos_major in {"補助記号", "空白"}:
            continue
        pos_sub = pos[1] if len(pos) > 1 else "*"
        pos_tags.append(f"{pos_major}:{pos_sub}")
    if len(pos_tags) < 10:
        return None
    bigrams = [f"{pos_tags[i]}>{pos_tags[i+1]}" for i in range(len(pos_tags) - 1)]
    unique_ratio = len(set(bigrams)) / max(1, len(bigrams))
    return round(unique_ratio, 4)


def _split_sentences(text: str) -> List[str]:
    body = _strip_headings(text)
    parts = [s.strip() for s in _TERMINAL_PUNCT.split(body) if s.strip()]
    return [p for p in parts if len(p) >= 4]


def _split_paragraphs(text: str) -> List[str]:
    paragraphs = _PARAGRAPH_SEP.split(text or "")
    result: List[str] = []
    for p in paragraphs:
        stripped = p.strip()
        if not stripped:
            continue
        if _HEADING_LINE.match(stripped) and "\n" not in stripped.strip():
            continue
        if _LIST_LINE.match(stripped):
            continue
        result.append(stripped)
    return result


def _count_sentences(paragraph: str) -> int:
    return len(_TERMINAL_PUNCT.findall(paragraph))


def _strip_headings(text: str) -> str:
    lines = (text or "").splitlines()
    return "\n".join(ln for ln in lines if not _HEADING_LINE.match(ln.strip()))


def _sigmoid_score(value: float, center: float, width: float) -> float:
    """Bell-curve-ish score: 1.0 at center, drops toward 0 away from it."""
    if width <= 0:
        return 0.5
    z = (value - center) / width
    return math.exp(-0.5 * z * z)


def _compute_unpredictability_enhanced(
    sl_cv: float,
    pl_cv: float,
    conj_rate: float,
    subj_rate: float,
    p_entropy: float,
    p_max: float,
    bigram_mono: float,
    se_fine_entropy: float = 0.0,
    so_entropy: float = 0.0,
    comma_cv: float = 0.0,
    morph_ngram_entropy: float = 0.0,
    morph_diversity: Dict[str, float] = None,
    syntactic_complexity: Dict[str, float] = None,
) -> float:
    """Enhanced unpredictability score with morphological fingerprinting.
    
    Integrates traditional metrics with advanced morphological analysis
    for more sophisticated AI-text detection evasion.
    """
    if morph_diversity is None:
        morph_diversity = {}
    if syntactic_complexity is None:
        syntactic_complexity = {}
        
    scores: List[float] = []

    # Traditional metrics (R14)
    scores.append(_sigmoid_score(sl_cv, center=0.4, width=0.25))
    scores.append(_sigmoid_score(pl_cv, center=0.35, width=0.2))
    scores.append(max(0.0, 1.0 - conj_rate / 0.5))
    
    subj_score = 1.0 - min(1.0, abs(subj_rate - 0.25) / 0.30)
    scores.append(max(0.0, subj_score))
    
    if p_max > 0:
        scores.append(min(1.0, p_entropy / p_max))
    else:
        scores.append(0.5)
        
    scores.append(min(1.0, bigram_mono / 0.7))

    # R14 fine-grained metrics
    if se_fine_entropy > 0:
        scores.append(min(1.0, se_fine_entropy / 3.5))
    else:
        scores.append(0.5)
        
    if so_entropy > 0:
        scores.append(min(1.0, so_entropy / 3.0))
    else:
        scores.append(0.5)
        
    scores.append(_sigmoid_score(comma_cv, center=0.45, width=0.25))
    
    # Enhanced morphological metrics (kotomegane)
    # Morphological n-gram entropy: higher is better
    if morph_ngram_entropy > 0:
        scores.append(min(1.0, morph_ngram_entropy / 4.0))
    else:
        scores.append(0.5)
        
    # POS sequence entropy: higher is better
    pos_seq_entropy = morph_diversity.get("pos_sequence_entropy", 0)
    if pos_seq_entropy > 0:
        scores.append(min(1.0, pos_seq_entropy / 3.0))
    else:
        scores.append(0.5)
        
    # Inflection entropy: higher is better
    inf_entropy = morph_diversity.get("inflection_entropy", 0)
    if inf_entropy > 0:
        scores.append(min(1.0, inf_entropy / 2.5))
    else:
        scores.append(0.5)
        
    # Syntactic complexity: moderate depth is human-like
    dep_depth = syntactic_complexity.get("dependency_depth_avg", 0)
    if dep_depth > 0:
        # Optimal range: 2.0-4.0 (human-like complexity)
        complexity_score = _sigmoid_score(dep_depth, center=3.0, width=2.0)
        scores.append(complexity_score)
    else:
        scores.append(0.5)
        
    # NOTE:
    # pos_diversity_index is reported in syntactic_complexity telemetry, but is
    # intentionally excluded from the enhanced aggregate score until calibrated.
    # Keep the aggregate vector length stable to avoid accidental score drift.
    #
    # Enhanced weights (13 metrics total)
    weights = [
        0.10,  # sentence_length_cv
        0.07,  # paragraph_length_cv
        0.08,  # conjunction_rate
        0.08,  # subject_explicit_rate
        0.10,  # particle_entropy
        0.08,  # bigram_monotonicity
        0.12,  # sentence_ending_fine_entropy
        0.10,  # sentence_opening_entropy
        0.08,  # comma_position_cv
        0.07,  # morphological_ngram_entropy
        0.06,  # pos_sequence_entropy
        0.04,  # inflection_entropy
        0.02,  # syntactic_complexity
    ]
    
    total = sum(s * w for s, w in zip(scores, weights))
    return min(1.0, max(0.0, total))


def _compute_unpredictability(
    sl_cv: float,
    pl_cv: float,
    conj_rate: float,
    subj_rate: float,
    p_entropy: float,
    p_max: float,
    bigram_mono: float,
    se_fine_entropy: float = 0.0,
    so_entropy: float = 0.0,
    comma_cv: float = 0.0,
) -> float:
    """Legacy unpredictability computation (R14)."""
    scores: List[float] = []

    # sentence length CV: 0.3~0.7 is human-like
    scores.append(_sigmoid_score(sl_cv, center=0.4, width=0.25))

    # paragraph length CV: 0.2~0.6 is human-like
    scores.append(_sigmoid_score(pl_cv, center=0.35, width=0.2))

    # conjunction rate: low is better (< 0.3)
    scores.append(max(0.0, 1.0 - conj_rate / 0.5))

    # subject explicit rate: 0.15~0.35 is natural Japanese
    subj_score = 1.0 - min(1.0, abs(subj_rate - 0.25) / 0.30)
    scores.append(max(0.0, subj_score))

    # particle entropy: higher is better (more distributed)
    if p_max > 0:
        scores.append(min(1.0, p_entropy / p_max))
    else:
        scores.append(0.5)

    # bigram monotonicity: higher unique ratio = better
    scores.append(min(1.0, bigram_mono / 0.7))

    # R14: 文末形態素fine-grainedエントロピー (target: 2.5+, max ~4.0)
    if se_fine_entropy > 0:
        scores.append(min(1.0, se_fine_entropy / 3.5))
    else:
        scores.append(0.5)

    # R14: 文頭パターンエントロピー (target: 2.0+, max ~3.5)
    if so_entropy > 0:
        scores.append(min(1.0, so_entropy / 3.0))
    else:
        scores.append(0.5)

    # R14: 読点位置CV (target: 0.3~0.7)
    scores.append(_sigmoid_score(comma_cv, center=0.45, width=0.25))

    # Weighted average (R14: 9指標に拡張)
    weights = [0.12, 0.08, 0.10, 0.10, 0.12, 0.10, 0.15, 0.13, 0.10]
    total = sum(s * w for s, w in zip(scores, weights))
    return min(1.0, max(0.0, total))


# ---------------------------------------------------------------------------
# Advanced Morphological Fingerprinting (Enhanced for kotomegane)
# ---------------------------------------------------------------------------

def morphological_ngram_entropy(text: str, n: int = 2) -> float:
    """形態素n-gramのエントロピーを計算（高度な言語的指紋抽出）。
    
    Sudachi形態素解析を用いて、品詞・活用形・表層形の組み合わせパターンを分析。
    AIは均一な形態素パターンを生成する傾向がある。
    
    Args:
        text: 分析対象テキスト
        n: n-gramの長さ（デフォルト2）
        
    Returns:
        Shannon entropy (0.0~max_bits). 高い値ほど多様で人間的。
    """
    if not text or len(text) < 50:
        return 0.0
        
    tokens = _tokenize_sudachi(text)
    if not tokens or len(tokens) < n + 1:
        return 0.0
        
    # 形態素特徴の抽出（品詞+活用形+表層形の組み合わせ）
    morph_features: List[str] = []
    for token in tokens:
        pos = token.part_of_speech()
        if not pos or pos[0] in ("補助記号", "空白"):
            continue
            
        # 品詞大分類+活用形+表層形の最初3文字（長すぎる場合を避けるため）
        pos_major = pos[0]
        conj_form = pos[4] if len(pos) > 4 else "*"  # 活用形
        surface_prefix = token.surface()[:3] if len(token.surface()) >= 3 else token.surface()
        
        feature = f"{pos_major}:{conj_form}:{surface_prefix}"
        morph_features.append(feature)
    
    if len(morph_features) < n + 1:
        return 0.0
        
    # n-gram生成
    ngrams: List[str] = []
    for i in range(len(morph_features) - n + 1):
        ngram = "+".join(morph_features[i:i+n])
        ngrams.append(ngram)
        
    # エントロピー計算
    if not ngrams:
        return 0.0
        
    counts: Counter = Counter(ngrams)
    total = sum(counts.values())
    entropy = 0.0
    for cnt in counts.values():
        if cnt > 0:
            p = cnt / total
            entropy -= p * math.log2(p)
            
    return round(entropy, 4)


def morphological_pattern_diversity(text: str) -> Dict[str, float]:
    """形態素パターンの多様性を複数の側面から分析。
    
    Returns:
        Dict with keys:
        - pos_sequence_entropy: 品詞系列エントロピー
        - inflection_entropy: 活用形エントロピー  
        - morph_length_cv: 形態素長の変動係数
        - function_content_ratio: 機能語/内容語比率
    """
    if not text or len(text) < 50:
        return {"pos_sequence_entropy": 0.0, "inflection_entropy": 0.0, 
                "morph_length_cv": 0.0, "function_content_ratio": 0.0}
                
    tokens = _tokenize_sudachi(text)
    if not tokens or len(tokens) < 5:
        return {"pos_sequence_entropy": 0.0, "inflection_entropy": 0.0, 
                "morph_length_cv": 0.0, "function_content_ratio": 0.0}
    
    # 品詞系列エントロピー
    pos_sequence: List[str] = []
    inflection_types: List[str] = []
    morph_lengths: List[int] = []
    function_count = 0
    content_count = 0
    
    for token in tokens:
        pos = token.part_of_speech()
        if not pos:
            continue
            
        pos_major = pos[0]
        pos_sequence.append(pos_major)
        
        # 活用形（動詞、形容詞、助動詞）
        if pos_major in ("動詞", "形容詞", "助動詞"):
            conj_form = pos[4] if len(pos) > 4 else "*"
            inflection_types.append(conj_form)
            
        # 形態素長
        morph_lengths.append(len(token.surface()))
        
        # 機能語 vs 内容語
        if pos_major in ("名詞", "動詞", "形容詞", "副詞"):
            content_count += 1
        elif pos_major in ("助詞", "助動詞", "接続詞", "接頭辞", "接尾辞"):
            function_count += 1
    
    # 各指標の計算
    result: Dict[str, float] = {}
    
    # 品詞系列エントロピー（2-gram）
    if len(pos_sequence) >= 3:
        pos_bigrams = [f"{pos_sequence[i]}>{pos_sequence[i+1]}" 
                      for i in range(len(pos_sequence) - 1)]
        pos_counts: Counter = Counter(pos_bigrams)
        total = sum(pos_counts.values())
        entropy = 0.0
        for cnt in pos_counts.values():
            if cnt > 0:
                p = cnt / total
                entropy -= p * math.log2(p)
        result["pos_sequence_entropy"] = round(entropy, 4)
    else:
        result["pos_sequence_entropy"] = 0.0
        
    # 活用形エントロピー
    if inflection_types:
        inf_counts: Counter = Counter(inflection_types)
        total = sum(inf_counts.values())
        entropy = 0.0
        for cnt in inf_counts.values():
            if cnt > 0:
                p = cnt / total
                entropy -= p * math.log2(p)
        result["inflection_entropy"] = round(entropy, 4)
    else:
        result["inflection_entropy"] = 0.0
        
    # 形態素長の変動係数
    if morph_lengths and len(morph_lengths) >= 3:
        mean = sum(morph_lengths) / len(morph_lengths)
        if mean > 0:
            variance = sum((l - mean) ** 2 for l in morph_lengths) / len(morph_lengths)
            cv = (variance ** 0.5) / mean
            result["morph_length_cv"] = round(cv, 4)
        else:
            result["morph_length_cv"] = 0.0
    else:
        result["morph_length_cv"] = 0.0
        
    # 機能語/内容語比率
    total_tokens = function_count + content_count
    if total_tokens > 0:
        result["function_content_ratio"] = round(function_count / total_tokens, 4)
    else:
        result["function_content_ratio"] = 0.0
        
    return result


def syntactic_complexity_fingerprint(text: str) -> Dict[str, float]:
    """統語的複雑性の指紋を抽出（係り受け構造の近似分析）。
    
    Sudachiの依存構造情報を活用して、文の複雑さを多角的に評価。
    AIは単純な統語構造を好む傾向がある。
    
    Returns:
        Dict with syntactic complexity metrics.
    """
    if not text or len(text) < 50:
        return {"dependency_depth_avg": 0.0, "clause_density": 0.0,
                "embedding_ratio": 0.0, "pos_diversity_index": 0.0}
                
    sentences = _split_sentences(text)
    if len(sentences) < 2:
        return {"dependency_depth_avg": 0.0, "clause_density": 0.0,
                "embedding_ratio": 0.0, "pos_diversity_index": 0.0}
    
    total_depth = 0
    total_clauses = 0
    embedded_clauses = 0
    all_pos_types: set = set()
    sentence_count = 0
    
    for sentence in sentences:
        tokens = _tokenize_sudachi(sentence)
        if not tokens or len(tokens) < 3:
            continue
            
        sentence_count += 1
        
        # 依存深度の近似（形態素位置に基づく）
        depth_estimate = 0
        clause_indicators = 0
        
        for i, token in enumerate(tokens):
            pos = token.part_of_speech()
            if not pos:
                continue
                
            pos_major = pos[0]
            all_pos_types.add(pos_major)
            
            # 節の指標（接続助詞、従属接続詞など）
            if pos_major in ("接続詞", "助動詞"):
                if token.surface() in ("て", "で", "に", "を", "と", "が", "の"):
                    clause_indicators += 1
                    depth_estimate += 1
                    
            # 埋め込み節の指標（関係詞的な表現）
            if pos_major == "名詞" and i > 0:
                prev_pos = tokens[i-1].part_of_speech()
                if prev_pos and prev_pos[0] in ("動詞", "形容詞"):
                    embedded_clauses += 1
                    
        total_depth += depth_estimate
        total_clauses += max(1, clause_indicators)
    
    # 指標の計算
    result: Dict[str, float] = {}
    
    if sentence_count > 0:
        result["dependency_depth_avg"] = round(total_depth / sentence_count, 4)
        result["clause_density"] = round(total_clauses / sentence_count, 4)
        result["embedding_ratio"] = round(embedded_clauses / max(1, total_clauses), 4)
        result["pos_diversity_index"] = round(len(all_pos_types) / 12.0, 4)  # 想定最大品詞数で正規化
    else:
        result["dependency_depth_avg"] = 0.0
        result["clause_density"] = 0.0
        result["embedding_ratio"] = 0.0
        result["pos_diversity_index"] = 0.0
        
    return result


# ---------------------------------------------------------------------------
# Lightweight correction engine (R5-T01~T04)
# ---------------------------------------------------------------------------

@dataclass
class CorrectionResult:
    """Result of lightweight fingerprint-based correction."""
    text: str
    applied_rules: List[str] = field(default_factory=list)
    rewrite_ratio: float = 0.0
    discarded: bool = False
    discard_reason: str = ""


_CONJUNCTION_REMOVAL_TARGETS = re.compile(
    r"^(さらに|また|そして|加えて|つまり|したがって|ちなみに|なお)",
)

_SUBJECT_DROP_PATTERN = re.compile(
    r"^(?:私|わたし|僕|俺|我々|私たち|自分|あなた|皆さん|読者)[はが]"
)

_SENTENCE_END_DESU = re.compile(r"です。$")
_SENTENCE_END_MASU = re.compile(r"ます。$")

_SENTENCE_END_ALTERNATIVES_DESU = [
    "でしょう。", "ですね。", "かもしれません。", "と言えます。",
]
_SENTENCE_END_ALTERNATIVES_MASU = [
    "ました。", "ましょう。", "ませんか。", "るでしょう。",
]

_MAX_REWRITE_RATIO = 0.08
_ENABLE_SENTENCE_END_VARIATION_CORRECTION = False
_ENABLE_SENTENCE_OPENING_VARIATION_CORRECTION = False


def apply_fingerprint_corrections(
    text: str,
    report: FingerprintReport,
    max_rewrite_ratio: float = _MAX_REWRITE_RATIO,
) -> CorrectionResult:
    """Apply lightweight corrections based on fingerprint flat-zone flags.

    Rules (applied only when corresponding flat-zone flag is present):
      1. conjunction_rate_high -> remove some paragraph-initial conjunctions
      2. subject_explicit_high -> drop some explicit subject markers
      3. sentence_length_cv_flat / bigram_mono_low -> diversify sentence endings

    Returns original text if rewrite_ratio exceeds *max_rewrite_ratio*.
    """
    if not text or not report.flat_zone_flags:
        return CorrectionResult(text=text)

    current = text
    applied: List[str] = []

    if "conjunction_rate_high" in report.flat_zone_flags:
        current, did = _correct_conjunction_rate(current)
        if did:
            applied.append("conjunction_reduction")

    if "subject_explicit_high" in report.flat_zone_flags:
        current, did = _correct_subject_drop(current)
        if did:
            applied.append("subject_drop")

    if _ENABLE_SENTENCE_END_VARIATION_CORRECTION and any(
        f in report.flat_zone_flags for f in ("sentence_length_cv_flat", "bigram_mono_low")
    ):
        current, did = _correct_sentence_end_variation(current)
        if did:
            applied.append("sentence_end_variation")

    # R14: 読点位置が均一すぎる場合、位置を変動させる
    if "comma_position_cv_low" in report.flat_zone_flags:
        current, did = _correct_comma_position_variation(current)
        if did:
            applied.append("comma_position_variation")

    # R14: 文頭パターンが均一すぎる場合、書き出しを変動させる
    if _ENABLE_SENTENCE_OPENING_VARIATION_CORRECTION and "sentence_opening_entropy_low" in report.flat_zone_flags:
        current, did = _correct_sentence_opening_variation(current)
        if did:
            applied.append("sentence_opening_variation")

    if not applied:
        return CorrectionResult(text=text)

    # Rewrite ratio guard (R5-T04)
    orig_len = max(1, len(text))
    changed_chars = sum(1 for a, b in zip(text, current) if a != b) + abs(len(text) - len(current))
    ratio = changed_chars / orig_len

    if ratio > max_rewrite_ratio:
        return CorrectionResult(
            text=text,
            applied_rules=[],
            rewrite_ratio=round(ratio, 4),
            discarded=True,
            discard_reason=f"rewrite_ratio {ratio:.4f} > {max_rewrite_ratio}",
        )

    return CorrectionResult(
        text=current,
        applied_rules=applied,
        rewrite_ratio=round(ratio, 4),
    )


def _correct_conjunction_rate(text: str) -> Tuple[str, bool]:
    """Remove every other paragraph-initial conjunction to reduce rate."""
    paragraphs = text.split("\n\n")
    changed = False
    hit_count = 0
    result_parts: List[str] = []
    for para in paragraphs:
        lines = para.split("\n")
        first = lines[0].strip()
        if first.startswith("#"):
            result_parts.append(para)
            continue
        m = _CONJUNCTION_REMOVAL_TARGETS.match(first)
        if m:
            hit_count += 1
            if hit_count % 2 == 0:
                lines[0] = _CONJUNCTION_REMOVAL_TARGETS.sub("", lines[0]).lstrip("\u3001").lstrip()
                changed = True
        result_parts.append("\n".join(lines))
    return "\n\n".join(result_parts), changed


def _correct_subject_drop(text: str) -> Tuple[str, bool]:
    """Drop some sentence-initial explicit subjects to lower subject_explicit_rate."""
    sentences = _TERMINAL_PUNCT.split(text)
    if len(sentences) < 4:
        return text, False
    changed = False
    hit_count = 0
    current = text
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        normalized = _normalize_sentence_for_subject_scan(sent)
        m = _SUBJECT_DROP_PATTERN.match(normalized)
        if m:
            hit_count += 1
            if hit_count % 3 == 0:
                prefix_len = len(sent) - len(sent.lstrip())
                leading = sent[:prefix_len]
                body = sent[prefix_len:]
                while body and body[0] in "「『（(":
                    leading += body[0]
                    body = body[1:]
                new_body = _SUBJECT_DROP_PATTERN.sub("", body, count=1).lstrip()
                new_sent = f"{leading}{new_body}"
                if new_sent and len(new_sent) > 4:
                    current = current.replace(sent, new_sent, 1)
                    changed = True
    return current, changed


def _correct_sentence_opening_variation(text: str) -> Tuple[str, bool]:
    """R14: 文頭パターンが均一すぎる場合、書き出しを変動させる。

    AI文は「名詞+は」の主語開始が均一になりがち。
    連続する「〜は」開始文の一部を、接続表現や副詞で書き出しを変える。
    """
    import random as _random_mod

    # 「〜は」で始まる文を検出（名詞+は パターン）
    noun_ha_start = re.compile(r"^([一-龯ァ-ヶー]{1,10})は[、,]?")

    paragraphs = text.split("\n\n")
    rng = _random_mod.Random(len(text))
    changed = False
    action_count = 0
    max_actions = max(2, len(paragraphs) // 3)

    # 「〜は」開始を置き換える接頭表現
    opening_alternatives = [
        "注目すべきは、",
        "ここで重要なのが、",
        "見落とされがちだが、",
        "実際のところ、",
        "興味深いことに、",
        "意外にも、",
        "特筆すべき点として、",
        "あまり知られていないが、",
    ]

    result_parts: List[str] = []
    for para in paragraphs:
        if action_count >= max_actions:
            result_parts.append(para)
            continue

        lines = para.split("\n")
        new_lines: List[str] = []
        consecutive_noun_ha = 0

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                new_lines.append(line)
                consecutive_noun_ha = 0
                continue

            # 文を句点で分割して各文の先頭をチェック
            sentences = [s for s in re.split(r"(?<=[。！？])", stripped) if s.strip()]
            new_sentences: List[str] = []
            for sent in sentences:
                sent_stripped = sent.strip()
                m = noun_ha_start.match(sent_stripped)
                if m:
                    consecutive_noun_ha += 1
                    # 3文以上連続した場合、3文目以降を変換
                    if consecutive_noun_ha >= 3 and action_count < max_actions:
                        alt = rng.choice(opening_alternatives)
                        new_sent = alt + sent_stripped[0].lower() + sent_stripped[1:]
                        new_sentences.append(new_sent)
                        changed = True
                        action_count += 1
                        consecutive_noun_ha = 0
                        continue
                else:
                    consecutive_noun_ha = 0
                new_sentences.append(sent)

            new_lines.append("".join(new_sentences))

        result_parts.append("\n".join(new_lines))

    return "\n\n".join(result_parts), changed


def _correct_comma_position_variation(text: str) -> Tuple[str, bool]:
    """R14: 読点位置が均一すぎる場合、位置を変動させる。

    戦略:
    1. 文頭近く（相対位置 < 0.25）にしか読点がない短い節 → 読点を削除
    2. 長い文（20字以上）で後半に読点がない → 助詞の後に読点を追加
    これにより読点の相対位置分布のCVが上がる。
    """
    import random as _random_mod

    sentences = _TERMINAL_PUNCT.split(text)
    if len(sentences) < 4:
        return text, False

    rng = _random_mod.Random(len(text))
    current = text
    changed = False
    action_count = 0
    max_actions = max(2, len(sentences) // 5)  # 全文の20%まで

    # 助詞パターン（読点を追加できる安全な位置）
    comma_insert_re = re.compile(r"([はがをにでともへより])")

    for sent in sentences:
        sent = sent.strip()
        if not sent or len(sent) < 10 or action_count >= max_actions:
            continue

        comma_positions = [i for i, ch in enumerate(sent) if ch == "、"]
        if not comma_positions:
            # 読点なしの長い文 → 後半に読点を追加
            if len(sent) >= 25:
                # 文の40%〜70%の位置にある助詞の後に読点を挿入
                target_start = int(len(sent) * 0.4)
                target_end = int(len(sent) * 0.7)
                candidates = []
                for m in comma_insert_re.finditer(sent):
                    pos = m.end()
                    if target_start <= pos <= target_end:
                        candidates.append(pos)
                if candidates:
                    insert_pos = rng.choice(candidates)
                    new_sent = sent[:insert_pos] + "、" + sent[insert_pos:]
                    current = current.replace(sent, new_sent, 1)
                    changed = True
                    action_count += 1
            continue

        # 読点がすべて文頭近く（相対位置 < 0.3）に集中している場合
        all_early = all(p / max(1, len(sent) - 1) < 0.3 for p in comma_positions)
        if all_early and len(comma_positions) == 1 and len(sent) < 20:
            # 短い文の文頭読点を削除（3回に1回）
            if rng.random() < 0.33:
                new_sent = sent.replace("、", "", 1)
                if len(new_sent) >= 6:
                    current = current.replace(sent, new_sent, 1)
                    changed = True
                    action_count += 1

    return current, changed


def _correct_sentence_end_variation(text: str) -> Tuple[str, bool]:
    """Diversify repetitive sentence endings."""
    import random as _random_mod
    lines = text.split("\n")
    changed = False
    desu_count = 0
    masu_count = 0
    result_lines: List[str] = []
    rng = _random_mod.Random(len(text))

    for line in lines:
        stripped = line.rstrip()
        if _SENTENCE_END_DESU.search(stripped):
            desu_count += 1
            if desu_count % 4 == 0:
                alt = rng.choice(_SENTENCE_END_ALTERNATIVES_DESU)
                stripped = _SENTENCE_END_DESU.sub(alt, stripped)
                changed = True
        elif _SENTENCE_END_MASU.search(stripped):
            masu_count += 1
            if masu_count % 4 == 0:
                alt = rng.choice(_SENTENCE_END_ALTERNATIVES_MASU)
                stripped = _SENTENCE_END_MASU.sub(alt, stripped)
                changed = True
        result_lines.append(stripped)
    return "\n".join(result_lines), changed


# ---------------------------------------------------------------------------
# K-candidate vocabulary overlap penalty (R8-T13)
# ---------------------------------------------------------------------------

def compute_vocab_overlap_penalty(
    candidates: List[str],
    target_index: int,
) -> float:
    """Compute vocabulary overlap penalty for a candidate vs all others (R8-T13).

    Returns 0.0 (no overlap, best) to 1.0 (complete overlap, worst).
    Uses content-word lemmas via Sudachi/fallback.
    """
    if len(candidates) < 2 or target_index >= len(candidates):
        return 0.0

    target_lemmas = set(_extract_lemmas(candidates[target_index]))
    if not target_lemmas:
        return 0.0

    max_overlap = 0.0
    for i, cand in enumerate(candidates):
        if i == target_index:
            continue
        other_lemmas = set(_extract_lemmas(cand))
        if not other_lemmas:
            continue
        intersection = target_lemmas & other_lemmas
        union = target_lemmas | other_lemmas
        if union:
            jaccard = len(intersection) / len(union)
            max_overlap = max(max_overlap, jaccard)

    return round(max_overlap, 4)


# ---------------------------------------------------------------------------
# Paragraph expression similarity penalty (R8-T14)
# ---------------------------------------------------------------------------

def compute_paragraph_similarity_penalty(
    text: str,
    preceding_text: str,
) -> float:
    """Compute expression similarity between text and preceding paragraph (R8-T14).

    Returns 0.0 (no similarity) to 1.0 (identical expressions).
    Penalizes candidates that repeat the same expressions as the previous section.
    """
    if not text or not preceding_text:
        return 0.0

    target_lemmas = set(_extract_lemmas(text))
    prev_lemmas = set(_extract_lemmas(preceding_text))

    if not target_lemmas or not prev_lemmas:
        return 0.0

    intersection = target_lemmas & prev_lemmas
    # Normalize by target size (how much of the new text is borrowed)
    overlap_ratio = len(intersection) / max(1, len(target_lemmas))
    return round(min(1.0, overlap_ratio), 4)


# ---------------------------------------------------------------------------
# Candidate A vs B selection (R8-T17)
# ---------------------------------------------------------------------------

@dataclass
class CandidateSelection:
    """Result of A vs B candidate comparison."""
    selected: str  # "a" or "b"
    text: str
    score_a: float = 0.0
    score_b: float = 0.0
    reason: str = ""
    fallback_used: bool = False


def select_best_candidate(
    candidate_a: str,
    candidate_b: Optional[str],
    min_unpredictability: float = 0.35,
    preceding_text: str = "",
) -> CandidateSelection:
    """Compare candidate A and B, return the best one (R8-T17).

    Selection rules:
    1. If candidate_b is None/empty, select A (fallback).
    2. Compute fingerprint scores for both.
    3. Apply vocab overlap penalty if both exist.
    4. Apply paragraph similarity penalty vs preceding text.
    5. Select the candidate with higher adjusted score.
    6. If winner's score < min_unpredictability, still select it but flag.
    """
    if not candidate_b or len(candidate_b.strip()) < 50:
        analyzer = FingerprintAnalyzer()
        try:
            report_a = analyzer.analyze(candidate_a)
            score_a = report_a.overall_unpredictability
        except Exception:
            score_a = 0.0
        return CandidateSelection(
            selected="a", text=candidate_a,
            score_a=round(score_a, 4), score_b=0.0,
            reason="candidate_b_unavailable", fallback_used=True,
        )

    candidates = [candidate_a, candidate_b]
    analyzer = FingerprintAnalyzer()

    try:
        report_a = analyzer.analyze(candidate_a)
        score_a = report_a.overall_unpredictability
    except Exception:
        report_a = FingerprintReport()
        score_a = 0.0

    try:
        report_b = analyzer.analyze(candidate_b)
        score_b = report_b.overall_unpredictability
    except Exception:
        report_b = FingerprintReport()
        score_b = 0.0

    # Vocab overlap penalty (lower overlap = better)
    overlap_a = compute_vocab_overlap_penalty(candidates, 0)
    overlap_b = compute_vocab_overlap_penalty(candidates, 1)

    # Paragraph similarity penalty vs preceding text
    para_pen_a = compute_paragraph_similarity_penalty(candidate_a, preceding_text) if preceding_text else 0.0
    para_pen_b = compute_paragraph_similarity_penalty(candidate_b, preceding_text) if preceding_text else 0.0

    # Lexical diversity bonus
    mtld_a = min(1.0, report_a.mtld / 120.0) if report_a.mtld > 0 else 0.0
    mtld_b = min(1.0, report_b.mtld / 120.0) if report_b.mtld > 0 else 0.0

    overlap_w, para_w, flat_w = _get_candidate_penalty_weights()
    flat_pen_a = len(report_a.flat_zone_flags) * flat_w
    flat_pen_b = len(report_b.flat_zone_flags) * flat_w

    # Adjusted scores
    adj_a = score_a + mtld_a * 0.15 - overlap_a * overlap_w - para_pen_a * para_w - flat_pen_a
    adj_b = score_b + mtld_b * 0.15 - overlap_b * overlap_w - para_pen_b * para_w - flat_pen_b

    adj_a = round(max(0.0, min(1.0, adj_a)), 4)
    adj_b = round(max(0.0, min(1.0, adj_b)), 4)

    if adj_b > adj_a:
        selected = "b"
        text = candidate_b
        reason = f"b_wins(adj_a={adj_a},adj_b={adj_b})"
    else:
        selected = "a"
        text = candidate_a
        reason = f"a_wins(adj_a={adj_a},adj_b={adj_b})"

    winner_score = adj_b if selected == "b" else adj_a
    if winner_score < min_unpredictability:
        reason += f" below_min({min_unpredictability})"

    return CandidateSelection(
        selected=selected, text=text,
        score_a=adj_a, score_b=adj_b,
        reason=reason, fallback_used=False,
    )


# ---------------------------------------------------------------------------
# HLCv2 rerank scoring (R8-T06/T07)
# ---------------------------------------------------------------------------

@dataclass
class RerankCandidate:
    """A candidate text with its rerank score breakdown."""
    text: str
    index: int = 0
    unpredictability: float = 0.0
    mtld_score: float = 0.0
    hd_d_score: float = 0.0
    flat_zone_count: int = 0
    weighted_score: float = 0.0
    selected: bool = False


# Default rerank weights (R8-T07)
_RERANK_WEIGHTS: Dict[str, float] = {
    "unpredictability": 0.35,
    "lexical_diversity": 0.20,
    "low_flat_zones": 0.15,
    "layout_ok": 0.15,
    "vocab_overlap_penalty": 0.10,
    "template_similarity": 0.05,
}


def rerank_candidates(
    candidates: List[str],
    weights: Optional[Dict[str, float]] = None,
) -> List[RerankCandidate]:
    """Score and rank candidate texts using fingerprint metrics (R8-T06/T07).

    Returns candidates sorted by weighted_score descending.
    The top candidate has ``selected=True``.
    """
    if not candidates:
        return []

    w = dict(_RERANK_WEIGHTS)
    if weights:
        w.update(weights)

    analyzer = FingerprintAnalyzer()
    results: List[RerankCandidate] = []

    for idx, text in enumerate(candidates):
        try:
            report = analyzer.analyze(text)
        except Exception:
            report = FingerprintReport()

        # Normalize sub-scores to 0..1
        unpred = min(1.0, max(0.0, report.overall_unpredictability))

        # Lexical diversity: MTLD normalized (cap at 120)
        mtld_norm = min(1.0, report.mtld / 120.0) if report.mtld > 0 else 0.0
        hdd_norm = min(1.0, max(0.0, report.hd_d))
        lex_div = (mtld_norm + hdd_norm) / 2.0

        # Flat zone penalty: fewer flags = better
        max_flags = 9  # total possible flag types
        flat_score = max(0.0, 1.0 - len(report.flat_zone_flags) / max_flags)

        # Layout: simple check - has content and reasonable length
        layout_score = 1.0 if len(text.strip()) > 50 else 0.3

        # Weighted combination
        score = (
            w.get("unpredictability", 0.35) * unpred
            + w.get("lexical_diversity", 0.20) * lex_div
            + w.get("low_flat_zones", 0.15) * flat_score
            + w.get("layout_ok", 0.15) * layout_score
            + w.get("vocab_overlap_penalty", 0.10) * 0.5  # neutral default
            + w.get("template_similarity", 0.05) * 0.5  # neutral default
        )

        results.append(RerankCandidate(
            text=text,
            index=idx,
            unpredictability=round(unpred, 4),
            mtld_score=round(mtld_norm, 4),
            hd_d_score=round(hdd_norm, 4),
            flat_zone_count=len(report.flat_zone_flags),
            weighted_score=round(score, 4),
        ))

    # Sort descending by score
    results.sort(key=lambda c: c.weighted_score, reverse=True)
    if results:
        results[0].selected = True

    return results


# ---------------------------------------------------------------------------
# Resonance dynamic tuning (R6-T01~T05)
# ---------------------------------------------------------------------------

@dataclass
class ResonanceTuningResult:
    """Before/after values for resonance parameter tuning."""
    enabled: bool = False
    before: Dict[str, float] = field(default_factory=dict)
    after: Dict[str, float] = field(default_factory=dict)
    adjustments: Dict[str, float] = field(default_factory=dict)
    score_band: str = ""
    reason: str = ""


# R6-T03: Safe adjustment ranges per score band
# band -> (humanity_intensity_delta, phrase_probability_delta, pronoun_reduction_ratio_delta)
_TUNING_BANDS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "very_low": {  # unpredictability < 0.25
        "humanity_intensity": (0.10, 0.25),
        "phrase_probability": (-0.15, -0.05),
        "pronoun_reduction_ratio": (-0.15, -0.05),
    },
    "low": {  # 0.25 <= unpredictability < 0.40
        "humanity_intensity": (0.05, 0.15),
        "phrase_probability": (-0.10, -0.03),
        "pronoun_reduction_ratio": (-0.10, -0.03),
    },
    "medium": {  # 0.40 <= unpredictability < 0.60
        "humanity_intensity": (0.0, 0.05),
        "phrase_probability": (-0.03, 0.0),
        "pronoun_reduction_ratio": (-0.03, 0.0),
    },
    "high": {  # unpredictability >= 0.60 -> no adjustment
        "humanity_intensity": (0.0, 0.0),
        "phrase_probability": (0.0, 0.0),
        "pronoun_reduction_ratio": (0.0, 0.0),
    },
}

# Absolute safe limits for tuned values
_TUNING_CLAMPS: Dict[str, Tuple[float, float]] = {
    "humanity_intensity": (0.0, 1.0),
    "phrase_probability": (0.3, 1.0),
    "pronoun_reduction_ratio": (0.1, 0.8),
}


def compute_resonance_tuning(
    report: FingerprintReport,
    current_params: Dict[str, float],
    style_profile: Optional[Dict[str, Any]] = None,
) -> ResonanceTuningResult:
    """Compute resonance parameter adjustments based on fingerprint scores (R6-T01).

    Only adjusts for low-scoring articles. High-scoring articles are left as-is.
    Targets (R6-T02): humanity_intensity, phrase_probability, pronoun_reduction_ratio.
    When *style_profile* is provided (R6-T09), adjustment ranges are constrained:
    - 'flat' emotional_waveform -> no adjustment (announcements)
    - 'steady' -> halve the adjustment delta
    """
    score = report.overall_unpredictability

    if score < 0.25:
        band = "very_low"
    elif score < 0.40:
        band = "low"
    elif score < 0.60:
        band = "medium"
    else:
        band = "high"

    # R6-T09: style profile constraint multiplier
    profile_multiplier = 1.0
    if style_profile:
        waveform = style_profile.get("emotional_waveform", "dynamic")
        if waveform == "flat":
            profile_multiplier = 0.0
        elif waveform == "steady":
            profile_multiplier = 0.5

    ranges = _TUNING_BANDS[band]
    before: Dict[str, float] = {}
    after: Dict[str, float] = {}
    adjustments: Dict[str, float] = {}

    for param, (delta_min, delta_max) in ranges.items():
        current_val = current_params.get(param, 0.5)
        before[param] = round(current_val, 4)
        delta = (delta_min + delta_max) / 2.0 * profile_multiplier
        clamp_lo, clamp_hi = _TUNING_CLAMPS.get(param, (0.0, 1.0))
        new_val = max(clamp_lo, min(clamp_hi, current_val + delta))
        after[param] = round(new_val, 4)
        adjustments[param] = round(new_val - current_val, 4)

    has_change = any(abs(v) > 0.001 for v in adjustments.values())
    reason = f"score_band={band} unpredictability={score:.3f}"
    if style_profile:
        reason += f" profile_multiplier={profile_multiplier}"
    if not has_change:
        reason += " (no adjustment needed)"

    return ResonanceTuningResult(
        enabled=True,
        before=before,
        after=after,
        adjustments=adjustments,
        score_band=band,
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Orthographic variation (R6-T12~T14)
# ---------------------------------------------------------------------------

# Dictionary: normalized_form -> [variant1, variant2, ...]
# Each entry maps a canonical form to its kana/kanji/katakana alternatives.
_ORTHO_VARIATION_DICT: Dict[str, List[str]] = {
    "事": ["こと", "コト"],
    "物": ["もの", "モノ"],
    "所": ["ところ", "トコロ"],
    "時": ["とき", "トキ"],
    "為": ["ため", "タメ"],
    "様": ["よう", "ヨウ"],
    "訳": ["わけ", "ワケ"],
    "筈": ["はず", "ハズ"],
    "迄": ["まで"],
    "位": ["くらい", "ぐらい"],
    "程": ["ほど", "ホド"],
    "通り": ["とおり", "トオリ"],
    "中": ["なか", "ナカ"],
    "方": ["ほう", "かた"],
    "気": ["き"],
    "先": ["さき"],
    "上": ["うえ"],
    "下": ["した"],
    "間": ["あいだ"],
    "頃": ["ころ", "ごろ"],
    "沢山": ["たくさん", "タクサン"],
    "綺麗": ["きれい", "キレイ"],
    "可愛い": ["かわいい", "カワイイ"],
    "面白い": ["おもしろい"],
    "嬉しい": ["うれしい"],
    "難しい": ["むずかしい", "ムズカシイ"],
    "素敵": ["すてき", "ステキ"],
    "駄目": ["だめ", "ダメ"],
    "凄い": ["すごい", "スゴイ"],
    "流石": ["さすが", "サスガ"],
}

# Reverse map: variant -> list of (canonical, all_variants)
_ORTHO_REVERSE: Dict[str, Tuple[str, List[str]]] = {}
for _canon, _variants in _ORTHO_VARIATION_DICT.items():
    all_forms = [_canon] + _variants
    for _form in all_forms:
        _ORTHO_REVERSE[_form] = (_canon, [f for f in all_forms if f != _form])


def apply_orthographic_variation(
    text: str,
    rate: float = 0.0,
) -> str:
    """Apply orthographic variation to text at the given rate (R6-T13).

    *rate* controls the probability of replacing a matched token with a variant.
    0.0 = no variation (announcements), 0.3 = high variation (hobby).
    Uses Sudachi normalized forms when available, falls back to dictionary lookup.
    """
    if rate <= 0.0 or not text:
        return text

    import random as _rmod
    rng = _rmod.Random(len(text))

    # Try Sudachi-based replacement first
    tokens = _tokenize_sudachi(text)
    if tokens:
        return _apply_ortho_sudachi(text, tokens, rate, rng)

    # Fallback: direct string replacement from dictionary
    return _apply_ortho_fallback(text, rate, rng)


def _apply_ortho_sudachi(
    text: str,
    tokens: list,
    rate: float,
    rng: "random.Random",
) -> str:
    """Sudachi-based orthographic variation."""
    result_parts: List[str] = []
    last_end = 0
    for m in tokens:
        surface = m.surface()
        normalized = m.normalized_form()
        begin = m.begin()
        end = m.end()
        # Add any text between tokens
        if begin > last_end:
            result_parts.append(text[last_end:begin])
        # Check if this token has variants
        lookup_key = normalized if normalized in _ORTHO_REVERSE else surface
        if lookup_key in _ORTHO_REVERSE and rng.random() < rate:
            _, variants = _ORTHO_REVERSE[lookup_key]
            if variants:
                replacement = rng.choice(variants)
                result_parts.append(replacement)
                last_end = end
                continue
        result_parts.append(text[begin:end])
        last_end = end
    if last_end < len(text):
        result_parts.append(text[last_end:])
    return "".join(result_parts)


def _apply_ortho_fallback(
    text: str,
    rate: float,
    rng: "random.Random",
) -> str:
    """Fallback orthographic variation using direct string replacement."""
    result = text
    for form, (canon, variants) in _ORTHO_REVERSE.items():
        if not variants or form not in result:
            continue
        if rng.random() < rate:
            replacement = rng.choice(variants)
            # Replace only the first occurrence to keep changes minimal
            result = result.replace(form, replacement, 1)
    return result
