"""Discourse planning for note-oriented newalgorithm pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, ClassVar, Dict, List

from note.natural_blog_core import (
    build_note4000_discourse_plan,
    build_note4000_length_plan,
    resolve_note4000_section_prompt_contract,
)


@dataclass
class DiscourseSection:
    CANONICAL_PLAN_FIELDS: ClassVar[tuple[str, ...]] = (
        "heading",
        "intent",
        "target_chars",
        "topic_seed",
        "fact_slot",
        "related_terms",
        "reader_question",
        "bridge_hint",
        "must_cover",
        "source_grounding_items",
        "new_information",
        "section_user_instruction",
        "instruction_anchor_terms",
    )
    CANONICAL_ROUTE_EXTENSION_FIELDS: ClassVar[tuple[str, ...]] = (
        "related_terms",
        "must_cover",
        "source_grounding_items",
        "instruction_anchor_terms",
    )
    CANONICAL_SOURCE_GROUNDING_FIELDS: ClassVar[tuple[str, ...]] = (
        "bucket",
        "fact_text",
        "source_title",
        "locator",
        "slot_key",
        "slot_label",
        "slot_role",
        "slot_optional",
        "slot_intents",
    )

    heading: str
    objective: str
    target_chars: int = 520
    topic_seed: str = ""
    fact_slot: str = ""
    related_terms: List[str] = field(default_factory=list)
    reader_question: str = ""
    bridge_hint: str = ""
    must_cover: List[str] = field(default_factory=list)
    source_grounding_items: List[Dict[str, Any]] = field(default_factory=list)
    new_information: str = ""
    section_user_instruction: str = ""
    instruction_anchor_terms: List[str] = field(default_factory=list)

    @property
    def intent(self) -> str:
        return self.objective

    @classmethod
    def from_section_plan(cls, *, item: Any, prompt_contract: Dict[str, object]) -> "DiscourseSection":
        section = cls(
            heading=str(getattr(item, "heading", "") or ""),
            objective=str(getattr(item, "intent", "") or ""),
            target_chars=int(getattr(item, "target_chars", 520) or 520),
            topic_seed=str(getattr(item, "topic_seed", "") or getattr(item, "heading", "") or ""),
            fact_slot=str(getattr(item, "fact_slot", "") or ""),
            related_terms=list(getattr(item, "related_terms", []) or []),
            reader_question=str(getattr(item, "reader_question", "") or ""),
            bridge_hint=str(getattr(item, "bridge_hint", "") or ""),
            must_cover=list(getattr(item, "must_cover", []) or []),
            source_grounding_items=[],
            new_information=str(getattr(item, "new_information", "") or getattr(item, "topic_seed", "") or ""),
            section_user_instruction=str(prompt_contract.get("user_instruction") or ""),
            instruction_anchor_terms=_normalize_text_list(prompt_contract.get("instruction_anchor_terms")),
        )
        return section.normalize()

    def normalize(self) -> "DiscourseSection":
        self.objective = _normalize_discourse_text(self.objective) or "body"
        self.target_chars = _normalize_target_chars(self.target_chars)
        self.must_cover = _normalize_text_list(self.must_cover)
        self.reader_question = _normalize_discourse_text(self.reader_question)
        self.bridge_hint = _normalize_discourse_text(self.bridge_hint)
        self.fact_slot = _normalize_discourse_text(self.fact_slot)
        self.source_grounding_items = _normalize_source_grounding_items(self.source_grounding_items)
        primary_label = _resolve_section_primary_label(self)
        self.heading = _normalize_discourse_text(self.heading) or primary_label or "この節"
        normalized_topic_seed = _normalize_discourse_text(self.topic_seed)
        if not normalized_topic_seed or _looks_broken_topic_seed(normalized_topic_seed):
            normalized_topic_seed = primary_label or self.heading
        self.topic_seed = normalized_topic_seed
        normalized_new_information = _normalize_discourse_text(self.new_information)
        if not normalized_new_information or _looks_broken_topic_seed(normalized_new_information):
            normalized_new_information = primary_label or self.topic_seed
        self.new_information = normalized_new_information
        normalized_section_instruction = _normalize_discourse_text(self.section_user_instruction)
        if not normalized_section_instruction or _looks_broken_topic_seed(normalized_section_instruction):
            normalized_section_instruction = primary_label or self.heading
        self.section_user_instruction = normalized_section_instruction
        self.related_terms = _normalize_discourse_related_terms(self)
        self.instruction_anchor_terms = _normalize_discourse_instruction_anchor_terms(self)
        return self

    def to_canonical_state(self) -> Dict[str, Any]:
        self.normalize()
        return {
            "heading": self.heading,
            "intent": self.intent,
            "target_chars": self.target_chars,
            "topic_seed": self.topic_seed,
            "fact_slot": self.fact_slot,
            "related_terms": list(self.related_terms),
            "reader_question": self.reader_question,
            "bridge_hint": self.bridge_hint,
            "must_cover": list(self.must_cover),
            "source_grounding_items": [dict(item) for item in list(self.source_grounding_items or [])],
            "new_information": self.new_information,
            "section_user_instruction": self.section_user_instruction,
            "instruction_anchor_terms": list(self.instruction_anchor_terms),
        }


_OVERLITERAL_FOCUS_RE = re.compile(
    r"(含める|解説記事|業界分析|比較レビュー|日常記事|記事|ブログ|まとめ|(?:企業|会社|自社)(?:の)?紹介)"
)
_CASE_STUDY_BEFORE_FACT_RE = re.compile(
    r"(導入前|改善前|見直し前|背景説明が長|読みづら|判断できなかった|迷い|つまず|止ま|課題|遅延|延びていた)"
)
_CASE_STUDY_PROCESS_FACT_RE = re.compile(
    r"(進め方|手順|後段|退避|分類|並べ替え|洗い出し|確認ポイント|所要時間|対象者|試験運用|役割)"
)
_CASE_STUDY_CHANGE_FACT_RE = re.compile(
    r"(導入後|改善後|見直し後|変わ|改善|減っ|増え|短くな|早くな|そろっ|分かりやす|完了率|差し戻し理由|立ち止まる場面が減)"
)
_CASE_STUDY_CONDITION_FACT_RE = re.compile(
    r"(再現条件|条件として|条件は|前提として|前提を|前提が|ただし|限界|例外|場合|分岐|退避先|必要があります|必要です)"
)

_ANNOUNCEMENT_DENSE_BRIDGE_HINTS = [
    "変更点の確定事実を先に置き、準備項目へ自然につなぐ",
    "対象者と時期の混線を避け、利用影響の説明に渡す",
    "必要な行動を先に言い切り、確認観点を補う",
    "迷いやすい点と影響範囲を分けて置き、確認先へつなぐ",
    "公式情報の確認先と最後の対応だけを簡潔に残す",
]

_ANNOUNCEMENT_DENSE_READER_QUESTIONS = [
    "変更点",
    "対象者と実施時期",
    "更新前後の確認事項",
    "迷いやすい判断ポイント",
    "公式情報の確認先",
]
_BROKEN_TOPIC_SEED_RE = re.compile(r"^[ぁ-んァ-ヶーa-zA-Z0-9]{1,3}$")


def _is_compact_focus_anchor(text: str, *, raw_topic: str = "") -> bool:
    value = str(text or "").strip()
    topic = str(raw_topic or "").strip()
    if not value:
        return False
    if len(value) > 32:
        return False
    if "。" in value and len(value) > 18:
        return False
    if topic and value == topic and len(value) > 20:
        return False
    if _OVERLITERAL_FOCUS_RE.search(value):
        return False
    return True


def _normalize_text_list(values: object) -> List[str]:
    if not isinstance(values, list):
        return []
    normalized: List[str] = []
    for item in values:
        text = str(item or "").strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _normalize_discourse_text(value: object) -> str:
    return str(value or "").strip()


def _normalize_target_chars(value: object) -> int:
    try:
        normalized = int(value or 0)
    except (TypeError, ValueError):
        normalized = 0
    return normalized if normalized > 0 else 520


def _resolve_section_primary_label(section: DiscourseSection) -> str:
    topic_seed = _normalize_discourse_text(section.topic_seed)
    candidates: List[str] = []
    if topic_seed and not _looks_broken_topic_seed(topic_seed):
        candidates.append(topic_seed)
    candidates.extend(_normalize_discourse_text(item) for item in list(section.must_cover or [])[:1])
    source_anchor = _derive_source_grounding_label(list(section.source_grounding_items or []))
    if source_anchor:
        candidates.append(source_anchor)
    candidates.extend(
        [
            _normalize_discourse_text(section.reader_question),
            _normalize_discourse_text(section.heading),
            _normalize_discourse_text(section.objective),
        ]
    )
    for candidate in candidates:
        if candidate:
            return candidate
    return ""


def _looks_broken_topic_seed(text: object) -> bool:
    value = _normalize_discourse_text(text)
    if not value:
        return True
    if _BROKEN_TOPIC_SEED_RE.fullmatch(value):
        return True
    if len(value) <= 4 and not re.search(r"[一-龥々]", value):
        return True
    return False


def _derive_source_grounding_label(items: List[Dict[str, Any]]) -> str:
    for item in items:
        fact_text = _normalize_discourse_text(item.get("fact_text"))
        if not fact_text:
            continue
        label = re.split(r"[。!?]", fact_text, maxsplit=1)[0].strip(" 　、。")
        if len(label) > 28 and "、" in label:
            label = label.split("、", 1)[0].strip(" 　、。")
        label = re.sub(r"(?:です|ます|でした|である|しています|している|があります|がある)$", "", label)
        label = label.strip(" 　、。")
        if 6 <= len(label) <= 28:
            return label
    return ""


def _normalize_discourse_related_terms(section: DiscourseSection) -> List[str]:
    return _normalize_text_list(
        [
            *list(section.related_terms or []),
            section.topic_seed,
            *list(section.must_cover or [])[:2],
        ]
    )[:4]


def _normalize_discourse_instruction_anchor_terms(section: DiscourseSection) -> List[str]:
    return _normalize_text_list(
        [
            *list(section.instruction_anchor_terms or []),
            *list(section.must_cover or []),
            section.section_user_instruction,
            section.reader_question,
            *list(section.related_terms or []),
            section.topic_seed,
        ]
    )[:4]


_GENERIC_SOURCE_SLOT_SPECS: Dict[str, Dict[str, Any]] = {
    "overview": {
        "slot_key": "context_anchor",
        "slot_label": "前提・背景",
        "slot_role": "primary",
        "slot_optional": False,
        "slot_intents": ["hook", "problem", "value", "closing"],
    },
    "company": {
        "slot_key": "context_anchor",
        "slot_label": "前提・背景",
        "slot_role": "primary",
        "slot_optional": False,
        "slot_intents": ["hook", "problem", "value", "closing"],
    },
    "strength": {
        "slot_key": "value_signal",
        "slot_label": "価値・強み",
        "slot_role": "primary",
        "slot_optional": False,
        "slot_intents": ["value", "practice", "decision", "closing", "action"],
    },
    "values": {
        "slot_key": "operating_principle",
        "slot_label": "価値観・判断軸",
        "slot_role": "support",
        "slot_optional": True,
        "slot_intents": ["value", "decision", "closing", "action"],
    },
    "history": {
        "slot_key": "history_anchor",
        "slot_label": "経緯・歩み",
        "slot_role": "support",
        "slot_optional": True,
        "slot_intents": ["hook", "closing", "action", "decision"],
    },
    "構成とサイズ": {
        "slot_key": "context_anchor",
        "slot_label": "前提・背景",
        "slot_role": "primary",
        "slot_optional": False,
        "slot_intents": ["hook", "problem", "decision"],
    },
    "主な特徴": {
        "slot_key": "value_signal",
        "slot_label": "主な特徴",
        "slot_role": "primary",
        "slot_optional": False,
        "slot_intents": ["value", "practice", "decision", "action"],
    },
    "活用場面": {
        "slot_key": "usage_scene",
        "slot_label": "活用場面",
        "slot_role": "support",
        "slot_optional": True,
        "slot_intents": ["practice", "decision", "closing", "action"],
    },
    "公開条件": {
        "slot_key": "access_condition",
        "slot_label": "公開条件",
        "slot_role": "primary",
        "slot_optional": False,
        "slot_intents": ["decision", "condition", "action"],
    },
    "使う環境": {
        "slot_key": "environment_requirement",
        "slot_label": "使う環境",
        "slot_role": "support",
        "slot_optional": True,
        "slot_intents": ["practice", "condition", "decision"],
    },
    "主要な数値": {
        "slot_key": "metric_signal",
        "slot_label": "主要な数値",
        "slot_role": "support",
        "slot_optional": True,
        "slot_intents": ["hook", "change", "decision", "closing"],
    },
    "other": {
        "slot_key": "support_detail",
        "slot_label": "補足事実",
        "slot_role": "support",
        "slot_optional": True,
        "slot_intents": ["hook", "problem", "practice", "decision", "change", "condition", "action", "closing"],
    },
}

_CASE_STUDY_SOURCE_SLOT_SPECS: Dict[str, Dict[str, Any]] = {
    "case_before": {
        "slot_key": "case_before_state",
        "slot_label": "導入前の状態",
        "slot_role": "primary",
        "slot_optional": False,
        "slot_intents": ["hook", "problem"],
    },
    "case_process": {
        "slot_key": "case_process_step",
        "slot_label": "進め方・途中の工夫",
        "slot_role": "primary",
        "slot_optional": False,
        "slot_intents": ["practice", "decision", "condition"],
    },
    "case_change": {
        "slot_key": "case_change_result",
        "slot_label": "結果として起きた変化",
        "slot_role": "primary",
        "slot_optional": False,
        "slot_intents": ["change", "decision", "closing"],
    },
    "case_condition": {
        "slot_key": "case_reproduction_condition",
        "slot_label": "再現条件",
        "slot_role": "primary",
        "slot_optional": False,
        "slot_intents": ["condition", "decision", "action"],
    },
    "other": {
        "slot_key": "case_supporting_detail",
        "slot_label": "補足事実",
        "slot_role": "support",
        "slot_optional": True,
        "slot_intents": ["problem", "practice", "decision", "change", "condition"],
    },
}


def _normalize_slot_intents(values: object) -> List[str]:
    raw_values: List[object]
    if isinstance(values, list):
        raw_values = list(values)
    elif isinstance(values, tuple):
        raw_values = list(values)
    elif str(values or "").strip():
        raw_values = [values]
    else:
        return []
    normalized: List[str] = []
    for item in raw_values:
        text = str(item or "").strip().lower()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _normalize_slot_optional(value: object, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value or "").strip().lower()
    if not normalized:
        return default
    if normalized in {"1", "true", "yes", "optional"}:
        return True
    if normalized in {"0", "false", "no", "required"}:
        return False
    return default


def _normalize_slot_role(value: object, *, default: str) -> str:
    normalized = str(value or default).strip().lower() or default
    return normalized if normalized in {"primary", "support"} else default


def _resolve_source_slot_spec(*, bucket: str, article_type: str) -> Dict[str, Any]:
    normalized_bucket = str(bucket or "other").strip() or "other"
    normalized_type = str(article_type or "").strip().lower()
    if normalized_bucket.startswith("case_") and normalized_bucket in _CASE_STUDY_SOURCE_SLOT_SPECS:
        return dict(_CASE_STUDY_SOURCE_SLOT_SPECS[normalized_bucket])
    if normalized_type == "case_study" and normalized_bucket == "other":
        return dict(_CASE_STUDY_SOURCE_SLOT_SPECS["other"])
    return dict(_GENERIC_SOURCE_SLOT_SPECS.get(normalized_bucket, _GENERIC_SOURCE_SLOT_SPECS["other"]))


def _normalize_source_grounding_item(
    item: Dict[str, Any],
    *,
    article_type: str = "",
    preserve_slot_metadata: bool = True,
) -> Dict[str, Any] | None:
    fact_text = str(item.get("fact_text") or "").strip()
    if not fact_text:
        return None
    bucket = str(item.get("bucket") or "other").strip() or "other"
    slot_spec = _resolve_source_slot_spec(bucket=bucket, article_type=article_type)
    existing_slot_key = item.get("slot_key") if preserve_slot_metadata else ""
    existing_slot_label = item.get("slot_label") if preserve_slot_metadata else ""
    existing_slot_role = item.get("slot_role") if preserve_slot_metadata else ""
    existing_slot_optional = item.get("slot_optional") if preserve_slot_metadata else None
    existing_slot_intents = item.get("slot_intents") if preserve_slot_metadata else []
    slot_intents = _normalize_slot_intents(existing_slot_intents) or list(slot_spec["slot_intents"])
    return {
        "bucket": bucket,
        "fact_text": fact_text,
        "source_title": str(item.get("source_title") or "").strip(),
        "locator": str(item.get("locator") or "").strip(),
        "slot_key": str(existing_slot_key or slot_spec["slot_key"]).strip() or str(slot_spec["slot_key"]),
        "slot_label": str(existing_slot_label or slot_spec["slot_label"]).strip() or str(slot_spec["slot_label"]),
        "slot_role": _normalize_slot_role(existing_slot_role, default=str(slot_spec["slot_role"])),
        "slot_optional": _normalize_slot_optional(existing_slot_optional, default=bool(slot_spec["slot_optional"])),
        "slot_intents": slot_intents,
    }


def _normalize_source_grounding_items(
    values: object,
    *,
    article_type: str = "",
    preserve_slot_metadata: bool = True,
) -> List[Dict[str, Any]]:
    if not isinstance(values, list):
        return []
    normalized: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in values:
        if not isinstance(item, dict):
            continue
        normalized_item = _normalize_source_grounding_item(
            item,
            article_type=article_type,
            preserve_slot_metadata=preserve_slot_metadata,
        )
        if normalized_item is None:
            continue
        fact_text = str(normalized_item.get("fact_text") or "").strip()
        dedupe_key = "".join(fact_text.split())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        normalized.append(normalized_item)
    return normalized


def _case_study_grounding_bucket(item: Dict[str, Any]) -> str:
    explicit_bucket = str(item.get("bucket") or "").strip()
    if explicit_bucket and explicit_bucket != "other":
        return explicit_bucket
    fact_text = str(item.get("fact_text") or "").strip()
    if not fact_text:
        return explicit_bucket or "other"
    if _CASE_STUDY_CONDITION_FACT_RE.search(fact_text):
        return "case_condition"
    if _CASE_STUDY_BEFORE_FACT_RE.search(fact_text):
        return "case_before"
    if _CASE_STUDY_PROCESS_FACT_RE.search(fact_text):
        return "case_process"
    if _CASE_STUDY_CHANGE_FACT_RE.search(fact_text):
        return "case_change"
    return explicit_bucket or "other"


def _prepare_route_source_grounding_items(
    items: List[Dict[str, Any]],
    *,
    article_type: str,
) -> List[Dict[str, Any]]:
    normalized_type = str(article_type or "").strip().lower()
    if normalized_type != "case_study":
        return _normalize_source_grounding_items(items, article_type=normalized_type)
    prepared: List[Dict[str, Any]] = []
    for item in items:
        routed = dict(item)
        routed["bucket"] = _case_study_grounding_bucket(routed)
        prepared.append(routed)
    return _normalize_source_grounding_items(
        prepared,
        article_type=normalized_type,
        preserve_slot_metadata=False,
    )


def _source_item_supports_intent(item: Dict[str, Any], *, section_intent: str) -> bool:
    normalized_intent = str(section_intent or "").strip().lower()
    if not normalized_intent:
        return True
    slot_intents = _normalize_slot_intents(item.get("slot_intents"))
    if not slot_intents:
        return True
    return normalized_intent in slot_intents


def _pick_grounding_item(
    items: List[Dict[str, Any]],
    used_indexes: set[int],
    preferred_buckets: List[str],
    *,
    section_intent: str = "",
) -> int:
    for bucket in preferred_buckets:
        for index, item in enumerate(items):
            if index in used_indexes:
                continue
            if str(item.get("bucket") or "other") != bucket:
                continue
            if not _source_item_supports_intent(item, section_intent=section_intent):
                continue
            return index
    for bucket in preferred_buckets:
        for index, item in enumerate(items):
            if index in used_indexes:
                continue
            if str(item.get("bucket") or "other") == bucket:
                return index
    if str(section_intent or "").strip():
        for index, item in enumerate(items):
            if index in used_indexes:
                continue
            if _source_item_supports_intent(item, section_intent=section_intent):
                return index
    for index, _item in enumerate(items):
        if index not in used_indexes:
            return index
    return -1


def _preferred_grounding_buckets_by_index(
    *,
    section_count: int,
    article_type: str,
    semantic_article_key: str,
) -> Dict[int, List[str]]:
    base_preferences: Dict[int, List[str]] = {
        0: ["overview", "strength", "other", "history"],
        1: ["strength", "overview", "other", "history"],
        2: ["other", "strength", "overview", "history"],
        max(0, section_count - 2): ["history", "strength", "overview", "other"],
        section_count - 1: ["strength", "overview", "history", "other"],
    }
    if article_type == "branding" and semantic_article_key == "product_introduction":
        base_preferences[max(0, section_count - 2)] = ["other", "strength", "overview", "history"]
        base_preferences[section_count - 1] = ["other", "overview", "strength", "history"]
    if article_type == "case_study":
        base_preferences[0] = ["case_before", "history", "overview", "other", "case_process"]
        base_preferences[1] = ["case_before", "case_process", "overview", "other", "history"]
        base_preferences[2] = ["case_process", "case_before", "case_change", "other", "overview"]
        base_preferences[max(0, section_count - 2)] = [
            "case_change",
            "case_process",
            "case_condition",
            "other",
            "overview",
        ]
        base_preferences[section_count - 1] = [
            "case_condition",
            "case_process",
            "case_change",
            "other",
            "overview",
        ]
    return base_preferences


def _preferred_grounding_indices(
    *,
    section_count: int,
    article_type: str,
) -> List[int]:
    if section_count <= 0:
        return []
    normalized_type = str(article_type or "").strip().lower()
    if normalized_type == "case_study":
        return [index for index in [0, 1, max(0, section_count - 2), section_count - 1, 2, 3] if 0 <= index < section_count]
    return [index for index in [0, 1, 2, max(0, section_count - 2), section_count - 1] if 0 <= index < section_count]


def _ensure_case_study_tail_grounding(
    sections: List[DiscourseSection],
    source_grounding_items: List[Dict[str, Any]],
    preferred_buckets_by_index: Dict[int, List[str]],
) -> None:
    if not sections or not source_grounding_items:
        return
    for section_index, section in enumerate(sections):
        if str(section.intent or "").strip().lower() not in {"change", "condition"}:
            continue
        if list(section.source_grounding_items or []):
            continue
        pick = _pick_grounding_item(
            source_grounding_items,
            set(),
            preferred_buckets_by_index.get(section_index, ["case_change", "case_condition", "case_process", "other"]),
            section_intent=section.intent,
        )
        if pick < 0:
            continue
        section.source_grounding_items.append(dict(source_grounding_items[pick]))


def _apply_source_grounding(
    sections: List[DiscourseSection],
    source_grounding_items: List[Dict[str, Any]],
    *,
    article_type: str = "",
    semantic_article_key: str = "",
) -> None:
    if not sections or not source_grounding_items:
        return
    routed_grounding_items = _prepare_route_source_grounding_items(
        source_grounding_items,
        article_type=article_type,
    )
    preferred_indices = _preferred_grounding_indices(
        section_count=len(sections),
        article_type=article_type,
    )
    target_indices: List[int] = []
    for index in preferred_indices:
        if index not in target_indices:
            target_indices.append(index)
    preferred_buckets_by_index = _preferred_grounding_buckets_by_index(
        section_count=len(sections),
        article_type=str(article_type or "").strip().lower(),
        semantic_article_key=str(semantic_article_key or "").strip().lower(),
    )
    used_indexes: set[int] = set()
    for section_index in target_indices:
        pick = _pick_grounding_item(
            routed_grounding_items,
            used_indexes,
            preferred_buckets_by_index.get(section_index, ["overview", "strength", "history", "other"]),
            section_intent=sections[section_index].intent,
        )
        if pick < 0:
            continue
        sections[section_index].source_grounding_items.append(dict(routed_grounding_items[pick]))
        used_indexes.add(pick)
    if str(article_type or "").strip().lower() == "case_study":
        _ensure_case_study_tail_grounding(sections, routed_grounding_items, preferred_buckets_by_index)
    remaining_indexes = [index for index in range(len(routed_grounding_items)) if index not in used_indexes]
    if not remaining_indexes:
        return
    round_robin_indices = [index for index in range(len(sections)) if index not in target_indices] or target_indices
    for offset, item_index in enumerate(remaining_indexes):
        target_index = round_robin_indices[offset % len(round_robin_indices)]
        sections[target_index].source_grounding_items.append(dict(routed_grounding_items[item_index]))


def _resolve_lens_section_index(lens: str, section_count: int) -> int:
    if section_count <= 1:
        return 0
    value = str(lens or "")
    if any(keyword in value for keyword in ("法務", "コンプライアンス", "リーガル")):
        return max(1, section_count - 2)
    if any(keyword in value for keyword in ("ブランド", "ブランディング", "広報")):
        return min(section_count - 1, 1)
    return min(section_count - 1, 2)


def _apply_focus_bundle(
    sections: List[DiscourseSection],
    *,
    main_focus: str,
    support_points: List[str],
    raw_topic: str = "",
    semantic_article_key: str = "",
) -> None:
    if not sections:
        return
    first_section = sections[0]
    anchor = str(main_focus or "").strip()
    if anchor and _is_compact_focus_anchor(anchor, raw_topic=raw_topic):
        if anchor not in first_section.related_terms:
            first_section.related_terms.insert(0, anchor)
        if str(semantic_article_key or "").strip().lower() == "product_introduction":
            return
        first_section.topic_seed = anchor
        if anchor not in first_section.objective:
            first_section.objective = f"{first_section.objective}。{anchor}を起点に話を進める"
        first_section.new_information = anchor


def _stabilize_explanatory_must_cover_headings(sections: List[DiscourseSection]) -> None:
    if not sections:
        return
    rewritten_labels: set[str] = set()
    heading_map = {
        "前提": "前提をそろえる",
        "判断軸": "判断軸を整理する",
        "実務での使いどころ": "実務での使いどころを見る",
    }
    for section in sections:
        primary = str((section.must_cover or [""])[0] or "").strip()
        if not primary or primary in rewritten_labels:
            continue
        replacement = heading_map.get(primary, "")
        if not replacement or primary in str(section.heading or ""):
            rewritten_labels.add(primary)
            continue
        section.heading = replacement
        rewritten_labels.add(primary)


def _stabilize_case_study_hook_section(sections: List[DiscourseSection]) -> None:
    if not sections:
        return
    first_section = sections[0]
    if str(first_section.intent or "").strip() != "hook":
        return

    before_focus = "導入前の課題"
    if before_focus not in list(first_section.must_cover or []):
        first_section.must_cover = [before_focus, *list(first_section.must_cover or [])]

    first_section.topic_seed = before_focus
    first_section.reader_question = "どこで止まっていたか"
    first_section.section_user_instruction = before_focus
    first_section.new_information = before_focus
    first_section.instruction_anchor_terms = _normalize_text_list(
        [
            before_focus,
            first_section.reader_question,
            *list(first_section.instruction_anchor_terms or []),
            *list(first_section.must_cover or []),
            *list(first_section.related_terms or []),
        ]
    )[:4]
    first_section.related_terms = _normalize_text_list(
        [
            before_focus,
            "どこで止まっていたか",
            *list(first_section.related_terms or []),
        ]
    )[:4]


def _is_announcement_dense_route(
    contract: Dict[str, object],
    *,
    article_type: str,
    semantic_article_key: str,
    must_cover_items: List[str],
) -> bool:
    ui_journey = dict(contract.get("ui_journey", {}) or {})
    return (
        article_type == "announcement"
        and semantic_article_key == "announcement"
        and str(contract.get("content_goal") or "").strip().lower() == "action"
        and str(contract.get("writing_focus") or "").strip().lower() == "explanation"
        and str(contract.get("length_mode") or "").strip().lower() == "short"
        and str(ui_journey.get("purpose_key") or "").strip().lower() == "announce"
        and str(ui_journey.get("target_key") or "").strip().lower() == "standard"
        and len(must_cover_items) >= 3
    )


def _stabilize_announcement_dense_sections(
    sections: List[DiscourseSection],
    *,
    must_cover_items: List[str],
) -> None:
    if len(sections) < 3 or len(must_cover_items) < 3:
        return
    heading_map = {
        "変更点": "変更点を先に整理する",
        "対象と時期": "対象と時期を確認する",
        "必要な行動": "必要な行動と確認ポイント",
    }
    for index, label in enumerate(must_cover_items[:3]):
        normalized_label = str(label or "").strip()
        if not normalized_label:
            continue
        section = sections[index]
        existing_must_cover = [
            str(item or "").strip()
            for item in list(section.must_cover or [])
            if str(item or "").strip()
        ]
        section.must_cover = [normalized_label, *[item for item in existing_must_cover if item != normalized_label]]
        section.heading = heading_map.get(normalized_label, section.heading)
        section.topic_seed = normalized_label
        if normalized_label not in section.related_terms:
            section.related_terms.insert(0, normalized_label)
        if normalized_label not in section.instruction_anchor_terms:
            section.instruction_anchor_terms.insert(0, normalized_label)
        if not str(section.section_user_instruction or "").strip():
            section.section_user_instruction = normalized_label
    for index, bridge_hint in enumerate(_ANNOUNCEMENT_DENSE_BRIDGE_HINTS):
        if index >= len(sections):
            break
        sections[index].bridge_hint = bridge_hint
    for index, reader_question in enumerate(_ANNOUNCEMENT_DENSE_READER_QUESTIONS):
        if index >= len(sections):
            break
        sections[index].reader_question = reader_question


def _pick_product_intro_followthrough_label(
    must_cover_items: List[str],
    *,
    prefer_keywords: List[str],
    fallback: str,
) -> str:
    for item in must_cover_items:
        value = str(item or "").strip()
        if value and any(keyword in value for keyword in prefer_keywords):
            return value
    for item in must_cover_items:
        value = str(item or "").strip()
        if value:
            return value
    return fallback


def _stabilize_product_intro_followthrough_sections(
    sections: List[DiscourseSection],
    *,
    must_cover_items: List[str],
) -> None:
    if len(sections) < 4:
        return
    criteria_label = _pick_product_intro_followthrough_label(
        must_cover_items,
        prefer_keywords=["判断", "選ぶ", "比較"],
        fallback="選ぶ判断材料",
    )
    caution_label = _pick_product_intro_followthrough_label(
        must_cover_items,
        prefer_keywords=["注意", "導入", "確認"],
        fallback="導入時の注意点",
    )
    for section in sections[3:]:
        label = criteria_label if str(section.intent or "").strip() == "decision" else caution_label
        existing_must_cover = [
            str(item or "").strip()
            for item in list(section.must_cover or [])
            if str(item or "").strip()
        ]
        section.must_cover = [label, *[item for item in existing_must_cover if item != label]]
        section.topic_seed = label
        section.section_user_instruction = label
        section.new_information = label
        if label not in section.related_terms:
            section.related_terms.insert(0, label)
        if label not in section.instruction_anchor_terms:
            section.instruction_anchor_terms.insert(0, label)


def _canonicalize_sections(sections: List[DiscourseSection]) -> List[DiscourseSection]:
    for section in sections:
        section.normalize()
    return sections


def build_discourse_plan(contract: Dict[str, object]) -> List[DiscourseSection]:
    article_type = str(contract.get("article_type") or "explanatory_article").strip().lower()
    semantic_article_key = str(contract.get("semantic_article_key") or article_type).strip().lower()
    length_mode = str(contract.get("length_mode") or "normal").strip().lower() or "normal"
    topic = str(contract.get("topic") or "")
    focus_bundle = dict(contract.get("focus_bundle", {}) or {})
    goal_bias = str(focus_bundle.get("goal_bias") or "").strip()
    topic_statement = str(focus_bundle.get("main_focus") or contract.get("topic_statement") or "").strip()
    support_points = _normalize_text_list(focus_bundle.get("support_points"))
    source_grounding_items = _normalize_source_grounding_items(contract.get("source_grounding_items"), article_type=article_type)
    must_cover_items = _normalize_text_list(contract.get("must_cover"))
    company_intro_like = (
        semantic_article_key == "company_introduction"
        or (
            article_type == "branding"
            and semantic_article_key == "branding"
            and goal_bias == "human_company_outline"
            and bool(source_grounding_items)
            and bool(contract.get("prompt_instruction_items"))
        )
    )
    user_instruction_terms: List[str] = []
    for item in [topic_statement, *support_points]:
        text = str(item or "").strip()
        if item == topic_statement and not _is_compact_focus_anchor(text, raw_topic=topic):
            continue
        if text and text not in user_instruction_terms:
            user_instruction_terms.append(text)
    if company_intro_like:
        reader_question_candidates = [
            "まずどんな会社か",
            "何を担う会社か",
            "どんな強みがあるか",
            "どんな歩みを重ねてきたか",
            "今どんな価値を提供しているか",
            "読み終えたときにどんな輪郭が残るか",
        ]
    elif article_type == "comparative_review":
        reader_question_candidates = []
    else:
        reader_question_candidates = [
            "何を先に理解すべきか",
            "現場でどこが迷いやすいか",
            "次にどんな行動へつながるか",
        ]
    base_template = "announcement" if article_type == "announcement" else (
        "company_introduction" if company_intro_like else (
            "branding" if article_type in {"branding", "daily_story"} else "analysis"
        )
    )
    desired_section_count = 5 if article_type == "announcement" else 6
    if article_type not in {"case_study", "comparative_review"} and length_mode in {"adaptive", "short"}:
        desired_section_count = 5
    length_plan = build_note4000_length_plan(
        length_mode=length_mode,
        section_count=desired_section_count,
        max_section_count=6 if article_type in {"case_study", "comparative_review"} else None,
    )
    discourse = build_note4000_discourse_plan(
        article_type=article_type,
        base_template=base_template,
        user_prompt=topic,
        must_cover=must_cover_items,
        user_instruction_terms=user_instruction_terms,
        thesis=topic_statement or topic,
        reader_question_candidates=reader_question_candidates,
        length_plan=length_plan,
        source_grounding_items=source_grounding_items,
    )
    sections: List[DiscourseSection] = []
    for index, item in enumerate(discourse):
        prompt_contract = resolve_note4000_section_prompt_contract(
            section=item,
            section_index=index,
            discourse_sections=discourse,
            contract=contract,
        )
        sections.append(DiscourseSection.from_section_plan(item=item, prompt_contract=prompt_contract))
    if article_type not in {"announcement", "case_study", "comparative_review"}:
        _apply_focus_bundle(
            sections,
            main_focus=topic_statement,
            support_points=support_points,
            raw_topic=topic,
            semantic_article_key=semantic_article_key,
        )
    if article_type == "explanatory_article":
        _stabilize_explanatory_must_cover_headings(sections)
    if article_type == "case_study":
        _stabilize_case_study_hook_section(sections)
    if _is_announcement_dense_route(
        contract,
        article_type=article_type,
        semantic_article_key=semantic_article_key,
        must_cover_items=must_cover_items,
    ):
        _stabilize_announcement_dense_sections(sections, must_cover_items=must_cover_items)
    if article_type == "branding" and semantic_article_key == "product_introduction":
        _stabilize_product_intro_followthrough_sections(sections, must_cover_items=must_cover_items)
    _apply_source_grounding(
        sections,
        source_grounding_items,
        article_type=article_type,
        semantic_article_key=semantic_article_key,
    )
    return _canonicalize_sections(sections)
