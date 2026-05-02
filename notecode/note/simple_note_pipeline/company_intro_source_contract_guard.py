"""Company introduction source contract constants and pure helpers."""
from __future__ import annotations

import re
from typing import Any, Mapping


_COMPANY_INTRO_SOURCE_SLOTS: tuple[str, ...] = (
    "current_business",
    "customer_situation_or_entry_point",
    "support_scope_boundary",
    "operating_process_steps",
    "pre_contact_decision",
    "proof_signal",
    "source_limit",
)
_COMPANY_INTRO_REQUIRED_SOURCE_SLOTS: tuple[str, ...] = (
    "current_business",
    "customer_situation_or_entry_point",
    "support_scope_boundary",
)
_COMPANY_INTRO_OPTIONAL_SOURCE_SLOTS: tuple[str, ...] = (
    "operating_process_steps",
    "pre_contact_decision",
    "proof_signal",
)
_COMPANY_INTRO_SCRIPT_UNITS: tuple[tuple[str, str], ...] = (
    ("current_business", "current_business"),
    ("entry_point", "customer_situation_or_entry_point"),
    ("support_boundary", "support_scope_boundary"),
    ("process", "operating_process_steps"),
    ("reader_decision", "pre_contact_decision"),
)
_COMPANY_INTRO_SCRIPT_SLOT_BY_UNIT = {
    unit: slot for unit, slot in _COMPANY_INTRO_SCRIPT_UNITS
}
_COMPANY_INTRO_SCRIPT_UNIT_BY_SLOT = {
    slot: unit for unit, slot in _COMPANY_INTRO_SCRIPT_UNITS
}
_COMPANY_INTRO_SLOT_LABELS = {
    "current_business": "現在事業",
    "customer_situation_or_entry_point": "顧客接点",
    "support_scope_boundary": "支援範囲",
    "operating_process_steps": "進め方",
    "pre_contact_decision": "相談前判断",
    "proof_signal": "根拠サイン",
    "source_limit": "素材制約",
}
_COMPANY_INTRO_SLOT_PATTERNS = {
    "current_business": re.compile(r"(?:事業|サービス|提供|支援|対応|制作|開発|運用|業務|データ|調査|分析|システム)"),
    "customer_situation_or_entry_point": re.compile(
        r"(?:相談前|問い合わせ前|依頼前|顧客|お客さま|担当者|現場|迷|困|入口|入り口|課題|相談|お悩み|わからな|"
        r"分野|用途|対象|利用|使用|家庭|法人|産業|医療|福祉|学校|研究|飲食|ホテル|旅館|オフィス|商業施設)"
    ),
    "support_scope_boundary": re.compile(
        r"(?:支援範囲|対応範囲|範囲|対象|領域|分野|用途|地域|エリア|家庭|法人|産業|医療|福祉|学校|研究|"
        r"飲食|ホテル|旅館|オフィス|商業施設|支援|サポート|対応|できること|できないこと|線引き|境界)"
        r"|(?:支える|支え|任せ|頼め|頼みたい工程|委ね)"
    ),
    "operating_process_steps": re.compile(
        r"(?:進め方|工程|手順|初回(?:ヒアリング)?|ヒアリング|打ち合わせ|資料確認|納品確認|"
        r"作業範囲|範囲整理|運用ルール|担当者導線|FAQ整備|問い合わせ整理|週次|"
        r"お見積(?:り|もり)?|見積(?:り|もり)?|"
        r"(?:相談|導入|進行|作業)の流れ|"
        r"入力(?:と|・)?チェック|チェック(?:と|・)?納品)"
    ),
    "pre_contact_decision": re.compile(
        r"(?:相談前|問い合わせ前|依頼前|確認点|確認する|見るべき|判断材料|判断しやす|準備|そろえ|整理しておく|"
        r"問い合わせ整理|問い合わせを|"
        r"お問い合わせのあと|お問合せのあと|お見積(?:り|もり)?|見積(?:り|もり)?|"
        r"小さなことから(?:でも)?(?:ぜひ)?ご相談|お悩み|課題から)"
    ),
    "proof_signal": re.compile(r"(?:実際|記録|問い合わせ|質問|FAQ|メモ|見直し|確認|支援例|掲載|公式)"),
    "source_limit": re.compile(r"(?:素材|公開情報|未確認|確認できない|記載なし|範囲|source|限る|分からない)"),
}
_COMPANY_INTRO_UNSUPPORTED_CLAIM_RE = re.compile(
    r"(?:[0-9０-９]+(?:[.,．][0-9０-９]+)?\s*(?:%|％|割|倍|件|時間|分|日|人|社|円|万円|回|ポイント)|"
    r"無料|有料|価格|料金|成果(?!物)|実績|削減|改善率|満足度|受賞|表彰|提携|協業|パートナー|顧客名|導入企業|"
    r"株式会社[一-龥A-Za-z0-9・ー]{1,24}|[一-龥A-Za-z0-9・ー]{1,24}株式会社)"
)
_COMPANY_INTRO_VISIBLE_EXPERIMENT_TERM_RE = re.compile(
    r"(?:persona|ペルソナ|hidden|editor|full_rewrite|middle_onward|late_35_only|sparse|source_contract|"
    r"company_intro_hidden_persona_contract_v1|trial|実験|operational packet|company-profile packet)",
    flags=re.IGNORECASE,
)
_COMPANY_INTRO_SOURCE_LIMIT_VISIBLE_RE = re.compile(
    r"(?:source_limit|素材制約|公開情報で確認できる範囲|公開資料で確認できる範囲|確認できる範囲に限る|"
    r"未確認のため書かない|sourceにない)",
    flags=re.IGNORECASE,
)


def _company_intro_source_contract_failure_count(validation: Mapping[str, Any]) -> int:
    return len(list(validation.get("repair_trigger_ids") or []))


def _company_intro_source_contract_improved(
    current: Mapping[str, Any],
    repaired: Mapping[str, Any],
) -> bool:
    if not bool(current.get("scope_match")):
        return True
    if bool(repaired.get("unsupported_claim_added")) or bool(repaired.get("source_limit_visible_leakage")):
        return False
    return _company_intro_source_contract_failure_count(repaired) < _company_intro_source_contract_failure_count(current)


def _build_company_intro_source_contract_validation_snapshot(validation: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "checked": bool(validation.get("checked")),
        "scope_match": bool(validation.get("scope_match")),
        "pattern": str(validation.get("pattern") or ""),
        "required_slots": list(validation.get("required_slots") or _COMPANY_INTRO_REQUIRED_SOURCE_SLOTS),
        "optional_slots": list(validation.get("optional_slots") or _COMPANY_INTRO_OPTIONAL_SOURCE_SLOTS),
        "guard_only_slots": list(validation.get("guard_only_slots") or ["source_limit"]),
        "repair_trigger_ids": list(validation.get("repair_trigger_ids") or []),
        "failure_count": _company_intro_source_contract_failure_count(validation),
        "unsupported_claim_added": bool(validation.get("unsupported_claim_added")),
        "unsupported_claim_hits": list(validation.get("unsupported_claim_hits") or []),
        "source_limit_visible_leakage": bool(validation.get("source_limit_visible_leakage")),
        "missing_required_slots": list(validation.get("missing_required_slots") or []),
        "unbacked_required_slots": list(validation.get("unbacked_required_slots") or []),
        "support_scope_boundary_missing_final": bool(
            validation.get("support_scope_boundary_missing_final")
        ),
        "pre_contact_decision_missing_final": bool(
            validation.get("pre_contact_decision_missing_final")
        ),
        "slot_presence": dict(validation.get("slot_presence") or {}),
        "source_slot_presence": dict(validation.get("source_slot_presence") or {}),
        "script_packet_statuses": dict(validation.get("script_packet_statuses") or {}),
        "hard_trigger_ids": list(validation.get("hard_trigger_ids") or []),
        "degraded_trigger_ids": list(validation.get("degraded_trigger_ids") or []),
        "degraded_slots": list(validation.get("degraded_slots") or []),
        "advisory_missing_slots": list(validation.get("advisory_missing_slots") or []),
        "public_contract_present": bool(validation.get("public_contract_present")),
        "private_contract_present": bool(validation.get("private_contract_present")),
    }
