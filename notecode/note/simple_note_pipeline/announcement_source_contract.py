"""Announcement source contract constants and pure helpers."""
from __future__ import annotations

import re
from typing import Any, Dict, Mapping, Sequence

from note.simple_note_pipeline.hidden_late_validation import _hidden_late_source_text
from note.simple_note_pipeline.postprocess import DraftSections
from note.simple_note_pipeline.rendering import build_source_pack


_SHADOW_TOKEN_RE = re.compile(r"[一-龥]{2,}|[ぁ-ん]{2,}|[ァ-ヴー]{2,}|[A-Za-z][A-Za-z0-9_-]{2,}")
_ANNOUNCEMENT_SOURCE_SLOTS: tuple[str, ...] = (
    "date_or_timing",
    "target_audience",
    "change_or_news",
    "impact_scope",
    "next_action",
    "preparation_or_contact",
)
_ANNOUNCEMENT_REQUIRED_SOURCE_SLOTS: tuple[str, ...] = (
    "date_or_timing",
    "target_audience",
    "change_or_news",
    "next_action",
)
_ANNOUNCEMENT_SLOT_LABELS = {
    "date_or_timing": "時期",
    "target_audience": "対象",
    "change_or_news": "変更内容",
    "impact_scope": "影響範囲",
    "next_action": "次の行動",
    "preparation_or_contact": "準備/連絡",
}
_ANNOUNCEMENT_SLOT_PATTERNS = {
    "date_or_timing": re.compile(r"(?:20\d{2}年|本日|明日|来週|来月|開始|実施|予定|から|上旬|中旬|下旬)"),
    "target_audience": re.compile(r"(?:対象|向け|担当者|利用者|ユーザー|お客様|企業|チーム|部門)"),
    "change_or_news": re.compile(r"(?:追加|変更|開始|始め|受付|リリース|公開|導入|更新|新しい|お知らせ)"),
    "impact_scope": re.compile(r"(?:既存|継続|影響|範囲|変わりません|そのまま|使えます|停止|確認しやす)"),
    "next_action": re.compile(r"(?:問い合わせ|お問い合わせ|申し込|申込|確認|準備|まとめ|連絡|手続き|対応してください)"),
    "preparation_or_contact": re.compile(r"(?:事前|準備|確認|ツール|関係者|連絡先|問い合わせ先|紙|Excel|現在の運用)"),
}
_ANNOUNCEMENT_DATETIME_RE = re.compile(
    r"(?:20\d{2}年\s*\d{1,2}月(?:\s*\d{1,2}日)?(?:\s*(?:上旬|中旬|下旬))?|"
    r"20\d{2}/\d{1,2}(?:/\d{1,2})?|\d{1,2}月\s*\d{1,2}日|\d{1,2}月(?:上旬|中旬|下旬)|"
    r"本日|明日|明後日|来週|来月)"
)
_ANNOUNCEMENT_PRICE_OR_RESULT_RE = re.compile(
    r"(?:[0-9０-９]+(?:[.,．][0-9０-９]+)?\s*(?:%|％|割|倍|件|時間|分|日|人|社|円|万円|回|ポイント)|"
    r"無料|有料|価格|料金|成果|実績|削減|改善率|満足度)"
)
_ANNOUNCEMENT_CUSTOMER_PARTNER_RE = re.compile(
    r"(?:顧客名|導入企業|提携|協業|パートナー|受賞|表彰|株式会社[一-龥A-Za-z0-9・ー]{1,24}|[一-龥A-Za-z0-9・ー]{1,24}株式会社)"
)
_ANNOUNCEMENT_VISIBLE_EXPERIMENT_TERM_RE = re.compile(
    r"(?:企業広報担当ブロガー|PR会社編集担当|書き手方針|編集方針|persona|ペルソナ|hidden|editor|"
    r"full_rewrite|middle_onward|late_35_only|sparse|source_contract|structured source|戻り先)",
    flags=re.IGNORECASE,
)


def _clean_inline_text(value: Any, *, limit: int = 180) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _extract_shadow_tokens(value: Any, *, limit: int = 4) -> list[str]:
    tokens: list[str] = []
    for token in _SHADOW_TOKEN_RE.findall(_clean_inline_text(value or "", limit=240)):
        normalized = token.lower().strip()
        if re.fullmatch(r"[ぁ-ん]{2,}", normalized):
            continue
        if not normalized or normalized in tokens:
            continue
        tokens.append(normalized)
        if len(tokens) >= limit:
            break
    return tokens


def _announcement_scope_active(contract: Mapping[str, Any]) -> bool:
    return str(contract.get("article_type") or "").strip().lower() == "announcement"


def _announcement_source_sentences(source_pack: Mapping[str, Any]) -> list[str]:
    source_text = _hidden_late_source_text(source_pack)
    sentences: list[str] = []
    for part in re.split(r"(?<=[。！？!?])\s*|\n+", source_text):
        text = _clean_inline_text(part, limit=220)
        if text and text not in sentences:
            sentences.append(text)
    for item in list(source_pack.get("grounding_items") or []):
        if not isinstance(item, Mapping):
            continue
        fact_text = _clean_inline_text(item.get("fact_text") or "", limit=220)
        if not fact_text:
            continue
        for part in re.split(r"(?<=[。！？!?])\s*|\n+", fact_text):
            text = _clean_inline_text(part, limit=220)
            if text and text not in sentences:
                sentences.append(text)
    return sentences[:24]


def _announcement_slot_from_bucket(bucket: Any) -> str:
    normalized = re.sub(r"[\s_\-/]+", "", str(bucket or "").strip().lower())
    aliases = {
        "dateortiming": "date_or_timing",
        "date": "date_or_timing",
        "timing": "date_or_timing",
        "時期": "date_or_timing",
        "日時": "date_or_timing",
        "対象": "target_audience",
        "target": "target_audience",
        "targetaudience": "target_audience",
        "対象者": "target_audience",
        "change": "change_or_news",
        "news": "change_or_news",
        "changeornews": "change_or_news",
        "変更": "change_or_news",
        "変更内容": "change_or_news",
        "お知らせ": "change_or_news",
        "impact": "impact_scope",
        "impactscope": "impact_scope",
        "影響": "impact_scope",
        "影響範囲": "impact_scope",
        "next": "next_action",
        "nextaction": "next_action",
        "action": "next_action",
        "次の行動": "next_action",
        "対応": "next_action",
        "preparation": "preparation_or_contact",
        "contact": "preparation_or_contact",
        "preparationorcontact": "preparation_or_contact",
        "準備": "preparation_or_contact",
        "連絡": "preparation_or_contact",
    }
    return aliases.get(normalized, "")


def _announcement_slot_candidate_score(slot: str, text: str) -> int:
    normalized = _clean_inline_text(text, limit=220)
    if not normalized:
        return -100
    score = min(len(normalized), 180) // 18
    if slot == "date_or_timing":
        if _ANNOUNCEMENT_DATETIME_RE.search(normalized):
            score += 12
        if re.search(r"(?:から|開始|実施|予定)", normalized):
            score += 4
    elif slot == "target_audience":
        if "対象" in normalized:
            score += 10
        if re.search(r"(?:担当者|承認者|利用者|ユーザー|お客様)", normalized):
            score += 6
    elif slot == "change_or_news":
        if re.search(r"(?:一段階|二段階|変更|追加|開始|更新)", normalized):
            score += 10
        if "お知らせ" in normalized:
            score += 2
    elif slot == "impact_scope":
        if re.search(r"(?:旧手順|参照専用|影響|範囲|継続|残る)", normalized):
            score += 10
    elif slot == "next_action":
        if re.search(r"(?:当日|確認事項|下書き保存|差し戻し通知|公開日時)", normalized):
            score += 14
        if re.search(r"(?:確認|準備|対応|手続き)", normalized):
            score += 4
    elif slot == "preparation_or_contact":
        if re.search(r"(?:事前準備|承認者の再設定|通知先の確認)", normalized):
            score += 14
        if re.search(r"(?:準備|確認|連絡|問い合わせ)", normalized):
            score += 4
    if re.fullmatch(r"[A-Fa-f0-9_\\-]{12,}.*", normalized):
        score -= 20
    return score


def _build_announcement_runtime_source_contract(
    contract: Mapping[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    active = _announcement_scope_active(contract)
    slots: Dict[str, str] = {slot: "" for slot in _ANNOUNCEMENT_SOURCE_SLOTS}
    if not active:
        return {
            "checked": True,
            "scope_match": False,
            "slots": slots,
            "required_slots": list(_ANNOUNCEMENT_REQUIRED_SOURCE_SLOTS),
            "optional_slots": ["impact_scope", "preparation_or_contact"],
            "pattern": "announcement_01_base",
        }

    explicit_contract = contract.get("announcement_source_contract")
    has_explicit_contract = isinstance(explicit_contract, Mapping)
    if isinstance(explicit_contract, Mapping):
        for slot in _ANNOUNCEMENT_SOURCE_SLOTS:
            value = _clean_inline_text(explicit_contract.get(slot) or "", limit=180)
            if value:
                slots[slot] = value

    structured_slots: set[str] = set()
    for item in list(source_pack.get("grounding_items") or []):
        if not isinstance(item, Mapping):
            continue
        slot = _announcement_slot_from_bucket(item.get("bucket"))
        value = _clean_inline_text(item.get("fact_text") or "", limit=180)
        if slot and value:
            structured_slots.add(slot)
            if not slots.get(slot):
                slots[slot] = value

    sentences = _announcement_source_sentences(source_pack)
    for slot in _ANNOUNCEMENT_SOURCE_SLOTS:
        if slots.get(slot):
            continue
        pattern = _ANNOUNCEMENT_SLOT_PATTERNS.get(slot)
        if not pattern:
            continue
        candidates = [sentence for sentence in sentences if pattern.search(sentence)]
        if candidates:
            slots[slot] = sorted(
                candidates,
                key=lambda item: (-_announcement_slot_candidate_score(slot, item), sentences.index(item)),
            )[0]

    source_contract_available = bool(
        has_explicit_contract
        or all(_clean_inline_text(slots.get(slot) or "", limit=180) for slot in _ANNOUNCEMENT_REQUIRED_SOURCE_SLOTS)
    )
    if not source_contract_available:
        return {
            "checked": True,
            "scope_match": False,
            "slots": slots,
            "required_slots": list(_ANNOUNCEMENT_REQUIRED_SOURCE_SLOTS),
            "optional_slots": ["impact_scope", "preparation_or_contact"],
            "pattern": "announcement_01_base",
            "source_contract_available": False,
        }

    return {
        "checked": True,
        "scope_match": True,
        "slots": slots,
        "required_slots": list(_ANNOUNCEMENT_REQUIRED_SOURCE_SLOTS),
        "optional_slots": ["impact_scope", "preparation_or_contact"],
        "pattern": "announcement_01_base",
        "source_contract_available": True,
    }


def _merge_announcement_runtime_contract_into_payload(
    contract: Mapping[str, Any],
    announcement_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    updated = dict(contract)
    updated["_announcement_source_contract"] = dict(announcement_contract)
    if not bool(announcement_contract.get("scope_match")):
        return updated

    slots = dict(announcement_contract.get("slots") or {})
    existing_grounding = [
        dict(item)
        for item in list(updated.get("source_grounding_items") or [])
        if isinstance(item, Mapping)
    ]
    existing_pairs = {
        (
            str(item.get("bucket") or "").strip(),
            _clean_inline_text(item.get("fact_text") or "", limit=180),
        )
        for item in existing_grounding
    }
    for slot in _ANNOUNCEMENT_SOURCE_SLOTS:
        value = _clean_inline_text(slots.get(slot) or "", limit=180)
        if not value:
            continue
        bucket = _ANNOUNCEMENT_SLOT_LABELS.get(slot, slot)
        pair = (bucket, value)
        if pair in existing_pairs:
            continue
        existing_grounding.append(
            {
                "bucket": bucket,
                "fact_text": value,
                "source_title": "announcement source",
                "locator": "",
            }
        )
        existing_pairs.add(pair)
    updated["source_grounding_items"] = existing_grounding[:10]

    existing_must_cover: list[str] = []
    for item in list(updated.get("must_cover") or []):
        text = _clean_inline_text(item, limit=120)
        if text and text not in existing_must_cover:
            existing_must_cover.append(text)
    for slot in (*_ANNOUNCEMENT_REQUIRED_SOURCE_SLOTS, "preparation_or_contact"):
        value = _clean_inline_text(slots.get(slot) or "", limit=120)
        if not value:
            continue
        label = _ANNOUNCEMENT_SLOT_LABELS.get(slot, slot)
        item = f"{label}: {value}"
        if item not in existing_must_cover:
            existing_must_cover.append(item)
    if existing_must_cover:
        updated["must_cover"] = existing_must_cover[:8]

    existing_hints: list[str] = []
    for item in list(updated.get("system_hint_items") or []):
        text = str(item or "").strip()
        if text and text not in existing_hints:
            existing_hints.append(text)
    contract_hints = [
        "お知らせ本文では、対象、変更点、次の行動を前半で明確に残し、背景説明を長くしない。",
        "読者が準備/連絡すべきことを具体に置き、硬い案内文やヘルプ記事へ寄せすぎない。",
        "価格、成果数値、顧客名、提携内容、素材にない日付は足さない。",
    ]
    for hint in contract_hints:
        if hint not in existing_hints:
            existing_hints.append(hint)
    updated["system_hint_items"] = existing_hints[:8]
    return updated


def _prepare_announcement_runtime_contract(contract: Mapping[str, Any]) -> Dict[str, Any]:
    base_contract = dict(contract)
    initial_source_pack = build_source_pack(base_contract)
    announcement_contract = _build_announcement_runtime_source_contract(base_contract, initial_source_pack)
    return _merge_announcement_runtime_contract_into_payload(base_contract, announcement_contract)


def _announcement_text_for_validation(draft: DraftSections) -> str:
    return "\n".join(str(part or "") for part in (draft.title, draft.lead, draft.body)).strip()


def _announcement_slot_value_reflected(text: str, value: Any) -> bool:
    source_tokens = _extract_shadow_tokens(value, limit=6)
    if not source_tokens:
        return False
    normalized_text = _clean_inline_text(text, limit=2400).lower()
    hit_count = sum(1 for token in source_tokens if token in normalized_text)
    return hit_count >= max(1, min(2, len(source_tokens)))


def _announcement_slot_present(slot: str, text: str, source_value: Any) -> bool:
    if slot == "date_or_timing" and _ANNOUNCEMENT_DATETIME_RE.search(str(source_value or "")):
        return bool(_ANNOUNCEMENT_DATETIME_RE.search(str(text or "")))
    if _announcement_slot_value_reflected(text, source_value):
        return True
    pattern = _ANNOUNCEMENT_SLOT_PATTERNS.get(slot)
    return bool(pattern and pattern.search(text))


def _normalize_announcement_claim_token(value: Any) -> str:
    text = str(value or "").translate(str.maketrans("０１２３４５６７８９％．，", "0123456789%.,"))
    return re.sub(r"\s+", "", text)


def _announcement_unsupported_hits(
    text: str,
    source_text: str,
    pattern: re.Pattern[str],
) -> list[str]:
    source_tokens = {
        _normalize_announcement_claim_token(match.group(0))
        for match in pattern.finditer(source_text)
    }
    hits: list[str] = []
    for match in pattern.finditer(text):
        raw = match.group(0)
        normalized = _normalize_announcement_claim_token(raw)
        if normalized and normalized not in source_tokens and raw not in hits:
            hits.append(raw)
    return hits[:8]


def _announcement_wrong_article_type_drift(text: str, missing_required_slots: Sequence[str]) -> bool:
    if re.search(r"(?:事例です|改善前|導入後|残った課題|結果として)", text):
        return True
    if re.search(r"(?:会社紹介|当社は[^。]{0,40}(?:会社|企業)です|事業内容|提供価値)", text):
        return True
    if re.search(r"(?:ヘルプ|FAQ|手順書|操作方法|設定方法|クリック|画面で)", text) and missing_required_slots:
        return True
    return False


def _announcement_explanatory_drift(text: str) -> bool:
    return bool(
        re.search(
            r"(?:この記事では|以下で解説|背景として|なぜなら|重要です|大切です|ポイントです)",
            text,
        )
    )


def _announcement_target_action_buried(
    text: str,
    slot_presence: Mapping[str, bool],
    slots: Mapping[str, Any],
) -> bool:
    if not bool(slot_presence.get("target_audience")) or not bool(slot_presence.get("next_action")):
        return False
    front_text = _clean_inline_text(text, limit=720)
    target_front = _announcement_slot_present("target_audience", front_text, slots.get("target_audience"))
    action_front = _announcement_slot_present("next_action", front_text, slots.get("next_action"))
    return not bool(target_front and action_front)


def _announcement_source_contract_failure_count(validation: Mapping[str, Any]) -> int:
    return (
        len(list(validation.get("missing_required_slots") or []))
        + len(list(validation.get("unsupported_date_or_timing_hits") or []))
        + len(list(validation.get("unsupported_price_or_result_hits") or []))
        + len(list(validation.get("unsupported_customer_or_partner_hits") or []))
        + (1 if bool(validation.get("wrong_article_type_drift")) else 0)
        + (1 if bool(validation.get("target_action_buried")) else 0)
        + (1 if bool(validation.get("explanatory_drift")) else 0)
    )


def _announcement_source_contract_improved(
    current: Mapping[str, Any],
    repaired: Mapping[str, Any],
) -> bool:
    if not bool(current.get("scope_match")):
        return True
    if bool(repaired.get("unsupported_claim_added")):
        return False
    return _announcement_source_contract_failure_count(repaired) < _announcement_source_contract_failure_count(current)


def _evaluate_announcement_source_contract_validation(
    contract: Mapping[str, Any],
    draft: DraftSections,
    diagnostics: Dict[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    announcement_contract = dict(contract.get("_announcement_source_contract") or {})
    if not announcement_contract:
        announcement_contract = _build_announcement_runtime_source_contract(contract, source_pack)
    slots = dict(announcement_contract.get("slots") or {})
    if not _announcement_scope_active(contract) or (
        bool(announcement_contract.get("checked")) and not bool(announcement_contract.get("scope_match"))
    ):
        return {
            "checked": True,
            "scope_match": False,
            "pattern": "announcement_01_base",
            "required_slots": list(_ANNOUNCEMENT_REQUIRED_SOURCE_SLOTS),
            "optional_slots": ["impact_scope", "preparation_or_contact"],
            "slot_presence": {slot: False for slot in _ANNOUNCEMENT_SOURCE_SLOTS},
            "missing_required_slots": [],
            "target_action_buried": False,
            "explanatory_drift": False,
            "help_article_drift": False,
            "company_intro_drift": False,
            "wrong_article_type_drift": False,
            "unsupported_claim_added": False,
            "unsupported_date_or_timing_hits": [],
            "unsupported_price_or_result_hits": [],
            "unsupported_customer_or_partner_hits": [],
            "visible_leakage_hits": [],
            "repair_trigger_ids": [],
        }
    text = _announcement_text_for_validation(draft)
    source_text = _hidden_late_source_text(source_pack)

    slot_presence: Dict[str, bool] = {}
    for slot in _ANNOUNCEMENT_SOURCE_SLOTS:
        slot_presence[slot] = _announcement_slot_present(slot, text, slots.get(slot))

    missing_required = [
        slot
        for slot in _ANNOUNCEMENT_REQUIRED_SOURCE_SLOTS
        if not bool(slot_presence.get(slot))
    ]
    unsupported_date_hits = _announcement_unsupported_hits(text, source_text, _ANNOUNCEMENT_DATETIME_RE)
    unsupported_price_or_result_hits = _announcement_unsupported_hits(
        text,
        source_text,
        _ANNOUNCEMENT_PRICE_OR_RESULT_RE,
    )
    unsupported_customer_or_partner_hits = _announcement_unsupported_hits(
        text,
        source_text,
        _ANNOUNCEMENT_CUSTOMER_PARTNER_RE,
    )
    visible_leakage_hits = []
    for match in _ANNOUNCEMENT_VISIBLE_EXPERIMENT_TERM_RE.finditer(text):
        hit = match.group(0)
        if hit and hit not in visible_leakage_hits:
            visible_leakage_hits.append(hit)

    target_action_buried = _announcement_target_action_buried(text, slot_presence, slots)
    wrong_type_drift = _announcement_wrong_article_type_drift(text, missing_required)
    help_article_drift = bool(re.search(r"(?:ヘルプ|FAQ|手順書|操作方法|設定方法|クリック|画面で)", text))
    company_intro_drift = bool(re.search(r"(?:会社紹介|当社は[^。]{0,40}(?:会社|企業)です|事業内容|提供価値)", text))
    explanatory_drift = _announcement_explanatory_drift(text)
    unsupported_claim_added = bool(
        unsupported_date_hits
        or unsupported_price_or_result_hits
        or unsupported_customer_or_partner_hits
    )

    trigger_ids: list[str] = []
    for slot in missing_required:
        trigger_ids.append(f"missing_required_slot:{slot}")
    if unsupported_date_hits:
        trigger_ids.append("unsupported_date_or_timing_added")
    if unsupported_price_or_result_hits:
        trigger_ids.append("unsupported_price_or_result_added")
    if unsupported_customer_or_partner_hits:
        trigger_ids.append("unsupported_customer_or_partner_added")
    if wrong_type_drift:
        trigger_ids.append("wrong_article_type_drift")
    if target_action_buried:
        trigger_ids.append("target_action_buried")
    if explanatory_drift:
        trigger_ids.append("explanatory_drift")

    validation = {
        "checked": True,
        "scope_match": _announcement_scope_active(contract),
        "pattern": "announcement_01_base",
        "required_slots": list(_ANNOUNCEMENT_REQUIRED_SOURCE_SLOTS),
        "optional_slots": ["impact_scope", "preparation_or_contact"],
        "slot_presence": slot_presence,
        "missing_required_slots": missing_required,
        "target_action_buried": bool(target_action_buried),
        "explanatory_drift": bool(explanatory_drift),
        "help_article_drift": bool(help_article_drift),
        "company_intro_drift": bool(company_intro_drift),
        "wrong_article_type_drift": bool(wrong_type_drift),
        "unsupported_claim_added": bool(unsupported_claim_added),
        "unsupported_date_or_timing_hits": unsupported_date_hits,
        "unsupported_price_or_result_hits": unsupported_price_or_result_hits,
        "unsupported_customer_or_partner_hits": unsupported_customer_or_partner_hits,
        "visible_leakage_hits": visible_leakage_hits[:8],
        "repair_trigger_ids": trigger_ids,
    }
    if not bool(validation["scope_match"]) or not trigger_ids:
        return validation

    repair_instructions: list[str] = []
    for item in list(diagnostics.get("repair_instructions") or []):
        text_item = str(item or "").strip()
        if text_item and text_item not in repair_instructions:
            repair_instructions.append(text_item)
    for line in (
        "お知らせ本文を、対象、変更点、次の行動が前半で分かる形へ戻す。",
        "素材にない日付、価格、成果数値、顧客名、提携内容は足さない。",
        "ヘルプ記事や会社紹介へ広げず、背景説明は短くする。",
    ):
        if line not in repair_instructions:
            repair_instructions.append(line)
    diagnostics["repair_instructions"] = repair_instructions[:12]

    soft_warnings: list[str] = []
    for item in list(diagnostics.get("soft_warnings") or []):
        text_item = str(item or "").strip()
        if text_item and text_item not in soft_warnings:
            soft_warnings.append(text_item)
    if "announcement:source_contract" not in soft_warnings:
        soft_warnings.append("announcement:source_contract")
    diagnostics["soft_warnings"] = soft_warnings[:14]
    diagnostics["repair_trigger_score"] = max(float(diagnostics.get("repair_trigger_score") or 0.0), 0.63)
    diagnostics["repair_required"] = True
    diagnostics["issue_count"] = max(
        int(diagnostics.get("issue_count", 0) or 0),
        len(repair_instructions),
        len(soft_warnings),
        len(trigger_ids),
    )
    diagnostics["severity"] = max(int(diagnostics.get("severity", 0) or 0), 2)
    return validation
