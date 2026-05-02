"""Phase 04 style drift guard driven by citation-source profile."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import re
import unicodedata
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple
from urllib.parse import urlparse

from core.app_config import get_source_reading_config

try:
    from sudachipy import dictionary as sudachi_dictionary
    from sudachipy import tokenizer as sudachi_tokenizer

    SUDACHI_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    sudachi_dictionary = None
    sudachi_tokenizer = None
    SUDACHI_AVAILABLE = False


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+|[一-龯]+|[ぁ-ん]+|[ァ-ヶー]+")
JP_PATTERN = re.compile(r"[ぁ-んァ-ヶ一-龯]")
URL_LABEL_PATTERN = re.compile(r"[a-z0-9]{3,}")

PROTECTED_BLOCK_KEYWORDS: Tuple[str, ...] = (
    "免責",
    "参考文献",
    "references",
    "disclaimer",
    "出典:",
)

COMMON_TERMS: Set[str] = {
    "記事",
    "内容",
    "今回",
    "情報",
    "改善",
    "対応",
    "検討",
    "ポイント",
    "読者",
    "企業",
    "説明",
    "解説",
    "取り組み",
    "運用",
    "導入",
    "共有",
    "実施",
    "方法",
    "結果",
    "状況",
    "also",
    "this",
    "that",
    "with",
    "from",
    "into",
    "and",
}

DOMAIN_LEXICONS: Dict[str, Tuple[str, ...]] = {
    "food": ("食品", "食材", "飲食", "惣菜", "冷凍", "在庫", "物流", "店舗", "スーパー", "原料", "衛生"),
    "medical": ("医療", "病院", "患者", "診療", "臨床", "治療", "医薬品", "処方", "看護", "薬剤"),
    "technical": ("システム", "エンジニア", "開発", "api", "データ", "クラウド", "インフラ", "実装", "アルゴリズム"),
    "finance": ("金融", "投資", "資産", "決算", "会計", "株式", "融資", "収益", "予算", "キャッシュフロー"),
    "legal": ("法務", "契約", "規約", "法令", "弁護士", "訴訟", "コンプライアンス", "責任", "条項"),
    "education": ("教育", "学習", "学校", "授業", "教材", "受講", "研修", "生徒", "講師"),
    "manufacturing": ("製造", "工場", "生産", "品質管理", "工程", "設備", "歩留まり", "検査"),
    "retail": ("小売", "販売", "売場", "顧客", "販促", "購買", "店舗運営", "流通"),
    "hospitality": ("宿泊", "ホテル", "観光", "接客", "予約", "客室", "レストラン"),
    "hr": ("採用", "人材", "人事", "評価制度", "育成", "組織開発", "エンゲージメント"),
    "energy": ("電力", "発電", "再生可能", "蓄電", "送電", "エネルギー", "脱炭素"),
}

DOMAIN_TERM_INDEX: Dict[str, Set[str]] = defaultdict(set)
for domain_name, words in DOMAIN_LEXICONS.items():
    for word in words:
        DOMAIN_TERM_INDEX[word.strip().lower()].add(domain_name)

TERM_NEUTRAL_REPLACEMENTS: Dict[str, str] = {
    "医療": "現場",
    "医療従事者": "現場担当者",
    "患者": "利用者",
    "診療": "サービス提供",
    "臨床": "現場検証",
    "治療": "対応",
    "医薬品": "商品",
    "処方": "提供計画",
    "看護": "現場支援",
    "投資家": "関係者",
    "株式": "指標",
    "融資": "資金計画",
    "訴訟": "法的対応",
    "契約条項": "条件",
    "生徒": "受講者",
    "講師": "担当者",
}

CASUAL_TO_FORMAL_RULES: Tuple[Tuple[re.Pattern[str], str, float, str], ...] = (
    (re.compile(r"ぶっちゃけ"), "率直に言うと", 0.6, "casual phrase mismatch"),
    (re.compile(r"マジで"), "本当に", 0.6, "casual phrase mismatch"),
    (re.compile(r"ヤバい"), "課題が大きい", 0.7, "casual phrase mismatch"),
    (re.compile(r"すごく"), "非常に", 0.4, "casual phrase mismatch"),
    (re.compile(r"っす"), "です", 0.6, "casual phrase mismatch"),
)

HYPE_TO_EXPLAIN_RULES: Tuple[Tuple[re.Pattern[str], str, float, str], ...] = (
    (re.compile(r"最強"), "有効", 0.7, "hype phrase mismatch for explanatory intent"),
    (re.compile(r"神"), "優れた", 0.7, "hype phrase mismatch for explanatory intent"),
    (re.compile(r"圧倒的"), "高い", 0.6, "hype phrase mismatch for explanatory intent"),
    (re.compile(r"絶対"), "十分に", 0.5, "absolute phrase mismatch for explanatory intent"),
)

PURPOSE_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "branding": ("ブランド", "訴求", "価値", "認知", "導入事例", "ブランディング", "branding"),
    "explain": ("解説", "説明", "手順", "比較", "ポイント", "background", "explain"),
    "casual": ("体験", "エピソード", "雑談", "気づき", "率直", "casual"),
    "thought_leadership": ("提言", "見解", "戦略", "考察", "示唆", "analysis", "thought"),
}

STRICTNESS_MIN_DOMAIN_HITS: Dict[str, int] = {
    "relaxed": 2,
    "normal": 1,
    "strict": 1,
}

STRICTNESS_CORRECTION_RATIO: Dict[str, float] = {
    "relaxed": 0.08,
    "normal": 0.12,
    "strict": 0.18,
}

STRICTNESS_CONFIDENCE_MIN: Dict[str, float] = {
    "relaxed": 0.30,
    "normal": 0.18,
    "strict": 0.10,
}


@dataclass(frozen=True)
class StyleDriftContext:
    topic_hint: str = ""
    source_urls: Tuple[str, ...] = ()
    writing_intent: str = ""
    target_audience: str = ""
    article_type: str = ""
    writing_focus: str = ""
    source_text: str = ""
    platform: str = ""
    perspective: str = ""


@dataclass(frozen=True)
class DriftAlert:
    paragraph_index: int
    sentence_index: int
    sentence_excerpt: str
    alert_type: str
    drift_term: str
    inferred_domain: str
    inferred_purpose: str
    suggested_replacement: str
    severity: float
    reason: str


@dataclass(frozen=True)
class StyleCorrection:
    paragraph_index: int
    sentence_index: int
    original_sentence: str
    corrected_sentence: str
    inferred_purpose: str
    replacements: Tuple[str, ...]
    reason: str


@dataclass
class StyleDriftResult:
    style_alignment_score: float
    inferred_domain: str
    inferred_purpose: str
    active_source_domains: Tuple[str, ...] = ()
    drift_alerts: List[DriftAlert] = field(default_factory=list)
    style_corrections: List[StyleCorrection] = field(default_factory=list)
    correction_cap: int = 0


@dataclass(frozen=True)
class _ParagraphBlock:
    index: int
    text: str
    is_heading: bool
    is_protected: bool


@dataclass
class _SourceProfile:
    source_terms: Set[str] = field(default_factory=set)
    domain_scores: Dict[str, float] = field(default_factory=dict)
    active_domains: Set[str] = field(default_factory=set)
    primary_domain: str = "general"
    confidence: float = 0.0


class Phase04StyleDrift:
    """Detect style/domain drift and provide minimal purpose-aware corrections."""

    def __init__(
        self,
        style_alignment_min_score: float = 0.72,
        domain_guard_strictness: str = "normal",
    ) -> None:
        self.style_alignment_min_score = max(0.0, min(1.0, float(style_alignment_min_score)))
        self.domain_guard_strictness = self._normalize_strictness(domain_guard_strictness)
        self._source_reading_config: Dict[str, Any] = get_source_reading_config()
        self._sudachi = None
        self._sudachi_mode = None
        self._sudachi_ready = False
        self._init_sudachi()

    def _get_source_text_max_chars(self) -> int:
        cfg = get_source_reading_config()
        if isinstance(cfg, dict) and cfg:
            self._source_reading_config = cfg
        source_cfg = dict(getattr(self, "_source_reading_config", {}) or {})
        return int(source_cfg.get("style_drift_source_text_max_chars", 12000) or 12000)

    def analyze(
        self,
        text: str,
        context: Optional[Dict[str, Any] | StyleDriftContext] = None,
    ) -> StyleDriftResult:
        if not text:
            return StyleDriftResult(
                style_alignment_score=1.0,
                inferred_domain="general",
                inferred_purpose="explain",
            )

        normalized_context = self._normalize_context(context)
        source_profile = self._build_source_profile(normalized_context)
        inferred_purpose = self._infer_purpose(text, normalized_context)

        blocks = self._split_blocks(text)
        total_sentences = 0
        alerts: List[DriftAlert] = []
        corrections: List[StyleCorrection] = []
        correction_cap = self._correction_cap(self._count_content_sentences(blocks))

        for block in blocks:
            if block.is_heading or block.is_protected:
                continue
            sentences = self._split_sentences(block.text)
            for sentence_index, sentence in enumerate(sentences, start=1):
                original = sentence.strip()
                if not original:
                    continue
                total_sentences += 1

                sentence_alerts, corrected_sentence, replacements = self._inspect_sentence(
                    sentence=original,
                    paragraph_index=block.index,
                    sentence_index=sentence_index,
                    source_profile=source_profile,
                    inferred_purpose=inferred_purpose,
                )
                if not sentence_alerts:
                    continue
                alerts.extend(sentence_alerts)
                if corrected_sentence != original and len(corrections) < correction_cap:
                    corrections.append(
                        StyleCorrection(
                            paragraph_index=block.index,
                            sentence_index=sentence_index,
                            original_sentence=original,
                            corrected_sentence=corrected_sentence,
                            inferred_purpose=inferred_purpose,
                            replacements=tuple(replacements),
                            reason="citation-source profile aligned minimal correction",
                        )
                    )

        style_alignment_score = self._style_alignment_score(alerts, total_sentences)
        return StyleDriftResult(
            style_alignment_score=style_alignment_score,
            inferred_domain=source_profile.primary_domain,
            inferred_purpose=inferred_purpose,
            active_source_domains=tuple(sorted(source_profile.active_domains)),
            drift_alerts=alerts,
            style_corrections=corrections,
            correction_cap=correction_cap,
        )

    def apply_minimal_corrections(
        self,
        text: str,
        corrections: Sequence[StyleCorrection],
    ) -> Tuple[str, float, List[StyleCorrection]]:
        if not text or not corrections:
            return text, 0.0, []

        blocks = self._split_blocks(text)
        block_map: Dict[int, _ParagraphBlock] = {block.index: block for block in blocks}
        block_texts: Dict[int, str] = {block.index: block.text for block in blocks}

        total_sentences = self._count_content_sentences(blocks)
        correction_cap = self._correction_cap(total_sentences)
        if correction_cap <= 0:
            return text, 0.0, []

        applied: List[StyleCorrection] = []
        for correction in corrections:
            if len(applied) >= correction_cap:
                break
            block = block_map.get(correction.paragraph_index)
            if block is None or block.is_heading or block.is_protected:
                continue

            current = block_texts.get(block.index, block.text)
            sentences = self._split_sentences(current)
            sentence_pos = correction.sentence_index - 1
            if not (0 <= sentence_pos < len(sentences)):
                continue
            if sentences[sentence_pos].strip() != correction.original_sentence.strip():
                continue

            sentences[sentence_pos] = correction.corrected_sentence
            block_texts[block.index] = self._compose_paragraph(sentences, current)
            applied.append(correction)

        rebuilt = [block_texts.get(block.index, block.text) for block in blocks]
        rewritten_text = "\n\n".join(segment for segment in rebuilt if segment.strip())
        correction_ratio = round(len(applied) / max(1, total_sentences), 4)
        return rewritten_text, correction_ratio, applied

    def _normalize_context(self, context: Optional[Dict[str, Any] | StyleDriftContext]) -> StyleDriftContext:
        if isinstance(context, StyleDriftContext):
            return context
        if not isinstance(context, dict):
            return StyleDriftContext()
        source_urls = context.get("source_urls")
        if not isinstance(source_urls, list):
            source_urls = []
        return StyleDriftContext(
            topic_hint=str(context.get("topic_hint") or ""),
            source_urls=tuple(str(url) for url in source_urls if str(url).strip()),
            writing_intent=str(context.get("writing_intent") or ""),
            target_audience=str(context.get("target_audience") or ""),
            article_type=str(context.get("article_type") or ""),
            writing_focus=str(context.get("writing_focus") or ""),
            source_text=str(context.get("source_text") or ""),
            platform=str(context.get("platform") or ""),
            perspective=str(context.get("perspective") or ""),
        )

    def _build_source_profile(self, context: StyleDriftContext) -> _SourceProfile:
        source_text_max_chars = self._get_source_text_max_chars()
        source_blob = " ".join(
            [
                context.topic_hint,
                context.writing_intent,
                context.target_audience,
                context.article_type,
                context.writing_focus,
                context.source_text[:source_text_max_chars],
                self._extract_url_terms(context.source_urls),
            ]
        ).lower()
        tokens = self._extract_content_terms(source_blob)
        token_counter = Counter(tokens)

        domain_scores: Dict[str, float] = {}
        for domain, keywords in DOMAIN_LEXICONS.items():
            score = 0.0
            for word in keywords:
                normalized_word = self._normalize_token(word)
                if not normalized_word:
                    continue
                score += float(max(token_counter.get(normalized_word, 0), source_blob.count(normalized_word)))
            domain_scores[domain] = score

        if not domain_scores:
            return _SourceProfile()

        primary_domain = max(domain_scores, key=domain_scores.get)
        primary_score = domain_scores[primary_domain]
        total_score = sum(domain_scores.values())
        confidence = primary_score / max(0.0001, total_score) if total_score > 0 else 0.0

        active_domains: Set[str] = set()
        if primary_score > 0:
            floor = max(1.0, primary_score * 0.45)
            active_domains = {domain for domain, score in domain_scores.items() if score >= floor}
        if not active_domains:
            active_domains = {"general"}
            primary_domain = "general"

        source_terms = {
            token
            for token, count in token_counter.items()
            if count >= 2 and token not in COMMON_TERMS and len(token) >= 2
        }
        for domain in active_domains:
            for term in DOMAIN_LEXICONS.get(domain, ()):
                source_terms.add(self._normalize_token(term))

        return _SourceProfile(
            source_terms=source_terms,
            domain_scores=domain_scores,
            active_domains=active_domains,
            primary_domain=primary_domain,
            confidence=confidence,
        )

    def _infer_purpose(self, text: str, context: StyleDriftContext) -> str:
        focus_key = (context.writing_focus or "").strip().lower()
        if focus_key == "analysis":
            return "thought_leadership"
        if focus_key == "experience":
            return "casual"
        if focus_key == "explanation":
            return "explain"

        article_type = (context.article_type or "").strip().lower()
        if article_type == "branding":
            return "branding"
        if article_type in ("ai", "announcement"):
            return "explain"
        if article_type == "case_study":
            return "thought_leadership"

        combined = " ".join([context.writing_intent, context.topic_hint, text[:1800]]).lower()
        scores: Dict[str, int] = {
            purpose: self._keyword_hits(combined, keywords)
            for purpose, keywords in PURPOSE_KEYWORDS.items()
        }
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "explain"

    def _inspect_sentence(
        self,
        sentence: str,
        paragraph_index: int,
        sentence_index: int,
        source_profile: _SourceProfile,
        inferred_purpose: str,
    ) -> Tuple[List[DriftAlert], str, List[str]]:
        alerts: List[DriftAlert] = []
        corrected = sentence
        replacements: List[str] = []

        sentence_lower = sentence.lower()
        tokens = set(self._extract_content_terms(sentence))
        sentence_domain_terms: Dict[str, List[str]] = defaultdict(list)
        for token in tokens:
            if token in source_profile.source_terms:
                continue
            domains = DOMAIN_TERM_INDEX.get(token)
            if not domains:
                continue
            for domain in domains:
                sentence_domain_terms[domain].append(token)
        for domain, lexicon in DOMAIN_LEXICONS.items():
            for term in lexicon:
                normalized_term = self._normalize_token(term)
                if not normalized_term:
                    continue
                if normalized_term in source_profile.source_terms:
                    continue
                if normalized_term not in sentence_lower:
                    continue
                sentence_domain_terms[domain].append(normalized_term)

        strictness_hits = STRICTNESS_MIN_DOMAIN_HITS[self.domain_guard_strictness]
        confidence_min = STRICTNESS_CONFIDENCE_MIN[self.domain_guard_strictness]
        if source_profile.confidence >= confidence_min:
            for domain, drift_terms in sentence_domain_terms.items():
                if domain in source_profile.active_domains:
                    continue
                if len(drift_terms) < strictness_hits:
                    continue
                for term in sorted(set(drift_terms)):
                    replacement = TERM_NEUTRAL_REPLACEMENTS.get(term, "")
                    if replacement:
                        corrected = re.sub(re.escape(term), replacement, corrected)
                        replacements.append(f"{term}->{replacement}")
                    alerts.append(
                        DriftAlert(
                            paragraph_index=paragraph_index,
                            sentence_index=sentence_index,
                            sentence_excerpt=self._excerpt(sentence),
                            alert_type="domain",
                            drift_term=term,
                            inferred_domain=source_profile.primary_domain,
                            inferred_purpose=inferred_purpose,
                            suggested_replacement=replacement,
                            severity=1.0,
                            reason=(
                                f"term '{term}' belongs to domain '{domain}' outside source profile "
                                f"{sorted(source_profile.active_domains)}"
                            ),
                        )
                    )

        tone_rules = self._tone_rules_for_purpose(inferred_purpose)
        for pattern, replacement, severity, reason in tone_rules:
            if not pattern.search(corrected):
                continue
            corrected = pattern.sub(replacement, corrected)
            replacements.append(f"{pattern.pattern}->{replacement}")
            alerts.append(
                DriftAlert(
                    paragraph_index=paragraph_index,
                    sentence_index=sentence_index,
                    sentence_excerpt=self._excerpt(sentence),
                    alert_type="tone",
                    drift_term=pattern.pattern,
                    inferred_domain=source_profile.primary_domain,
                    inferred_purpose=inferred_purpose,
                    suggested_replacement=replacement,
                    severity=severity,
                    reason=reason,
                )
            )

        return alerts, corrected, replacements

    def _tone_rules_for_purpose(
        self,
        inferred_purpose: str,
    ) -> Tuple[Tuple[re.Pattern[str], str, float, str], ...]:
        if inferred_purpose in ("explain", "thought_leadership"):
            return CASUAL_TO_FORMAL_RULES + HYPE_TO_EXPLAIN_RULES
        if inferred_purpose == "branding":
            return CASUAL_TO_FORMAL_RULES
        return ()

    def _style_alignment_score(self, alerts: Sequence[DriftAlert], total_sentences: int) -> float:
        if total_sentences <= 0:
            return 1.0
        severity_sum = sum(max(0.2, alert.severity) for alert in alerts)
        penalty = min(1.0, severity_sum / max(1.0, total_sentences * 2.3))
        return round(max(0.0, 1.0 - penalty), 4)

    def _split_blocks(self, text: str) -> List[_ParagraphBlock]:
        chunks = [chunk.strip() for chunk in re.split(r"\n{2,}", text or "") if chunk.strip()]
        blocks: List[_ParagraphBlock] = []
        for index, chunk in enumerate(chunks, start=1):
            blocks.append(
                _ParagraphBlock(
                    index=index,
                    text=chunk,
                    is_heading=self._is_heading_block(chunk),
                    is_protected=self._is_protected_block(chunk),
                )
            )
        return blocks

    def _is_heading_block(self, block_text: str) -> bool:
        line = block_text.strip().splitlines()[0] if block_text.strip() else ""
        return bool(line.lstrip().startswith("#"))

    def _is_protected_block(self, block_text: str) -> bool:
        lowered = (block_text or "").lower()
        if any(keyword in lowered for keyword in PROTECTED_BLOCK_KEYWORDS):
            return True
        lines = [line.strip() for line in block_text.splitlines() if line.strip()]
        if lines and all(line.startswith("http://") or line.startswith("https://") for line in lines):
            return True
        return False

    def _split_sentences(self, text: str) -> List[str]:
        if not text:
            return []
        fragments = re.split(r"(?<=[。！？!?])\s*|(?<=\.)\s+(?=[A-Za-z0-9])|\n+", text.strip())
        return [fragment.strip() for fragment in fragments if fragment and fragment.strip()]

    def _compose_paragraph(self, sentences: Sequence[str], original_text: str) -> str:
        cleaned = [sentence.strip() for sentence in sentences if sentence and sentence.strip()]
        if not cleaned:
            return original_text.strip()
        if self._contains_japanese(original_text):
            return "".join(cleaned)
        return " ".join(cleaned)

    def _contains_japanese(self, text: str) -> bool:
        return bool(JP_PATTERN.search(text or ""))

    def _count_content_sentences(self, blocks: Sequence[_ParagraphBlock]) -> int:
        return sum(
            len(self._split_sentences(block.text))
            for block in blocks
            if not block.is_heading and not block.is_protected
        )

    def _correction_cap(self, sentence_count: int) -> int:
        if sentence_count <= 0:
            return 0
        ratio = STRICTNESS_CORRECTION_RATIO[self.domain_guard_strictness]
        cap = int(sentence_count * ratio)
        if cap == 0 and sentence_count >= 1 and ratio > 0:
            cap = 1
        return max(0, min(sentence_count, cap))

    def _init_sudachi(self) -> None:
        if not SUDACHI_AVAILABLE or sudachi_dictionary is None or sudachi_tokenizer is None:
            return
        try:
            self._sudachi = sudachi_dictionary.Dictionary().create()
            self._sudachi_mode = sudachi_tokenizer.Tokenizer.SplitMode.B
            self._sudachi_ready = True
        except Exception:  # pragma: no cover - defensive fallback
            self._sudachi = None
            self._sudachi_mode = None
            self._sudachi_ready = False

    def _tokenize_sudachi(self, text: str):
        if not self._sudachi_ready or not self._sudachi:
            return []
        try:
            return list(self._sudachi.tokenize(text or "", self._sudachi_mode))
        except Exception:  # pragma: no cover - defensive fallback
            return []

    def _extract_content_terms(self, text: str) -> List[str]:
        if not text:
            return []
        if self._sudachi_ready:
            terms = self._extract_content_terms_sudachi(text)
            if terms:
                return terms
        return self._normalize_tokens(TOKEN_PATTERN.findall(text))

    def _extract_content_terms_sudachi(self, text: str) -> List[str]:
        terms: List[str] = []
        for morpheme in self._tokenize_sudachi(text):
            pos = morpheme.part_of_speech()
            if not pos:
                continue
            pos_major = pos[0]
            if pos_major in {"補助記号", "助詞", "助動詞", "空白"}:
                continue
            lemma = self._lemma_from_morpheme(morpheme)
            normalized = self._normalize_token(lemma)
            if normalized:
                terms.append(normalized)
        return terms

    def _lemma_from_morpheme(self, morpheme) -> str:
        try:
            lemma = morpheme.dictionary_form() or morpheme.surface()
        except Exception:  # pragma: no cover - defensive fallback
            lemma = morpheme.surface()
        return str(lemma or morpheme.surface())

    def _normalize_token(self, token: str) -> str:
        normalized = unicodedata.normalize("NFKC", str(token or "")).strip().lower()
        if not normalized:
            return ""
        if normalized.isdigit():
            return ""
        if len(normalized) <= 1:
            return ""
        return normalized

    def _normalize_tokens(self, tokens: Sequence[str]) -> List[str]:
        normalized = []
        for token in tokens:
            value = self._normalize_token(token)
            if not value:
                continue
            normalized.append(value)
        return normalized

    def _extract_url_terms(self, urls: Sequence[str]) -> str:
        terms: List[str] = []
        for raw in urls:
            try:
                host = urlparse(raw).netloc.lower()
            except Exception:
                host = ""
            if not host:
                continue
            labels = [label for label in host.split(".") if label and label not in {"www", "co", "com", "jp", "net", "org"}]
            for label in labels:
                terms.extend(URL_LABEL_PATTERN.findall(label))
        return " ".join(terms)

    def _keyword_hits(self, text: str, keywords: Sequence[str]) -> int:
        if not text:
            return 0
        lowered = text.lower()
        return sum(1 for keyword in keywords if keyword and keyword.lower() in lowered)

    def _normalize_strictness(self, strictness: str) -> str:
        candidate = (strictness or "normal").strip().lower()
        if candidate in {"relaxed", "normal", "strict"}:
            return candidate
        return "normal"

    def _excerpt(self, sentence: str, max_chars: int = 90) -> str:
        clean = sentence.strip()
        if len(clean) <= max_chars:
            return clean
        return clean[: max_chars - 1] + "…"
