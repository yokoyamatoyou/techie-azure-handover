"""Section generation with note-oriented prompts."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from note.llm_client import LLMClient, LLMRuntimeError
from note.natural_blog_core import (
    build_note4000_section_prompt,
    build_note4000_style_profile,
)
from note.natural_blog_types import NaturalStyleProfile
from . import error_codes
from .discourse_planner import DiscourseSection
from .strict_saas import requires_llm_execution


@dataclass
class SectionGenerationResult:
    body: str
    retries: int
    fallback_used: bool
    warnings: List[str] = field(default_factory=list)
    section_summaries: List[str] = field(default_factory=list)
    section_ledgers: List[Dict[str, Any]] = field(default_factory=list)
    style_profile: Dict[str, object] = field(default_factory=dict)
    runtime: Dict[str, object] = field(default_factory=dict)


class SectionGenerationRuntimeError(RuntimeError):
    def __init__(self, message: str, *, reason_code: str, runtime: Optional[Dict[str, object]] = None) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.runtime = dict(runtime or {})


@dataclass
class _SectionGenerationState:
    previous_summary: str = ""
    section_summaries: List[str] = field(default_factory=list)
    remaining_must_cover: List[str] = field(default_factory=list)
    used_fact_slots: List[str] = field(default_factory=list)
    section_ledger: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_contract(cls, contract: Dict[str, object]) -> "_SectionGenerationState":
        return cls(
            remaining_must_cover=[
                str(item or "").strip()
                for item in list(contract.get("must_cover") or [])
                if str(item or "").strip()
            ]
        )

    @property
    def recent_summaries(self) -> List[str]:
        return [str(item or "").strip() for item in self.section_summaries[-2:] if str(item or "").strip()]


def _resolve_style_profile(contract: Dict[str, object]) -> NaturalStyleProfile:
    article_type = str(contract.get("article_type") or "explanatory_article")
    focus = str(contract.get("writing_focus") or "auto")
    tone_profile = str(contract.get("tone_profile") or "auto")
    if tone_profile == "warm":
        style_profile = "casual"
    elif tone_profile in {"formal", "calm"} or article_type == "announcement":
        style_profile = "formal"
    else:
        style_profile = "balanced"
    register_policy = contract.get("register_policy", {})
    base_register = "polite"
    if isinstance(register_policy, dict):
        base_register = str(register_policy.get("base_register") or "polite")
    return build_note4000_style_profile(
        article_type=article_type,
        focus=focus,
        tone_profile=tone_profile,
        style_profile=style_profile,
        base_register=base_register,
    )


def _summarize_for_bridge(text: str) -> str:
    cleaned = " ".join(str(text or "").replace("\r", " ").replace("\n", " ").split())
    if not cleaned:
        return ""
    return cleaned[:120]


_BRIDGE_SUMMARY_PATTERNS: Dict[str, tuple[re.Pattern[str], ...]] = {
    "change": (
        re.compile(r"(変わ|変化|改善|減っ|増え|短くな|そろっ|見えて|でき|分かっ|移った)"),
    ),
    "condition": (
        re.compile(r"(条件|前提|限界|再現|ただし|一方で|例外|場合)"),
    ),
}

_BRIDGE_SUMMARY_CONTROL_PREFIX_RE = re.compile(
    r"^(?:次に|最後に|まず|あわせて|そのうえで|ここで|ここから)"
)
_BRIDGE_SUMMARY_IMPERATIVE_RE = re.compile(
    r"(?:ご確認ください|確認してください|お願いします|進めてください|見てください|従ってください)"
)
_BRIDGE_SUMMARY_META_RE = re.compile(
    r"(?:この記事|本文|この節|ここでは|この会社の輪郭があります|そこに、この会社の輪郭があります)"
)
_BRIDGE_SUMMARY_ABSTRACT_RE = re.compile(
    r"(?:そこに[^。]{0,24}(?:あります|あります。)|(?:大切|重要|必要|価値)です|と捉えています|と感じます)"
)
_BRIDGE_SUMMARY_CONTENT_TOKEN_RE = re.compile(r"[A-Za-z0-9一-龥ぁ-んァ-ヶー]{2,16}")
_BRIDGE_SUMMARY_SPECIFICITY_RE = re.compile(
    r"(?:\d{4}年|\d+月|\d+日|\d+時|対象|管理者|利用者|SSO|metadata|バックアップ|停止|継続|影響|設定|手順|権限|"
    r"問い合わせ|再取得|事前準備|具体例|製造業|医療機関|製薬企業|判断|条件|前提|例外|手戻り|確認先|再現)"
)
_LEDGER_TOKEN_RE = re.compile(r"[A-Za-z0-9一-龥ぁ-んァ-ヶー]{2,16}")
_BRIDGE_FACT_SLOT_PATTERNS: Dict[str, tuple[re.Pattern[str], ...]] = {
    "change": (
        re.compile(r"(?:\d{4}年|\d+月|\d+日|\d+時|更新|変更|切り替え|新しい設定)"),
    ),
    "who_when": (
        re.compile(r"(?:対象|対象者|管理者|利用者|開始時期|切り替え日|日時)"),
    ),
    "impact": (
        re.compile(r"(?:影響|停止|継続|ログイン|認証|接続先)"),
    ),
    "check": (
        re.compile(r"(?:確認事項|ログインテスト|引き継ぎ|連絡先|事前設定)"),
    ),
    "caution": (
        re.compile(r"(?:注意点|認証エラー|旧手順|差し替え|対象外|混同)"),
    ),
    "action": (
        re.compile(r"(?:公式|ヘルプ|サポート|案内ページ|確認先|最新の案内)"),
    ),
}


def _bridge_anchor_terms(section: DiscourseSection) -> List[str]:
    candidates: List[str] = []
    for item in [
        str(getattr(section, "topic_seed", "") or "").strip(),
        str(getattr(section, "reader_question", "") or "").strip(),
        *[str(value or "").strip() for value in list(getattr(section, "must_cover", []) or [])],
        *[str(value or "").strip() for value in list(getattr(section, "related_terms", []) or [])],
    ]:
        compact = item.strip(" 　、。！？")
        if len(compact) < 2 or compact in candidates:
            continue
        candidates.append(compact)
        if len(candidates) >= 8:
            break
    return candidates


def _normalize_bridge_text(text: str) -> str:
    return re.sub(r"\s+", "", str(text or "").strip())


def _looks_like_bridge_heading_echo(section: DiscourseSection, sentence: str) -> bool:
    normalized_sentence = _normalize_bridge_text(sentence)
    if not normalized_sentence:
        return False
    for source in [
        str(getattr(section, "heading", "") or ""),
        str(getattr(section, "reader_question", "") or ""),
    ]:
        candidate = _normalize_bridge_text(source).strip("。！？")
        if len(candidate) < 4:
            continue
        prefix = candidate[: min(len(candidate), 14)]
        if (
            normalized_sentence.startswith(prefix)
            or normalized_sentence.startswith(f"{prefix}は")
            or normalized_sentence.startswith(f"{prefix}とは")
            or normalized_sentence.startswith(f"{prefix}というと")
        ):
            return True
    return False


def _bridge_sentence_penalty(section: DiscourseSection, sentence: str) -> int:
    normalized = _normalize_bridge_text(sentence)
    penalty = 0
    if _BRIDGE_SUMMARY_CONTROL_PREFIX_RE.match(normalized):
        penalty += 5
    if _BRIDGE_SUMMARY_IMPERATIVE_RE.search(normalized):
        penalty += 4
    if _BRIDGE_SUMMARY_META_RE.search(normalized):
        penalty += 4
    if _looks_like_bridge_heading_echo(section, sentence):
        penalty += 6
    if _BRIDGE_SUMMARY_ABSTRACT_RE.search(normalized):
        penalty += 3
    return penalty


def _bridge_sentence_specificity(section: DiscourseSection, sentence: str) -> int:
    normalized = _normalize_bridge_text(sentence)
    if not normalized:
        return 0
    score = 0
    if any(char.isdigit() for char in normalized):
        score += 3
    if len(normalized) >= 28:
        score += 1
    if len(normalized) >= 44:
        score += 1
    content_tokens = {
        token for token in _BRIDGE_SUMMARY_CONTENT_TOKEN_RE.findall(str(sentence or "")) if len(token) >= 2
    }
    if len(content_tokens) >= 4:
        score += 2
    elif len(content_tokens) >= 2:
        score += 1
    if _BRIDGE_SUMMARY_SPECIFICITY_RE.search(normalized):
        score += 2
    slot = str(getattr(section, "fact_slot", "") or "").strip().lower()
    for pattern in _BRIDGE_FACT_SLOT_PATTERNS.get(slot, ()):
        if pattern.search(normalized):
            score += 2
    return score


def _select_bridge_summary(section: DiscourseSection, text: str) -> str:
    cleaned = " ".join(str(text or "").replace("\r", " ").replace("\n", " ").split())
    if not cleaned:
        return ""
    sentences = [item.strip() for item in re.split(r"(?<=[。！？])", cleaned) if item.strip()]
    if not sentences:
        return cleaned[:120]
    patterns = _BRIDGE_SUMMARY_PATTERNS.get(str(section.intent or "").strip().lower(), ())
    anchor_terms = _bridge_anchor_terms(section)
    scored_sentences: List[tuple[int, int, int, int, str]] = []
    for index, sentence in enumerate(sentences):
        pattern_hits = sum(1 for pattern in patterns if pattern.search(sentence))
        anchor_hits = sum(1 for term in anchor_terms if term and term in sentence)
        specificity = _bridge_sentence_specificity(section, sentence)
        penalty = _bridge_sentence_penalty(section, sentence)
        score = pattern_hits * 6 + anchor_hits * 4 + specificity - penalty
        scored_sentences.append((score, specificity, anchor_hits, -index, sentence))
    if scored_sentences:
        scored_sentences.sort(reverse=True)
        return scored_sentences[0][4][:120]
    return sentences[0][:120]


def _clean_generated_paragraph(text: str) -> str:
    body = str(text or "").strip()
    if not body:
        return ""
    paragraph_chunks: List[str] = []
    current_lines: List[str] = []
    for raw_line in body.splitlines():
        stripped = raw_line.strip()
        if re.match(r"^#{1,6}\s+", stripped):
            continue
        if not stripped:
            if current_lines:
                paragraph_chunks.append(" ".join(current_lines).strip())
                current_lines = []
            continue
        current_lines.append(stripped.strip("- ").rstrip())
    if current_lines:
        paragraph_chunks.append(" ".join(current_lines).strip())
    return "\n\n".join(chunk for chunk in paragraph_chunks if chunk).strip()


_COMPARATIVE_FRAGMENT_ENDINGS = (
    "でも",
    "では",
    "ではなく",
    "だけでなく",
    "ても",
    "ですし",
    "が",
    "で",
    "のは",
    "と",
    "とき",
    "多くても",
    "ため",
    "うえで",
    "ままでは",
    "方が",
    "視点が",
    "ものの",
)


_COMPARATIVE_PREDICATE_ENDINGS = (
    "です",
    "ます",
    "でした",
    "ました",
    "ません",
    "ない",
    "たい",
    "する",
    "した",
    "している",
    "してます",
    "できる",
    "なる",
    "なった",
    "である",
    "だった",
    "やすい",
    "にくい",
)


def _looks_like_comparative_list_fragment(base: str, next_sentence: str) -> bool:
    next_head = re.sub(r"[。！？!?]+\s*$", "", str(next_sentence or "").strip())
    if not re.match(r"^[^。！？]{1,24}[、，,]", next_head):
        return False
    tail = re.split(r"[、，,]\s*", str(base or "").strip())[-1].strip()
    if not tail or len(tail) > 12:
        return False
    if not re.fullmatch(r"[一-龥ぁ-んァ-ヶA-Za-z0-9ー・]+", tail):
        return False
    return not any(str(base or "").endswith(ending) for ending in _COMPARATIVE_PREDICATE_ENDINGS)


def _looks_like_comparative_topic_fragment(base: str) -> bool:
    normalized = re.sub(r"[。！？!?]+\s*$", "", str(base or "").strip())
    if len(normalized) < 3 or len(normalized) > 24:
        return False
    if not normalized.endswith(("は", "が")):
        return False
    if any(normalized.endswith(ending) for ending in _COMPARATIVE_PREDICATE_ENDINGS):
        return False
    stem = normalized[:-1].strip()
    if len(stem) < 2:
        return False
    return bool(re.fullmatch(r"[一-龥ぁ-んァ-ヶA-Za-z0-9ー・]+", stem))


_COMPARATIVE_FRAGMENT_START_PREFIXES = (
    "誰が",
    "どこで",
    "何を",
    "どの",
    "どう",
    "実際は",
    "見落とし",
    "現場では",
)


def _looks_like_comparative_clause_fragment(base: str, next_sentence: str) -> bool:
    normalized = re.sub(r"[。！？!?]+\s*$", "", str(base or "").strip())
    if len(normalized) < 2 or len(normalized) > 48:
        return False
    next_head = re.sub(r"[。！？!?]+\s*$", "", str(next_sentence or "").strip())
    if len(next_head) < 3:
        return False
    if normalized.endswith(("止め", "通し", "分け", "比べ", "考え", "見極め")):
        return next_head.startswith(_COMPARATIVE_FRAGMENT_START_PREFIXES)
    if normalized.endswith(("ため", "ものの")):
        return next_head.startswith(_COMPARATIVE_FRAGMENT_START_PREFIXES)
    return False


_COMPARATIVE_INTERROGATIVE_SUMMARY_PREFIXES = (
    "ここ",
    "この",
    "それ",
    "その",
    "そう",
    "こう",
)

def _repair_comparative_demonstrative_noun_predicate(sentence: str) -> str:
    normalized = str(sentence or "").strip()
    match = re.fullmatch(
        r"((?:ここ|これ|それ)(?:が|は)[一-龥ぁ-んァ-ヶA-Za-z0-9ー・]{1,16})のです([。！？!?]*)",
        normalized,
    )
    if not match:
        return normalized
    suffix = match.group(2) or "。"
    return f"{match.group(1)}です{suffix}"


def _looks_like_comparative_interrogative_fragment(base: str, next_sentence: str) -> bool:
    normalized = re.sub(r"[。！？!?]+\s*$", "", str(base or "").strip())
    if len(normalized) < 6 or len(normalized) > 48:
        return False
    if not normalized.endswith(("のか", "なのか", "だろうか")):
        return False
    next_head = re.sub(r"[。！？!?]+\s*$", "", str(next_sentence or "").strip())
    if len(next_head) < 4:
        return False
    return next_head.startswith(_COMPARATIVE_INTERROGATIVE_SUMMARY_PREFIXES)


def _repair_comparative_review_sentence_fragments(text: str) -> str:
    paragraphs = [chunk for chunk in str(text or "").split("\n\n") if chunk.strip()]
    repaired_paragraphs: List[str] = []
    for paragraph in paragraphs:
        sentences = [item for item in re.split(r"(?<=[。！？])", paragraph) if item.strip()]
        if not sentences:
            repaired_paragraphs.append(paragraph.strip())
            continue
        rebuilt: List[str] = []
        idx = 0
        while idx < len(sentences):
            sentence = sentences[idx].strip()
            base = re.sub(r"[。！？!?]+\s*$", "", sentence)
            should_join = False
            if idx + 1 < len(sentences):
                next_sentence = sentences[idx + 1].lstrip()
                should_join = any(base.endswith(ending) for ending in _COMPARATIVE_FRAGMENT_ENDINGS)
                if not should_join:
                    should_join = _looks_like_comparative_list_fragment(base, next_sentence)
                if not should_join:
                    should_join = _looks_like_comparative_topic_fragment(base)
                if not should_join:
                    should_join = _looks_like_comparative_interrogative_fragment(base, next_sentence)
                if not should_join:
                    should_join = _looks_like_comparative_clause_fragment(base, next_sentence)
                if not should_join:
                    should_join = bool(
                        re.search(r"(?:前者|後者)は[^。！？]{0,48}向き$", base)
                        and re.match(r"^(?:前者|後者)は", next_sentence)
                    )
                if should_join:
                    connector = "" if base.endswith("、") else "、"
                    sentence = f"{base}{connector}{next_sentence}"
                    idx += 1
            sentence = sentence.replace(
                "評価軸を先に決める、比較の場では、",
                "評価軸を先に決める。比較の場では、",
                1,
            )
            sentence = sentence.replace("置いてください、通常は", "置いてください。通常は", 1)
            sentence = sentence.replace(
                "という価格帯に見合って、",
                "という価格帯に見合う形で、",
                1,
            )
            sentence = sentence.replace("可能性がありますし、", "可能性があり、", 1)
            sentence = _repair_comparative_demonstrative_noun_predicate(sentence)
            rebuilt.append(sentence)
            idx += 1
        repaired_paragraphs.append("".join(rebuilt).strip())
    return "\n\n".join(chunk for chunk in repaired_paragraphs if chunk).strip()

def _normalize_fact_fragment(text: str) -> str:
    return str(text or "").strip(" 　、。")


def _normalize_ledger_match_text(text: str) -> str:
    return re.sub(r"\s+", "", str(text or "").strip())


def _must_cover_reflected_in_text(text: str, must_cover: str) -> bool:
    normalized_text = _normalize_ledger_match_text(text)
    normalized_item = _normalize_ledger_match_text(must_cover)
    if not normalized_text or not normalized_item:
        return False
    if normalized_item in normalized_text:
        return True
    tokens = []
    for token in _LEDGER_TOKEN_RE.findall(str(must_cover or "")):
        compact = token.strip()
        if compact and compact not in tokens:
            tokens.append(compact)
    if not tokens:
        return False
    matched = sum(1 for token in tokens if _normalize_ledger_match_text(token) in normalized_text)
    threshold = 2 if len(tokens) >= 2 else 1
    return matched >= threshold


def _remaining_must_cover_after_text(text: str, remaining_items: List[str]) -> List[str]:
    unresolved: List[str] = []
    for item in remaining_items:
        normalized = str(item or "").strip()
        if not normalized:
            continue
        if not _must_cover_reflected_in_text(text, normalized):
            unresolved.append(normalized)
    return unresolved


def _build_source_grounding_ledger_items(section: DiscourseSection) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    for item in list(section.source_grounding_items or []):
        if not isinstance(item, dict):
            continue
        items.append(
            {
                "bucket": str(item.get("bucket") or "").strip(),
                "fact_text": str(item.get("fact_text") or "").strip(),
                "source_title": str(item.get("source_title") or "").strip(),
                "locator": str(item.get("locator") or "").strip(),
            }
        )
    return items


def _build_section_ledger(
    *,
    section_index: int,
    section: DiscourseSection,
    previous_summary: str,
    recent_summaries: List[str],
    remaining_before: List[str],
    remaining_after: List[str],
    used_fact_slots_before: List[str],
    used_fact_slots_after: List[str],
    selected_summary: str,
) -> Dict[str, Any]:
    return {
        "section_index": int(section_index),
        "heading": str(section.heading or "").strip(),
        "intent": str(section.intent or "").strip(),
        "fact_slot": str(section.fact_slot or "").strip(),
        "assigned_must_cover": [
            str(item or "").strip()
            for item in list(section.must_cover or [])
            if str(item or "").strip()
        ],
        "assigned_source_grounding_items": _build_source_grounding_ledger_items(section),
        "previous_summary": str(previous_summary or "").strip(),
        "recent_summaries": [str(item or "").strip() for item in recent_summaries if str(item or "").strip()],
        "remaining_must_cover_before": list(remaining_before),
        "remaining_must_cover_after": list(remaining_after),
        "used_fact_slots_before": list(used_fact_slots_before),
        "used_fact_slots_after": list(used_fact_slots_after),
        "selected_summary": str(selected_summary or "").strip(),
    }


def _merge_used_fact_slots(existing_slots: List[str], new_slots: List[str]) -> List[str]:
    merged: List[str] = []
    for slot in [*list(existing_slots or []), *list(new_slots or [])]:
        normalized = str(slot or "").strip()
        if normalized and normalized not in merged:
            merged.append(normalized)
    return merged


def _resolve_section_fact_slots(section: DiscourseSection) -> List[str]:
    slots: List[str] = []
    primary_slot = str(section.fact_slot or "").strip()
    if primary_slot:
        slots.append(primary_slot)
    for item in list(section.source_grounding_items or []):
        if not isinstance(item, dict):
            continue
        slot_key = str(item.get("slot_key") or "").strip()
        if slot_key and slot_key not in slots:
            slots.append(slot_key)
    return slots


def _build_owner_local_state_lines(
    section: DiscourseSection,
    state: _SectionGenerationState,
) -> List[str]:
    lines: List[str] = []
    if state.remaining_must_cover:
        lines.append(f"未回収must_cover: {' / '.join(state.remaining_must_cover[:3])}")
    if state.used_fact_slots:
        lines.append(f"既出fact_slot: {' / '.join(state.used_fact_slots[-4:])}")
    latest_ledger = dict(state.section_ledger[-1]) if state.section_ledger else {}
    latest_heading = str(latest_ledger.get("heading") or "").strip()
    latest_summary = str(latest_ledger.get("selected_summary") or "").strip()
    if latest_heading and latest_summary:
        lines.append(f"直前section ledger: {latest_heading} => {latest_summary}")
    current_slots = _resolve_section_fact_slots(section)
    if current_slots:
        lines.append(f"今回のfact_slot: {' / '.join(current_slots[:4])}")
    return lines


def _advance_section_generation_state(
    *,
    state: _SectionGenerationState,
    section_index: int,
    section: DiscourseSection,
    paragraph: str,
) -> None:
    remaining_before = list(state.remaining_must_cover)
    recent_summaries = list(state.recent_summaries)
    used_fact_slots_before = list(state.used_fact_slots)
    remaining_after = _remaining_must_cover_after_text(paragraph, state.remaining_must_cover)
    used_fact_slots_after = _merge_used_fact_slots(state.used_fact_slots, _resolve_section_fact_slots(section))
    selected_summary = _select_bridge_summary(section, paragraph)
    state.section_ledger.append(
        _build_section_ledger(
            section_index=section_index,
            section=section,
            previous_summary=state.previous_summary,
            recent_summaries=recent_summaries,
            remaining_before=remaining_before,
            remaining_after=remaining_after,
            used_fact_slots_before=used_fact_slots_before,
            used_fact_slots_after=used_fact_slots_after,
            selected_summary=selected_summary,
        )
    )
    state.remaining_must_cover = remaining_after
    state.used_fact_slots = used_fact_slots_after
    state.previous_summary = selected_summary
    state.section_summaries.append(selected_summary)


def _shorten_seed(text: str) -> str:
    value = str(text or "").strip(" 　、。")
    value = value.replace("会社として初めてのnote投稿で、", "")
    value = value.replace("自社の全体像を紹介する", "会社の輪郭")
    if len(value) > 28:
        value = value[:28].rstrip(" 　、。")
    return value or "この話題"


def _fallback_opening(section: DiscourseSection) -> str:
    seed = _shorten_seed(section.topic_seed)
    opening_map = {
        "hook": f"{section.heading}では、{seed}から全体像をつかみます。",
        "problem": f"{section.heading}では、{seed}がどこで詰まりやすかったかを置きます。",
        "value": f"{section.heading}では、{seed}がどこで効くのかを見ていきます。",
        "practice": f"{section.heading}では、{seed}を現場の進め方に引き寄せます。",
        "decision": f"{section.heading}では、{seed}を判断の基準に置きます。",
        "change": f"{section.heading}では、{seed}で何が変わったかを先に確かめます。",
        "condition": f"{section.heading}では、{seed}が成り立つ条件と限界を整理します。",
        "reflection": f"{section.heading}では、{seed}から見えてくる変化を振り返ります。",
        "closing": f"{section.heading}では、{seed}を次の一歩につなげます。",
    }
    return opening_map.get(section.intent, f"{section.heading}では、{seed}を軸に整理します。")


def _fallback_focus_line(section: DiscourseSection, must_cover: str) -> str:
    focus_map = {
        "hook": f"{must_cover}の輪郭を先に置きます。",
        "problem": f"{must_cover}がどの場面で起きていたかを切り分けます。",
        "value": f"{must_cover}が抽象論にならないよう、言葉の置きどころを絞ります。",
        "practice": f"{must_cover}を現場で動く形まで落とし込みます。",
        "decision": f"{must_cover}を比べながら、優先順位が見える形に整えます。",
        "change": f"{must_cover}について、変化した状態を具体文で置きます。",
        "condition": f"{must_cover}について、再現条件と前提を分けて残します。",
        "reflection": f"{must_cover}を振り返り、どこが変わったかを確かめます。",
        "closing": f"{must_cover}を踏まえて、ここから何を進めるかまで結びます。",
    }
    return focus_map.get(section.intent, f"{must_cover}を具体化しながら、読者が次の判断につなげやすい形で整理します。")


def _fallback_closing(section: DiscourseSection) -> str:
    if section.intent == "condition":
        return section.bridge_hint or "ここで再現条件と限界を残し、成功談だけで閉じません。"
    if section.intent == "change":
        return section.bridge_hint or "ここで見えた変化を、次の条件整理へつなげます。"
    if section.intent == "closing":
        return section.bridge_hint or "本文の要点をなぞるだけで終えず、次の動きへ結びます。"
    if section.intent == "reflection":
        return section.bridge_hint or "ここで見えた変化を次の判断へ渡します。"
    return section.bridge_hint or "ここで置いた材料を次の節へつなげます。"


def _resolve_prompt_context_hint(contract: Dict[str, object]) -> str:
    for item in list(contract.get("prompt_context_items", []) or []):
        value = str(item or "").strip()
        if value:
            return value
    return ""


def _fallback_paragraph(
    topic: str,
    section: DiscourseSection,
    compact: bool,
    *,
    prompt_context_hint: str = "",
) -> str:
    must_cover = "、".join(section.must_cover[:2]) if section.must_cover else (section.topic_seed or section.objective)
    grounded_facts = [
        _normalize_fact_fragment(item.get("fact_text", ""))
        for item in list(section.source_grounding_items or [])
        if isinstance(item, dict) and _normalize_fact_fragment(item.get("fact_text", ""))
    ]
    context_line = ""
    if prompt_context_hint and str(section.heading or "").strip() == "会社の輪郭を最初に置く":
        context_line = prompt_context_hint.rstrip("。") + "。"
    if grounded_facts:
        primary_fact = grounded_facts[0]
        secondary_fact = grounded_facts[1] if len(grounded_facts) > 1 else ""
        if compact:
            lead = f"{section.heading}では、{primary_fact}。"
            detail = f"{secondary_fact}。" if secondary_fact else ""
            focus = f"{must_cover}に絞って確認します。"
            return lead + context_line + detail + focus
        lead = _fallback_opening(section)
        fact_line = f"{primary_fact}。"
        detail = f"{secondary_fact}。" if secondary_fact else ""
        focus = _fallback_focus_line(section, must_cover)
        close = _fallback_closing(section)
        return lead + context_line + fact_line + detail + focus + close
    if compact:
        return (
            f"{topic}では、まず{_shorten_seed(section.topic_seed)}を押さえます。"
            f"{context_line}"
            f"{must_cover}に絞って、次の判断に必要な情報だけを整理します。"
        )
    return (
        f"{_fallback_opening(section)}"
        f"{context_line}"
        f"{_fallback_focus_line(section, must_cover)}"
        f"{_fallback_closing(section)}"
    )


def _read_llm_runtime(llm_client: object) -> Dict[str, object]:
    getter = getattr(llm_client, "get_last_call_metadata", None)
    if callable(getter):
        value = getter()
        if isinstance(value, dict):
            return dict(value)
    return {
        "primary_model": "",
        "selected_model": "",
        "base_model": "",
        "model_source": "",
        "task_type": "",
        "article_type": "",
        "effective_reasoning_effort": "",
        "effective_temperature": None,
        "effective_top_p": None,
        "effective_presence_penalty": None,
        "effective_frequency_penalty": None,
        "effective_verbosity": "",
        "compatibility_suppressed_params": [],
        "same_model_retry_count": 0,
        "retry_events": [],
        "last_retry_event": "",
        "model_fallback_attempted": False,
        "model_fallback_blocked": True,
        "prompt_truncation_attempted": False,
        "prompt_truncation_blocked": False,
        "execution_mode": "llm",
    }


def _merge_retry_events(*values: object) -> List[str]:
    merged: List[str] = []
    for value in values:
        if not isinstance(value, list):
            continue
        for item in value:
            text = str(item or "").strip()
            if not text:
                continue
            merged.append(text)
            if len(merged) >= 16:
                return merged
    return merged


def _reason_code_from_exception(exc: Exception) -> str:
    legacy_map = {
        "TRN_RATE_LIMIT": error_codes.TRN_PRIMARY_MODEL_RATE_LIMIT,
        "TRN_TIMEOUT": error_codes.TRN_PRIMARY_MODEL_TIMEOUT,
        "TRN_NETWORK_RESET": error_codes.TRN_PRIMARY_MODEL_NETWORK_RESET,
        "TRN_UPSTREAM_5XX": error_codes.TRN_PRIMARY_MODEL_UPSTREAM_5XX,
    }
    explicit = str(getattr(exc, "reason_code", "") or "").strip()
    if explicit:
        return legacy_map.get(explicit, explicit)
    text = str(exc or "").strip()
    if ":" in text:
        candidate = text.split(":", 1)[0].strip().upper()
        if candidate.startswith(("TRN_", "SYS_", "SEC_", "INP_", "POL_")):
            return legacy_map.get(candidate, candidate)
    return error_codes.SYS_PIPELINE_FAILURE


def _resolve_section_user_instruction(
    section: DiscourseSection,
) -> str:
    for candidate in [
        str(section.section_user_instruction or "").strip(),
        str(section.topic_seed or "").strip(),
        str(section.heading or "").strip(),
    ]:
        if candidate:
            return candidate
    return ""


def _resolve_instruction_anchor_terms(
    section: DiscourseSection,
) -> List[str]:
    if section.instruction_anchor_terms:
        anchors = [str(item or "").strip() for item in list(section.instruction_anchor_terms or []) if str(item or "").strip()][:4]
    else:
        anchors = []
    if not anchors:
        reader_terms = re.findall(r"[A-Za-z0-9一-龥ぁ-んァ-ヶー]{2,16}", str(section.reader_question or ""))
        for item in [
            *list(section.must_cover or []),
            *reader_terms[:2],
            *list(section.related_terms or []),
            str(section.topic_seed or "").strip(),
        ]:
            text = str(item or "").strip()
            if text and text not in anchors:
                anchors.append(text)
            if len(anchors) >= 4:
                break
    return anchors[:4]


def _build_owner_local_prompt_guard_lines(
    section: DiscourseSection,
    contract: Dict[str, object],
) -> List[str]:
    article_type = str(contract.get("article_type") or "").strip().lower()
    allow_experience = bool(contract.get("allow_experience", False))
    has_source_grounding = bool(list(section.source_grounding_items or []))
    lines: List[str] = [
        "同じ役割の短文を連ねず、抽象説明の次は条件・観察・判断のどれかに役割をずらす",
    ]
    if article_type not in {"announcement", "case_study"}:
        lines.append(
            "実在根拠がないのに『変更前/変更後』『導入前/導入後』『以前は/その後』の改善ストーリーを作らない"
        )
    if has_source_grounding:
        lines.append(
            "sourceにない業種・企業規模・部門名・時系列を持ち込まない。具体例はsourceの事実とユーザー指示の範囲だけで組み立てる"
        )
    elif not allow_experience:
        lines.append(
            "具体例を置くなら作業や判断の場面の粒度にとどめ、架空の業種・会社規模・部署構成・地名を足さない"
        )
    return lines


def generate_sections(
    *,
    topic: str,
    media: str,
    sections: List[DiscourseSection],
    contract: Dict[str, object],
    llm_client: Optional[LLMClient] = None,
) -> SectionGenerationResult:
    retries = 0
    warnings: List[str] = []
    compact = bool(contract.get("style_compact_for_seo", False))
    fallback_used = False
    strict_saas_mode = str(contract.get("strict_saas_mode") or "")
    style_profile = _resolve_style_profile(contract)
    runtime: Dict[str, object] = {
        "primary_model": "offline_deterministic",
        "selected_model": "offline_deterministic",
        "base_model": "offline_deterministic",
        "model_source": "deterministic_fallback",
        "task_type": "section",
        "article_type": str(contract.get("article_type") or ""),
        "effective_reasoning_effort": "",
        "effective_temperature": None,
        "effective_top_p": None,
        "effective_presence_penalty": None,
        "effective_frequency_penalty": None,
        "effective_verbosity": "",
        "compatibility_suppressed_params": [],
        "same_model_retry_count": 0,
        "retry_events": [],
        "last_retry_event": "",
        "model_fallback_attempted": False,
        "model_fallback_blocked": True,
        "prompt_truncation_attempted": False,
        "prompt_truncation_blocked": False,
        "execution_mode": "offline_deterministic",
    }

    local_llm: Optional[LLMClient] = llm_client

    chunks: List[str] = []
    state = _SectionGenerationState.from_contract(contract)
    for section_index, section in enumerate(sections):
        paragraph = ""
        recent_summaries = list(state.recent_summaries)
        if local_llm is not None:
            prompt = build_note4000_section_prompt(
                section=section,
                speaker_profile=str(contract.get("speaker_profile") or "書き手"),
                audience_profile=str(contract.get("audience_profile") or "読者"),
                relationship_mode=str(contract.get("relationship_mode") or "guide"),
                style_profile=style_profile,
                previous_summary=state.previous_summary,
                recent_summaries=recent_summaries,
                forbidden_topics=list(contract.get("forbidden_topics", []) or []),
                allowed_pronouns=list(contract.get("allowed_pronouns", []) or []),
                user_instruction=_resolve_section_user_instruction(section),
                instruction_anchor_terms=_resolve_instruction_anchor_terms(section),
                source_grounding_items=list(section.source_grounding_items or []),
            )
            owner_local_state_lines = _build_owner_local_state_lines(section, state)
            if owner_local_state_lines:
                prompt = (
                    f"{prompt}\n【SECTION_STATE】\n"
                    + "\n".join(f"- {line}" for line in owner_local_state_lines)
                )
            owner_local_prompt_guard_lines = _build_owner_local_prompt_guard_lines(section, contract)
            if owner_local_prompt_guard_lines:
                prompt = (
                    f"{prompt}\n【補足ルール】\n"
                    + "\n".join(f"- {line}" for line in owner_local_prompt_guard_lines)
                )
            try:
                paragraph = local_llm.generate_text(
                    prompt,
                    max_tokens=max(360, int(section.target_chars * 1.35)),
                    task_type="section",
                    article_type=str(contract.get("article_type") or ""),
                    runtime_policy=dict(contract.get("llm_runtime_policy", {}) or {}),
                ).strip()
                paragraph = _clean_generated_paragraph(paragraph)
                if str(contract.get("article_type") or "").strip().lower() == "comparative_review":
                    paragraph = _repair_comparative_review_sentence_fragments(paragraph)
                call_runtime = _read_llm_runtime(local_llm)
                total_retries = int(runtime.get("same_model_retry_count", 0)) + int(
                    call_runtime.get("same_model_retry_count", 0)
                )
                retry_events = _merge_retry_events(
                    runtime.get("retry_events"),
                    call_runtime.get("retry_events"),
                )
                last_retry_event = str(
                    call_runtime.get("last_retry_event") or runtime.get("last_retry_event") or ""
                )
                runtime.update(call_runtime)
                runtime["same_model_retry_count"] = total_retries
                runtime["retry_events"] = retry_events
                runtime["last_retry_event"] = last_retry_event
                retries = int(runtime.get("same_model_retry_count", 0))
            except LLMRuntimeError as exc:
                call_runtime = dict(getattr(exc, "call_metadata", {}) or {})
                total_retries = int(runtime.get("same_model_retry_count", 0)) + int(
                    call_runtime.get("same_model_retry_count", 0)
                )
                retry_events = _merge_retry_events(
                    runtime.get("retry_events"),
                    call_runtime.get("retry_events"),
                )
                last_retry_event = str(
                    call_runtime.get("last_retry_event") or runtime.get("last_retry_event") or ""
                )
                runtime.update(call_runtime)
                runtime["same_model_retry_count"] = total_retries
                runtime["retry_events"] = retry_events
                runtime["last_retry_event"] = last_retry_event
                retries = int(runtime.get("same_model_retry_count", 0))
                raise SectionGenerationRuntimeError(
                    str(exc),
                    reason_code=str(getattr(exc, "reason_code", error_codes.SYS_LLM_RETRY_EXHAUSTED)),
                    runtime=runtime,
                ) from exc
            except Exception as exc:
                raise SectionGenerationRuntimeError(
                    str(exc),
                    reason_code=_reason_code_from_exception(exc),
                    runtime=runtime,
                ) from exc
            if not paragraph:
                warnings.append(error_codes.SYS_LLM_RETRY_EXHAUSTED)
                raise SectionGenerationRuntimeError(
                    "Primary model returned empty section body",
                    reason_code=error_codes.SYS_PRIMARY_MODEL_RETRY_EXHAUSTED,
                    runtime=runtime,
                )
        else:
            if requires_llm_execution(strict_saas_mode):
                raise SectionGenerationRuntimeError(
                    "LLM client is required in strict SaaS mode",
                    reason_code=error_codes.SYS_LLM_CLIENT_REQUIRED,
                    runtime=runtime,
                )
            paragraph = _fallback_paragraph(
                topic,
                section,
                compact,
                prompt_context_hint=_resolve_prompt_context_hint(contract),
            )
            fallback_used = True
        chunks.append(f"## {section.heading}\n{paragraph}")
        _advance_section_generation_state(
            state=state,
            section_index=section_index,
            section=section,
            paragraph=paragraph,
        )

    return SectionGenerationResult(
        body="\n\n".join(chunks).strip(),
        retries=retries,
        fallback_used=fallback_used,
        warnings=warnings,
        section_summaries=list(state.section_summaries),
        section_ledgers=[dict(item) for item in list(state.section_ledger or [])],
        style_profile=style_profile.to_dict(),
        runtime=runtime,
    )
