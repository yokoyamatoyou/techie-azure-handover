"""Single-pass note generation pipeline focused on orchestration."""
from __future__ import annotations

import ast
import json
import re
from typing import Any, Dict, Mapping, Optional, Sequence

from human_resonance2.fingerprint_metrics import FingerprintAnalyzer, apply_fingerprint_corrections
from note.current_mainline_persona_trial import enrich_persona_trial_contract
from note.input_contract_v1 import is_prompt_only_source_less_generation_allowed
from note.llm_client import LLMClient
from note.newalgorithm_pipeline.editor_guard import apply_minimal_editor_guard
from note.newalgorithm_pipeline import error_codes
from note.prompt_echo_detector import build_prompt_echo_references, detect_prompt_echo_sentences
from note.simple_note_pipeline.postprocess import (
    DraftSections,
    finalize_note_draft,
    inspect_tagged_output_contract,
    parse_tagged_output,
)
from note.simple_note_pipeline.company_intro_patch_scope import (
    evaluate_company_intro_patch_scope,
)
from note.simple_note_pipeline.prompt_builder import (
    build_experimental_prompt_stack_from_contract,
    build_compact_plan_prompt_from_contract,
    build_generation_prompt_from_contract,
    build_repair_prompt_from_diagnostics,
    heading_target,
    parse_compact_plan_output,
    resolve_title_hint,
    target_chars,
)
from note.simple_note_pipeline.quality_guard import evaluate_quality_guard, measure_diagnostics
from note.simple_note_pipeline.rendering import (
    build_input_stop_result,
    build_result,
    build_source_pack,
    normalize_hashtags,
)
from note.simple_note_pipeline.announcement_source_contract import (
    _ANNOUNCEMENT_CUSTOMER_PARTNER_RE,
    _ANNOUNCEMENT_DATETIME_RE,
    _ANNOUNCEMENT_PRICE_OR_RESULT_RE,
    _ANNOUNCEMENT_REQUIRED_SOURCE_SLOTS,
    _ANNOUNCEMENT_SLOT_LABELS,
    _ANNOUNCEMENT_SLOT_PATTERNS,
    _ANNOUNCEMENT_SOURCE_SLOTS,
    _ANNOUNCEMENT_VISIBLE_EXPERIMENT_TERM_RE,
    _announcement_explanatory_drift,
    _announcement_scope_active,
    _announcement_slot_candidate_score,
    _announcement_slot_from_bucket,
    _announcement_slot_present,
    _announcement_slot_value_reflected,
    _announcement_source_contract_failure_count,
    _announcement_source_contract_improved,
    _announcement_source_sentences,
    _announcement_target_action_buried,
    _announcement_text_for_validation,
    _announcement_unsupported_hits,
    _announcement_wrong_article_type_drift,
    _build_announcement_runtime_source_contract,
    _evaluate_announcement_source_contract_validation,
    _merge_announcement_runtime_contract_into_payload,
    _normalize_announcement_claim_token,
    _prepare_announcement_runtime_contract,
)
from note.simple_note_pipeline.comparative_review_source_contract import (
    _COMPARATIVE_APPROVAL_RE,
    _COMPARATIVE_AXIS_LABELS,
    _COMPARATIVE_FIT_RE,
    _COMPARATIVE_GENERIC_MUST_COVER,
    _COMPARATIVE_PRICE_OR_PLAN_RE,
    _COMPARATIVE_REQUIRED_SOURCE_SLOTS,
    _COMPARATIVE_RESULT_OR_VENDOR_CLAIM_RE,
    _COMPARATIVE_SLOT_LABELS,
    _COMPARATIVE_SLOT_PATTERNS,
    _COMPARATIVE_SOURCE_SLOTS,
    _COMPARATIVE_SUPPORT_RE,
    _COMPARATIVE_VISIBLE_EXPERIMENT_TERM_RE,
    _build_comparative_runtime_source_contract,
    _comparative_absolute_winner_drift,
    _comparative_affiliate_review_tone,
    _comparative_axis_labels,
    _comparative_exaggerated_superiority,
    _comparative_first_matching_sentence,
    _comparative_generic_recommendation_only,
    _comparative_join_matching_sentences,
    _comparative_must_cover_is_generic,
    _comparative_ranking_drift,
    _comparative_slot_from_bucket,
    _comparative_slot_present,
    _comparative_slot_value_reflected,
    _comparative_source_backed_fallback_slots,
    _comparative_source_contract_failure_count,
    _comparative_source_contract_improved,
    _comparative_source_contract_scope_active,
    _comparative_source_sentences,
    _comparative_text_for_validation,
    _comparative_unsupported_hits,
    _comparative_wrong_article_type_drift,
    _evaluate_comparative_source_contract_validation,
    _filter_comparative_unsupported_price_hits,
    _merge_comparative_runtime_contract_into_payload,
    _prepare_comparative_runtime_contract,
)
from note.simple_note_pipeline.hidden_late_validation import (
    _HIDDEN_LATE_ABSTRACT_CLOSING_RE,
    _HIDDEN_LATE_COMPANY_INTRO_TOKEN_PATTERNS,
    _HIDDEN_LATE_VALIDATION_BODY_WARNING_CONTAINS,
    _HIDDEN_LATE_VALIDATION_HEADING_CONTAINS,
    _HIDDEN_LATE_VALIDATION_HEADING_EXACT,
    _build_hidden_late_validation_contract,
    _company_intro_late_operational_closing_rescued,
    _evaluate_hidden_late_validation,
    _has_visible_forbidden_heading,
    _hidden_late_body_leakage_warning_hits,
    _hidden_late_required_tokens,
    _hidden_late_source_text,
    _hidden_late_validation_failure_count,
    _hidden_late_validation_improved,
    _hidden_late_window_text,
    _normalize_hidden_late_heading,
)
from note.simple_note_pipeline.company_intro_source_contract_guard import (
    _COMPANY_INTRO_REQUIRED_SOURCE_SLOTS,
    _COMPANY_INTRO_SCRIPT_SLOT_BY_UNIT,
    _COMPANY_INTRO_SCRIPT_UNIT_BY_SLOT,
    _COMPANY_INTRO_SCRIPT_UNITS,
    _COMPANY_INTRO_SLOT_LABELS,
    _COMPANY_INTRO_SLOT_PATTERNS,
    _COMPANY_INTRO_SOURCE_LIMIT_VISIBLE_RE,
    _COMPANY_INTRO_SOURCE_SLOTS,
    _COMPANY_INTRO_UNSUPPORTED_CLAIM_RE,
    _COMPANY_INTRO_VISIBLE_EXPERIMENT_TERM_RE,
    _build_company_intro_source_contract_validation_snapshot,
    _company_intro_source_contract_failure_count,
    _company_intro_source_contract_improved,
)
from note.simple_note_pipeline.company_intro_source_contract import (
    _build_company_intro_runtime_source_contract,
    _build_company_intro_script_packet,
    _company_intro_abstract_philosophy_only,
    _company_intro_brochure_only_drift,
    _company_intro_explanation_candidate,
    _company_intro_final_text,
    _company_intro_generic_copy_drift,
    _company_intro_negated_unsupported_claim_context,
    _company_intro_profile_packet_drift,
    _company_intro_quote_windows,
    _company_intro_runtime_contract_ready_for_public_use,
    _company_intro_script_quote_score,
    _company_intro_slot_candidate_score,
    _company_intro_slot_from_bucket,
    _company_intro_slot_present,
    _company_intro_slot_value_reflected,
    _company_intro_source_contract_scope_active,
    _company_intro_source_entry_parts,
    _company_intro_source_limit_leakage_hits,
    _company_intro_source_sentences,
    _company_intro_text_for_validation,
    _company_intro_unsupported_claim_hits,
    _company_intro_wrong_article_type_drift,
    _evaluate_company_intro_source_contract_validation,
    _merge_company_intro_runtime_contract_into_payload,
    _prepare_company_intro_runtime_contract,
)
from note.simple_note_pipeline.company_intro_opener_guard import (
    _company_intro_operational_identity_heading,
    _company_intro_visible_opener_drift_failed,
    _evaluate_company_intro_visible_opener_drift,
)
from note.simple_note_pipeline.repair_acceptance import (
    _repair_improves_company_intro_fingerprint,
    _repair_improves_ending_monotony,
    _repair_improves_explanatory_fingerprint,
    _repair_improves_explanatory_longform,
    _repair_preserves_alignment,
)
from note.simple_note_pipeline.ui_prompt_distillation import build_explanatory_source_use_digest


class PipelineRuntimeError(RuntimeError):
    """Runtime error with reason code."""

    def __init__(self, message: str, reason_code: str = error_codes.SYS_PIPELINE_FAILURE) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class ExperimentalPromptStackStageError(RuntimeError):
    """Stage-level error that preserves prompt-stack telemetry."""

    def __init__(self, message: str, *, stage_summary: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.stage_summary = dict(stage_summary or {})


_SHADOW_TOKEN_RE = re.compile(r"[一-龥]{2,}|[ぁ-ん]{2,}|[ァ-ヴー]{2,}|[A-Za-z][A-Za-z0-9_-]{2,}")
_EXPERIMENTAL_PROMPT_STACK = "experimental_prompt_stack"
_EXPERIMENTAL_PROMPT_STACK_STAGE_ORDER = ("support", "planner", "writer", "editor", "audit")
_SECTION_WRAPPER_RE = re.compile(r"\[SECTION\]\s*(.*?)\s*\[/SECTION\]", flags=re.DOTALL)
_USED_FACT_IDS_TAG_RE = re.compile(r"\[USED_FACT_IDS\]\s*([\s\S]*?)\s*\[/USED_FACT_IDS\]", re.IGNORECASE)
_COMPARATIVE_CLOSING_HEADING = "結論とおすすめの分け方"
_MATERIALIZED_LATE_HALF_ISSUE_TYPES = {
    "late_half_source_return",
    "late_half_closing_specificity",
    "late_half_surface_rhythm",
}
_MATERIALIZED_LATE_HALF_REPAIR_LINES = {
    "later_recall_not_visible_in_late_half": "後半に、素材にある具体情報を一つ戻してから結ぶ。source外の情報は足さない。",
    "late_half_empty": "後半の空白や薄さを、素材にある具体情報だけで補う。",
    "generic_closing_phrase": "最後を一般論で閉じず、素材にある条件・対応範囲・確認材料のどれかへ戻す。",
    "late_half_sentence_ending_repetition": "後半の文末・句読点・接続を局所的に散らし、意味と見出し順は変えない。",
    "ending_bucket_monotony": "文末単調は target sentence cluster と直前直後だけで散らし、対象外の本文は変えない。",
}
_CROSS_DEPARTMENT_PROMPT_ECHO_RE = re.compile(
    r"複数部門で記事作成を回す(?:なら|場合)[^。]{0,100}(?:承認フロー|責任分担|責任の置き方|担当責任)",
)

MATERIALIZED_ONEPASS_ROUTE_ID = "materialized_onepass_editor_route_v1"
ANCHOR_PATCH_ROUTE_ID = "materialized_anchor_patch_route_v2"
SIMPLE_ONEPASS_ROUTE_ID = "materialized_simple_onepass_route_v1"
_REJECTED_MATERIALIZED_ROUTE_FLAGS = (
    "enable_materialized_onepass_editor_route_v1",
    "enable_materialized_anchor_patch_route_v2",
    "enable_materialized_simple_onepass_route_v1",
)
_REJECTED_MATERIALIZED_ROUTE_IDS = (
    MATERIALIZED_ONEPASS_ROUTE_ID,
    ANCHOR_PATCH_ROUTE_ID,
    SIMPLE_ONEPASS_ROUTE_ID,
)


def _has_rejected_materialized_route_request(contract: Mapping[str, Any]) -> bool:
    if any(bool(contract.get(flag)) for flag in _REJECTED_MATERIALIZED_ROUTE_FLAGS):
        return True
    requested_ids = {
        str(contract.get("vnext_route_id") or "").strip(),
        str(contract.get("vnext_route_variant_id") or "").strip(),
        str(contract.get("route_id") or "").strip(),
        str(contract.get("route_variant_id") or "").strip(),
    }
    return bool(requested_ids.intersection(_REJECTED_MATERIALIZED_ROUTE_IDS))
_COMPANY_INTRO_CURRENT_BUSINESS_ECHO_RE = re.compile(
    r"^(?P<subject>.+?)(?:は|では)[、,\s]*(?P<activities>.+?)を支援(?:してい(?:ます|る)|する)(?:会社)?(?:です)?。?$"
)
_CASE_STUDY_SOURCE_SLOTS: tuple[str, ...] = (
    "before_blocker",
    "action_or_change",
    "process_detail",
    "after_change",
    "remaining_issue",
    "source_backed_evidence",
)
_CASE_STUDY_REQUIRED_SOURCE_SLOTS: tuple[str, ...] = (
    "before_blocker",
    "action_or_change",
    "after_change",
    "remaining_issue",
)
_CASE_STUDY_SLOT_LABELS = {
    "before_blocker": "改善前",
    "action_or_change": "変更",
    "process_detail": "進め方",
    "after_change": "変化",
    "remaining_issue": "残課題",
    "source_backed_evidence": "根拠",
}
_CASE_STUDY_SLOT_PATTERNS = {
    "before_blocker": re.compile(r"(?:課題|困|迷|分散|ばらつ|戻って|止まり|改善前|導入前|以前|対応前)"),
    "action_or_change": re.compile(r"(?:棚卸|整理|見直|変更|導入(?!前)|まとめ|そろえ|揃え|一本化|反映|行い|取り組|変え)"),
    "process_detail": re.compile(r"(?:週次|毎週|手順|流れ|進め方|確認しながら|運用|プロセス|反映して|見直し)"),
    "after_change": re.compile(r"(?:その結果|結果|改善後|導入後|減り|減っ|そろえやす|揃えやす|しやすく|できるよう|変化|変えた)"),
    "remaining_issue": re.compile(r"(?:一方|ただし|残って|残り|今後|引き続き|これから|課題です|必要です|続ける|条件|必要|すべき|決める)"),
    "source_backed_evidence": re.compile(r"(?:実際|記録|確認|測定|データ|資料|公式|問い合わせ|質問|声|ログ)"),
}
_CASE_STUDY_NUMERIC_METRIC_RE = re.compile(
    r"(?:[0-9０-９]+(?:[.,．][0-9０-９]+)?\s*(?:%|％|割|倍|件|時間|分|日|人|社|円|万円|回|ポイント)|半減|倍増|満足度|削減率|改善率)"
)
_CASE_STUDY_CUSTOMER_AWARD_RE = re.compile(
    r"(?:受賞|表彰|導入企業|顧客名|株式会社[一-龥A-Za-z0-9・ー]{1,24}|[一-龥A-Za-z0-9・ー]{1,24}株式会社)"
)
_CASE_STUDY_VISIBLE_EXPERIMENT_TERM_RE = re.compile(
    r"(?:persona|ペルソナ|hidden|editor|full_rewrite|sparse|source_contract)",
    flags=re.IGNORECASE,
)
_BRANDING_SOURCE_SLOTS: tuple[str, ...] = (
    "brand_subject_anchor",
    "customer_touchpoint",
    "operating_behavior",
    "decision_principle",
    "support_process",
    "brand_posture_in_action",
    "proof_signal",
)
_BRANDING_REQUIRED_SOURCE_SLOTS: tuple[str, ...] = (
    "brand_subject_anchor",
    "customer_touchpoint",
    "operating_behavior",
    "decision_principle",
    "support_process",
    "brand_posture_in_action",
)
_BRANDING_SLOT_LABELS = {
    "brand_subject_anchor": "ブランド対象",
    "customer_touchpoint": "顧客接点",
    "operating_behavior": "運用行動",
    "decision_principle": "判断原則",
    "support_process": "支援プロセス",
    "brand_posture_in_action": "行動としてのブランド姿勢",
    "proof_signal": "根拠サイン",
}
_BRANDING_SLOT_PATTERNS = {
    "brand_subject_anchor": re.compile(r"(?:株式会社|合同会社|有限会社|SaaS|サービス|システム|ツール|アプリ|プロダクト|製品|商品|ブランド)"),
    "customer_touchpoint": re.compile(r"(?:相談前|問い合わせ前|顧客|利用者|担当者|迷い|不安|接点|入口|入り口)"),
    "operating_behavior": re.compile(r"(?:運用|確認|整理|見直|順番|FAQ|メモ|質問|小さく試|残したい)"),
    "decision_principle": re.compile(r"(?:判断|原則|急がせ|結論を急|無理に|前提|決める|広げすぎない)"),
    "support_process": re.compile(r"(?:支援範囲|支援|サポート|初回|相談|問い合わせ|導入後|見直し|確認質問|FAQ)"),
    "brand_posture_in_action": re.compile(r"(?:姿勢|行動|急がせない|受け止め|話しやす|続けられる|小さく試|運用の積み重ね)"),
    "proof_signal": re.compile(r"(?:実際|記録|問い合わせ|質問|FAQ|メモ|見直し|確認|繰り返|戻ってきた)"),
}
_BRANDING_UNSUPPORTED_CLAIM_RE = re.compile(
    r"(?:[0-9０-９]+(?:[.,．][0-9０-９]+)?\s*(?:%|％|割|倍|件|時間|分|日|人|社|円|万円|回|ポイント)|"
    r"無料|有料|価格|料金|成果|実績|削減|改善率|満足度|受賞|表彰|提携|協業|パートナー|顧客名|導入企業|"
    r"株式会社[一-龥A-Za-z0-9・ー]{1,24}|[一-龥A-Za-z0-9・ー]{1,24}株式会社)"
)
_BRANDING_VISIBLE_EXPERIMENT_TERM_RE = re.compile(
    r"(?:運用改善を読むブランドストーリーブロガー|CS責任者|広報が本職のブロガー|note編集者|"
    r"採用広報も見る企業noteライター|企業広報編集者|branding_operational_posture|branding_01_base|"
    r"persona|ペルソナ|hidden|editor|full_rewrite|middle_onward|late_35_only|sparse|source_contract)",
    flags=re.IGNORECASE,
)
_BRANDING_SUBJECT_ANCHOR_SLOT = "brand_subject_anchor"
_BRANDING_COMPANY_NAME_RE = re.compile(
    r"(?:[一-龥ァ-ヴーA-Za-z0-9・ー]{2,32}(?:株式会社|合同会社|有限会社)|"
    r"(?:株式会社|合同会社|有限会社)[一-龥ァ-ヴーA-Za-z0-9・ー]{2,32})"
)
_BRANDING_QUOTED_OFFERING_RE = re.compile(
    r"[「『]([^」』]{2,40})[」』]\s*(?:SaaS|サービス|システム|ツール|アプリ|プロダクト|製品|商品|ブランド)?"
)
_BRANDING_OFFERING_ANCHOR_RE = re.compile(
    r"([一-龥ァ-ヴーA-Za-z0-9・ー]{2,48}"
    r"(?:向け|用|業務|導入|運用|定着|管理|支援|サポート|SaaS|サービス|システム|ツール|アプリ|プロダクト|製品|商品|ブランド)"
    r"[一-龥ァ-ヴーA-Za-z0-9・ーのをする・、]{0,32}"
    r"(?:SaaS|サービス|システム|ツール|アプリ|プロダクト|製品|商品|ブランド|支援|サポート))"
)
_BRANDING_SUBJECT_ANCHOR_DETAIL_RE = re.compile(
    r"([一-龥ァ-ヴーA-Za-z0-9・ー]{2,36}"
    r"(?:SaaS|サービス|システム|ツール|アプリ|プロダクト|製品|商品|支援|サポート))"
)
_BRANDING_SUBJECT_ANCHOR_DOMAIN_RE = re.compile(
    r"(?:業務SaaS|業務整理|導入定着|運用定着|導入初期の運用定着|FAQ整備|初回設定|サポート運用|オンボーディング)"
)
_CROSS_DEPARTMENT_AXIS_LABELS = {
    "approval_flow": "承認フロー",
    "ownership": "責任の置き方",
    "auditability": "監査のしやすさ",
    "承認フロー": "承認フロー",
    "責任分担": "責任の置き方",
    "責任の置き方": "責任の置き方",
    "担当責任": "責任の置き方",
    "担当責任の置き方": "責任の置き方",
    "監査のしやすさ": "監査のしやすさ",
}


def _to_plain_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _to_plain_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _clean_inline_text(value: Any, *, limit: int = 180) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _draft_has_visible_content(draft: DraftSections) -> bool:
    return bool(str(draft.body or "").strip())


def _compact_text_len(text: Any) -> int:
    return len(re.sub(r"\s+", "", str(text or "")))


def _split_body_sections(body: Any) -> list[Dict[str, str]]:
    sections: list[Dict[str, str]] = []
    current_heading = ""
    current_lines: list[str] = []
    for raw_line in str(body or "").replace("\r\n", "\n").replace("\r", "\n").splitlines():
        matched = re.match(r"^##\s+(.+)$", raw_line.strip())
        if matched:
            if current_heading:
                sections.append({"heading": current_heading, "body": "\n".join(current_lines).strip()})
            current_heading = matched.group(1).strip()
            current_lines = []
            continue
        if current_heading:
            current_lines.append(raw_line)
    if current_heading:
        sections.append({"heading": current_heading, "body": "\n".join(current_lines).strip()})
    return sections


def _clean_stage_items(values: Any, *, limit: int, char_limit: int) -> list[str]:
    items: list[str] = []
    raw_values = [values] if isinstance(values, str) else list(values or [])
    for item in raw_values:
        text = _clean_inline_text(item, limit=char_limit)
        if not text or text in items:
            continue
        items.append(text)
        if len(items) >= limit:
            break
    return items


def _escape_control_chars_in_json_strings(text: str) -> str:
    escaped_chars: list[str] = []
    in_string = False
    escape_next = False
    for char in str(text or ""):
        if in_string:
            if escape_next:
                escaped_chars.append(char)
                escape_next = False
                continue
            if char == "\\":
                escaped_chars.append(char)
                escape_next = True
                continue
            if char == '"':
                escaped_chars.append(char)
                in_string = False
                continue
            if char == "\n":
                escaped_chars.append("\\n")
                continue
            if char == "\r":
                escaped_chars.append("\\r")
                continue
            if char == "\t":
                escaped_chars.append("\\t")
                continue
            escaped_chars.append(char)
            continue
        escaped_chars.append(char)
        if char == '"':
            in_string = True
    return "".join(escaped_chars)


def _try_parse_json_object(text: str) -> Dict[str, Any]:
    candidates = [str(text or "")]
    repaired = _escape_control_chars_in_json_strings(text)
    if repaired != candidates[0]:
        candidates.append(repaired)
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return dict(parsed)
    return {}


def _extract_json_object(raw_text: Any) -> Dict[str, Any]:
    text = str(raw_text or "").strip()
    if not text:
        return {}
    text = re.sub(r"^\s*`{3,}[^\n]*\n", "", text)
    text = re.sub(r"\n\s*`{3,}\s*$", "", text).strip()
    parsed = _try_parse_json_object(text)
    if parsed:
        return parsed
    matched = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not matched:
        return {}
    return _try_parse_json_object(matched.group(0))


def _mapping_get_any(mapping: Mapping[str, Any] | None, *keys: str) -> Any:
    if not isinstance(mapping, Mapping):
        return None
    lowered = {str(key).strip().lower(): value for key, value in dict(mapping).items()}
    for key in keys:
        if key in mapping:
            return mapping.get(key)
        normalized_key = str(key or "").strip().lower()
        if normalized_key in lowered:
            return lowered[normalized_key]
    return None


def _extract_balanced_braced_objects(text: Any) -> list[str]:
    raw_text = str(text or "")
    candidates: list[str] = []
    start: int | None = None
    depth = 0
    in_string = False
    escape_next = False
    for index, char in enumerate(raw_text):
        if in_string:
            if escape_next:
                escape_next = False
            elif char == "\\":
                escape_next = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
            continue
        if char == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start is not None:
                candidates.append(raw_text[start : index + 1])
                start = None
    return candidates


def _extract_stage_text_candidates(raw_text: Any, *, tag_names: Sequence[str] = ()) -> list[tuple[str, str]]:
    text = str(raw_text or "").strip()
    if not text:
        return []
    candidates: list[tuple[str, str]] = [("raw", text)]
    for tag_name in tag_names:
        normalized_tag = re.escape(str(tag_name or "").strip())
        if not normalized_tag:
            continue
        patterns = (
            rf"<{normalized_tag}>\s*([\s\S]*?)\s*</{normalized_tag}>",
            rf"\[{normalized_tag}\]\s*([\s\S]*?)\s*\[/{normalized_tag}\]",
        )
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                candidate = str(match.group(1) or "").strip()
                if candidate:
                    candidates.insert(0, ("tagged", candidate))
    for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE):
        candidate = str(match.group(1) or "").strip()
        if candidate:
            candidates.insert(0, ("fenced", candidate))
    seen: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for source, candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        deduped.append((source, candidate))
    return deduped


def _quote_bare_json_keys(text: str) -> str:
    return re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', str(text or ""))


def _remove_trailing_json_commas(text: str) -> str:
    return re.sub(r",(\s*[}\]])", r"\1", str(text or ""))


def _try_parse_python_mapping(text: str) -> Dict[str, Any]:
    try:
        parsed = ast.literal_eval(str(text or ""))
    except (SyntaxError, ValueError):
        return {}
    if isinstance(parsed, dict):
        return dict(parsed)
    return {}


def _try_parse_json_like_object(text: str) -> tuple[Dict[str, Any], str]:
    raw_text = str(text or "").strip()
    if not raw_text:
        return {}, ""
    quoted_keys = _quote_bare_json_keys(raw_text)
    repaired_variants = [
        ("strict_json", raw_text),
        ("escaped_json", _escape_control_chars_in_json_strings(raw_text)),
        ("quoted_keys_json", quoted_keys),
        ("quoted_keys_escaped_json", _escape_control_chars_in_json_strings(quoted_keys)),
        ("quoted_keys_no_trailing_commas_json", _remove_trailing_json_commas(quoted_keys)),
        (
            "quoted_keys_no_trailing_commas_escaped_json",
            _escape_control_chars_in_json_strings(_remove_trailing_json_commas(quoted_keys)),
        ),
    ]
    seen_json_candidates: set[str] = set()
    for mode, candidate in repaired_variants:
        if not candidate or candidate in seen_json_candidates:
            continue
        seen_json_candidates.add(candidate)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return dict(parsed), mode
    literal_variants = [
        ("python_literal", raw_text),
        ("quoted_keys_python_literal", quoted_keys),
        ("quoted_keys_no_trailing_commas_python_literal", _remove_trailing_json_commas(quoted_keys)),
    ]
    seen_literal_candidates: set[str] = set()
    for mode, candidate in literal_variants:
        if not candidate or candidate in seen_literal_candidates:
            continue
        seen_literal_candidates.add(candidate)
        parsed = _try_parse_python_mapping(candidate)
        if parsed:
            return parsed, mode
    return {}, ""


def _normalize_stage_certainty(value: Any) -> str:
    normalized = str(value or "").strip().upper()
    if normalized in {"SUPPORTED", "UNCLEAR", "CONFLICTED"}:
        return normalized
    return "UNCLEAR"


def _normalize_support_facts(values: Any) -> list[Dict[str, str]]:
    facts: list[Dict[str, str]] = []
    for index, item in enumerate(list(values or [])[:12], start=1):
        if isinstance(item, str):
            claim = _clean_inline_text(item, limit=160)
            if not claim:
                continue
            facts.append(
                {
                    "fact_id": f"F{index}",
                    "source_id": f"S{index}",
                    "claim": claim,
                    "evidence_excerpt": claim,
                    "certainty": "UNCLEAR",
                }
            )
            continue
        if not isinstance(item, Mapping):
            continue
        fact_id = _clean_inline_text(_mapping_get_any(item, "fact_id", "id") or f"F{index}", limit=16) or f"F{index}"
        source_id = _clean_inline_text(_mapping_get_any(item, "source_id", "source", "source_ref") or f"S{index}", limit=16) or f"S{index}"
        claim = _clean_inline_text(
            _mapping_get_any(item, "claim", "fact", "summary", "detail", "statement") or "",
            limit=160,
        )
        evidence_excerpt = _clean_inline_text(
            _mapping_get_any(item, "evidence_excerpt", "evidence", "excerpt", "quote") or "",
            limit=160,
        )
        certainty = _normalize_stage_certainty(_mapping_get_any(item, "certainty", "confidence", "support"))
        if not claim:
            continue
        facts.append(
            {
                "fact_id": fact_id,
                "source_id": source_id,
                "claim": claim,
                "evidence_excerpt": evidence_excerpt or claim,
                "certainty": certainty,
            }
        )
    return facts


def _normalize_support_section_brief_item(
    item: Mapping[str, Any],
    *,
    source_digest: list[str],
    fact_lookup: Mapping[str, str],
) -> Dict[str, str]:
    def resolve_fact_anchor(value: Any) -> str:
        values = list(value) if isinstance(value, list) else [value]
        anchors: list[str] = []
        for raw_value in values:
            text = _clean_inline_text(raw_value or "", limit=96)
            if not text:
                continue
            resolved = _clean_inline_text(fact_lookup.get(text) or text, limit=96)
            if resolved and resolved not in anchors:
                anchors.append(resolved)
        return " / ".join(anchors)[:96]

    def normalize_stringish(value: Any, *, limit: int) -> str:
        if isinstance(value, list):
            return _clean_inline_text(" / ".join(_clean_stage_items(value, limit=3, char_limit=limit)), limit=limit)
        return _clean_inline_text(value or "", limit=limit)

    heading = _clean_inline_text(_mapping_get_any(item, "heading", "title", "section", "name") or "", limit=48)
    section_focus = normalize_stringish(
        _mapping_get_any(
            item,
            "section_focus",
            "focus",
            "summary",
            "claim",
            "key_message",
            "purpose",
            "section_purpose",
            "section_goal",
        )
        or "",
        limit=80,
    )
    fact_anchor = resolve_fact_anchor(
        _mapping_get_any(item, "fact_anchor", "anchor", "supporting_fact", "evidence", "fact", "source_anchor") or ""
    )
    fact_id = _clean_inline_text(_mapping_get_any(item, "fact_id", "source_fact_id") or "", limit=24)
    if not fact_anchor and fact_id:
        fact_anchor = _clean_inline_text(fact_lookup.get(fact_id) or "", limit=96)
    why_it_matters = normalize_stringish(
        _mapping_get_any(item, "why_it_matters", "importance", "reason", "why", "so_what") or "",
        limit=96,
    )
    do_not_mix = normalize_stringish(
        _mapping_get_any(item, "do_not_mix", "guardrail", "avoid", "boundary", "dont_mix") or "",
        limit=80,
    )
    if not section_focus:
        section_focus = _clean_inline_text(heading or why_it_matters, limit=80)
    if not heading or not section_focus or not fact_anchor:
        return {}
    if not why_it_matters:
        why_it_matters = section_focus
    if not do_not_mix:
        do_not_mix = "他節の論点を混ぜない"
    if fact_anchor not in source_digest:
        source_digest.append(fact_anchor)
        del source_digest[6:]
    return {
        "heading": heading,
        "section_focus": section_focus,
        "fact_anchor": fact_anchor,
        "why_it_matters": why_it_matters,
        "do_not_mix": do_not_mix,
    }


def _clean_support_recovery_value(value: Any, *, limit: int) -> str:
    text = str(value or "").strip().strip(",")
    text = text.strip('"').strip("'")
    text = re.sub(r"^[\[\{]\s*", "", text)
    text = re.sub(r"\s*[\]\}]$", "", text)
    return _clean_inline_text(text, limit=limit)


def _split_support_recovery_key_value(line: str) -> tuple[str, str]:
    matched = re.match(
        r'^[\-\*\d\.\)\s"\']*(?P<key>[A-Za-z_][A-Za-z0-9_ ]{0,40}?)[\s"\']*[:=]\s*(?P<value>.+?)\s*$',
        str(line or ""),
    )
    if not matched:
        return "", ""
    key = str(matched.group("key") or "").strip().strip('"').strip("'").replace(" ", "_").lower()
    value = str(matched.group("value") or "").strip()
    return key, value


def _recover_support_section_briefs(raw_text: Any, *, fact_lookup: Mapping[str, str]) -> list[Dict[str, str]]:
    text = str(raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not text:
        return []
    text = re.sub(r"```(?:json)?", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"`{3,}", "\n", text)
    text = re.sub(r"(?i)</?script_json>", "\n", text)
    text = re.sub(r"(?i)\[/?script_json\]", "\n", text)
    text = re.sub(r",\s*(?=(?:[\"']?[A-Za-z_][A-Za-z0-9_ ]*[\"']?\s*[:=]))", "\n", text)
    text = text.replace("{", "\n").replace("}", "\n").replace("[", "\n").replace("]", "\n")

    heading_keys = {"heading", "title", "section", "name"}
    focus_keys = {"section_focus", "focus", "summary", "claim", "key_message", "purpose"}
    fact_anchor_keys = {"fact_anchor", "anchor", "supporting_fact", "evidence", "fact", "source_anchor"}
    fact_id_keys = {"fact_id", "source_fact_id"}
    why_keys = {"why_it_matters", "importance", "reason", "why", "so_what"}
    do_not_mix_keys = {"do_not_mix", "guardrail", "avoid", "boundary", "dont_mix"}

    recovered: list[Dict[str, str]] = []
    source_digest: list[str] = []
    current: Dict[str, Any] = {}

    def flush_current() -> None:
        nonlocal current
        if not current:
            return
        normalized = _normalize_support_section_brief_item(current, source_digest=source_digest, fact_lookup=fact_lookup)
        if normalized:
            recovered.append(normalized)
        current = {}

    for raw_line in text.splitlines():
        key, value = _split_support_recovery_key_value(raw_line.strip())
        if not key or not value:
            continue
        if key in heading_keys:
            flush_current()
            current = {"heading": _clean_support_recovery_value(value, limit=48)}
            continue
        if not current:
            continue
        if key in focus_keys:
            current["section_focus"] = _clean_support_recovery_value(value, limit=80)
        elif key in fact_anchor_keys:
            current["fact_anchor"] = _clean_support_recovery_value(value, limit=96)
        elif key in fact_id_keys:
            current["fact_id"] = _clean_support_recovery_value(value, limit=24)
        elif key in why_keys:
            current["why_it_matters"] = _clean_support_recovery_value(value, limit=96)
        elif key in do_not_mix_keys:
            current["do_not_mix"] = _clean_support_recovery_value(value, limit=80)
    flush_current()
    return recovered[:6]


def _detect_stage_payload_keys(raw_text: Any) -> list[str]:
    keys: list[str] = []
    for match in re.finditer(r'["\']?([A-Za-z_][A-Za-z0-9_]{1,40})["\']?\s*[:=]', str(raw_text or "")):
        key = str(match.group(1) or "").strip()
        if not key or key in keys:
            continue
        keys.append(key)
        if len(keys) >= 16:
            break
    return keys


def _parse_support_script(raw_text: Any, contract: Mapping[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    payload: Dict[str, Any] = {}
    payload_source = ""
    parse_mode = ""
    for source_label, candidate in _extract_stage_text_candidates(raw_text, tag_names=("SCRIPT_JSON",)):
        payload, parse_mode = _try_parse_json_like_object(candidate)
        if payload:
            payload_source = source_label
            break
        for braced_candidate in _extract_balanced_braced_objects(candidate):
            payload, parse_mode = _try_parse_json_like_object(braced_candidate)
            if payload:
                payload_source = source_label
                break
        if payload:
            break

    normalized = _normalize_support_script(payload, contract)
    fact_lookup = {
        _clean_inline_text(item.get("fact_id") or "", limit=24): _clean_inline_text(
            item.get("evidence_excerpt") or item.get("claim") or "",
            limit=96,
        )
        for item in list(normalized.get("facts") or [])
        if isinstance(item, Mapping)
    }
    section_source = "missing"
    if normalized.get("section_briefs"):
        raw_section_values = _mapping_get_any(payload, "section_briefs", "sections", "section_outline", "section_plan", "briefs")
        if _mapping_get_any(payload, "section_briefs") is not None:
            section_source = "section_briefs"
        elif raw_section_values is not None:
            section_source = "section_alias"
        else:
            section_source = "mapping"
    else:
        recovered_briefs = _recover_support_section_briefs(raw_text, fact_lookup=fact_lookup)
        if recovered_briefs:
            normalized["section_briefs"] = recovered_briefs
            for item in recovered_briefs:
                fact_anchor = _clean_inline_text(item.get("fact_anchor") or "", limit=96)
                if fact_anchor and fact_anchor not in list(normalized.get("source_digest") or []):
                    normalized.setdefault("source_digest", []).append(fact_anchor)
                    normalized["source_digest"] = list(normalized.get("source_digest") or [])[:6]
            section_source = "key_value_recovery"
            if not parse_mode:
                parse_mode = "key_value_recovery"
        elif not parse_mode:
            parse_mode = "failed"

    summary = {
        "parse_mode": parse_mode or "failed",
        "payload_source": payload_source or "raw",
        "section_briefs_source": section_source,
        "section_brief_count": len(list(normalized.get("section_briefs") or [])),
        "fact_count": len(list(normalized.get("facts") or [])),
        "source_digest_count": len(list(normalized.get("source_digest") or [])),
        "detected_keys": _detect_stage_payload_keys(raw_text),
        "raw_char_count": len(str(raw_text or "")),
        "raw_preview": _clean_inline_text(raw_text, limit=240),
    }
    return normalized, summary


def _normalize_support_script(script: Mapping[str, Any], contract: Mapping[str, Any]) -> Dict[str, Any]:
    source_digest = _clean_stage_items(
        _mapping_get_any(script, "source_digest", "source_summary", "source_notes"),
        limit=6,
        char_limit=120,
    )
    facts = _normalize_support_facts(_mapping_get_any(script, "facts", "fact_items", "supporting_facts"))
    fact_lookup = {
        _clean_inline_text(item.get("fact_id") or "", limit=24): _clean_inline_text(
            item.get("evidence_excerpt") or item.get("claim") or "",
            limit=96,
        )
        for item in facts
    }
    section_briefs: list[Dict[str, str]] = []
    raw_section_values = _mapping_get_any(script, "section_briefs", "sections", "section_outline", "section_plan", "briefs")
    for item in list(raw_section_values or [])[:6]:
        if not isinstance(item, Mapping):
            continue
        normalized_item = _normalize_support_section_brief_item(item, source_digest=source_digest, fact_lookup=fact_lookup)
        if normalized_item:
            section_briefs.append(normalized_item)
    for fact in facts:
        claim = _clean_inline_text(fact.get("claim") or "", limit=120)
        if claim and claim not in source_digest:
            source_digest.append(claim)
            del source_digest[6:]
    return {
        "reader": _clean_inline_text(
            _mapping_get_any(script, "reader", "audience") or contract.get("audience_profile") or "一般読者",
            limit=80,
        ),
        "search_intent": _clean_inline_text(_mapping_get_any(script, "search_intent", "intent") or "", limit=120),
        "article_stance": _clean_inline_text(_mapping_get_any(script, "article_stance", "stance") or "", limit=80),
        "assertion_level": _clean_inline_text(
            _mapping_get_any(script, "assertion_level", "assertion") or "balanced",
            limit=24,
        ),
        "narrative_distance": _clean_inline_text(
            _mapping_get_any(script, "narrative_distance", "distance") or "guide",
            limit=24,
        ),
        "core_message": _clean_inline_text(
            _mapping_get_any(script, "core_message", "message") or contract.get("core_message") or contract.get("topic_statement") or "",
            limit=120,
        ),
        "facts": facts,
        "interpretations": _clean_stage_items(_mapping_get_any(script, "interpretations", "insights"), limit=6, char_limit=120),
        "unknowns": _clean_stage_items(_mapping_get_any(script, "unknowns", "open_questions"), limit=6, char_limit=120),
        "prompt_injection_risks": _clean_stage_items(
            _mapping_get_any(script, "prompt_injection_risks", "risks"),
            limit=6,
            char_limit=140,
        ),
        "source_digest": source_digest,
        "section_briefs": section_briefs,
        "writing_cautions": _clean_stage_items(_mapping_get_any(script, "writing_cautions", "cautions"), limit=6, char_limit=96),
    }


def _normalize_planner_output(planner: Mapping[str, Any]) -> Dict[str, Any]:
    heading_candidates = _clean_stage_items(planner.get("heading_candidates"), limit=6, char_limit=48)
    if not heading_candidates:
        for item in list(planner.get("sections") or [])[:6]:
            if not isinstance(item, Mapping):
                continue
            heading = _clean_inline_text(item.get("heading") or "", limit=48)
            if heading and heading not in heading_candidates:
                heading_candidates.append(heading)
    return {
        "provisional_title": _clean_inline_text(
            planner.get("provisional_title") or planner.get("title_intent") or "",
            limit=96,
        ),
        "reader": _clean_inline_text(planner.get("reader") or "", limit=80),
        "search_intent": _clean_inline_text(planner.get("search_intent") or "", limit=120),
        "article_stance": _clean_inline_text(planner.get("article_stance") or "", limit=80),
        "assertion_level": _clean_inline_text(planner.get("assertion_level") or "balanced", limit=24),
        "narrative_distance": _clean_inline_text(planner.get("narrative_distance") or "guide", limit=24),
        "claim_core": _clean_inline_text(planner.get("claim_core") or planner.get("lead_intent") or "", limit=120),
        "intro_role": _clean_inline_text(planner.get("intro_role") or "", limit=96),
        "middle_role": _clean_inline_text(planner.get("middle_role") or "", limit=96),
        "ending_role": _clean_inline_text(planner.get("ending_role") or "", limit=96),
        "heading_candidates": heading_candidates,
        "overlap_guard": _clean_stage_items(planner.get("overlap_guard"), limit=6, char_limit=96),
        "required_fact_ids": _clean_stage_items(planner.get("required_fact_ids"), limit=10, char_limit=24),
        "optional_fact_ids": _clean_stage_items(planner.get("optional_fact_ids"), limit=10, char_limit=24),
        "style_anchor": _clean_stage_items(planner.get("style_anchor"), limit=8, char_limit=120),
        "edit_start_ratio": max(0.5, min(0.85, float(planner.get("edit_start_ratio", 0.7) or 0.7))),
    }


def _snapshot_support_script(script: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "reader": _clean_inline_text(script.get("reader") or "", limit=80),
        "search_intent": _clean_inline_text(script.get("search_intent") or "", limit=120),
        "article_stance": _clean_inline_text(script.get("article_stance") or "", limit=80),
        "assertion_level": _clean_inline_text(script.get("assertion_level") or "", limit=24),
        "narrative_distance": _clean_inline_text(script.get("narrative_distance") or "", limit=24),
        "core_message": _clean_inline_text(script.get("core_message") or "", limit=120),
        "facts": [
            {
                "fact_id": _clean_inline_text(item.get("fact_id") or "", limit=16),
                "source_id": _clean_inline_text(item.get("source_id") or "", limit=16),
                "claim": _clean_inline_text(item.get("claim") or "", limit=96),
                "certainty": _clean_inline_text(item.get("certainty") or "", limit=16),
            }
            for item in list(script.get("facts") or [])[:4]
            if isinstance(item, Mapping)
        ],
        "prompt_injection_risks": list(script.get("prompt_injection_risks") or [])[:4],
        "source_digest": list(script.get("source_digest") or [])[:4],
        "section_briefs": [
            {
                "heading": _clean_inline_text(item.get("heading") or "", limit=48),
                "section_focus": _clean_inline_text(item.get("section_focus") or "", limit=80),
                "fact_anchor": _clean_inline_text(item.get("fact_anchor") or "", limit=96),
                "why_it_matters": _clean_inline_text(item.get("why_it_matters") or "", limit=96),
                "do_not_mix": _clean_inline_text(item.get("do_not_mix") or "", limit=80),
            }
            for item in list(script.get("section_briefs") or [])[:4]
            if isinstance(item, Mapping)
        ],
        "writing_cautions": list(script.get("writing_cautions") or [])[:4],
    }


def _snapshot_planner_output(planner: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "provisional_title": _clean_inline_text(planner.get("provisional_title") or "", limit=96),
        "claim_core": _clean_inline_text(planner.get("claim_core") or "", limit=120),
        "intro_role": _clean_inline_text(planner.get("intro_role") or "", limit=96),
        "middle_role": _clean_inline_text(planner.get("middle_role") or "", limit=96),
        "ending_role": _clean_inline_text(planner.get("ending_role") or "", limit=96),
        "heading_candidates": list(planner.get("heading_candidates") or [])[:4],
        "required_fact_ids": list(planner.get("required_fact_ids") or [])[:6],
        "style_anchor": list(planner.get("style_anchor") or [])[:4],
        "edit_start_ratio": float(planner.get("edit_start_ratio", 0.7) or 0.7),
    }


def _normalize_section_wrappers(text: Any) -> str:
    normalized = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    normalized = _SECTION_WRAPPER_RE.sub(
        lambda match: f"## {_clean_inline_text(match.group(1) or '', limit=80)}",
        normalized,
    )
    normalized = re.sub(r"(?m)^\s*\[/?SECTION\]\s*$", "", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _extract_used_fact_ids(raw_text: Any) -> list[str]:
    matched = _USED_FACT_IDS_TAG_RE.search(str(raw_text or ""))
    if not matched:
        return []
    ids: list[str] = []
    for raw_line in matched.group(1).splitlines():
        text = re.sub(r"^[\-\*\d\.\s]+", "", raw_line).strip()
        if not text or text in ids:
            continue
        ids.append(text[:24])
    return ids


def _compose_tagged_article_text(draft: DraftSections, *, used_fact_ids: Sequence[str] | None = None) -> str:
    blocks = [
        "[TITLE]",
        str(draft.title or "").strip(),
        "[/TITLE]",
        "[LEAD]",
        str(draft.lead or "").strip(),
        "[/LEAD]",
        "[BODY]",
        str(draft.body or "").strip(),
        "[/BODY]",
        "[HASHTAGS]",
        str(draft.hashtags or "").strip(),
        "[/HASHTAGS]",
    ]
    if list(used_fact_ids or []):
        blocks.extend(
            [
                "[USED_FACT_IDS]",
                "\n".join(f"- {item}" for item in list(used_fact_ids or [])[:12]),
                "[/USED_FACT_IDS]",
            ]
        )
    return "\n".join(blocks).strip()


def _join_sections(sections: Sequence[Mapping[str, Any]]) -> str:
    chunks: list[str] = []
    for item in sections:
        heading = _clean_inline_text(item.get("heading") or "", limit=80)
        body = str(item.get("body") or "").strip()
        if not heading:
            continue
        section_text = f"## {heading}"
        if body:
            section_text = f"{section_text}\n\n{body}"
        chunks.append(section_text.strip())
    return "\n\n".join(chunk for chunk in chunks if chunk).strip()


def _build_suffix_edit_window(body: Any, *, start_ratio: float) -> Dict[str, Any]:
    normalized_body = str(body or "").strip()
    if not normalized_body:
        return {"keep_prefix": "", "edit_target_suffix": "", "basis": "empty", "split_ratio": start_ratio}
    sections = _split_body_sections(normalized_body)
    bounded_ratio = max(0.5, min(0.85, float(start_ratio or 0.7)))
    if len(sections) >= 2:
        split_index = int(len(sections) * bounded_ratio)
        split_index = min(max(split_index, 1), len(sections) - 1)
        return {
            "keep_prefix": _join_sections(sections[:split_index]),
            "edit_target_suffix": _join_sections(sections[split_index:]),
            "basis": "section_boundary",
            "split_ratio": bounded_ratio,
        }
    paragraphs = [chunk.strip() for chunk in re.split(r"\n\s*\n", normalized_body) if chunk.strip()]
    if len(paragraphs) >= 2:
        split_index = int(len(paragraphs) * bounded_ratio)
        split_index = min(max(split_index, 1), len(paragraphs) - 1)
        return {
            "keep_prefix": "\n\n".join(paragraphs[:split_index]).strip(),
            "edit_target_suffix": "\n\n".join(paragraphs[split_index:]).strip(),
            "basis": "paragraph_boundary",
            "split_ratio": bounded_ratio,
        }
    split_at = max(1, int(len(normalized_body) * bounded_ratio))
    breakpoint = normalized_body.find("。", split_at)
    if breakpoint >= 0:
        split_at = breakpoint + 1
    return {
        "keep_prefix": normalized_body[:split_at].strip(),
        "edit_target_suffix": normalized_body[split_at:].strip(),
        "basis": "character_boundary",
        "split_ratio": bounded_ratio,
    }


def _normalize_suffix_edit_output(raw_text: Any, original_suffix: str) -> Dict[str, Any]:
    payload = _extract_json_object(raw_text)
    bridge_sentence = _clean_inline_text(payload.get("bridge_sentence") or "", limit=160)
    if bridge_sentence in {"必要なし", "なし", "none", "None"}:
        bridge_sentence = ""
    revised_suffix = _normalize_section_wrappers(payload.get("revised_suffix") or "")
    return {
        "bridge_sentence": bridge_sentence,
        "revised_suffix": revised_suffix or str(original_suffix or "").strip(),
        "edit_notes": _clean_stage_items(payload.get("edit_notes"), limit=6, char_limit=120),
    }


def _compose_suffix_edited_body(keep_prefix: str, bridge_sentence: str, revised_suffix: str) -> str:
    parts: list[str] = []
    prefix = str(keep_prefix or "").strip()
    bridge = str(bridge_sentence or "").strip()
    suffix = str(revised_suffix or "").strip()
    if prefix:
        parts.append(prefix)
    if bridge:
        parts.append(bridge)
    if suffix:
        parts.append(suffix)
    return "\n\n".join(part for part in parts if part).strip()


def _normalize_audit_result(raw_text: Any) -> Dict[str, Any]:
    payload = _extract_json_object(raw_text)
    verdict = str(
        payload.get("overall_judgement")
        or payload.get("総合判定")
        or payload.get("verdict")
        or ""
    ).strip().upper()
    if verdict not in {"PASS", "WARN", "FAIL"}:
        verdict = ""
    findings: list[Dict[str, str]] = []
    for item in list(payload.get("findings") or payload.get("FINDINGS") or [])[:8]:
        if not isinstance(item, Mapping):
            continue
        findings.append(
            {
                "severity": _clean_inline_text(item.get("severity") or "", limit=16).upper(),
                "location": _clean_inline_text(item.get("location") or "", limit=80),
                "issue": _clean_inline_text(item.get("issue") or "", limit=120),
                "reason": _clean_inline_text(item.get("reason") or "", limit=140),
                "fix_direction": _clean_inline_text(item.get("fix_direction") or "", limit=140),
            }
        )
    return {
        "overall_judgement": verdict,
        "findings": findings,
        "minimal_fix_instructions": _clean_stage_items(
            payload.get("minimal_fix_instructions") or payload.get("MINIMAL_FIX_INSTRUCTIONS"),
            limit=8,
            char_limit=140,
        ),
        "next_action": _clean_inline_text(payload.get("next_action") or "", limit=40).upper(),
    }


def _build_experimental_prompt_stack_visibility_summary(
    stage_summary: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    normalized_summary = dict(stage_summary or {})
    audit_result = dict(normalized_summary.get("audit_result") or {})
    verdict = str(audit_result.get("overall_judgement") or "").strip().upper()
    if verdict not in {"PASS", "WARN", "FAIL"}:
        verdict = ""
    completed_stages = [
        str(item).strip()
        for item in list(normalized_summary.get("stages_completed") or [])
        if str(item or "").strip()
    ]
    findings = [
        dict(item)
        for item in list(audit_result.get("findings") or [])
        if isinstance(item, Mapping)
    ]
    top_finding = dict(findings[0]) if findings else {}
    fallback_reason = str(normalized_summary.get("fallback_reason") or "").strip()
    used_fallback_generation = bool(normalized_summary.get("used_fallback_generation", False))
    if used_fallback_generation:
        run_state = "fallback"
        compare_ready = False
        compare_reason = fallback_reason or "fallback_generation_used"
    elif verdict == "PASS":
        run_state = "completed"
        compare_ready = True
        compare_reason = "ready_for_compare"
    elif verdict == "WARN":
        run_state = "completed"
        compare_ready = True
        compare_reason = "compare_with_audit_warning"
    elif verdict == "FAIL":
        run_state = "completed"
        compare_ready = False
        compare_reason = "audit_failed"
    elif completed_stages:
        run_state = "partial"
        compare_ready = False
        compare_reason = "audit_verdict_missing"
    else:
        run_state = "not_started"
        compare_ready = False
        compare_reason = "stage_execution_missing"
    return {
        "experiment": _EXPERIMENTAL_PROMPT_STACK,
        "run_state": run_state,
        "audit_verdict": verdict,
        "next_action": str(audit_result.get("next_action") or "").strip().upper(),
        "finding_count": len(findings),
        "top_issue": str(top_finding.get("issue") or "").strip(),
        "top_fix_direction": str(top_finding.get("fix_direction") or "").strip(),
        "used_fallback_generation": used_fallback_generation,
        "fallback_reason": fallback_reason,
        "completed_stages": completed_stages,
        "completed_stage_count": len(completed_stages),
        "expected_stage_count": len(_EXPERIMENTAL_PROMPT_STACK_STAGE_ORDER),
        "compare_ready": compare_ready,
        "compare_reason": compare_reason,
    }


def _render_stage_prompt(
    base_prompt: str,
    *,
    script_json: Mapping[str, Any] | None = None,
    planner_json: Mapping[str, Any] | None = None,
    draft_article: str = "",
    keep_prefix: str = "",
    edit_target_suffix: str = "",
    final_article: str = "",
    used_fact_ids: Sequence[str] | None = None,
) -> str:
    rendered = str(base_prompt or "")
    if script_json is not None:
        script_block = "<SCRIPT_JSON>\n" + json.dumps(script_json, ensure_ascii=False, indent=2) + "\n</SCRIPT_JSON>"
        rendered = rendered.replace("<SCRIPT_JSON>...</SCRIPT_JSON>", script_block)
    if planner_json is not None:
        planner_block = "<PLANNER_JSON>\n" + json.dumps(planner_json, ensure_ascii=False, indent=2) + "\n</PLANNER_JSON>"
        rendered = rendered.replace("<PLANNER_JSON>...</PLANNER_JSON>", planner_block)
    if draft_article:
        draft_block = "<DRAFT_ARTICLE>\n" + draft_article.strip() + "\n</DRAFT_ARTICLE>"
        rendered = rendered.replace("<DRAFT_ARTICLE>...</DRAFT_ARTICLE>", draft_block)
    if keep_prefix:
        keep_prefix_block = "<KEEP_PREFIX>\n" + keep_prefix.strip() + "\n</KEEP_PREFIX>"
        rendered = rendered.replace("<KEEP_PREFIX>...</KEEP_PREFIX>", keep_prefix_block)
    if edit_target_suffix:
        edit_target_suffix_block = "<EDIT_TARGET_SUFFIX>\n" + edit_target_suffix.strip() + "\n</EDIT_TARGET_SUFFIX>"
        rendered = rendered.replace("<EDIT_TARGET_SUFFIX>...</EDIT_TARGET_SUFFIX>", edit_target_suffix_block)
    if final_article:
        final_article_block = "<FINAL_ARTICLE>\n" + final_article.strip() + "\n</FINAL_ARTICLE>"
        rendered = rendered.replace("<FINAL_ARTICLE>...</FINAL_ARTICLE>", final_article_block)
    if used_fact_ids is not None:
        used_fact_id_lines = "\n".join(f"- {item}" for item in list(used_fact_ids or [])[:12])
        used_fact_ids_block = "<USED_FACT_IDS>\n" + used_fact_id_lines + "\n</USED_FACT_IDS>"
        rendered = rendered.replace("<USED_FACT_IDS>...</USED_FACT_IDS>", used_fact_ids_block)
    return rendered


def _normalize_prompt_stack_experiment(value: Any) -> str:
    return str(value or "").strip().lower()


def _is_prompt_stack_experiment_enabled(contract: Mapping[str, Any]) -> bool:
    return _normalize_prompt_stack_experiment(contract.get("body_generation_experiment")) == _EXPERIMENTAL_PROMPT_STACK


def _split_japanese_sentences(text: Any) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[。！？])\s*", str(text or "").strip()) if item.strip()]


def _section_body_after_heading(body: str, heading: str) -> str:
    if not heading or f"## {heading}" not in str(body or ""):
        return ""
    tail = str(body or "").split(f"## {heading}", 1)[-1]
    next_heading = re.search(r"\n##\s+", tail)
    if next_heading:
        tail = tail[: next_heading.start()]
    return tail.strip()


def _replace_section_body_after_heading(body: str, heading: str, section_body: str) -> str:
    text = str(body or "").strip()
    replacement = str(section_body or "").strip()
    if not text or not heading or f"## {heading}" not in text or not replacement:
        return text
    pattern = re.compile(
        rf"(?ms)^##\s+{re.escape(heading)}\s*\n\n.*?(?=^\s*##\s+|\Z)"
    )
    return pattern.sub(f"## {heading}\n\n{replacement}\n\n", text, count=1).strip()


def _join_japanese_or_list(items: Sequence[str]) -> str:
    cleaned = [str(item or "").strip(" 、,") for item in items if str(item or "").strip(" 、,")]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]}や{cleaned[1]}"
    return f"{'、'.join(cleaned[:-1])}や{cleaned[-1]}"


def _build_company_intro_current_business_paraphrase(value: Any) -> str:
    text = _clean_inline_text(value or "", limit=180)
    if not text:
        return ""
    matched = _COMPANY_INTRO_CURRENT_BUSINESS_ECHO_RE.match(text)
    if not matched:
        return ""
    subject = _clean_inline_text(matched.group("subject") or "", limit=40).strip(" 、,")
    activities_text = _clean_inline_text(matched.group("activities") or "", limit=120).strip(" 、,")
    if not subject or not activities_text:
        return ""
    activities = [
        _clean_inline_text(item, limit=32).strip(" 、,")
        for item in re.split(r"[、,]", activities_text)
        if _clean_inline_text(item, limit=32).strip(" 、,")
    ]
    joined_activities = _join_japanese_or_list(activities)
    if joined_activities:
        return f"{subject}では、{joined_activities}といった実務を支えています。"
    return f"{subject}では、{activities_text}に関わる実務を支えています。"


def _normalize_revision_surface_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _extract_revision_sections(body: Any) -> list[tuple[str, str]]:
    text = str(body or "").strip()
    if not text:
        return []
    sections: list[tuple[str, str]] = []
    for match in re.finditer(r"(?ms)^##\s+(.+?)\s*\n(.*?)(?=^\s*##\s+|\Z)", text):
        heading = _clean_inline_text(match.group(1) or "", limit=80)
        section_body = str(match.group(2) or "").strip()
        if heading:
            sections.append((heading, section_body))
    return sections


def _repair_preserves_flagged_scope(
    current_draft: DraftSections,
    repaired_draft: DraftSections,
    flagged_spans: list[Dict[str, str]],
) -> bool:
    if not flagged_spans:
        return True
    if _normalize_revision_surface_text(current_draft.title) != _normalize_revision_surface_text(repaired_draft.title):
        return False
    if _normalize_revision_surface_text(current_draft.lead) != _normalize_revision_surface_text(repaired_draft.lead):
        return False
    if _normalize_revision_surface_text(current_draft.hashtags) != _normalize_revision_surface_text(repaired_draft.hashtags):
        return False

    current_sections = _extract_revision_sections(current_draft.body)
    repaired_sections = _extract_revision_sections(repaired_draft.body)
    current_headings = [heading for heading, _body in current_sections]
    repaired_headings = [heading for heading, _body in repaired_sections]
    if current_headings != repaired_headings:
        return False
    if not current_sections:
        return _normalize_revision_surface_text(current_draft.body) == _normalize_revision_surface_text(repaired_draft.body)

    changed_headings = [
        heading
        for (heading, current_body), (_same_heading, repaired_body) in zip(current_sections, repaired_sections)
        if _normalize_revision_surface_text(current_body) != _normalize_revision_surface_text(repaired_body)
    ]
    if not changed_headings:
        return True

    scoped_headings = {
        _clean_inline_text(item.get("section_heading") or "", limit=80)
        for item in flagged_spans
        if _clean_inline_text(item.get("section_heading") or "", limit=80)
    }
    if scoped_headings:
        return all(heading in scoped_headings for heading in changed_headings)
    return len(changed_headings) <= 1


def _repair_preserves_local_monotony_scope(
    current_draft: DraftSections,
    repaired_draft: DraftSections,
    *,
    max_changed_headings: int = 3,
    min_section_overlap_ratio: float = 0.45,
    min_length_ratio: float = 0.55,
    max_length_ratio: float = 2.5,
) -> bool:
    if _normalize_revision_surface_text(current_draft.title) != _normalize_revision_surface_text(repaired_draft.title):
        return False
    if _normalize_revision_surface_text(current_draft.lead) != _normalize_revision_surface_text(repaired_draft.lead):
        return False
    if _normalize_revision_surface_text(current_draft.hashtags) != _normalize_revision_surface_text(repaired_draft.hashtags):
        return False

    current_sections = _extract_revision_sections(current_draft.body)
    repaired_sections = _extract_revision_sections(repaired_draft.body)
    current_headings = [heading for heading, _body in current_sections]
    repaired_headings = [heading for heading, _body in repaired_sections]
    if current_headings != repaired_headings:
        return False
    changed_sections = [
        (heading, current_body, repaired_body)
        for (heading, current_body), (_same_heading, repaired_body) in zip(current_sections, repaired_sections)
        if _normalize_revision_surface_text(current_body) != _normalize_revision_surface_text(repaired_body)
    ]
    if not changed_sections:
        return False
    if len(changed_sections) <= max_changed_headings:
        return True

    for _heading, current_body, repaired_body in changed_sections:
        current_surface = _normalize_revision_surface_text(current_body)
        repaired_surface = _normalize_revision_surface_text(repaired_body)
        current_chars = len(current_surface)
        repaired_chars = len(repaired_surface)
        if current_chars == 0 or repaired_chars == 0:
            return False
        length_ratio = repaired_chars / max(1, current_chars)
        if length_ratio < min_length_ratio or length_ratio > max_length_ratio:
            return False

        current_tokens = {token for token in _SHADOW_TOKEN_RE.findall(current_surface)}
        repaired_tokens = {token for token in _SHADOW_TOKEN_RE.findall(repaired_surface)}
        if not current_tokens or not repaired_tokens:
            return False
        overlap_ratio = len(current_tokens & repaired_tokens) / max(1, len(current_tokens))
        if overlap_ratio < min_section_overlap_ratio:
            return False
    return True


def _repair_preserves_local_patch_scope(
    current_draft: DraftSections,
    repaired_draft: DraftSections,
    *,
    target_headings: list[str] | None = None,
    max_changed_headings: int = 4,
    min_section_overlap_ratio: float = 0.45,
    min_length_ratio: float = 0.55,
    max_length_ratio: float = 2.5,
) -> bool:
    if _normalize_revision_surface_text(current_draft.title) != _normalize_revision_surface_text(repaired_draft.title):
        return False
    if _normalize_revision_surface_text(current_draft.lead) != _normalize_revision_surface_text(repaired_draft.lead):
        return False
    if _normalize_revision_surface_text(current_draft.hashtags) != _normalize_revision_surface_text(repaired_draft.hashtags):
        return False

    current_sections = _extract_revision_sections(current_draft.body)
    repaired_sections = _extract_revision_sections(repaired_draft.body)
    current_headings = [heading for heading, _body in current_sections]
    repaired_headings = [heading for heading, _body in repaired_sections]
    if current_headings != repaired_headings:
        return False

    changed_sections = [
        (heading, current_body, repaired_body)
        for (heading, current_body), (_same_heading, repaired_body) in zip(current_sections, repaired_sections)
        if _normalize_revision_surface_text(current_body) != _normalize_revision_surface_text(repaired_body)
    ]
    if not changed_sections or len(changed_sections) > max_changed_headings:
        return False

    scoped_headings = {
        _clean_inline_text(item, limit=80)
        for item in list(target_headings or [])
        if _clean_inline_text(item, limit=80)
    }
    if scoped_headings and any(heading not in scoped_headings for heading, _current_body, _repaired_body in changed_sections):
        return False

    for _heading, current_body, repaired_body in changed_sections:
        current_surface = _normalize_revision_surface_text(current_body)
        repaired_surface = _normalize_revision_surface_text(repaired_body)
        current_chars = len(current_surface)
        repaired_chars = len(repaired_surface)
        if current_chars == 0 or repaired_chars == 0:
            return False
        length_ratio = repaired_chars / max(1, current_chars)
        if length_ratio < min_length_ratio or length_ratio > max_length_ratio:
            return False

        current_tokens = {token for token in _SHADOW_TOKEN_RE.findall(current_surface)}
        repaired_tokens = {token for token in _SHADOW_TOKEN_RE.findall(repaired_surface)}
        if not current_tokens or not repaired_tokens:
            return False
        overlap_ratio = len(current_tokens & repaired_tokens) / max(1, len(current_tokens))
        if overlap_ratio < min_section_overlap_ratio:
            return False
    return True


def _local_monotony_patch_scope_enabled(
    *,
    use_patch_path: bool,
    flagged_issue_types: set[str],
) -> bool:
    return use_patch_path and bool(flagged_issue_types) and flagged_issue_types.issubset({"ending_bucket_monotony"})


def _normalize_cross_department_axis_label(value: Any) -> str:
    normalized = str(value or "").strip()
    compact = re.sub(r"[\s_\-]+", "", normalized).lower()
    if compact == "approvalflow":
        return "承認フロー"
    if compact == "ownership":
        return "責任の置き方"
    if compact == "auditability":
        return "監査のしやすさ"
    return _CROSS_DEPARTMENT_AXIS_LABELS.get(normalized, "")


def _cross_department_axis_labels(contract: Mapping[str, Any]) -> list[str]:
    labels: list[str] = []
    ui_journey = dict(contract.get("ui_journey") or {})
    for item in (
        list(contract.get("comparison_axes") or [])
        + list(ui_journey.get("comparison_axes") or [])
        + list(contract.get("must_cover") or [])
    ):
        label = _normalize_cross_department_axis_label(item)
        if label and label not in labels:
            labels.append(label)
    return labels[:3]


def _is_cross_department_governance_compare(contract: Mapping[str, Any]) -> bool:
    article_type = str(contract.get("article_type") or "").strip().lower()
    if article_type != "comparative_review":
        return False
    prompt_probe = " ".join(
        [
            str(contract.get("prompt_raw") or "").strip(),
            str(contract.get("topic") or "").strip(),
            str(contract.get("audience_profile") or "").strip(),
        ]
    )
    if "複数部門" not in prompt_probe:
        return False
    return len(_cross_department_axis_labels(contract)) >= 2


def _cross_department_closing_seed(contract: Mapping[str, Any]) -> str:
    labels = _cross_department_axis_labels(contract)
    if len(labels) >= 3:
        joined = "・".join(labels[:3])
    elif len(labels) == 2:
        joined = "と".join(labels[:2])
    else:
        return ""
    return f"結論では、{joined}を同じ順番で見比べると、部門横断運用で何を優先するかが整理しやすくなります。"


def _collect_cross_department_prompt_echo_hits(closing_body: str, contract: Mapping[str, Any]) -> list[str]:
    prompt_refs = build_prompt_echo_references(
        user_prompt=str(contract.get("prompt_raw") or contract.get("topic") or ""),
        extra=list(contract.get("must_cover") or []),
        include_must_cover=False,
    )
    prompt_echo_hits = detect_prompt_echo_sentences(
        closing_body,
        references=prompt_refs,
        max_hits=2,
    )
    for sentence in _split_japanese_sentences(closing_body):
        if not _CROSS_DEPARTMENT_PROMPT_ECHO_RE.search(sentence):
            continue
        excerpt = sentence[:140]
        if excerpt not in prompt_echo_hits:
            prompt_echo_hits.append(excerpt)
    return prompt_echo_hits[:3]


def _stabilize_cross_department_comparative_body(body: str, contract: Mapping[str, Any]) -> tuple[str, list[str]]:
    original = str(body or "").strip()
    if not original or not _is_cross_department_governance_compare(contract):
        return original, []
    closing_body = _section_body_after_heading(original, _COMPARATIVE_CLOSING_HEADING)
    if not closing_body:
        return original, []
    prompt_echo_hits = _collect_cross_department_prompt_echo_hits(closing_body, contract)
    if not prompt_echo_hits:
        return original, []
    replacement = _cross_department_closing_seed(contract)
    if not replacement:
        return original, prompt_echo_hits
    filtered_sentences = [
        sentence
        for sentence in _split_japanese_sentences(closing_body)
        if not any(str(hit or "").strip() and str(hit).strip() in sentence for hit in prompt_echo_hits)
    ]
    rebuilt_sentences = [replacement]
    for sentence in filtered_sentences:
        if sentence != replacement:
            rebuilt_sentences.append(sentence)
    rebuilt_body = " ".join(sentence for sentence in rebuilt_sentences if sentence).strip()
    if not rebuilt_body or rebuilt_body == closing_body:
        return original, prompt_echo_hits
    return _replace_section_body_after_heading(original, _COMPARATIVE_CLOSING_HEADING, rebuilt_body), prompt_echo_hits


def _maybe_stabilize_experimental_comparative_draft(
    *,
    contract: Mapping[str, Any],
    draft: DraftSections,
    diagnostics: Mapping[str, Any],
    editor_report: Mapping[str, Any],
    source_pack: Mapping[str, Any],
    compact_plan: list[Dict[str, str]],
) -> tuple[DraftSections, Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    metadata = {
        "checked": False,
        "rewritten": False,
        "hit_count": 0,
    }
    if not _is_prompt_stack_experiment_enabled(contract):
        return draft, dict(diagnostics), dict(editor_report), {}, metadata
    if str(contract.get("article_type") or "").strip().lower() != "comparative_review":
        return draft, dict(diagnostics), dict(editor_report), {}, metadata
    if not _is_cross_department_governance_compare(contract):
        return draft, dict(diagnostics), dict(editor_report), {}, metadata
    metadata["checked"] = True
    stabilized_body, prompt_echo_hits = _stabilize_cross_department_comparative_body(draft.body, contract)
    metadata["hit_count"] = len(prompt_echo_hits)
    if stabilized_body == str(draft.body or "").strip():
        return draft, dict(diagnostics), dict(editor_report), {}, metadata
    stabilized_draft = DraftSections(
        title=draft.title,
        lead=draft.lead,
        body=stabilized_body,
        hashtags=draft.hashtags,
    )
    stabilized_draft, stabilized_editor_report = _apply_editor_guard_to_draft(contract, stabilized_draft)
    stabilized_diagnostics, stabilized_controlled_realization = _refresh_diagnostics_state(
        contract,
        stabilized_draft,
        stabilized_editor_report,
        compact_plan,
        source_pack,
    )
    metadata["rewritten"] = True
    return (
        stabilized_draft,
        stabilized_diagnostics,
        stabilized_editor_report,
        dict(stabilized_controlled_realization),
        metadata,
    )


_COMPANY_INTRO_NATURALNESS_REPAIR_LINES: tuple[str, ...] = (
    "事業内容説明を先に展開し、歴史や沿革の描写よりも『今なにを、誰向けに、どう提供しているか』の具体を増やす。",
    "文末の『です／ます』を3文以上連打しない。段落ごとに短い断定・理由句（〜ため／〜ので）・体言止めを1箇所は混ぜる。",
    "同じ名詞（会社／企業名／地名／業種語／先代 など）を同段落で繰り返さず、代名詞や言い換えで受ける。",
    "1段落を1文だけで終わらせず、事実・条件・理由のどれかを1つ補って段落に厚みを作る。",
    "短い修飾節（〜という／〜を前提に／〜ことで／〜からこそ）を数箇所だけ足し、依存構造の深さを増やす。",
)


def _company_intro_naturalness_scope_active(contract: Mapping[str, Any]) -> bool:
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    return article_type == "branding" and semantic_key == "company_introduction"

def _case_study_scope_active(contract: Mapping[str, Any]) -> bool:
    return str(contract.get("article_type") or "").strip().lower() == "case_study"


def _case_study_source_sentences(source_pack: Mapping[str, Any]) -> list[str]:
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


def _case_study_strong_slot_from_text(value: Any) -> str:
    text = _clean_inline_text(value, limit=220)
    if not text:
        return ""
    if re.search(r"(?:改善前|導入前|対応前)", text):
        return "before_blocker"
    if re.search(r"(?:改善後|導入後|その結果|変化|変えた)", text):
        return "after_change"
    if re.search(r"(?:一方|ただし|残って|残り|今後|条件|必要|すべき|決める)", text):
        return "remaining_issue"
    return ""


def _case_study_slot_from_bucket(bucket: Any) -> str:
    normalized = re.sub(r"[\s_\-]+", "", str(bucket or "").strip().lower())
    aliases = {
        "beforeblocker": "before_blocker",
        "casebefore": "before_blocker",
        "改善前": "before_blocker",
        "課題": "before_blocker",
        "actionorchange": "action_or_change",
        "caseaction": "action_or_change",
        "変更": "action_or_change",
        "対応": "action_or_change",
        "processdetail": "process_detail",
        "process": "process_detail",
        "進め方": "process_detail",
        "手順": "process_detail",
        "afterchange": "after_change",
        "caseafter": "after_change",
        "変化": "after_change",
        "結果": "after_change",
        "remainingissue": "remaining_issue",
        "remaining": "remaining_issue",
        "残課題": "remaining_issue",
        "今後": "remaining_issue",
        "sourcebackedevidence": "source_backed_evidence",
        "evidence": "source_backed_evidence",
        "根拠": "source_backed_evidence",
    }
    return aliases.get(normalized, "")


def _build_case_study_runtime_source_contract(
    contract: Mapping[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    active = _case_study_scope_active(contract)
    slots: Dict[str, str] = {slot: "" for slot in _CASE_STUDY_SOURCE_SLOTS}
    if not active:
        return {
            "checked": True,
            "scope_match": False,
            "slots": slots,
            "required_slots": list(_CASE_STUDY_REQUIRED_SOURCE_SLOTS),
            "optional_slots": ["process_detail", "source_backed_evidence"],
        }

    explicit_contract = contract.get("case_study_source_contract")
    if isinstance(explicit_contract, Mapping):
        for slot in _CASE_STUDY_SOURCE_SLOTS:
            value = _clean_inline_text(explicit_contract.get(slot) or "", limit=180)
            if value:
                slots[slot] = value

    for item in list(source_pack.get("grounding_items") or []):
        if not isinstance(item, Mapping):
            continue
        slot = _case_study_slot_from_bucket(item.get("bucket"))
        value = _clean_inline_text(item.get("fact_text") or "", limit=180)
        strong_slot = _case_study_strong_slot_from_text(value)
        if strong_slot and strong_slot != slot and value:
            if not slots.get(strong_slot):
                slots[strong_slot] = value
            continue
        if slot and value and not slots.get(slot):
            slots[slot] = value

    sentences = _case_study_source_sentences(source_pack)
    for slot in _CASE_STUDY_SOURCE_SLOTS:
        if slots.get(slot):
            continue
        pattern = _CASE_STUDY_SLOT_PATTERNS.get(slot)
        if not pattern:
            continue
        for sentence in sentences:
            if pattern.search(sentence):
                slots[slot] = sentence
                break

    return {
        "checked": True,
        "scope_match": True,
        "slots": slots,
        "required_slots": list(_CASE_STUDY_REQUIRED_SOURCE_SLOTS),
        "optional_slots": ["process_detail", "source_backed_evidence"],
    }


def _merge_case_study_runtime_contract_into_payload(
    contract: Mapping[str, Any],
    case_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    updated = dict(contract)
    updated["_case_study_source_contract"] = dict(case_contract)
    if not bool(case_contract.get("scope_match")):
        return updated

    slots = dict(case_contract.get("slots") or {})
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
    for slot in _CASE_STUDY_SOURCE_SLOTS:
        value = _clean_inline_text(slots.get(slot) or "", limit=180)
        if not value:
            continue
        bucket = _CASE_STUDY_SLOT_LABELS.get(slot, slot)
        pair = (bucket, value)
        if pair in existing_pairs:
            continue
        existing_grounding.append(
            {
                "bucket": bucket,
                "fact_text": value,
                "source_title": "case study source",
                "locator": "",
            }
        )
        existing_pairs.add(pair)
    updated["source_grounding_items"] = existing_grounding[:10]

    existing_must_cover: list[str] = []
    for slot in _CASE_STUDY_REQUIRED_SOURCE_SLOTS:
        value = _clean_inline_text(slots.get(slot) or "", limit=96)
        if not value:
            continue
        label = _CASE_STUDY_SLOT_LABELS.get(slot, slot)
        item = f"{label}: {value}"
        if item not in existing_must_cover:
            existing_must_cover.append(item)
    for item in list(updated.get("must_cover") or []):
        text = _clean_inline_text(item, limit=96)
        if text and text not in existing_must_cover:
            existing_must_cover.append(text)
    if existing_must_cover:
        updated["must_cover"] = existing_must_cover[:8]

    shadow_spec_inputs = dict(updated.get("_shadow_spec_inputs") or {})
    if existing_grounding:
        source_fact_pool = [
            str(item.get("fact_text") or "").strip()
            for item in existing_grounding
            if str(item.get("fact_text") or "").strip()
        ]
        if source_fact_pool:
            shadow_spec_inputs["source_fact_pool"] = source_fact_pool[:6]
        shadow_must_cover = [
            str(item or "").strip()
            for item in list(shadow_spec_inputs.get("must_cover") or [])
            if str(item or "").strip()
        ]
        for item in existing_must_cover[:6]:
            if item and item not in shadow_must_cover:
                shadow_must_cover.append(item)
        if shadow_must_cover:
            shadow_spec_inputs["must_cover"] = shadow_must_cover[:6]
        if shadow_spec_inputs:
            updated["_shadow_spec_inputs"] = shadow_spec_inputs

    existing_hints: list[str] = []
    for item in list(updated.get("system_hint_items") or []):
        text = str(item or "").strip()
        if text and text not in existing_hints:
            existing_hints.append(text)
    contract_hints = [
        "事例本文では、改善前の詰まり、行った変更、変化、残った課題を素材にある範囲で残す。",
        "進め方や根拠が素材にある場合だけ使い、薄い素材では成果を補完しない。",
        "成果数字、改善率、顧客名、受賞、価格は素材にない限り書かない。",
    ]
    for hint in contract_hints:
        if hint not in existing_hints:
            existing_hints.append(hint)
    updated["system_hint_items"] = existing_hints[:8]
    return updated


def _prepare_case_study_runtime_contract(contract: Mapping[str, Any]) -> Dict[str, Any]:
    base_contract = dict(contract)
    initial_source_pack = build_source_pack(base_contract)
    case_contract = _build_case_study_runtime_source_contract(base_contract, initial_source_pack)
    return _merge_case_study_runtime_contract_into_payload(base_contract, case_contract)


def _branding_source_contract_scope_active(contract: Mapping[str, Any]) -> bool:
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    return article_type == "branding" and semantic_key in {"", "branding"}


def _branding_source_sentences(source_pack: Mapping[str, Any]) -> list[str]:
    source_text = _hidden_late_source_text(source_pack)
    sentences: list[str] = []
    for part in re.split(r"(?<=[。！？!?])\s*|\n+", source_text):
        text = _clean_inline_text(part, limit=220)
        if text and text not in sentences:
            sentences.append(text)
    return sentences[:24]


def _branding_subject_anchor_candidate(sentence: Any) -> str:
    text = _clean_inline_text(sentence, limit=180)
    if not text:
        return ""
    company_match = _BRANDING_COMPANY_NAME_RE.search(text)
    quoted_match = _BRANDING_QUOTED_OFFERING_RE.search(text)
    offering_match = _BRANDING_OFFERING_ANCHOR_RE.search(text)
    if company_match and (offering_match or quoted_match):
        return text[:120].rstrip("、。")
    if company_match:
        return company_match.group(0).strip()
    if offering_match:
        return offering_match.group(1).strip("、。")
    if quoted_match:
        return quoted_match.group(1).strip("、。")
    return ""


def _branding_slot_from_bucket(bucket: Any) -> str:
    normalized = re.sub(r"[\s_\-/]+", "", str(bucket or "").strip().lower())
    aliases = {
        "brandsubjectanchor": "brand_subject_anchor",
        "brandsubject": "brand_subject_anchor",
        "subjectanchor": "brand_subject_anchor",
        "subject": "brand_subject_anchor",
        "ブランド対象": "brand_subject_anchor",
        "何のブランドか": "brand_subject_anchor",
        "customertouchpoint": "customer_touchpoint",
        "touchpoint": "customer_touchpoint",
        "顧客接点": "customer_touchpoint",
        "問い合わせ前": "customer_touchpoint",
        "operatingbehavior": "operating_behavior",
        "operation": "operating_behavior",
        "運用": "operating_behavior",
        "運用行動": "operating_behavior",
        "decisionprinciple": "decision_principle",
        "principle": "decision_principle",
        "判断原則": "decision_principle",
        "判断": "decision_principle",
        "supportprocess": "support_process",
        "support": "support_process",
        "支援": "support_process",
        "支援プロセス": "support_process",
        "brandpostureinaction": "brand_posture_in_action",
        "posture": "brand_posture_in_action",
        "行動としてのブランド姿勢": "brand_posture_in_action",
        "ブランド姿勢": "brand_posture_in_action",
        "proofsignal": "proof_signal",
        "proof": "proof_signal",
        "根拠": "proof_signal",
        "根拠サイン": "proof_signal",
    }
    return aliases.get(normalized, "")


def _build_branding_runtime_source_contract(
    contract: Mapping[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    active = _branding_source_contract_scope_active(contract)
    slots: Dict[str, str] = {slot: "" for slot in _BRANDING_SOURCE_SLOTS}
    if not active:
        return {
            "checked": True,
            "scope_match": False,
            "pattern": "branding_operational_source_contract_v1",
            "slots": slots,
            "required_slots": list(_BRANDING_REQUIRED_SOURCE_SLOTS),
            "optional_slots": ["proof_signal"],
        }

    explicit_contract = contract.get("branding_source_contract")
    candidate_contract = contract.get("branding_validation_candidate")
    if not isinstance(explicit_contract, Mapping) and isinstance(candidate_contract, Mapping):
        explicit_contract = candidate_contract.get("source_contract")
    if isinstance(explicit_contract, Mapping):
        for slot in _BRANDING_SOURCE_SLOTS:
            value = _clean_inline_text(explicit_contract.get(slot) or "", limit=180)
            if value:
                slots[slot] = value

    for item in list(source_pack.get("grounding_items") or []):
        if not isinstance(item, Mapping):
            continue
        slot = _branding_slot_from_bucket(item.get("bucket"))
        value = _clean_inline_text(item.get("fact_text") or "", limit=180)
        if slot and value and not slots.get(slot):
            slots[slot] = value

    sentences = _branding_source_sentences(source_pack)
    if not slots.get(_BRANDING_SUBJECT_ANCHOR_SLOT):
        for sentence in sentences:
            candidate = _branding_subject_anchor_candidate(sentence)
            if candidate:
                slots[_BRANDING_SUBJECT_ANCHOR_SLOT] = candidate
                break
    for slot in _BRANDING_SOURCE_SLOTS:
        if slot == _BRANDING_SUBJECT_ANCHOR_SLOT:
            continue
        if slots.get(slot):
            continue
        pattern = _BRANDING_SLOT_PATTERNS.get(slot)
        if not pattern:
            continue
        for sentence in sentences:
            if pattern.search(sentence):
                slots[slot] = sentence
                break

    return {
        "checked": True,
        "scope_match": True,
        "pattern": "branding_operational_source_contract_v1",
        "slots": slots,
        "required_slots": list(_BRANDING_REQUIRED_SOURCE_SLOTS),
        "optional_slots": ["proof_signal"],
    }


def _merge_branding_runtime_contract_into_payload(
    contract: Mapping[str, Any],
    branding_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    updated = dict(contract)
    updated["_branding_source_contract"] = dict(branding_contract)
    if not bool(branding_contract.get("scope_match")):
        return updated

    slots = dict(branding_contract.get("slots") or {})
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
    for slot in _BRANDING_SOURCE_SLOTS:
        value = _clean_inline_text(slots.get(slot) or "", limit=180)
        if not value:
            continue
        bucket = _BRANDING_SLOT_LABELS.get(slot, slot)
        pair = (bucket, value)
        if pair in existing_pairs:
            continue
        existing_grounding.append(
            {
                "bucket": bucket,
                "fact_text": value,
                "source_title": "branding source",
                "locator": "",
            }
        )
        existing_pairs.add(pair)
    updated["source_grounding_items"] = existing_grounding[:10]

    existing_hints: list[str] = []
    for item in list(updated.get("system_hint_items") or []):
        text = str(item or "").strip()
        if text and text not in existing_hints:
            existing_hints.append(text)
    contract_hints = [
        "ブランド対象をタイトルまたはリードで明示し、誰の何のブランドかを冒頭で迷わせない。",
        "ブランド記事では、顧客接点を前半に置き、問い合わせ前の迷いから始める。",
        "運用順と支援範囲で具体化し、判断原則を本文中盤までに置く。",
        "素材外の成果、顧客名、受賞、価格、提携先は足さない。",
    ]
    for hint in contract_hints:
        if hint not in existing_hints:
            existing_hints.append(hint)
    updated["system_hint_items"] = existing_hints[:8]
    return updated


def _prepare_branding_runtime_contract(contract: Mapping[str, Any]) -> Dict[str, Any]:
    base_contract = dict(contract)
    initial_source_pack = build_source_pack(base_contract)
    branding_contract = _build_branding_runtime_source_contract(base_contract, initial_source_pack)
    return _merge_branding_runtime_contract_into_payload(base_contract, branding_contract)


def _branding_subject_anchor_source_insufficient(contract: Mapping[str, Any]) -> bool:
    if not _branding_source_contract_scope_active(contract):
        return False
    branding_contract = dict(contract.get("_branding_source_contract") or {})
    slots = dict(branding_contract.get("slots") or {})
    return not bool(_clean_inline_text(slots.get(_BRANDING_SUBJECT_ANCHOR_SLOT) or "", limit=120))


def _branding_subject_anchor_needs_input_items() -> list[Dict[str, Any]]:
    return [
        {
            "field": "brand_subject_anchor",
            "reason": "generic_branding_requires_subject_anchor",
            "message": "会社名、サービス名、商品名、または何を扱うブランドか分かる対象表現がsourceに必要です。",
        }
    ]




_EXPLANATORY_SOURCE_USE_BUCKETS: tuple[str, ...] = (
    "説明対象",
    "つまずき",
    "具体例",
    "文体注意",
    "言語注意",
    "補助",
)
_EXPLANATORY_FINGERPRINT_REPAIR_FLAGS = {
    "bigram_mono_low",
    "vocab_repetition",
    "syntactic_complexity_low",
    "ending_repetition",
    "comma_overuse",
}
_EXPLANATORY_FINGERPRINT_ISSUE_TYPE = "explanatory_fingerprint_flatness"
_COMPANY_INTRO_FINGERPRINT_REPAIR_FLAGS = {
    "paragraph_length_cv_flat",
    "bigram_mono_low",
    "vocab_repetition",
    "nominalization_rate_high",
    "syntactic_complexity_low",
    "ending_repetition",
    "comma_overuse",
}
_COMPANY_INTRO_SOURCE_REFLECTION_REPAIR_FLAG = "source_grounding_weak_reflection"
_COMPANY_INTRO_FINGERPRINT_ISSUE_TYPE = "company_intro_fingerprint_flatness"
_EXPLANATORY_OUTLINE_MUST_COVER_RE = re.compile(
    r"(?:エグゼクティブサマリー|背景と問題の所在|目的と構成|^#+|^\**\s*\d+(?:[.．]\d+)*\s*)"
)


def _explanatory_outline_must_cover_item(value: Any) -> bool:
    text = _clean_inline_text(value, limit=96).strip("*# 　")
    if not text:
        return False
    return bool(_EXPLANATORY_OUTLINE_MUST_COVER_RE.search(text))


def _explanatory_must_cover_from_source_use(value: Any) -> str:
    text = _clean_inline_text(value, limit=180).strip(" 　-・、。")
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"^(?:本報告書|報告書)は、", "", text)
    text = re.sub(r"^これは、", "", text)
    if "AI生成テキスト" in text and "AIっぽ" in text:
        return "AI生成テキストがなぜ「AIっぽい」と感じられるのか"
    if "ユニークな単語" in text and "Volume" in text:
        return "ユニークな単語、Volume、同義語の切り替え"
    if "堆積した文体" in text:
        return "堆積した文体（Sedimented Style）"
    if "日本語" in text and ("文末" in text or "です・ます" in text):
        return "日本語の文末反復やMarkdown風の見え方"
    if "認知" in text and ("制約" in text or "負荷" in text):
        return "認知負荷やワーキングメモリ制約とのずれ"
    clipped = text[:72].rstrip(" 　、")
    last_punctuation = max(clipped.rfind("。"), clipped.rfind("、"))
    if last_punctuation >= 28:
        clipped = clipped[:last_punctuation]
    return clipped.strip(" 　、。")


def _prepare_explanatory_runtime_contract(contract: Mapping[str, Any]) -> Dict[str, Any]:
    updated = dict(contract)
    article_type = str(updated.get("article_type") or "").strip().lower()
    if article_type != "explanatory_article":
        return updated
    source_pack = build_source_pack(updated)
    source_use_digest = build_explanatory_source_use_digest(updated, source_pack)
    if not source_use_digest:
        return updated

    source_documents = [item for item in list(updated.get("source_documents") or []) if isinstance(item, Mapping)]
    primary_document = dict(source_documents[0]) if source_documents else {}
    source_title = _clean_inline_text(primary_document.get("title") or "", limit=100)
    locator = _clean_inline_text(primary_document.get("locator") or "", limit=180)
    grounding_items: list[Dict[str, str]] = []
    seen_grounding_texts: set[str] = set()
    for index, fact_text in enumerate(source_use_digest[:5]):
        text = _explanatory_must_cover_from_source_use(fact_text) or _clean_inline_text(
            fact_text, limit=180
        ).strip(" 　-・、。")
        if not text or text in seen_grounding_texts:
            continue
        seen_grounding_texts.add(text)
        grounding_items.append(
            {
                "bucket": _EXPLANATORY_SOURCE_USE_BUCKETS[min(index, len(_EXPLANATORY_SOURCE_USE_BUCKETS) - 1)],
                "fact_text": text,
                "source_title": source_title,
                "locator": locator,
            }
        )
    if grounding_items:
        updated["source_grounding_items"] = grounding_items

    must_cover_items = [
        _clean_inline_text(item, limit=96)
        for item in list(updated.get("must_cover") or [])
        if _clean_inline_text(item, limit=96)
    ]
    if not must_cover_items or all(_explanatory_outline_must_cover_item(item) for item in must_cover_items):
        updated["must_cover"] = [
            item
            for item in (
                _explanatory_must_cover_from_source_use(grounding_item.get("fact_text") or "")
                for grounding_item in grounding_items[:4]
            )
            if item
        ][:4]
    return updated


def _prepare_runtime_source_contracts(contract: Mapping[str, Any]) -> Dict[str, Any]:
    prepared = _prepare_announcement_runtime_contract(contract)
    prepared = _prepare_case_study_runtime_contract(prepared)
    prepared = _prepare_branding_runtime_contract(prepared)
    prepared = _prepare_company_intro_runtime_contract(prepared)
    prepared = _prepare_explanatory_runtime_contract(prepared)
    prepared = _prepare_comparative_runtime_contract(prepared)
    return enrich_persona_trial_contract(prepared)


def _branding_text_for_validation(draft: DraftSections) -> str:
    return "\n".join(str(part or "") for part in (draft.title, draft.lead, draft.body)).strip()


def _branding_slot_value_reflected(text: str, value: Any) -> bool:
    source_tokens = _extract_shadow_tokens(value, limit=6)
    if not source_tokens:
        return False
    normalized_text = _clean_inline_text(text, limit=2400).lower()
    hit_count = sum(1 for token in source_tokens if token in normalized_text)
    return hit_count >= max(1, min(2, len(source_tokens)))


def _branding_compact_anchor_text(value: Any) -> str:
    return re.sub(r"[\s、。，．・/／「」『』（）()\[\]【】]+", "", str(value or "").lower())


def _branding_subject_anchor_detail_terms(value: Any) -> list[str]:
    text = _clean_inline_text(value, limit=180)
    terms: list[str] = []
    for pattern in (
        _BRANDING_QUOTED_OFFERING_RE,
        _BRANDING_OFFERING_ANCHOR_RE,
        _BRANDING_SUBJECT_ANCHOR_DETAIL_RE,
        _BRANDING_SUBJECT_ANCHOR_DOMAIN_RE,
    ):
        for match in pattern.finditer(text):
            term = match.group(1) if match.lastindex else match.group(0)
            term = _clean_inline_text(term, limit=80).strip("、。のを")
            compact = _branding_compact_anchor_text(term)
            if len(compact) < 4 or compact in {"サービス", "ブランド", "支援", "サポート"}:
                continue
            if term and term not in terms:
                terms.append(term)
            if len(terms) >= 6:
                return terms
    return terms


def _branding_subject_anchor_reflected(text: str, source_value: Any) -> bool:
    front = _branding_compact_anchor_text(_clean_inline_text(text, limit=900))
    source = _clean_inline_text(source_value, limit=180)
    if not front or not source:
        return False

    company_names = [
        match.group(0).strip()
        for match in _BRANDING_COMPANY_NAME_RE.finditer(source)
        if match.group(0).strip()
    ]
    detail_terms = _branding_subject_anchor_detail_terms(source)
    company_hit = any(_branding_compact_anchor_text(name) in front for name in company_names)
    detail_hit = any(_branding_compact_anchor_text(term) in front for term in detail_terms)

    if company_names and detail_terms:
        return company_hit and detail_hit
    if company_names:
        return company_hit
    return detail_hit


def _branding_slot_present(slot: str, text: str, source_value: Any) -> bool:
    if slot == _BRANDING_SUBJECT_ANCHOR_SLOT:
        return _branding_subject_anchor_reflected(text, source_value)
    if _branding_slot_value_reflected(text, source_value):
        return True
    pattern = _BRANDING_SLOT_PATTERNS.get(slot)
    return bool(pattern and pattern.search(text))


def _branding_front_text_for_subject_anchor(draft: DraftSections) -> str:
    parts = [str(draft.title or ""), str(draft.lead or "")]
    sections = _split_body_sections(draft.body)
    if sections:
        first_section = sections[0]
        heading = str(first_section.get("heading") or "").strip()
        body = str(first_section.get("body") or "").strip()
        if heading:
            parts.append(f"## {heading}")
        if body:
            parts.append(body)
    else:
        parts.append(str(draft.body or "")[:420])
    return "\n".join(part for part in parts if part).strip()[:900]


def _branding_unsupported_claim_hits(text: str, source_text: str) -> list[str]:
    source_tokens = {
        _normalize_announcement_claim_token(match.group(0))
        for match in _BRANDING_UNSUPPORTED_CLAIM_RE.finditer(source_text)
    }
    hits: list[str] = []
    for match in _BRANDING_UNSUPPORTED_CLAIM_RE.finditer(text):
        raw = match.group(0)
        normalized = _normalize_announcement_claim_token(raw)
        if normalized and normalized not in source_tokens and raw not in hits:
            hits.append(raw)
    return hits[:8]


def _branding_customer_touchpoint_buried(
    text: str,
    slot_presence: Mapping[str, bool],
    slots: Mapping[str, Any],
) -> bool:
    if not bool(slot_presence.get("customer_touchpoint")):
        return False
    front_text = _clean_inline_text(text, limit=720)
    return not _branding_slot_present("customer_touchpoint", front_text, slots.get("customer_touchpoint"))


def _branding_wrong_article_type_drift(text: str) -> bool:
    return bool(
        re.search(r"(?:お知らせ|開始します|申込|申し込み|リリース|ご案内|開催します)", text)
        or re.search(r"(?:会社紹介|当社は[^。]{0,40}(?:会社|企業)です|沿革|創業|事業内容|提供価値)", text)
        or re.search(r"(?:改善前|残った課題|事例です|その結果)", text)
    )


def _branding_advertising_copy_drift(text: str) -> bool:
    return bool(
        re.search(
            r"(?:ぜひ|お気軽に|お問い合わせください|今すぐ|選ばれています|No\.?1|唯一|最高|圧倒的|無料相談|キャンペーン)",
            text,
            flags=re.IGNORECASE,
        )
    )


def _branding_abstract_value_only(text: str, slot_presence: Mapping[str, bool]) -> bool:
    front_text = _clean_inline_text(text, limit=820)
    abstract_front = bool(re.search(r"(?:理念|価値観|想い|信頼|安心|大切|重要|寄り添)", front_text))
    concrete_front = bool(
        _BRANDING_SLOT_PATTERNS["customer_touchpoint"].search(front_text)
        and (_BRANDING_SLOT_PATTERNS["operating_behavior"].search(front_text) or _BRANDING_SLOT_PATTERNS["support_process"].search(front_text))
    )
    return bool(abstract_front and not concrete_front) or bool(
        not bool(slot_presence.get("operating_behavior")) and not bool(slot_presence.get("support_process"))
    )


def _branding_philosophy_only_drift(text: str, slot_presence: Mapping[str, bool]) -> bool:
    philosophy_terms = bool(re.search(r"(?:理念|哲学|価値観|想い|使命|ビジョン)", text))
    operational_slots = sum(
        1
        for slot in ("customer_touchpoint", "operating_behavior", "support_process", "brand_posture_in_action")
        if bool(slot_presence.get(slot))
    )
    return bool(philosophy_terms and operational_slots < 3)


def _branding_source_contract_failure_count(validation: Mapping[str, Any]) -> int:
    return (
        len(list(validation.get("missing_required_slots") or []))
        + len(list(validation.get("unsupported_claim_hits") or []))
        + (1 if bool(validation.get("wrong_article_type_drift")) else 0)
        + (1 if bool(validation.get("customer_touchpoint_buried")) else 0)
        + (1 if bool(validation.get("philosophy_only_drift")) else 0)
        + (1 if bool(validation.get("advertising_copy_drift")) else 0)
        + (1 if bool(validation.get("abstract_value_only")) else 0)
    )


def _branding_source_contract_improved(
    current: Mapping[str, Any],
    repaired: Mapping[str, Any],
) -> bool:
    if not bool(current.get("scope_match")):
        return True
    if bool(repaired.get("unsupported_claim_added")):
        return False
    return _branding_source_contract_failure_count(repaired) < _branding_source_contract_failure_count(current)


def _branding_subject_anchor_final_unresolved(validation: Mapping[str, Any]) -> bool:
    return bool(
        validation.get("scope_match")
        and validation.get("brand_subject_anchor_source_available")
        and not validation.get("brand_subject_anchor_fronted")
    )


def _evaluate_branding_source_contract_validation(
    contract: Mapping[str, Any],
    draft: DraftSections,
    diagnostics: Dict[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    branding_contract = dict(contract.get("_branding_source_contract") or {})
    if not branding_contract:
        branding_contract = _build_branding_runtime_source_contract(contract, source_pack)
    slots = dict(branding_contract.get("slots") or {})
    if not _branding_source_contract_scope_active(contract):
        return {
            "checked": True,
            "scope_match": False,
            "pattern": "branding_operational_source_contract_v1",
            "required_slots": list(_BRANDING_REQUIRED_SOURCE_SLOTS),
            "optional_slots": ["proof_signal"],
            "slot_presence": {slot: False for slot in _BRANDING_SOURCE_SLOTS},
            "brand_subject_anchor_source_available": False,
            "brand_subject_anchor_fronted": False,
            "missing_required_slots": [],
            "customer_touchpoint_buried": False,
            "philosophy_only_drift": False,
            "advertising_copy_drift": False,
            "abstract_value_only": False,
            "wrong_article_type_drift": False,
            "unsupported_claim_added": False,
            "unsupported_claim_hits": [],
            "visible_leakage_hits": [],
            "repair_trigger_ids": [],
        }

    text = _branding_text_for_validation(draft)
    front_text = _branding_front_text_for_subject_anchor(draft)
    source_text = _hidden_late_source_text(source_pack)
    slot_presence: Dict[str, bool] = {}
    for slot in _BRANDING_SOURCE_SLOTS:
        target_text = front_text if slot == _BRANDING_SUBJECT_ANCHOR_SLOT else text
        slot_presence[slot] = _branding_slot_present(slot, target_text, slots.get(slot))
    brand_subject_anchor_source_available = bool(
        _clean_inline_text(slots.get(_BRANDING_SUBJECT_ANCHOR_SLOT) or "", limit=120)
    )
    brand_subject_anchor_fronted = bool(slot_presence.get(_BRANDING_SUBJECT_ANCHOR_SLOT))

    missing_required = [
        slot
        for slot in _BRANDING_REQUIRED_SOURCE_SLOTS
        if not bool(slot_presence.get(slot))
    ]
    unsupported_claim_hits = _branding_unsupported_claim_hits(text, source_text)
    visible_leakage_hits = []
    for match in _BRANDING_VISIBLE_EXPERIMENT_TERM_RE.finditer(text):
        hit = match.group(0)
        if hit and hit not in visible_leakage_hits:
            visible_leakage_hits.append(hit)

    customer_touchpoint_buried = _branding_customer_touchpoint_buried(text, slot_presence, slots)
    philosophy_only_drift = _branding_philosophy_only_drift(text, slot_presence)
    advertising_copy_drift = _branding_advertising_copy_drift(text)
    abstract_value_only = _branding_abstract_value_only(text, slot_presence)
    wrong_type_drift = _branding_wrong_article_type_drift(text)

    trigger_ids: list[str] = []
    for slot in missing_required:
        trigger_ids.append(f"missing_required_slot:{slot}")
    if unsupported_claim_hits:
        trigger_ids.append("unsupported_claim_added")
    if wrong_type_drift:
        trigger_ids.append("wrong_article_type_drift")
    if philosophy_only_drift:
        trigger_ids.append("philosophy_only")
    if advertising_copy_drift:
        trigger_ids.append("advertising_copy")
    if abstract_value_only:
        trigger_ids.append("abstract_value_only")
    if customer_touchpoint_buried:
        trigger_ids.append("customer_touchpoint_buried")
    if brand_subject_anchor_source_available and not brand_subject_anchor_fronted:
        trigger_ids.append("brand_subject_anchor_not_fronted")

    validation = {
        "checked": True,
        "scope_match": _branding_source_contract_scope_active(contract),
        "pattern": "branding_operational_source_contract_v1",
        "required_slots": list(_BRANDING_REQUIRED_SOURCE_SLOTS),
        "optional_slots": ["proof_signal"],
        "slot_presence": slot_presence,
        "brand_subject_anchor_source_available": bool(brand_subject_anchor_source_available),
        "brand_subject_anchor_fronted": bool(brand_subject_anchor_fronted),
        "missing_required_slots": missing_required,
        "customer_touchpoint_buried": bool(customer_touchpoint_buried),
        "philosophy_only_drift": bool(philosophy_only_drift),
        "advertising_copy_drift": bool(advertising_copy_drift),
        "abstract_value_only": bool(abstract_value_only),
        "wrong_article_type_drift": bool(wrong_type_drift),
        "unsupported_claim_added": bool(unsupported_claim_hits),
        "unsupported_claim_hits": unsupported_claim_hits,
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
        "ブランド対象（誰の何のブランドか）をタイトル、リード、最初の見出しのいずれかに置く。",
        "ブランド本文を、顧客接点、運用行動、支援プロセス、判断原則、行動としてのブランド姿勢へ戻す。",
        "顧客接点を前半に置き、理念だけ・広告コピーだけ・抽象価値だけの結びにしない。",
        "素材にない成果、顧客名、受賞、価格、提携先は足さない。",
    ):
        if line not in repair_instructions:
            repair_instructions.append(line)
    diagnostics["repair_instructions"] = repair_instructions[:12]

    soft_warnings: list[str] = []
    for item in list(diagnostics.get("soft_warnings") or []):
        text_item = str(item or "").strip()
        if text_item and text_item not in soft_warnings:
            soft_warnings.append(text_item)
    if "branding:source_contract" not in soft_warnings:
        soft_warnings.append("branding:source_contract")
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


def _case_study_text_for_validation(draft: DraftSections) -> str:
    return "\n".join(str(part or "") for part in (draft.title, draft.lead, draft.body)).strip()


def _case_study_slot_value_reflected(text: str, value: Any) -> bool:
    source_tokens = _extract_shadow_tokens(value, limit=6)
    if not source_tokens:
        return False
    normalized_text = _clean_inline_text(text, limit=2400).lower()
    hit_count = sum(1 for token in source_tokens if token in normalized_text)
    return hit_count >= max(1, min(2, len(source_tokens)))


def _case_study_slot_present(slot: str, text: str, source_value: Any) -> bool:
    if _case_study_slot_value_reflected(text, source_value):
        return True
    pattern = _CASE_STUDY_SLOT_PATTERNS.get(slot)
    return bool(pattern and pattern.search(text))


def _normalize_case_study_metric_token(value: Any) -> str:
    text = str(value or "").translate(str.maketrans("０１２３４５６７８９％．，", "0123456789%.,"))
    return re.sub(r"\s+", "", text)


def _case_study_unsupported_metric_hits(text: str, source_text: str) -> list[str]:
    source_tokens = {
        _normalize_case_study_metric_token(match.group(0))
        for match in _CASE_STUDY_NUMERIC_METRIC_RE.finditer(source_text)
    }
    hits: list[str] = []
    for match in _CASE_STUDY_NUMERIC_METRIC_RE.finditer(text):
        raw = match.group(0)
        normalized = _normalize_case_study_metric_token(raw)
        if normalized and normalized not in source_tokens and raw not in hits:
            hits.append(raw)
    return hits[:6]


def _case_study_unsupported_customer_or_award_hits(text: str, source_text: str) -> list[str]:
    hits: list[str] = []
    for match in _CASE_STUDY_CUSTOMER_AWARD_RE.finditer(text):
        raw = match.group(0)
        if raw and raw not in source_text and raw not in hits:
            hits.append(raw)
    return hits[:6]


def _case_study_wrong_article_type_drift(text: str, missing_required_slots: Sequence[str]) -> bool:
    if re.search(r"(?:お知らせ|開催します|申込|申し込み|リリース|ご案内|キャンペーン)", text):
        return True
    if re.search(r"(?:会社紹介|サービス紹介|当社は[^。]{0,40}(?:会社|企業)です)", text):
        return True
    success_only = bool(re.search(r"(?:成功しました|大きな成果|解決しました|効果が出ました)", text))
    return bool(success_only and "remaining_issue" in set(missing_required_slots))


def _case_study_generic_advice_drift(text: str) -> bool:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", str(text or "").strip()) if part.strip()]
    final = paragraphs[-1] if paragraphs else str(text or "")[-260:]
    return bool(
        re.search(
            r"(?:同じような.{0,20}なら|まずは.{0,30}(?:確認|見直し)|してみるとよい|ことが重要です|ことが大切です)",
            final,
        )
    )


def _case_study_source_contract_failure_count(validation: Mapping[str, Any]) -> int:
    return (
        len(list(validation.get("missing_required_slots") or []))
        + len(list(validation.get("unsupported_metric_hits") or []))
        + len(list(validation.get("unsupported_customer_or_award_hits") or []))
        + (1 if bool(validation.get("wrong_article_type_drift")) else 0)
    )


def _case_study_source_contract_improved(
    current: Mapping[str, Any],
    repaired: Mapping[str, Any],
) -> bool:
    if not bool(current.get("scope_match")):
        return True
    if bool(repaired.get("unsupported_metric_added")) or bool(repaired.get("unsupported_customer_or_award_added")):
        return False
    return _case_study_source_contract_failure_count(repaired) < _case_study_source_contract_failure_count(current)


def _evaluate_case_study_source_contract_validation(
    contract: Mapping[str, Any],
    draft: DraftSections,
    diagnostics: Dict[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    case_contract = dict(contract.get("_case_study_source_contract") or {})
    if not case_contract:
        case_contract = _build_case_study_runtime_source_contract(contract, source_pack)
    slots = dict(case_contract.get("slots") or {})
    if not _case_study_scope_active(contract):
        return {
            "checked": True,
            "scope_match": False,
            "required_slots": list(_CASE_STUDY_REQUIRED_SOURCE_SLOTS),
            "optional_slots": ["process_detail", "source_backed_evidence"],
            "slot_presence": {slot: False for slot in _CASE_STUDY_SOURCE_SLOTS},
            "missing_required_slots": [],
            "unsupported_metric_added": False,
            "unsupported_metric_hits": [],
            "unsupported_customer_or_award_added": False,
            "unsupported_customer_or_award_hits": [],
            "success_story_only_drift": False,
            "generic_advice_drift": False,
            "wrong_article_type_drift": False,
            "visible_leakage_hits": [],
            "repair_trigger_ids": [],
        }
    text = _case_study_text_for_validation(draft)
    source_text = _hidden_late_source_text(source_pack)

    slot_presence: Dict[str, bool] = {}
    for slot in _CASE_STUDY_SOURCE_SLOTS:
        slot_presence[slot] = _case_study_slot_present(slot, text, slots.get(slot))

    missing_required = [
        slot
        for slot in _CASE_STUDY_REQUIRED_SOURCE_SLOTS
        if not bool(slot_presence.get(slot))
    ]
    unsupported_metric_hits = _case_study_unsupported_metric_hits(text, source_text)
    unsupported_customer_or_award_hits = _case_study_unsupported_customer_or_award_hits(text, source_text)
    visible_leakage_hits = []
    for match in _CASE_STUDY_VISIBLE_EXPERIMENT_TERM_RE.finditer(text):
        hit = match.group(0)
        if hit and hit not in visible_leakage_hits:
            visible_leakage_hits.append(hit)
    wrong_type_drift = _case_study_wrong_article_type_drift(text, missing_required)
    generic_advice_drift = _case_study_generic_advice_drift(text)
    success_story_only_drift = bool(
        "remaining_issue" in missing_required
        and re.search(r"(?:成功しました|成果が出ました|解決しました)", text)
    )

    trigger_ids: list[str] = []
    for slot in missing_required:
        trigger_ids.append(f"missing_required_slot:{slot}")
    if unsupported_metric_hits:
        trigger_ids.append("unsupported_metric_added")
    if unsupported_customer_or_award_hits:
        trigger_ids.append("unsupported_customer_or_award_added")
    if wrong_type_drift:
        trigger_ids.append("wrong_article_type_drift")

    validation = {
        "checked": True,
        "scope_match": _case_study_scope_active(contract),
        "required_slots": list(_CASE_STUDY_REQUIRED_SOURCE_SLOTS),
        "optional_slots": ["process_detail", "source_backed_evidence"],
        "slot_presence": slot_presence,
        "missing_required_slots": missing_required,
        "unsupported_metric_added": bool(unsupported_metric_hits),
        "unsupported_metric_hits": unsupported_metric_hits,
        "unsupported_customer_or_award_added": bool(unsupported_customer_or_award_hits),
        "unsupported_customer_or_award_hits": unsupported_customer_or_award_hits,
        "success_story_only_drift": bool(success_story_only_drift),
        "generic_advice_drift": bool(generic_advice_drift),
        "wrong_article_type_drift": bool(wrong_type_drift),
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
        "事例本文を、改善前の詰まり、行った変更、変化、残った課題へ戻す。素材にない成果数字や固有名詞は足さない。",
        "残課題を消して成功談だけで閉じず、素材にある範囲で次に残る運用上の課題を短く置く。",
    ):
        if line not in repair_instructions:
            repair_instructions.append(line)
    diagnostics["repair_instructions"] = repair_instructions[:12]

    soft_warnings: list[str] = []
    for item in list(diagnostics.get("soft_warnings") or []):
        text_item = str(item or "").strip()
        if text_item and text_item not in soft_warnings:
            soft_warnings.append(text_item)
    if "case_study:source_contract" not in soft_warnings:
        soft_warnings.append("case_study:source_contract")
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


def _company_intro_polite_bucket_ratio(diagnostics: Mapping[str, Any]) -> float:
    counts = dict(diagnostics.get("ending_bucket_counts") or {})
    total = sum(int(v or 0) for v in counts.values())
    if total <= 0:
        return 0.0
    return round(int(counts.get("polite", 0) or 0) / total, 4)


def _company_intro_naturalness_signals(diagnostics: Mapping[str, Any]) -> Dict[str, Any]:
    body_chars = int(diagnostics.get("body_chars", 0) or 0)
    target = int(diagnostics.get("target_chars", 0) or 0)
    polite_ratio = _company_intro_polite_bucket_ratio(diagnostics)
    monotony_score = float(diagnostics.get("ending_bucket_monotony_score", 0.0) or 0.0)
    max_run = int(diagnostics.get("ending_bucket_max_run", 0) or 0)
    single_sentence_ratio = float(diagnostics.get("single_sentence_paragraph_ratio", 0.0) or 0.0)
    paragraph_count = int(diagnostics.get("paragraph_count_for_ratio", 0) or 0)
    low_info_ratio = float(diagnostics.get("proposition_low_info_ratio", 0.0) or 0.0)
    informative_ratio = float(diagnostics.get("proposition_informative_ratio", 1.0) or 1.0)
    signals: Dict[str, Any] = {
        "polite_ratio": polite_ratio,
        "ending_bucket_monotony_score": round(monotony_score, 4),
        "ending_bucket_max_run": max_run,
        "single_sentence_paragraph_ratio": round(single_sentence_ratio, 4),
        "paragraph_count_for_ratio": paragraph_count,
        "body_chars": body_chars,
        "target_chars": target,
        "proposition_low_info_ratio": round(low_info_ratio, 4),
        "proposition_informative_ratio": round(informative_ratio, 4),
        "polite_heavy": polite_ratio >= 0.70,
        "ending_monotony_high": monotony_score >= 0.40 or max_run >= 8,
        "body_short": target > 0 and body_chars < int(target * 0.78),
        "fragmented_paragraphs": single_sentence_ratio >= 0.45 and paragraph_count >= 5,
        "low_info_present": low_info_ratio >= 0.02 or informative_ratio < 0.9,
    }
    signals["active_signal_count"] = sum(
        1
        for key in (
            "polite_heavy",
            "ending_monotony_high",
            "body_short",
            "fragmented_paragraphs",
            "low_info_present",
        )
        if bool(signals.get(key))
    )
    return signals


def _apply_company_intro_naturalness_enrichment(
    contract: Mapping[str, Any],
    diagnostics: Dict[str, Any],
) -> Dict[str, Any]:
    enrichment: Dict[str, Any] = {
        "scope_match": False,
        "activated": False,
        "signals": {},
        "signal_count": 0,
        "instructions_added": 0,
        "soft_warning_added": False,
    }
    if not _company_intro_naturalness_scope_active(contract):
        diagnostics["company_intro_naturalness_enrichment"] = enrichment
        return diagnostics
    enrichment["scope_match"] = True
    signals = _company_intro_naturalness_signals(diagnostics)
    enrichment["signals"] = signals
    enrichment["signal_count"] = int(signals.get("active_signal_count") or 0)
    if enrichment["signal_count"] < 2:
        diagnostics["company_intro_naturalness_enrichment"] = enrichment
        return diagnostics

    existing_instructions: list[str] = []
    for item in list(diagnostics.get("repair_instructions") or []):
        text = str(item or "").strip()
        if text and text not in existing_instructions:
            existing_instructions.append(text)
    added = 0
    for line in _COMPANY_INTRO_NATURALNESS_REPAIR_LINES:
        if line and line not in existing_instructions:
            existing_instructions.append(line)
            added += 1
    diagnostics["repair_instructions"] = existing_instructions[:16]
    enrichment["instructions_added"] = added

    soft_warnings: list[str] = []
    for item in list(diagnostics.get("soft_warnings") or []):
        text = str(item or "").strip()
        if text and text not in soft_warnings:
            soft_warnings.append(text)
    if "company_intro:naturalness_rescue" not in soft_warnings:
        soft_warnings.append("company_intro:naturalness_rescue")
        enrichment["soft_warning_added"] = True
    diagnostics["soft_warnings"] = soft_warnings[:14]

    diagnostics["repair_trigger_score"] = max(
        float(diagnostics.get("repair_trigger_score") or 0.0), 0.62
    )
    diagnostics["repair_required"] = True
    enrichment["activated"] = True
    diagnostics["company_intro_naturalness_enrichment"] = enrichment
    return diagnostics


def _materialized_late_half_issue_type(warning: str) -> str:
    if warning in {"later_recall_not_visible_in_late_half", "late_half_empty"}:
        return "late_half_source_return"
    if warning == "generic_closing_phrase":
        return "late_half_closing_specificity"
    if warning == "late_half_sentence_ending_repetition":
        return "late_half_surface_rhythm"
    if warning == "ending_bucket_monotony":
        return "ending_bucket_monotony"
    return "late_half_source_return"


def _materialized_anchor_patch_final_guard_ending_monotony(diagnostics: Mapping[str, Any]) -> bool:
    if int(diagnostics.get("ending_bucket_max_run", 0) or 0) >= 3:
        return True
    soft_warnings = {
        str(item or "").strip()
        for item in list(diagnostics.get("soft_warnings") or [])
        if str(item or "").strip()
    }
    if soft_warnings.intersection({"ending:bucket_monotony", "ai:ending_monotony"}):
        return True
    return any(
        isinstance(item, Mapping)
        and str(item.get("issue_type") or "").strip() == "ending_bucket_monotony"
        for item in list(diagnostics.get("flagged_spans") or [])
    )


def _materialized_late_half_target_headings(draft: DraftSections) -> list[str]:
    sections = _extract_revision_sections(draft.body)
    if not sections:
        return []
    split_at = max(0, len(sections) // 2)
    headings = [heading for heading, body in sections[split_at:] if heading and str(body or "").strip()]
    return headings[:3] or [sections[-1][0]]


def _apply_materialized_late_half_audit_repair_signal(
    contract: Mapping[str, Any],
    draft: DraftSections,
    diagnostics: Dict[str, Any],
    audit: Mapping[str, Any],
) -> Dict[str, Any]:
    return dict(diagnostics)


def _repair_improves_company_intro_naturalness(
    current: Mapping[str, Any],
    repaired: Mapping[str, Any],
) -> bool:
    current_body = int(current.get("body_chars", 0) or 0)
    repaired_body = int(repaired.get("body_chars", 0) or 0)
    if current_body > 0 and repaired_body < int(current_body * 0.9):
        return False
    current_polite = _company_intro_polite_bucket_ratio(current)
    repaired_polite = _company_intro_polite_bucket_ratio(repaired)
    polite_dropped = current_polite >= 0.60 and repaired_polite <= current_polite - 0.06
    current_monotony = float(current.get("ending_bucket_monotony_score", 0.0) or 0.0)
    repaired_monotony = float(repaired.get("ending_bucket_monotony_score", 0.0) or 0.0)
    monotony_dropped = repaired_monotony + 0.05 <= current_monotony
    body_expanded = current_body > 0 and repaired_body >= current_body + 120
    current_single = float(current.get("single_sentence_paragraph_ratio", 0.0) or 0.0)
    repaired_single = float(repaired.get("single_sentence_paragraph_ratio", 0.0) or 0.0)
    fragmentation_reduced = current_single >= 0.40 and repaired_single + 0.10 <= current_single
    current_fingerprint = dict(current.get("company_intro_fingerprint_repair") or {})
    fingerprint_reduced = bool(current_fingerprint.get("activated")) and _repair_improves_company_intro_fingerprint(
        current,
        repaired,
    )
    return bool(polite_dropped or monotony_dropped or body_expanded or fragmentation_reduced or fingerprint_reduced)


def _refresh_diagnostics_state(
    contract: Mapping[str, Any],
    draft: DraftSections,
    editor_report: Mapping[str, Any],
    compact_plan: list[Dict[str, str]] | None,
    source_pack: Mapping[str, Any],
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    diagnostics = measure_diagnostics(contract, draft, editor_report=editor_report)
    diagnostics, controlled_realization = _apply_controlled_realization(
        contract,
        draft,
        compact_plan,
        diagnostics,
    )
    diagnostics = _merge_quality_guard(
        diagnostics,
        evaluate_quality_guard(contract=contract, draft=draft, diagnostics=diagnostics, source_pack=source_pack),
    )
    diagnostics, controlled_realization = _apply_controlled_realization(
        contract,
        draft,
        compact_plan,
        diagnostics,
    )
    diagnostics = _activate_omission_repair(contract, diagnostics)
    diagnostics = _activate_longform_explanatory_repair(contract, draft, diagnostics)
    diagnostics = _activate_explanatory_fingerprint_repair(contract, draft, editor_report, diagnostics)
    diagnostics = _activate_company_intro_fingerprint_repair(contract, draft, editor_report, diagnostics)
    diagnostics = _activate_company_intro_source_reflection_repair(contract, draft, diagnostics)
    diagnostics = _apply_company_intro_naturalness_enrichment(contract, diagnostics)
    diagnostics["hidden_late_validation"] = _evaluate_hidden_late_validation(
        contract,
        draft,
        diagnostics,
        source_pack,
    )
    diagnostics["case_study_source_contract_validation"] = _evaluate_case_study_source_contract_validation(
        contract,
        draft,
        diagnostics,
        source_pack,
    )
    diagnostics["announcement_source_contract_validation"] = _evaluate_announcement_source_contract_validation(
        contract,
        draft,
        diagnostics,
        source_pack,
    )
    diagnostics["branding_source_contract_validation"] = _evaluate_branding_source_contract_validation(
        contract,
        draft,
        diagnostics,
        source_pack,
    )
    diagnostics["company_introduction_source_contract_validation"] = _evaluate_company_intro_source_contract_validation(
        contract,
        draft,
        diagnostics,
        source_pack,
    )
    diagnostics["comparative_review_source_contract_validation"] = _evaluate_comparative_source_contract_validation(
        contract,
        draft,
        diagnostics,
        source_pack,
    )
    flagged_spans = _build_flagged_spans(contract, diagnostics)
    diagnostics["flagged_spans"] = flagged_spans
    diagnostics["flagged_span_count"] = len(flagged_spans)
    return diagnostics, dict(controlled_realization)


def _topic_hint_for_opening(contract: Mapping[str, Any], draft: DraftSections) -> str:
    topic_hint = _clean_inline_text(
        contract.get("topic_statement")
        or contract.get("topic")
        or contract.get("core_message")
        or draft.title,
        limit=96,
    )
    topic_hint = re.split(r"[。！？!?]", topic_hint, maxsplit=1)[0].strip(" 、,")
    return topic_hint or _clean_inline_text(draft.title, limit=72) or "このテーマ"


def _shape_explanatory_title_by_tone(title: str, tone_profile: str) -> str:
    normalized = str(title or "").strip()
    if not normalized:
        return normalized
    if tone_profile == "warm":
        updated = normalized.replace(
            "運用定着の見方をそろえるべき理由から考える実務の見方",
            "運用定着の見方をそろえて迷いを減らす実務の見方",
        )
        return updated or normalized
    if tone_profile == "formal":
        updated = normalized.replace(
            "運用定着の見方をそろえるべき理由から考える実務の見方",
            "運用定着の見方をそろえる判断軸を整理する",
        )
        updated = updated.replace("まず", "")
        return re.sub(r"、{2,}", "、", updated).strip(" 、,") or normalized
    return normalized


def _shape_explanatory_lead_by_tone(contract: Mapping[str, Any], draft: DraftSections) -> str:
    return draft.lead


def _apply_tone_profile_opening_shape(contract: Mapping[str, Any], draft: DraftSections) -> DraftSections:
    article_type = str(contract.get("article_type") or "").strip().lower()
    tone_profile = str(contract.get("tone_profile") or "auto").strip().lower()
    if article_type != "explanatory_article" or tone_profile not in {"warm", "calm", "formal"}:
        return draft
    return DraftSections(
        title=_shape_explanatory_title_by_tone(draft.title, tone_profile),
        lead=_shape_explanatory_lead_by_tone(contract, draft),
        body=draft.body,
        hashtags=draft.hashtags,
    )


def _shape_daily_story_title(title: str) -> str:
    normalized = str(title or "").strip()
    suffix = "から見えたこと"
    if not normalized.endswith(suffix):
        return normalized
    stem = normalized[: -len(suffix)].strip(" 、,")
    if not stem:
        return normalized
    rewritten = re.sub(r"^(?P<context>.+?)に、(?P<subject>.+?)があった$", r"\g<context>にあった、\g<subject>", stem)
    if rewritten == stem:
        rewritten = re.sub(r"^(?P<context>.+?)に、?(?P<subject>.+?)があった$", r"\g<context>にあった、\g<subject>", stem)
    cleaned = re.sub(r"でした$", "", rewritten).strip(" 、,")
    cleaned = re.sub(r"、{2,}", "、", cleaned)
    return cleaned or normalized


def _apply_daily_story_title_shape(contract: Mapping[str, Any], draft: DraftSections) -> DraftSections:
    article_type = str(contract.get("article_type") or "").strip().lower()
    if article_type != "daily_story":
        return draft
    shaped_title = _shape_daily_story_title(draft.title)
    if shaped_title == draft.title:
        return draft
    return DraftSections(
        title=shaped_title,
        lead=draft.lead,
        body=draft.body,
        hashtags=draft.hashtags,
    )


def _rewrite_empty_aiish_phrases(text: str) -> str:
    rewritten = str(text or "")
    replacements = (
        (r"このやり方が効いたのは", "このやり方で差が出たのは"),
        (r"どこで効くか", "どこで差が出るか"),
        (r"効いてきます", "積み重なります"),
        (r"効いています", "影響しています"),
        (r"効いている", "影響している"),
        (r"効いた", "差が出た"),
        (r"効く", "差が出る"),
        (r"第一歩", "最初に確認すること"),
        (r"価値を提供", "役割を担う"),
        (r"最適なソリューション", "必要な対応"),
    )
    for pattern, replacement in replacements:
        rewritten = re.sub(pattern, replacement, rewritten)
    return rewritten


def _apply_empty_aiish_phrase_guard(draft: DraftSections) -> DraftSections:
    return DraftSections(
        title=_rewrite_empty_aiish_phrases(draft.title),
        lead=_rewrite_empty_aiish_phrases(draft.lead),
        body=_rewrite_empty_aiish_phrases(draft.body),
        hashtags=draft.hashtags,
    )


def _runtime_error_class(reason_code: str) -> str:
    code = str(reason_code or "").upper()
    if code.startswith("INP_"):
        return "user_input"
    if code.startswith(("POL_", "SEC_")):
        return "policy"
    if code.startswith("TRN_"):
        return "transient"
    return "system"


def _build_pipeline_failure_result(
    contract: Mapping[str, Any],
    *,
    reason_code: str,
    message: str,
    extra: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    normalized_reason = str(reason_code or error_codes.SYS_PIPELINE_FAILURE)
    error_payload: Dict[str, Any] = {
        "reason_code": normalized_reason,
        "message": str(message or normalized_reason),
    }
    if extra:
        for key, value in dict(extra).items():
            if not key or key in error_payload:
                continue
            error_payload[str(key)] = value
    return {
        "success": False,
        "title": "",
        "lead": "",
        "body": "",
        "references": "",
        "hashtags": "",
        "full_text": "",
        "reason_code": normalized_reason,
        "runtime_reason_code": normalized_reason,
        "runtime_error_class": _runtime_error_class(normalized_reason),
        "pipeline_check": {
            "pipeline_name": "simple_note_pipeline",
            "pipeline_version": "simple-note-v1",
            "input_contract": contract,
            "error": error_payload,
        },
    }


def _merge_quality_guard(diagnostics: Dict[str, Any], guard: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(diagnostics)
    repair_instructions: list[str] = []
    for item in list(diagnostics.get("repair_instructions") or []) + list(guard.get("repair_instructions") or []):
        text = str(item or "").strip()
        if text and text not in repair_instructions:
            repair_instructions.append(text)
    soft_warnings: list[str] = []
    for item in list(diagnostics.get("soft_warnings") or []) + list(guard.get("soft_warnings") or []):
        text = str(item or "").strip()
        if text and text not in soft_warnings:
            soft_warnings.append(text)
    merged["repair_instructions"] = repair_instructions[:10]
    merged["soft_warnings"] = soft_warnings[:12]
    merged["ai_index"] = _to_plain_dict(guard.get("ai_index"))
    merged["legal_summary"] = _to_plain_dict(guard.get("legal_summary"))
    merged["repair_trigger_score"] = float(guard.get("repair_trigger_score") or 0.0)
    merged["repair_required"] = bool(guard.get("repair_required"))
    merged["severity"] = max(int(merged.get("severity", 0) or 0), int(round(merged["repair_trigger_score"] * 4)))
    merged["issue_count"] = max(int(merged.get("issue_count", 0) or 0), len(repair_instructions), len(soft_warnings))
    return merged


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


def _text_hits_shadow(value: Any, tokens: list[str]) -> bool:
    normalized = _clean_inline_text(value or "", limit=1600).lower()
    return bool(tokens) and any(token in normalized for token in tokens)


def _split_heading_sections(body: Any) -> list[Dict[str, str]]:
    sections: list[Dict[str, str]] = []
    current_heading = ""
    current_lines: list[str] = []
    for raw_line in str(body or "").replace("\r\n", "\n").replace("\r", "\n").splitlines():
        matched = re.match(r"^##\s+(.+)$", raw_line.strip())
        if matched:
            if current_heading:
                sections.append({"heading": current_heading, "body": "\n".join(current_lines).strip()})
            current_heading = matched.group(1).strip()
            current_lines = []
            continue
        if current_heading:
            current_lines.append(raw_line)
    if current_heading:
        sections.append({"heading": current_heading, "body": "\n".join(current_lines).strip()})
    return sections


def _build_section_shadow_entries(
    contract: Mapping[str, Any],
    compact_plan: list[Dict[str, str]] | None,
) -> list[Dict[str, str]]:
    shadow_spec_inputs = contract.get("_shadow_spec_inputs") if isinstance(contract.get("_shadow_spec_inputs"), Mapping) else None
    if not isinstance(shadow_spec_inputs, Mapping):
        return []
    main_focus = _clean_inline_text(shadow_spec_inputs.get("main_focus") or "", limit=72)
    support_points = [
        _clean_inline_text(item, limit=40)
        for item in list(shadow_spec_inputs.get("support_points") or [])[:3]
        if _clean_inline_text(item, limit=40)
    ]
    comparison_axes = [
        _clean_inline_text(item, limit=32)
        for item in list(shadow_spec_inputs.get("comparison_axes") or [])[:2]
        if _clean_inline_text(item, limit=32)
    ]
    source_fact_pool = [
        _clean_inline_text(item, limit=96)
        for item in list(shadow_spec_inputs.get("source_fact_pool") or [])[:6]
        if _clean_inline_text(item, limit=96)
    ]
    entries: list[Dict[str, str]] = []
    for index, item in enumerate(list(compact_plan or [])[:6], start=1):
        heading = _clean_inline_text(item.get("heading") or "", limit=40)
        claim = _clean_inline_text(item.get("claim") or item.get("key_message") or "", limit=72)
        if not heading:
            continue
        entries.append(
            {
                "heading": heading,
                "focus": main_focus,
                "claim": claim,
                "support": support_points[min(index - 1, len(support_points) - 1)] if support_points else "",
                "axes": " / ".join(comparison_axes[:2]) if comparison_axes else "",
                "fact": source_fact_pool[min(index - 1, len(source_fact_pool) - 1)] if source_fact_pool else "",
            }
        )
    return entries


def _evaluate_controlled_realization(
    contract: Mapping[str, Any],
    draft: DraftSections,
    compact_plan: list[Dict[str, str]] | None,
) -> Dict[str, Any]:
    shadow_entries = _build_section_shadow_entries(contract, compact_plan)
    if not shadow_entries:
        return {
            "active": False,
            "shadow_section_count": 0,
            "checked_section_count": 0,
            "alignment_rate": 0.0,
            "drift_count": 0,
            "drift_headings": [],
            "global_focus_aligned": True,
        }
    sections = _split_heading_sections(draft.body)
    lead_and_opening = _clean_inline_text(f"{draft.lead}\n{draft.body[:280]}", limit=520)
    focus_tokens = _extract_shadow_tokens(shadow_entries[0].get("focus") or "", limit=4)
    global_focus_aligned = True if not focus_tokens else _text_hits_shadow(lead_and_opening, focus_tokens)
    alignment_scores: list[float] = []
    drift_headings: list[str] = []
    checked_section_count = 0
    for index, entry in enumerate(shadow_entries):
        expected_heading = str(entry.get("heading") or "").strip()
        section = sections[index] if index < len(sections) else {}
        actual_heading = str(section.get("heading") or expected_heading).strip()
        section_text = str(section.get("body") or "").strip()
        if not section_text:
            drift_headings.append(expected_heading or actual_heading)
            alignment_scores.append(0.0)
            continue
        checked_section_count += 1
        claim_hit = _text_hits_shadow(section_text, _extract_shadow_tokens(entry.get("claim") or "", limit=4))
        support_hit = _text_hits_shadow(section_text, _extract_shadow_tokens(entry.get("support") or "", limit=3))
        fact_hit = _text_hits_shadow(section_text, _extract_shadow_tokens(entry.get("fact") or "", limit=4))
        axis_hit = _text_hits_shadow(section_text, _extract_shadow_tokens(entry.get("axes") or "", limit=3))
        heading_hit = _text_hits_shadow(
            f"{actual_heading}\n{section_text[:140]}",
            _extract_shadow_tokens(expected_heading or actual_heading, limit=3),
        )
        component_hits = [claim_hit, heading_hit]
        if str(entry.get("support") or "").strip() or str(entry.get("fact") or "").strip() or str(entry.get("axes") or "").strip():
            component_hits.append(support_hit or fact_hit or axis_hit)
        alignment_scores.append(round(sum(1.0 for hit in component_hits if hit) / max(1, len(component_hits)), 4))
        if not claim_hit and not (support_hit or fact_hit or axis_hit):
            drift_headings.append(expected_heading or actual_heading)
    if focus_tokens and not global_focus_aligned and shadow_entries:
        lead_heading = str(shadow_entries[0].get("heading") or "").strip()
        if lead_heading and lead_heading not in drift_headings:
            drift_headings.insert(0, lead_heading)
    return {
        "active": True,
        "shadow_section_count": len(shadow_entries),
        "checked_section_count": checked_section_count,
        "alignment_rate": round(sum(alignment_scores) / max(1, len(alignment_scores)), 4),
        "drift_count": len(drift_headings),
        "drift_headings": drift_headings[:4],
        "global_focus_aligned": global_focus_aligned,
    }


def _apply_controlled_realization(
    contract: Mapping[str, Any],
    draft: DraftSections,
    compact_plan: list[Dict[str, str]] | None,
    diagnostics: Dict[str, Any],
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    activated = dict(diagnostics)
    controlled = _evaluate_controlled_realization(contract, draft, compact_plan)
    activated["controlled_realization_active"] = bool(controlled.get("active"))
    activated["shadow_section_count"] = int(controlled.get("shadow_section_count", 0) or 0)
    activated["shadow_checked_section_count"] = int(controlled.get("checked_section_count", 0) or 0)
    activated["shadow_alignment_rate"] = float(controlled.get("alignment_rate", 0.0) or 0.0)
    activated["shadow_drift_count"] = int(controlled.get("drift_count", 0) or 0)
    activated["shadow_drift_headings"] = list(controlled.get("drift_headings") or [])
    activated["shadow_global_focus_aligned"] = bool(controlled.get("global_focus_aligned", True))
    if not bool(controlled.get("active")) or int(controlled.get("drift_count", 0) or 0) <= 0:
        return activated, controlled
    repair_instructions: list[str] = []
    for item in list(activated.get("repair_instructions") or []):
        text = str(item or "").strip()
        if text and text not in repair_instructions:
            repair_instructions.append(text)
    controlled_lines = [
        "SECTION_SHADOW で決めた節順と claim を戻し、未指定の新論点へ広げない。",
    ]
    drift_headings = [str(item or "").strip() for item in list(controlled.get("drift_headings") or []) if str(item or "").strip()]
    if drift_headings:
        controlled_lines.append(f"shadow drift の見出し: {' / '.join(drift_headings[:3])}")
    for line in controlled_lines:
        if line not in repair_instructions:
            repair_instructions.append(line)
    soft_warnings: list[str] = []
    for item in list(activated.get("soft_warnings") or []):
        text = str(item or "").strip()
        if text and text not in soft_warnings:
            soft_warnings.append(text)
    if "shadow:section_drift" not in soft_warnings:
        soft_warnings.append("shadow:section_drift")
    activated["repair_instructions"] = repair_instructions[:10]
    activated["soft_warnings"] = soft_warnings[:12]
    activated["repair_trigger_score"] = max(float(activated.get("repair_trigger_score") or 0.0), 0.59)
    activated["repair_required"] = True
    activated["issue_count"] = max(int(activated.get("issue_count", 0) or 0), len(repair_instructions), len(soft_warnings))
    return activated, controlled


def _compact_plan_safe_scope(contract: Mapping[str, Any]) -> bool:
    article_type = str(contract.get("article_type") or "").strip().lower()
    semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
    length_mode = str(contract.get("length_mode") or "").strip().lower()
    writing_focus = str(contract.get("writing_focus") or "").strip().lower()
    content_goal = str(contract.get("content_goal") or "").strip().lower()
    prompt_surface = str(contract.get("prompt_raw") or contract.get("topic") or "").strip()
    return (
        article_type == "explanatory_article" and length_mode in {"short", "adaptive"}
    ) or (
        article_type == "industry_analysis" and length_mode == "short"
    ) or (
        article_type == "branding"
        and semantic_key == "company_introduction"
        and length_mode in {"short", "adaptive"}
        and bool(prompt_surface)
    ) or (
        article_type == "branding"
        and semantic_key == "branding"
        and length_mode in {"short", "adaptive"}
        and writing_focus == "explanation"
        and content_goal == "trust"
    )


def _activate_omission_repair(contract: Mapping[str, Any], diagnostics: Dict[str, Any]) -> Dict[str, Any]:
    activated = dict(diagnostics)
    if not _compact_plan_safe_scope(contract):
        return activated
    miss_count = int(activated.get("heading_reanchor_miss_count", 0) or 0)
    omission_score = float(activated.get("omission_ambiguity_score", 0.0) or 0.0)
    if miss_count <= 0 or omission_score < 0.5:
        return activated
    soft_warnings: list[str] = []
    for item in list(activated.get("soft_warnings") or []):
        text = str(item or "").strip()
        if text and text not in soft_warnings:
            soft_warnings.append(text)
    if "omission:heading_reanchor" not in soft_warnings:
        soft_warnings.append("omission:heading_reanchor")
    activated["soft_warnings"] = soft_warnings[:12]
    activated["omission_repair_active"] = True
    activated["repair_trigger_score"] = max(float(activated.get("repair_trigger_score") or 0.0), 0.58)
    activated["repair_required"] = True
    activated["issue_count"] = max(int(activated.get("issue_count", 0) or 0), miss_count)
    return activated


def _activate_longform_explanatory_repair(
    contract: Mapping[str, Any],
    draft: DraftSections,
    diagnostics: Dict[str, Any],
) -> Dict[str, Any]:
    activated = dict(diagnostics)
    article_type = str(contract.get("article_type") or "").strip().lower()
    length_mode = str(contract.get("length_mode") or "").strip().lower()
    if article_type != "explanatory_article" or length_mode not in {"normal", "long"}:
        activated["explanatory_thin_section_count"] = 0
        activated["explanatory_thin_section_headings"] = []
        return activated

    source_count = len(list(contract.get("source_documents") or []))
    target = int(activated.get("target_chars") or target_chars(length_mode, article_type, source_count=source_count) or 0)
    body_chars = int(activated.get("body_chars") or _compact_text_len(draft.body))
    activated["target_chars"] = target
    activated["body_chars"] = body_chars

    if target <= 0 or body_chars >= int(target * 0.82):
        activated["explanatory_thin_section_count"] = 0
        activated["explanatory_thin_section_headings"] = []
        return activated

    sections = _split_body_sections(draft.body)
    if len(sections) < 3:
        activated["explanatory_thin_section_count"] = 0
        activated["explanatory_thin_section_headings"] = []
        return activated

    per_section_target = max(180, int(target / max(1, len(sections))))
    thin_sections: list[tuple[int, str]] = []
    for section in sections:
        heading = str(section.get("heading") or "").strip()
        section_body = str(section.get("body") or "").strip()
        if not heading or not section_body:
            continue
        section_chars = _compact_text_len(section_body)
        sentence_count = len(_split_japanese_sentences(section_body))
        if section_chars <= max(150, int(per_section_target * 0.78)) or (
            sentence_count <= 2 and section_chars <= max(190, int(per_section_target * 0.92))
        ):
            thin_sections.append((section_chars, heading))

    if len(thin_sections) < 2 and body_chars >= int(target * 0.72):
        activated["explanatory_thin_section_count"] = 0
        activated["explanatory_thin_section_headings"] = []
        return activated

    thin_headings = [heading for _chars, heading in sorted(thin_sections)[:4]]
    if not thin_headings:
        thin_headings = [
            str(section.get("heading") or "").strip()
            for section in sections[:4]
            if str(section.get("heading") or "").strip()
        ]
    if not thin_headings:
        activated["explanatory_thin_section_count"] = 0
        activated["explanatory_thin_section_headings"] = []
        return activated

    repair_instructions: list[str] = []
    for item in list(activated.get("repair_instructions") or []):
        text = str(item or "").strip()
        if text and text not in repair_instructions:
            repair_instructions.append(text)
    for text in [
        "longform解説では、指定見出しを1段落で畳まず、背景・判断理由・実務上の見方を1つずつ足して厚みを戻す。",
        "薄い見出しは2〜4文で展開し、短い独立段落を連続させず、説明不足の一文だけで終えない。",
    ]:
        if text not in repair_instructions:
            repair_instructions.append(text)

    soft_warnings: list[str] = []
    for item in list(activated.get("soft_warnings") or []):
        text = str(item or "").strip()
        if text and text not in soft_warnings:
            soft_warnings.append(text)
    if "explanatory:longform_shortfall" not in soft_warnings:
        soft_warnings.append("explanatory:longform_shortfall")

    activated["repair_instructions"] = repair_instructions[:10]
    activated["soft_warnings"] = soft_warnings[:12]
    activated["explanatory_thin_section_count"] = len(thin_headings)
    activated["explanatory_thin_section_headings"] = thin_headings
    activated["explanatory_longform_shortfall_chars"] = max(0, target - body_chars)
    activated["repair_trigger_score"] = max(
        float(activated.get("repair_trigger_score") or 0.0),
        0.62 if body_chars < int(target * 0.72) else 0.58,
    )
    activated["repair_required"] = True
    activated["issue_count"] = max(int(activated.get("issue_count", 0) or 0), len(thin_headings), len(repair_instructions))
    activated["severity"] = max(int(activated.get("severity", 0) or 0), 2)
    return activated


def _explanatory_fingerprint_source_scope(contract: Mapping[str, Any]) -> bool:
    article_type = str(contract.get("article_type") or "").strip().lower()
    length_mode = str(contract.get("length_mode") or "").strip().lower()
    if article_type != "explanatory_article" or length_mode != "adaptive":
        return False
    source_documents = [item for item in list(contract.get("source_documents") or []) if isinstance(item, Mapping)]
    if len(source_documents) != 1:
        return False
    content = str(source_documents[0].get("content") or "")
    if len(content) < 4000:
        return False
    grounding_items = [item for item in list(contract.get("source_grounding_items") or []) if isinstance(item, Mapping)]
    grounding_buckets = {
        str(item.get("bucket") or "").strip()
        for item in grounding_items
        if str(item.get("bucket") or "").strip()
    }
    return len(grounding_items) >= 3 and bool(grounding_buckets.intersection(_EXPLANATORY_SOURCE_USE_BUCKETS))


def _explanatory_fingerprint_target_headings(draft: DraftSections) -> list[str]:
    sections = _extract_revision_sections(draft.body)
    headings = [heading for heading, body in sections if heading and str(body or "").strip()]
    if not headings:
        return []
    start_index = max(1, len(headings) // 2)
    targets = headings[start_index : start_index + 3]
    return targets or headings[-1:]


def _activate_explanatory_fingerprint_repair(
    contract: Mapping[str, Any],
    draft: DraftSections,
    editor_report: Mapping[str, Any],
    diagnostics: Dict[str, Any],
) -> Dict[str, Any]:
    activated = dict(diagnostics)
    fingerprint_report = dict(editor_report.get("fingerprint_guard") or {})
    if not bool(fingerprint_report.get("checked")):
        return activated
    if bool(fingerprint_report.get("correction_applied")):
        return activated
    if not _explanatory_fingerprint_source_scope(contract):
        return activated

    raw_flags = [
        str(item or "").strip()
        for item in list(fingerprint_report.get("flat_zone_flags") or [])
        if str(item or "").strip()
    ]
    flat_flags = [
        item
        for item in raw_flags
        if item in _EXPLANATORY_FINGERPRINT_REPAIR_FLAGS
    ]
    if len(set(flat_flags)) < 3:
        return activated

    target_headings = _explanatory_fingerprint_target_headings(draft)
    if not target_headings:
        return activated

    repair_instructions: list[str] = []
    for item in list(activated.get("repair_instructions") or []):
        text = str(item or "").strip()
        if text and text not in repair_instructions:
            repair_instructions.append(text)
    for text in [
        "source anchor は保ったまま、対象見出しの後半本文だけで文長・文末・読点位置を散らし、章要約調に戻さない。",
        "同義語の置換を増やさず、重要語は必要な反復を残し、source外の主張や新しい数値を足さない。",
    ]:
        if text not in repair_instructions:
            repair_instructions.append(text)

    soft_warnings: list[str] = []
    for item in list(activated.get("soft_warnings") or []):
        text = str(item or "").strip()
        if text and text not in soft_warnings:
            soft_warnings.append(text)
    if "explanatory:fingerprint_flatness" not in soft_warnings:
        soft_warnings.append("explanatory:fingerprint_flatness")

    source_anchor_count = len(
        [item for item in list(contract.get("source_grounding_items") or []) if isinstance(item, Mapping)]
    )
    activated["repair_instructions"] = repair_instructions[:10]
    activated["soft_warnings"] = soft_warnings[:12]
    activated["explanatory_fingerprint_repair"] = {
        "activated": True,
        "flat_zone_flags": sorted(set(flat_flags)),
        "target_headings": target_headings,
        "source_anchor_item_count": source_anchor_count,
        "correction_applied": False,
    }
    activated["repair_trigger_score"] = max(float(activated.get("repair_trigger_score") or 0.0), 0.59)
    activated["repair_required"] = True
    activated["issue_count"] = max(int(activated.get("issue_count", 0) or 0), len(set(flat_flags)))
    activated["severity"] = max(int(activated.get("severity", 0) or 0), 2)
    return activated


def _company_intro_fingerprint_source_scope(contract: Mapping[str, Any]) -> bool:
    if not _company_intro_source_contract_scope_active(contract):
        return False
    if not isinstance(contract.get("company_introduction_source_contract"), Mapping):
        return False
    source_documents = [item for item in list(contract.get("source_documents") or []) if isinstance(item, Mapping)]
    if not source_documents:
        return False
    grounding_items = [item for item in list(contract.get("source_grounding_items") or []) if isinstance(item, Mapping)]
    grounding_buckets = {
        str(item.get("bucket") or "").strip()
        for item in grounding_items
        if str(item.get("bucket") or "").strip()
    }
    required_buckets = {
        _COMPANY_INTRO_SLOT_LABELS.get(slot, slot)
        for slot in _COMPANY_INTRO_REQUIRED_SOURCE_SLOTS
    }
    return len(grounding_items) >= 3 and bool(grounding_buckets.intersection(required_buckets))


def _company_intro_fingerprint_target_headings(draft: DraftSections) -> list[str]:
    sections = _extract_revision_sections(draft.body)
    headings = [heading for heading, body in sections if heading and str(body or "").strip()]
    if not headings:
        return []
    return headings[:4]


def _activate_company_intro_fingerprint_repair(
    contract: Mapping[str, Any],
    draft: DraftSections,
    editor_report: Mapping[str, Any],
    diagnostics: Dict[str, Any],
) -> Dict[str, Any]:
    activated = dict(diagnostics)
    fingerprint_report = dict(editor_report.get("fingerprint_guard") or {})
    if not bool(fingerprint_report.get("checked")):
        return activated
    if bool(fingerprint_report.get("correction_applied")):
        return activated
    if not _company_intro_fingerprint_source_scope(contract):
        return activated

    raw_flags = [
        str(item or "").strip()
        for item in list(fingerprint_report.get("flat_zone_flags") or [])
        if str(item or "").strip()
    ]
    flat_flags = [
        item
        for item in raw_flags
        if item in _COMPANY_INTRO_FINGERPRINT_REPAIR_FLAGS
    ]
    if len(set(flat_flags)) < 3:
        return activated

    target_headings = _company_intro_fingerprint_target_headings(draft)
    if not target_headings:
        return activated

    repair_instructions: list[str] = []
    for item in list(activated.get("repair_instructions") or []):
        text = str(item or "").strip()
        if text and text not in repair_instructions:
            repair_instructions.append(text)
    for text in [
        "source anchor と会社紹介の支援範囲を保ったまま、対象見出しの本文だけで文長・文末・読点位置を散らす。",
        "同義語の置換を増やさず、事業・支援範囲・相談前判断の語は必要な反復を残し、source外の成果や顧客名を足さない。",
    ]:
        if text not in repair_instructions:
            repair_instructions.append(text)

    soft_warnings: list[str] = []
    for item in list(activated.get("soft_warnings") or []):
        text = str(item or "").strip()
        if text and text not in soft_warnings:
            soft_warnings.append(text)
    if "company_intro:fingerprint_flatness" not in soft_warnings:
        soft_warnings.append("company_intro:fingerprint_flatness")

    source_anchor_count = len(
        [item for item in list(contract.get("source_grounding_items") or []) if isinstance(item, Mapping)]
    )
    activated["repair_instructions"] = repair_instructions[:10]
    activated["soft_warnings"] = soft_warnings[:12]
    activated["company_intro_fingerprint_repair"] = {
        "activated": True,
        "flat_zone_flags": sorted(set(flat_flags)),
        "target_headings": target_headings,
        "source_anchor_item_count": source_anchor_count,
        "correction_applied": False,
    }
    activated["repair_trigger_score"] = max(float(activated.get("repair_trigger_score") or 0.0), 0.59)
    activated["repair_required"] = True
    activated["issue_count"] = max(int(activated.get("issue_count", 0) or 0), len(set(flat_flags)))
    activated["severity"] = max(int(activated.get("severity", 0) or 0), 2)
    return activated


def _company_intro_source_reflection_weak(diagnostics: Mapping[str, Any]) -> bool:
    soft_warnings = {
        str(item or "").strip()
        for item in list(diagnostics.get("soft_warnings") or [])
        if str(item or "").strip()
    }
    if "source_grounding:weak_reflection" in soft_warnings:
        return True
    source_trace = float(
        diagnostics.get("source_trace_coverage")
        or diagnostics.get("source_grounding_reflection_ratio")
        or diagnostics.get("must_cover_source_trace_coverage")
        or 0.0
    )
    source_items = int(diagnostics.get("source_grounding_item_count", 0) or 0)
    return bool(source_items >= 3 and 0.0 < source_trace < 0.45)


def _activate_company_intro_source_reflection_repair(
    contract: Mapping[str, Any],
    draft: DraftSections,
    diagnostics: Dict[str, Any],
) -> Dict[str, Any]:
    activated = dict(diagnostics)
    if not _company_intro_fingerprint_source_scope(contract):
        return activated
    if not _company_intro_source_reflection_weak(activated):
        return activated

    target_headings = _company_intro_fingerprint_target_headings(draft)
    if not target_headings:
        return activated

    soft_warnings = [
        str(item or "").strip()
        for item in list(activated.get("soft_warnings") or [])
        if str(item or "").strip()
    ]
    raw_flags = [
        warning.split(":", 1)[1].strip()
        for warning in soft_warnings
        if warning.startswith("fingerprint:")
    ]
    flat_flags = [
        item
        for item in raw_flags
        if item in _COMPANY_INTRO_FINGERPRINT_REPAIR_FLAGS
    ]
    current_state = dict(activated.get("company_intro_fingerprint_repair") or {})
    existing_flags = [
        str(item or "").strip()
        for item in list(current_state.get("flat_zone_flags") or [])
        if str(item or "").strip()
    ]
    combined_flags = sorted(
        {
            *existing_flags,
            *flat_flags,
            _COMPANY_INTRO_SOURCE_REFLECTION_REPAIR_FLAG,
        }
    )

    repair_instructions: list[str] = []
    for item in list(activated.get("repair_instructions") or []):
        text = str(item or "").strip()
        if text and text not in repair_instructions:
            repair_instructions.append(text)
    for text in [
        "source にある現在事業、支援範囲、進め方、相談前判断の接続を本文内へ戻し、短い項目列で終えない。",
        "source外の成果、顧客名、受賞、数値は足さず、既存見出しの範囲で説明を厚くする。",
    ]:
        if text not in repair_instructions:
            repair_instructions.append(text)

    if "company_intro:source_reflection_repair" not in soft_warnings:
        soft_warnings.append("company_intro:source_reflection_repair")

    source_anchor_count = len(
        [item for item in list(contract.get("source_grounding_items") or []) if isinstance(item, Mapping)]
    )
    activated["repair_instructions"] = repair_instructions[:12]
    activated["soft_warnings"] = soft_warnings[:14]
    activated["company_intro_fingerprint_repair"] = {
        "activated": True,
        "flat_zone_flags": combined_flags,
        "target_headings": target_headings,
        "source_anchor_item_count": source_anchor_count,
        "correction_applied": False,
        "source_reflection_repair": True,
    }
    activated["repair_trigger_score"] = max(float(activated.get("repair_trigger_score") or 0.0), 0.61)
    activated["repair_required"] = True
    activated["issue_count"] = max(
        int(activated.get("issue_count", 0) or 0),
        len(combined_flags),
        len(repair_instructions),
    )
    activated["severity"] = max(int(activated.get("severity", 0) or 0), 2)
    return activated


def _build_flagged_spans(contract: Mapping[str, Any], diagnostics: Mapping[str, Any]) -> list[Dict[str, str]]:
    flagged_spans: list[Dict[str, str]] = []
    article_type = str(contract.get("article_type") or "").strip().lower()
    if article_type == "comparative_review":
        if int(diagnostics.get("comparative_thin_section_count", 0) or 0) < 2:
            return []
        for item in list(diagnostics.get("comparative_thin_section_headings") or [])[:4]:
            heading = str(item or "").strip()
            if not heading:
                continue
            flagged_spans.append(
                {
                    "issue_type": "comparative_thin_section",
                    "section_heading": heading,
                    "sentence_window": "section_body_only",
                }
            )
        deduped_compare: list[Dict[str, str]] = []
        for item in flagged_spans:
            if item not in deduped_compare:
                deduped_compare.append(item)
        return deduped_compare[:4]
    if article_type == "explanatory_article" and str(contract.get("length_mode") or "").strip().lower() in {"normal", "long"}:
        if int(diagnostics.get("explanatory_thin_section_count", 0) or 0) < 2:
            return []
        for item in list(diagnostics.get("explanatory_thin_section_headings") or [])[:4]:
            heading = str(item or "").strip()
            if not heading:
                continue
            flagged_spans.append(
                {
                    "issue_type": "explanatory_thin_section",
                    "section_heading": heading,
                    "sentence_window": "section_body_only",
                }
            )
        deduped_explanatory: list[Dict[str, str]] = []
        for item in flagged_spans:
            if item not in deduped_explanatory:
                deduped_explanatory.append(item)
        return deduped_explanatory[:4]
    fingerprint_repair = dict(diagnostics.get("explanatory_fingerprint_repair") or {})
    if article_type == "explanatory_article" and bool(fingerprint_repair.get("activated")):
        for item in list(fingerprint_repair.get("target_headings") or [])[:3]:
            heading = str(item or "").strip()
            if not heading:
                continue
            flagged_spans.append(
                {
                    "issue_type": _EXPLANATORY_FINGERPRINT_ISSUE_TYPE,
                    "section_heading": heading,
                    "sentence_window": "late_section_local_surface",
                }
            )
    company_intro_fingerprint_repair = dict(diagnostics.get("company_intro_fingerprint_repair") or {})
    if (
        article_type == "branding"
        and str(contract.get("semantic_article_key") or "").strip().lower() == "company_introduction"
        and bool(company_intro_fingerprint_repair.get("activated"))
    ):
        for item in list(company_intro_fingerprint_repair.get("target_headings") or [])[:4]:
            heading = str(item or "").strip()
            if not heading:
                continue
            flagged_spans.append(
                {
                    "issue_type": _COMPANY_INTRO_FINGERPRINT_ISSUE_TYPE,
                    "section_heading": heading,
                    "sentence_window": "section_surface_only",
                }
            )
    if bool(diagnostics.get("controlled_realization_active")) and int(diagnostics.get("shadow_drift_count", 0) or 0) > 0:
        for item in list(diagnostics.get("shadow_drift_headings") or [])[:4]:
            heading = str(item or "").strip()
            if not heading:
                continue
            flagged_spans.append(
                {
                    "issue_type": "shadow_section_drift",
                    "section_heading": heading,
                    "sentence_window": "section_open_plus_two",
                }
            )
    if bool(diagnostics.get("omission_repair_active")) and int(diagnostics.get("heading_reanchor_miss_count", 0) or 0) > 0:
        for item in list(diagnostics.get("omission_soft_warnings") or [])[:4]:
            text = str(item or "").strip()
            if not text.startswith("heading_reanchor:"):
                continue
            heading = text.split(":", 1)[1].strip()
            flagged_spans.append(
                {
                    "issue_type": "heading_reanchor",
                    "section_heading": heading,
                    "sentence_window": "section_open_plus_two",
                }
            )
    if int(diagnostics.get("ending_bucket_max_run", 0) or 0) >= 3:
        flagged_spans.append(
            {
                "issue_type": "ending_bucket_monotony",
                "section_heading": "",
                "sentence_window": "local_run_plus_two",
            }
        )
    deduped: list[Dict[str, str]] = []
    for item in flagged_spans:
        if item not in deduped:
            deduped.append(item)
        if len(deduped) >= 4:
            break
    return deduped


def _flagged_issue_types(flagged_spans: Sequence[Mapping[str, Any]] | None) -> list[str]:
    issue_types: list[str] = []
    for item in list(flagged_spans or []):
        issue_type = str(item.get("issue_type") or "").strip()
        if issue_type and issue_type not in issue_types:
            issue_types.append(issue_type)
    return issue_types


def _patch_scaffold_enabled(contract: Mapping[str, Any]) -> bool:
    return bool(contract.get("_flagged_span_patch_scaffold"))


def _patch_activation_enabled(contract: Mapping[str, Any], flagged_spans: list[Dict[str, str]]) -> bool:
    if not flagged_spans:
        return False
    issue_types = {str(item.get("issue_type") or "").strip() for item in flagged_spans if str(item.get("issue_type") or "").strip()}
    article_type = str(contract.get("article_type") or "").strip().lower()
    if article_type == "comparative_review":
        return issue_types == {"comparative_thin_section"}
    if article_type == "explanatory_article" and str(contract.get("length_mode") or "").strip().lower() in {"normal", "long"}:
        return issue_types == {"explanatory_thin_section"}
    if (
        article_type == "branding"
        and str(contract.get("semantic_article_key") or "").strip().lower() == "company_introduction"
        and isinstance(contract.get("company_introduction_source_contract"), Mapping)
        and _COMPANY_INTRO_FINGERPRINT_ISSUE_TYPE in issue_types
    ):
        return issue_types.issubset({"ending_bucket_monotony", _COMPANY_INTRO_FINGERPRINT_ISSUE_TYPE})
    if not _compact_plan_safe_scope(contract):
        return False
    return issue_types.issubset(
        {
            "heading_reanchor",
            "ending_bucket_monotony",
            "shadow_section_drift",
            _EXPLANATORY_FINGERPRINT_ISSUE_TYPE,
            _COMPANY_INTRO_FINGERPRINT_ISSUE_TYPE,
        }
    )


def _build_repair_entry_telemetry(
    contract: Mapping[str, Any],
    diagnostics: Mapping[str, Any],
    *,
    repair_applied: bool,
    repair_metadata: Mapping[str, Any],
) -> Dict[str, Any]:
    flagged_spans = list(diagnostics.get("flagged_spans") or [])
    naturalness_enrichment = dict(diagnostics.get("company_intro_naturalness_enrichment") or {})
    hidden_late_validation = dict(diagnostics.get("hidden_late_validation") or {})
    materialized_late_half_repair = dict(diagnostics.get("materialized_late_half_repair") or {})
    entry = {
        "repair_required": bool(diagnostics.get("repair_required")),
        "repair_trigger_score": float(diagnostics.get("repair_trigger_score") or 0.0),
        "ending_bucket_max_run": int(diagnostics.get("ending_bucket_max_run", 0) or 0),
        "ending_bucket_monotony_score": float(diagnostics.get("ending_bucket_monotony_score") or 0.0),
        "flagged_span_count": len(flagged_spans),
        "flagged_issue_types": _flagged_issue_types(flagged_spans),
        "patch_path_candidate": bool(
            _patch_scaffold_enabled(contract) or _patch_activation_enabled(contract, flagged_spans)
        ),
        "company_intro_naturalness_rescue_active": bool(naturalness_enrichment.get("activated")),
        "company_intro_naturalness_signals": dict(naturalness_enrichment.get("signals") or {}),
        "company_intro_naturalness_instructions_added": int(
            naturalness_enrichment.get("instructions_added") or 0
        ),
        "hidden_late_validation": {
            "checked": bool(hidden_late_validation.get("checked")),
            "scope_match": bool(hidden_late_validation.get("scope_match")),
            "failed_tokens": list(hidden_late_validation.get("failed_tokens") or []),
            "visible_forbidden_heading_hits": list(
                hidden_late_validation.get("visible_forbidden_heading_hits") or []
            ),
            "body_leakage_warning_hits": list(hidden_late_validation.get("body_leakage_warning_hits") or []),
            "repair_trigger_ids": list(hidden_late_validation.get("repair_trigger_ids") or []),
        },
        "skip_reason": "",
    }
    if materialized_late_half_repair.get("checked"):
        entry["materialized_late_half_repair"] = {
            "checked": bool(materialized_late_half_repair.get("checked")),
            "activated": bool(materialized_late_half_repair.get("activated")),
            "stage": str(materialized_late_half_repair.get("stage") or ""),
            "repair_recommended": bool(materialized_late_half_repair.get("repair_recommended")),
            "repair_scope": str(materialized_late_half_repair.get("repair_scope") or ""),
            "warnings": list(materialized_late_half_repair.get("warnings") or [])[:8],
            "target_headings": list(materialized_late_half_repair.get("target_headings") or [])[:3],
        }
    reconstruction = dict(repair_metadata.get("materialized_anchor_patch_reconstruction") or {})
    if reconstruction.get("checked"):
        entry["materialized_anchor_patch_reconstruction"] = reconstruction
    raw_summary = dict(repair_metadata.get("repair_candidate_raw_summary") or {})
    if raw_summary:
        entry["repair_candidate_raw_summary"] = raw_summary
    reconstructed_summary = dict(repair_metadata.get("reconstructed_candidate_summary") or {})
    if reconstructed_summary:
        entry["reconstructed_candidate_summary"] = reconstructed_summary
    if repair_applied:
        entry["skip_reason"] = "repair_applied"
        entry["repair_applied"] = True
        entry["repair_rejected"] = False
        return entry
    if repair_metadata:
        entry.update(
            {
                "repair_applied": False,
                "repair_rejected": not bool(repair_metadata.get("skip_reason")),
                "skip_reason": str(repair_metadata.get("skip_reason") or ""),
                "acceptance_rejection_reason": str(
                    repair_metadata.get("acceptance_rejection_reason") or ""
                ),
                "scope_rejection_reason": str(
                    repair_metadata.get("scope_rejection_reason") or ""
                ),
                "patch_path_used": bool(repair_metadata.get("patch_path_used")),
                "patch_scope": dict(
                    repair_metadata.get("patch_scope")
                    or _patch_scope_observation(
                        flagged_spans,
                        patch_path_used=bool(repair_metadata.get("patch_path_used")),
                    )
                ),
                "fingerprint_before": dict(repair_metadata.get("fingerprint_before") or {}),
                "fingerprint_after": dict(repair_metadata.get("fingerprint_after") or {}),
            }
        )
        return entry
    if not bool(diagnostics.get("repair_required")):
        entry["skip_reason"] = "repair_not_required"
        entry["repair_applied"] = False
        entry["repair_rejected"] = False
        return entry
    entry["skip_reason"] = "repair_call_unavailable"
    entry["repair_applied"] = False
    entry["repair_rejected"] = False
    return entry


def _company_intro_naturalness_rescue_active(diagnostics: Mapping[str, Any]) -> bool:
    enrichment = dict(diagnostics.get("company_intro_naturalness_enrichment") or {})
    return bool(enrichment.get("activated"))


def _company_intro_naturalness_unresolved(
    diagnostics: Mapping[str, Any],
    repair_metadata: Mapping[str, Any],
) -> bool:
    if not _company_intro_naturalness_rescue_active(diagnostics):
        return False
    if bool(repair_metadata.get("company_intro_naturalness_improved")):
        return False
    if not repair_metadata:
        return False
    if str(repair_metadata.get("skip_reason") or "") in {
        "company_introduction_contract_disallows_ending_monotony_retry",
        "company_introduction_contract_disallows_naturalness_only_retry",
    }:
        return False
    if bool(repair_metadata.get("company_introduction_source_contract_cleared")):
        return False
    if bool(repair_metadata.get("company_introduction_operational_source_contract_present")):
        return False

    rejection_reason = str(repair_metadata.get("acceptance_rejection_reason") or "")
    if rejection_reason == "repair_output_contract_incomplete":
        return True

    enrichment = dict(diagnostics.get("company_intro_naturalness_enrichment") or {})
    signals = dict(enrichment.get("signals") or {})
    body_chars = int(signals.get("body_chars") or diagnostics.get("body_chars") or 0)
    complete_article = bool(repair_metadata.get("output_contract_complete_article"))
    return complete_article and body_chars >= 700


def _company_intro_source_contract_repair_unresolved(repair_metadata: Mapping[str, Any]) -> bool:
    if not bool(repair_metadata.get("company_introduction_source_contract_active")):
        return False
    if bool(repair_metadata.get("company_introduction_source_contract_cleared")):
        return False
    if bool(repair_metadata.get("company_introduction_operational_source_contract_present")):
        return True
    if not bool(repair_metadata.get("company_introduction_source_contract_improved")):
        return True
    if not bool(repair_metadata.get("company_introduction_unsupported_clear")):
        return True
    if not bool(repair_metadata.get("company_introduction_source_limit_clear")):
        return True
    return False


def _company_intro_final_hard_validation_unresolved(validation: Mapping[str, Any]) -> bool:
    if not bool(validation.get("checked")) or not bool(validation.get("scope_match")):
        return False
    return bool(list(validation.get("hard_trigger_ids") or []))


def _build_hidden_late_validation_failure_snapshot(diagnostics: Mapping[str, Any]) -> Dict[str, Any]:
    validation = dict(diagnostics.get("hidden_late_validation") or {})
    return {
        "checked": bool(validation.get("checked")),
        "scope_match": bool(validation.get("scope_match")),
        "failed_tokens": list(validation.get("failed_tokens") or []),
        "visible_forbidden_heading_hits": list(validation.get("visible_forbidden_heading_hits") or []),
        "body_leakage_warning_hits": list(validation.get("body_leakage_warning_hits") or []),
        "repair_trigger_ids": list(validation.get("repair_trigger_ids") or []),
        "abstract_closing_operational_rescued": bool(
            validation.get("abstract_closing_operational_rescued")
        ),
    }


def _failure_candidate_final_paragraph_excerpt(draft: DraftSections | None) -> str:
    if draft is None:
        return ""
    paragraphs: list[str] = []
    for paragraph in re.split(r"\n\s*\n", str(draft.body or "").strip()):
        lines = [
            line.strip()
            for line in paragraph.splitlines()
            if line.strip()
            and not line.strip().startswith("##")
            and not line.strip().startswith("[")
            and not line.strip().startswith("#")
        ]
        text = " ".join(lines).strip()
        if text:
            paragraphs.append(text)
    if not paragraphs:
        return ""
    return _clean_inline_text(paragraphs[-1], limit=220)


def _safe_float_metric(value: Any) -> float:
    try:
        return round(float(value or 0.0), 4)
    except (TypeError, ValueError):
        return 0.0


def _fingerprint_guard_observation(editor_report: Mapping[str, Any] | None) -> Dict[str, Any]:
    report = dict((editor_report or {}).get("fingerprint_guard") or {})
    return {
        "checked": bool(report.get("checked")),
        "flat_zone_flags": [
            str(item or "").strip()
            for item in list(report.get("flat_zone_flags") or [])[:12]
            if str(item or "").strip()
        ],
        "correction_applied": bool(report.get("correction_applied")),
        "applied_rules": [
            str(item or "").strip()
            for item in list(report.get("applied_rules") or [])[:8]
            if str(item or "").strip()
        ],
        "discarded": bool(report.get("discarded")),
        "discard_reason": str(report.get("discard_reason") or ""),
        "overall_unpredictability": _safe_float_metric(report.get("overall_unpredictability")),
        "subject_explicit_rate": _safe_float_metric(report.get("subject_explicit_rate")),
        "conjunction_repetition_rate": _safe_float_metric(report.get("conjunction_repetition_rate")),
        "sentence_opening_entropy": _safe_float_metric(report.get("sentence_opening_entropy")),
        "comma_position_cv": _safe_float_metric(report.get("comma_position_cv")),
    }


def _patch_scope_observation(
    flagged_spans: Sequence[Mapping[str, Any]] | None,
    *,
    patch_path_used: bool,
) -> Dict[str, Any]:
    spans: list[Dict[str, str]] = []
    for item in list(flagged_spans or [])[:6]:
        if not isinstance(item, Mapping):
            continue
        spans.append(
            {
                "issue_type": str(item.get("issue_type") or "").strip(),
                "section_heading": _clean_inline_text(item.get("section_heading") or "", limit=100),
                "sentence_window": str(item.get("sentence_window") or "").strip(),
            }
        )
    return {
        "patch_path_used": bool(patch_path_used),
        "flagged_span_count": len(list(flagged_spans or [])),
        "flagged_issue_types": _flagged_issue_types(flagged_spans),
        "anchors": spans,
    }


def _draft_observation_summary(
    draft: DraftSections | None,
    diagnostics: Mapping[str, Any] | None = None,
    editor_report: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    diagnostics = diagnostics or {}
    sections = _extract_revision_sections(draft.body if draft is not None else "")
    section_excerpts = [
        {
            "heading": _clean_inline_text(heading, limit=100),
            "excerpt": _clean_inline_text(body, limit=260),
        }
        for heading, body in sections[:6]
    ]
    return {
        "title": _clean_inline_text(draft.title if draft is not None else "", limit=120),
        "lead_excerpt": _clean_inline_text(draft.lead if draft is not None else "", limit=260),
        "body_chars": _compact_text_len(draft.body if draft is not None else ""),
        "heading_count": len(sections),
        "headings": [_clean_inline_text(heading, limit=100) for heading, _body in sections[:8]],
        "section_excerpts": section_excerpts,
        "final_paragraph_excerpt": _failure_candidate_final_paragraph_excerpt(draft),
        "repair_trigger_score": _safe_float_metric(diagnostics.get("repair_trigger_score")),
        "soft_warnings": [
            str(item or "").strip()
            for item in list(diagnostics.get("soft_warnings") or [])[:12]
            if str(item or "").strip()
        ],
        "ending_bucket_max_run": int(diagnostics.get("ending_bucket_max_run", 0) or 0),
        "fingerprint": _fingerprint_guard_observation(editor_report),
    }


def _company_intro_source_slot_coverage_observation(
    contract: Mapping[str, Any],
    diagnostics: Mapping[str, Any],
    source_pack: Mapping[str, Any],
) -> Dict[str, Any]:
    validation = dict(diagnostics.get("company_introduction_source_contract_validation") or {})
    private_contract = dict(contract.get("_company_introduction_source_contract") or {})
    public_contract = dict(contract.get("company_introduction_source_contract") or {})
    slots = dict(private_contract.get("slots") or {})
    required_slots = list(validation.get("required_slots") or _COMPANY_INTRO_REQUIRED_SOURCE_SLOTS)
    optional_slots = list(validation.get("optional_slots") or ["proof_signal"])
    guard_only_slots = list(validation.get("guard_only_slots") or ["source_limit"])
    source_presence = dict(validation.get("source_slot_presence") or {})
    if not source_presence:
        source_presence = {
            slot: bool(str(slots.get(slot) or public_contract.get(slot) or "").strip())
            for slot in _COMPANY_INTRO_SOURCE_SLOTS
        }
    slot_lengths = {
        slot: _compact_text_len(slots.get(slot) or public_contract.get(slot) or "")
        for slot in _COMPANY_INTRO_SOURCE_SLOTS
    }
    slot_excerpts = {
        slot: _clean_inline_text(slots.get(slot) or public_contract.get(slot) or "", limit=160)
        for slot in [*required_slots, *optional_slots]
        if slot != "source_limit" and str(slots.get(slot) or public_contract.get(slot) or "").strip()
    }
    script_packet = dict(contract.get("_company_introduction_script_packet") or {})
    return {
        "checked": bool(validation.get("checked") or private_contract),
        "scope_match": bool(validation.get("scope_match") or private_contract.get("scope_match")),
        "pattern": str(validation.get("pattern") or private_contract.get("pattern") or ""),
        "source_document_count": len(list(source_pack.get("source_documents") or [])),
        "required_slots": required_slots,
        "optional_slots": optional_slots,
        "guard_only_slots": guard_only_slots,
        "source_slot_presence": source_presence,
        "visible_slot_presence": dict(validation.get("slot_presence") or {}),
        "missing_required_slots": list(validation.get("missing_required_slots") or []),
        "unbacked_required_slots": list(validation.get("unbacked_required_slots") or []),
        "slot_text_lengths": slot_lengths,
        "slot_text_excerpts": slot_excerpts,
        "source_limit_present": bool(source_presence.get("source_limit") or slot_lengths.get("source_limit")),
        "script_packet_statuses": dict(validation.get("script_packet_statuses") or {}),
        "script_packet_quote_counts": {
            unit: len(list(dict(script_packet.get(unit) or {}).get("quotes") or []))
            for unit, _slot in _COMPANY_INTRO_SCRIPT_UNITS
        },
    }


def _company_intro_quality_observability(
    contract: Mapping[str, Any],
    source_pack: Mapping[str, Any],
    *,
    first_draft: DraftSections | None,
    final_draft: DraftSections | None,
    pre_repair_diagnostics: Mapping[str, Any],
    final_diagnostics: Mapping[str, Any],
    pre_repair_editor_report: Mapping[str, Any],
    final_editor_report: Mapping[str, Any],
    repair_metadata: Mapping[str, Any],
    repair_applied: bool,
) -> Dict[str, Any]:
    active = _company_intro_source_contract_scope_active(contract)
    repair_rejected = bool(repair_metadata) and not bool(repair_applied) and not bool(
        repair_metadata.get("skip_reason")
    )
    patch_scope = dict(repair_metadata.get("patch_scope") or {})
    if not patch_scope:
        patch_scope = _patch_scope_observation(
            pre_repair_diagnostics.get("flagged_spans") or [],
            patch_path_used=bool(repair_metadata.get("patch_path_used")),
        )
    patch_scope.update(
        {
            "scope_preserved": bool(repair_metadata.get("scope_preserved")),
            "effective_scope_preserved": bool(repair_metadata.get("effective_scope_preserved")),
            "alignment_preserved": bool(repair_metadata.get("alignment_preserved")),
            "effective_alignment_preserved": bool(repair_metadata.get("effective_alignment_preserved")),
            "scope_rejection_reason": str(repair_metadata.get("scope_rejection_reason") or ""),
        }
    )
    return {
        "active": bool(active),
        "route_key": (
            "branding/company_introduction" if active else ""
        ),
        "source_slot_coverage_before": _company_intro_source_slot_coverage_observation(
            contract,
            pre_repair_diagnostics,
            source_pack,
        ),
        "source_slot_coverage_final": _company_intro_source_slot_coverage_observation(
            contract,
            final_diagnostics,
            source_pack,
        ),
        "first_output_summary": _draft_observation_summary(
            first_draft,
            pre_repair_diagnostics,
            pre_repair_editor_report,
        ),
        "final_output_summary": _draft_observation_summary(
            final_draft,
            final_diagnostics,
            final_editor_report,
        ),
        "repair": {
            "repair_required": bool(pre_repair_diagnostics.get("repair_required")),
            "repair_applied": bool(repair_applied),
            "repair_rejected": repair_rejected,
            "skip_reason": str(repair_metadata.get("skip_reason") or ""),
            "acceptance_rejection_reason": str(
                repair_metadata.get("acceptance_rejection_reason") or ""
            ),
            "acceptance_path": str(repair_metadata.get("acceptance_path") or ""),
            "patch_path_available": bool(repair_metadata.get("patch_path_available")),
            "patch_path_used": bool(repair_metadata.get("patch_path_used")),
            "patch_scope": patch_scope,
            "fingerprint_before": dict(
                repair_metadata.get("fingerprint_before")
                or _fingerprint_guard_observation(pre_repair_editor_report)
            ),
            "fingerprint_after": dict(
                repair_metadata.get("fingerprint_after")
                or _fingerprint_guard_observation(final_editor_report)
            ),
            "company_intro_fingerprint_guard_active": bool(
                repair_metadata.get("company_intro_fingerprint_guard_active")
            ),
            "company_intro_fingerprint_improved": bool(
                repair_metadata.get("company_intro_fingerprint_improved")
            ),
            "company_intro_naturalness_rescue_active": bool(
                repair_metadata.get("company_intro_naturalness_rescue_active")
            ),
            "company_intro_naturalness_improved": bool(
                repair_metadata.get("company_intro_naturalness_improved")
            ),
            "source_contract_before_validation": dict(
                repair_metadata.get("company_introduction_source_contract_before_validation") or {}
            ),
            "source_contract_after_validation": dict(
                repair_metadata.get("company_introduction_source_contract_after_validation") or {}
            ),
            "repair_candidate_summary": dict(
                repair_metadata.get("repair_candidate_summary") or {}
            ),
            "repair_candidate_source_slot_coverage": dict(
                repair_metadata.get("repair_candidate_source_slot_coverage") or {}
            ),
        },
    }


def _build_failure_candidate_summary(
    draft: DraftSections | None,
    diagnostics: Mapping[str, Any],
    hidden_validation: Mapping[str, Any],
) -> Dict[str, Any]:
    sections = _extract_revision_sections(draft.body if draft is not None else "")
    first_heading = sections[0][0] if sections else ""
    first_section_body = sections[0][1] if sections else ""
    late_heading = sections[-1][0] if sections else ""
    return {
        "title": _clean_inline_text(draft.title if draft is not None else "", limit=120),
        "body_excerpt": _clean_inline_text(draft.body if draft is not None else "", limit=1800),
        "first_heading": _clean_inline_text(first_heading, limit=120),
        "first_section_excerpt": _clean_inline_text(first_section_body, limit=220),
        "late_heading": _clean_inline_text(late_heading, limit=120),
        "final_paragraph_excerpt": _failure_candidate_final_paragraph_excerpt(draft),
        "ending_bucket_max_run": int(diagnostics.get("ending_bucket_max_run", 0) or 0),
        "hidden_late_validation_failure_count": _hidden_late_validation_failure_count(hidden_validation),
        "visible_forbidden_heading_hit_count": len(
            list(hidden_validation.get("visible_forbidden_heading_hits") or [])
        ),
    }


def _build_company_intro_failure_payload_diagnostics(
    diagnostics: Mapping[str, Any],
    draft: DraftSections | None,
    repair_metadata: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    hidden_validation = _build_hidden_late_validation_failure_snapshot(diagnostics)
    payload = {
        "hidden_late_validation": hidden_validation,
        "failure_candidate_summary": _build_failure_candidate_summary(
            draft,
            diagnostics,
            hidden_validation,
        ),
    }
    if repair_metadata:
        payload["company_introduction_source_contract_repair"] = (
            _build_company_intro_source_contract_repair_telemetry(repair_metadata)
        )
    return payload


def _build_company_intro_source_contract_repair_telemetry(
    repair_metadata: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "active": bool(repair_metadata.get("company_introduction_source_contract_active")),
        "cleared": bool(repair_metadata.get("company_introduction_source_contract_cleared")),
        "improved": bool(repair_metadata.get("company_introduction_source_contract_improved")),
        "before_failure_count": int(
            repair_metadata.get("company_introduction_source_contract_before_failure_count") or 0
        ),
        "after_failure_count": int(
            repair_metadata.get("company_introduction_source_contract_after_failure_count") or 0
        ),
        "unsupported_clear": bool(repair_metadata.get("company_introduction_unsupported_clear")),
        "source_limit_clear": bool(repair_metadata.get("company_introduction_source_limit_clear")),
        "hidden_late_after_trigger_ids": list(
            repair_metadata.get("hidden_late_validation_after_trigger_ids") or []
        ),
        "before_validation": dict(
            repair_metadata.get("company_introduction_source_contract_before_validation") or {}
        ),
        "after_validation": dict(
            repair_metadata.get("company_introduction_source_contract_after_validation") or {}
        ),
        "acceptance_rejection_reason": str(
            repair_metadata.get("acceptance_rejection_reason") or ""
        ),
        "scope_rejection_reason": str(repair_metadata.get("scope_rejection_reason") or ""),
        "patch_scope": dict(repair_metadata.get("patch_scope") or {}),
        "fingerprint_before": dict(repair_metadata.get("fingerprint_before") or {}),
        "fingerprint_after": dict(repair_metadata.get("fingerprint_after") or {}),
        "repair_candidate_summary": dict(repair_metadata.get("repair_candidate_summary") or {}),
        "repair_candidate_source_slot_coverage": dict(
            repair_metadata.get("repair_candidate_source_slot_coverage") or {}
        ),
    }


def _build_company_intro_naturalness_unresolved_telemetry(
    diagnostics: Mapping[str, Any],
    repair_metadata: Mapping[str, Any],
    *,
    repair_applied: bool,
    draft: DraftSections | None = None,
) -> Dict[str, Any]:
    enrichment = dict(diagnostics.get("company_intro_naturalness_enrichment") or {})
    telemetry = {
        "rescue_active": True,
        "repair_applied": bool(repair_applied),
        "company_intro_naturalness_improved": bool(
            repair_metadata.get("company_intro_naturalness_improved")
        ),
        "acceptance_rejection_reason": str(
            repair_metadata.get("acceptance_rejection_reason") or ""
        ),
        "patch_path_used": bool(repair_metadata.get("patch_path_used")),
        "flagged_issue_types": list(repair_metadata.get("flagged_issue_types") or []),
        "output_contract_parse_mode": str(
            repair_metadata.get("output_contract_parse_mode") or ""
        ),
        "output_contract_complete_article": bool(
            repair_metadata.get("output_contract_complete_article")
        ),
        "repair_trigger_score": float(diagnostics.get("repair_trigger_score") or 0.0),
        "soft_warnings": list(diagnostics.get("soft_warnings") or []),
        "signals": dict(enrichment.get("signals") or {}),
        "company_introduction_source_contract_repair": (
            _build_company_intro_source_contract_repair_telemetry(repair_metadata)
        ),
    }
    telemetry.update(_build_company_intro_failure_payload_diagnostics(diagnostics, draft, repair_metadata))
    return telemetry


def _apply_company_intro_current_business_echo_guard(
    contract: Mapping[str, Any],
    draft: DraftSections,
) -> DraftSections:
    if not _company_intro_source_contract_scope_active(contract):
        return draft
    private_contract = dict(contract.get("_company_introduction_source_contract") or {})
    slots = dict(private_contract.get("slots") or {})
    public_contract = dict(contract.get("company_introduction_source_contract") or {})
    current_business = _clean_inline_text(
        slots.get("current_business") or public_contract.get("current_business") or "",
        limit=180,
    )
    if not current_business:
        return draft
    sections = _split_heading_sections(draft.body)
    if not sections:
        return draft
    first_heading = str(sections[0].get("heading") or "").strip()
    if not first_heading:
        return draft
    first_section_body = _section_body_after_heading(draft.body, first_heading)
    sentences = _split_japanese_sentences(first_section_body)
    if not sentences:
        return draft
    first_sentence = sentences[0]
    echo_hits = detect_prompt_echo_sentences(
        first_sentence,
        references=[current_business],
        max_hits=1,
        reference_coverage=0.74,
    )
    if not echo_hits:
        return draft
    paraphrase = _build_company_intro_current_business_paraphrase(current_business)
    if not paraphrase or paraphrase == first_sentence:
        return draft
    rebuilt_section_body = " ".join([paraphrase, *sentences[1:]]).strip()
    rebuilt_body = _replace_section_body_after_heading(draft.body, first_heading, rebuilt_section_body)
    if rebuilt_body == str(draft.body or "").strip():
        return draft
    return DraftSections(
        title=draft.title,
        lead=draft.lead,
        body=rebuilt_body,
        hashtags=draft.hashtags,
    )


def _normalize_draft(contract: Mapping[str, Any], draft: DraftSections) -> DraftSections:
    article_type = str(contract.get("article_type") or "").strip().lower()
    preprocessed_draft = DraftSections(
        title=draft.title,
        lead=draft.lead,
        body=_normalize_section_wrappers(draft.body),
        hashtags=draft.hashtags,
    )
    normalized_draft, note_rule_check = finalize_note_draft(preprocessed_draft, title_hint=resolve_title_hint(contract))
    if not note_rule_check.passed:
        raise PipelineRuntimeError(
            f"Note rule check failed: {', '.join(note_rule_check.failures)}",
            error_codes.SYS_PIPELINE_FAILURE,
    )
    normalized_draft = _apply_tone_profile_opening_shape(contract, normalized_draft)
    normalized_draft = _apply_daily_story_title_shape(contract, normalized_draft)
    normalized_draft = _apply_empty_aiish_phrase_guard(normalized_draft)
    normalized_draft = _apply_company_intro_current_business_echo_guard(contract, normalized_draft)
    hashtags = normalize_hashtags(
        normalized_draft.hashtags,
        fallback_terms=[
            normalized_draft.title,
            contract.get("semantic_article_key") or article_type,
            *(contract.get("comparison_axes") or []),
            *(contract.get("must_cover") or []),
        ],
    )
    return DraftSections(
        title=normalized_draft.title or resolve_title_hint(contract),
        lead=normalized_draft.lead,
        body=normalized_draft.body,
        hashtags=hashtags,
    )


def _require_visible_draft(draft: DraftSections) -> None:
    if _draft_has_visible_content(draft):
        return
    raise PipelineRuntimeError("Generated draft is empty", error_codes.SYS_PIPELINE_FAILURE)


def _apply_editor_guard_to_draft(contract: Mapping[str, Any], draft: DraftSections) -> tuple[DraftSections, Dict[str, Any]]:
    guarded_lead, lead_report = apply_minimal_editor_guard(draft.lead)
    guarded_body, body_report = apply_minimal_editor_guard(draft.body)
    repair_actions = []
    warnings: list[str] = []
    for report in (lead_report, body_report):
        repair_actions.extend(
            {
                "kind": action.kind,
                "sentence_index": int(action.sentence_index),
                "before_excerpt": action.before_excerpt,
                "after_excerpt": action.after_excerpt,
                "applied": bool(action.applied),
            }
            for action in list(report.repair_actions or [])
        )
        for warning in list(report.warnings or []):
            text = str(warning or "").strip()
            if text and text not in warnings:
                warnings.append(text)
    guarded_draft = _normalize_draft(
        contract,
        DraftSections(
            title=draft.title,
            lead=guarded_lead,
            body=guarded_body,
            hashtags=draft.hashtags,
        ),
    )
    editor_report = {
        "ai_phrase_replaced_count": int(lead_report.ai_phrase_replaced_count + body_report.ai_phrase_replaced_count),
        "legal_softened_count": int(lead_report.legal_softened_count + body_report.legal_softened_count),
        "duplicate_line_removed_count": int(
            lead_report.duplicate_line_removed_count + body_report.duplicate_line_removed_count
        ),
        "grammar_repair_count": int(lead_report.grammar_repair_count + body_report.grammar_repair_count),
        "sentence_integrity_repair_count": int(
            lead_report.sentence_integrity_repair_count + body_report.sentence_integrity_repair_count
        ),
        "sentence_integrity_warning_count": int(
            lead_report.sentence_integrity_warning_count + body_report.sentence_integrity_warning_count
        ),
        "repair_actions": repair_actions[:12],
        "warnings": warnings[:8],
    }
    return guarded_draft, editor_report


def _resolve_fingerprint_focus(contract: Mapping[str, Any]) -> str:
    writing_focus = str(contract.get("writing_focus") or "").strip().lower()
    if writing_focus in {"explanation", "analysis"}:
        return writing_focus
    article_type = str(contract.get("article_type") or "").strip().lower()
    if article_type == "explanatory_article":
        return "explanation"
    if article_type in {"industry_analysis", "comparative_review"}:
        return "analysis"
    return ""


def _apply_fingerprint_guard_to_draft(
    contract: Mapping[str, Any],
    draft: DraftSections,
) -> tuple[DraftSections, Dict[str, Any]]:
    fingerprint_report = {
        "checked": False,
        "focus": _resolve_fingerprint_focus(contract),
        "flat_zone_flags": [],
        "correction_hints": [],
        "overall_unpredictability": 0.0,
        "subject_explicit_rate": 0.0,
        "conjunction_repetition_rate": 0.0,
        "sentence_opening_entropy": 0.0,
        "comma_position_cv": 0.0,
        "correction_applied": False,
        "applied_rules": [],
        "rewrite_ratio": 0.0,
        "discarded": False,
        "discard_reason": "",
        "error": "",
    }
    body_text = str(draft.body or "").strip()
    if len(body_text) < 100:
        return draft, fingerprint_report

    try:
        analyzer = FingerprintAnalyzer()
        analyzed = analyzer.analyze(body_text, focus=fingerprint_report["focus"])
        fingerprint_report.update(
            {
                "checked": True,
                "flat_zone_flags": list(getattr(analyzed, "flat_zone_flags", []) or []),
                "correction_hints": list(getattr(analyzed, "correction_hints", []) or [])[:8],
                "overall_unpredictability": round(float(getattr(analyzed, "overall_unpredictability", 0.0) or 0.0), 4),
                "subject_explicit_rate": round(float(getattr(analyzed, "subject_explicit_rate", 0.0) or 0.0), 4),
                "conjunction_repetition_rate": round(
                    float(getattr(analyzed, "conjunction_repetition_rate", 0.0) or 0.0),
                    4,
                ),
                "sentence_opening_entropy": round(float(getattr(analyzed, "sentence_opening_entropy", 0.0) or 0.0), 4),
                "comma_position_cv": round(float(getattr(analyzed, "comma_position_cv", 0.0) or 0.0), 4),
            }
        )
    except Exception as exc:  # pragma: no cover - defensive fallback
        fingerprint_report["error"] = f"analyze_failed:{exc}"
        return draft, fingerprint_report

    if not fingerprint_report["flat_zone_flags"]:
        return draft, fingerprint_report

    try:
        correction = apply_fingerprint_corrections(body_text, analyzed)
        fingerprint_report.update(
            {
                "applied_rules": list(getattr(correction, "applied_rules", []) or []),
                "rewrite_ratio": round(float(getattr(correction, "rewrite_ratio", 0.0) or 0.0), 4),
                "discarded": bool(getattr(correction, "discarded", False)),
                "discard_reason": str(getattr(correction, "discard_reason", "") or ""),
            }
        )
        corrected_body = str(getattr(correction, "text", body_text) or body_text)
        if fingerprint_report["discarded"] or not fingerprint_report["applied_rules"] or corrected_body == body_text:
            return draft, fingerprint_report
        guarded_draft = _normalize_draft(
            contract,
            DraftSections(
                title=draft.title,
                lead=draft.lead,
                body=corrected_body,
                hashtags=draft.hashtags,
            ),
        )
        fingerprint_report["correction_applied"] = True
        return guarded_draft, fingerprint_report
    except Exception as exc:  # pragma: no cover - defensive fallback
        fingerprint_report["error"] = f"correction_failed:{exc}"
        return draft, fingerprint_report


def _apply_surface_guards_to_draft(contract: Mapping[str, Any], draft: DraftSections) -> tuple[DraftSections, Dict[str, Any]]:
    guarded_draft, editor_report = _apply_editor_guard_to_draft(contract, draft)
    guarded_draft, fingerprint_report = _apply_fingerprint_guard_to_draft(contract, guarded_draft)
    normalized_editor_report = dict(editor_report)
    normalized_editor_report["fingerprint_guard"] = fingerprint_report
    return guarded_draft, normalized_editor_report


class MinimalPipeline:
    """Simple single-pass pipeline compatible with current UI/runtime."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.llm_client = llm_client
        self.reset_generation_progress()

    def reset_generation_progress(self) -> None:
        self._generation_progress = {"stage": "", "percent": 0, "detail": "", "partial_body": ""}

    def get_generation_progress(self) -> Dict[str, Any]:
        return dict(self._generation_progress)

    def _set_generation_progress(self, stage: str, percent: int, *, detail: str = "", partial_body: str = "") -> None:
        self._generation_progress = {
            "stage": str(stage or "").strip(),
            "percent": max(0, min(100, int(percent))),
            "detail": str(detail or "").strip(),
            "partial_body": str(partial_body or ""),
        }

    def _call_llm(
        self,
        prompt: str,
        *,
        article_type: str,
        max_tokens: int,
        task_type: str = "section",
        verbosity: str = "high",
    ) -> tuple[str, Dict[str, Any]]:
        if self.llm_client is None:
            raise PipelineRuntimeError("LLM client is required", error_codes.SYS_LLM_CLIENT_REQUIRED)
        text = self.llm_client.generate_text(
            prompt,
            max_tokens=max_tokens,
            task_type=task_type,
            article_type=article_type,
            verbosity=verbosity,
        )
        return text, dict(self.llm_client.get_last_call_metadata())

    def _generate_single_pass_draft(
        self,
        contract: Mapping[str, Any],
        source_pack: Mapping[str, Any],
        *,
        article_type: str,
        compact_plan: list[Dict[str, str]],
        max_tokens: int,
    ) -> tuple[DraftSections, Dict[str, Any]]:
        prompt = build_generation_prompt_from_contract(contract, source_pack, compact_plan=compact_plan)
        raw_text, llm_metadata = self._call_llm(prompt, article_type=article_type, max_tokens=max_tokens)
        draft = _normalize_draft(contract, parse_tagged_output(raw_text))
        if _draft_has_visible_content(draft):
            return draft, llm_metadata

        self._set_generation_progress("single_pass_generation", 56, detail="出力を再確認しています。")
        raw_text, llm_metadata = self._call_llm(prompt, article_type=article_type, max_tokens=max_tokens)
        draft = _normalize_draft(contract, parse_tagged_output(raw_text))
        return draft, llm_metadata

    @staticmethod
    def _compact_plan_scaffold_enabled(contract: Mapping[str, Any]) -> bool:
        if bool(contract.get("_compact_plan_scaffold")):
            return True
        return _compact_plan_safe_scope(contract)

    def _maybe_build_compact_plan(
        self,
        contract: Mapping[str, Any],
        source_pack: Mapping[str, Any],
    ) -> list[Dict[str, str]]:
        if not self._compact_plan_scaffold_enabled(contract):
            return []
        article_type = str(contract.get("article_type") or "explanatory_article").strip().lower()
        semantic_key = str(contract.get("semantic_article_key") or "").strip().lower()
        length_mode = str(contract.get("length_mode") or "")
        self._set_generation_progress("compact_plan", 18, detail="構成の下書きを整理しています。")
        try:
            prompt = build_compact_plan_prompt_from_contract(contract, source_pack)
            raw_plan, _ = self._call_llm(
                prompt,
                article_type=article_type,
                max_tokens=1200,
                task_type="outline",
                verbosity="medium",
            )
        except Exception:
            return []
        return parse_compact_plan_output(
            raw_plan,
            max_sections=heading_target(length_mode, article_type, semantic_key),
        )

    def _generate_with_experimental_prompt_stack(
        self,
        contract: Mapping[str, Any],
        source_pack: Mapping[str, Any],
        *,
        article_type: str,
        max_tokens: int,
    ) -> tuple[DraftSections, Dict[str, Any], Dict[str, Any]]:
        stack = build_experimental_prompt_stack_from_contract(contract, source_pack)
        stage_summary: Dict[str, Any] = {
            "enabled": True,
            "experiment": _EXPERIMENTAL_PROMPT_STACK,
            "used_fallback_generation": False,
            "fallback_reason": "",
            "stages_completed": [],
            "script_section_count": 0,
            "planner_section_count": 0,
            "script_snapshot": {},
            "planner_snapshot": {},
            "source_packet_snapshot": {},
            "article_contract_snapshot": {},
            "writer_used_fact_ids": [],
            "suffix_edit_window": {},
            "audit_result": {},
            "visibility_summary": {},
            "stage_calls": {},
            "support_parse_summary": {},
        }

        support_raw, support_metadata = self._call_llm(
            stack["support"]["prompt"],
            article_type=article_type,
            max_tokens=1400,
            task_type="outline",
            verbosity="medium",
        )
        stage_summary["stage_calls"]["support"] = support_metadata
        support_script, support_parse_summary = _parse_support_script(support_raw, contract)
        stage_summary["support_parse_summary"] = support_parse_summary
        if not support_script.get("section_briefs"):
            stage_summary["fallback_reason"] = "support_parse_failed"
            raise ExperimentalPromptStackStageError(
                "support_parse_failed",
                stage_summary=stage_summary,
            )
        stage_summary["stages_completed"].append("support")
        stage_summary["script_section_count"] = len(list(support_script.get("section_briefs") or []))
        stage_summary["script_snapshot"] = _snapshot_support_script(support_script)
        stage_summary["source_packet_snapshot"] = dict(stage_summary["script_snapshot"])

        planner_prompt = _render_stage_prompt(stack["planner"]["prompt"], script_json=support_script)
        planner_raw, planner_metadata = self._call_llm(
            planner_prompt,
            article_type=article_type,
            max_tokens=1400,
            task_type="outline",
            verbosity="medium",
        )
        stage_summary["stage_calls"]["planner"] = planner_metadata
        planner_json = _normalize_planner_output(_extract_json_object(planner_raw))
        if not planner_json.get("heading_candidates") and not planner_json.get("claim_core"):
            raise ValueError("planner_parse_failed")
        stage_summary["stages_completed"].append("planner")
        stage_summary["planner_section_count"] = len(list(planner_json.get("heading_candidates") or []))
        stage_summary["planner_snapshot"] = _snapshot_planner_output(planner_json)
        stage_summary["article_contract_snapshot"] = dict(stage_summary["planner_snapshot"])

        writer_prompt = _render_stage_prompt(
            stack["writer"]["prompt"],
            script_json=support_script,
            planner_json=planner_json,
        )
        writer_raw, writer_metadata = self._call_llm(
            writer_prompt,
            article_type=article_type,
            max_tokens=max_tokens,
            task_type="section",
            verbosity="medium",
        )
        writer_draft = _normalize_draft(contract, parse_tagged_output(writer_raw))
        stage_summary["stage_calls"]["writer"] = writer_metadata
        stage_summary["stages_completed"].append("writer")
        writer_used_fact_ids = _extract_used_fact_ids(writer_raw)
        stage_summary["writer_used_fact_ids"] = list(writer_used_fact_ids)

        suffix_window = _build_suffix_edit_window(
            writer_draft.body,
            start_ratio=float(planner_json.get("edit_start_ratio", 0.7) or 0.7),
        )
        stage_summary["suffix_edit_window"] = {
            "basis": str(suffix_window.get("basis") or ""),
            "split_ratio": float(suffix_window.get("split_ratio", 0.7) or 0.7),
            "keep_prefix_chars": _compact_text_len(suffix_window.get("keep_prefix") or ""),
            "edit_target_chars": _compact_text_len(suffix_window.get("edit_target_suffix") or ""),
        }
        editor_prompt = _render_stage_prompt(
            stack["editor"]["prompt"],
            script_json=support_script,
            planner_json=planner_json,
            keep_prefix=str(suffix_window.get("keep_prefix") or ""),
            edit_target_suffix=str(suffix_window.get("edit_target_suffix") or ""),
        )
        editor_raw, editor_metadata = self._call_llm(
            editor_prompt,
            article_type=article_type,
            max_tokens=max_tokens,
            task_type="editor_review",
            verbosity="medium",
        )
        suffix_edit = _normalize_suffix_edit_output(
            editor_raw,
            str(suffix_window.get("edit_target_suffix") or ""),
        )
        editor_body = _compose_suffix_edited_body(
            str(suffix_window.get("keep_prefix") or ""),
            str(suffix_edit.get("bridge_sentence") or ""),
            str(suffix_edit.get("revised_suffix") or ""),
        )
        editor_draft = _normalize_draft(
            contract,
            DraftSections(
                title=writer_draft.title,
                lead=writer_draft.lead,
                body=editor_body or writer_draft.body,
                hashtags=writer_draft.hashtags,
            ),
        )
        stage_summary["stage_calls"]["editor"] = editor_metadata
        stage_summary["suffix_edit_window"]["bridge_sentence_present"] = bool(
            str(suffix_edit.get("bridge_sentence") or "").strip()
        )
        stage_summary["suffix_edit_window"]["edit_notes"] = list(suffix_edit.get("edit_notes") or [])
        if editor_draft.body:
            stage_summary["stages_completed"].append("editor")
        else:
            stage_summary["fallback_reason"] = "editor_parse_failed"
            editor_draft = writer_draft

        final_tagged_article = _compose_tagged_article_text(
            editor_draft,
            used_fact_ids=writer_used_fact_ids,
        )
        audit_prompt = _render_stage_prompt(
            stack["audit"]["prompt"],
            script_json=support_script,
            planner_json=planner_json,
            final_article=final_tagged_article,
            used_fact_ids=writer_used_fact_ids,
        )
        audit_raw, audit_metadata = self._call_llm(
            audit_prompt,
            article_type=article_type,
            max_tokens=1400,
            task_type="outline",
            verbosity="low",
        )
        stage_summary["stage_calls"]["audit"] = audit_metadata
        audit_result = _normalize_audit_result(audit_raw)
        stage_summary["audit_result"] = audit_result
        if audit_result.get("overall_judgement"):
            stage_summary["stages_completed"].append("audit")
        stage_summary["visibility_summary"] = _build_experimental_prompt_stack_visibility_summary(stage_summary)

        return editor_draft, writer_metadata, stage_summary

    def _run_optional_repair(
        self,
        *,
        contract: Mapping[str, Any],
        draft: DraftSections,
        diagnostics: Dict[str, Any],
        editor_report: Dict[str, Any],
        compact_plan: list[Dict[str, str]],
        source_pack: Mapping[str, Any],
        article_type: str,
        max_tokens: int,
        controlled_realization: Mapping[str, Any],
    ) -> tuple[DraftSections, Dict[str, Any], Dict[str, Any], bool, Dict[str, Any], Dict[str, Any]]:
        repair_applied = False
        repair_metadata: Dict[str, Any] = {}
        final_controlled_realization = dict(controlled_realization)
        if not bool(diagnostics.get("repair_required")):
            return draft, diagnostics, editor_report, repair_applied, repair_metadata, final_controlled_realization

        flagged_spans = list(diagnostics.get("flagged_spans") or [])
        flagged_issue_types = {
            str(item.get("issue_type") or "").strip()
            for item in flagged_spans
            if str(item.get("issue_type") or "").strip()
        }
        announcement_validation = dict(diagnostics.get("announcement_source_contract_validation") or {})
        announcement_contract_trigger_ids = list(announcement_validation.get("repair_trigger_ids") or [])
        if (
            article_type == "announcement"
            and bool(announcement_validation.get("scope_match"))
            and not announcement_contract_trigger_ids
            and flagged_issue_types
            and flagged_issue_types.issubset({"ending_bucket_monotony"})
        ):
            repair_metadata = {
                "skip_reason": "announcement_contract_disallows_ending_monotony_retry",
                "patch_path_available": bool(flagged_spans),
                "patch_path_used": False,
                "flagged_span_count": len(flagged_spans),
                "flagged_issue_types": sorted(flagged_issue_types),
                "announcement_source_contract_active": False,
                "announcement_source_contract_improved": True,
                "announcement_source_contract_before_failure_count": _announcement_source_contract_failure_count(
                    announcement_validation
                ),
                "announcement_source_contract_after_failure_count": _announcement_source_contract_failure_count(
                    announcement_validation
                ),
                "announcement_unsupported_clear": True,
            }
            return draft, diagnostics, editor_report, repair_applied, repair_metadata, final_controlled_realization
        company_intro_validation = dict(diagnostics.get("company_introduction_source_contract_validation") or {})
        company_intro_contract_trigger_ids = list(company_intro_validation.get("repair_trigger_ids") or [])
        company_intro_hidden_late_validation = dict(diagnostics.get("hidden_late_validation") or {})
        company_intro_hidden_late_trigger_ids = list(
            company_intro_hidden_late_validation.get("repair_trigger_ids") or []
        )
        company_intro_naturalness_active = bool(
            dict(diagnostics.get("company_intro_naturalness_enrichment") or {}).get("activated")
        )
        company_intro_naturalness_only_issue_types = {
            "ending_bucket_monotony",
            "general_naturalness",
            "polish",
            "length_only",
            "preference_only_rewrite",
        }
        company_intro_operational_source_contract_present = bool(
            contract.get("company_introduction_source_contract")
        )
        if (
            article_type == "branding"
            and company_intro_operational_source_contract_present
            and bool(company_intro_validation.get("scope_match"))
            and not company_intro_contract_trigger_ids
            and not company_intro_hidden_late_trigger_ids
            and (
                (
                    not company_intro_naturalness_active
                    and flagged_issue_types
                    and flagged_issue_types.issubset({"ending_bucket_monotony"})
                )
                or (
                    company_intro_naturalness_active
                    and (
                        not flagged_issue_types
                        or flagged_issue_types.issubset(company_intro_naturalness_only_issue_types)
                    )
                )
            )
        ):
            skip_reason = (
                "company_introduction_contract_disallows_ending_monotony_retry"
                if flagged_issue_types and flagged_issue_types.issubset({"ending_bucket_monotony"})
                else "company_introduction_contract_disallows_naturalness_only_retry"
            )
            repair_metadata = {
                "skip_reason": skip_reason,
                "patch_path_available": bool(flagged_spans),
                "patch_path_used": False,
                "flagged_span_count": len(flagged_spans),
                "flagged_issue_types": sorted(flagged_issue_types),
                "company_intro_naturalness_rescue_active": company_intro_naturalness_active,
                "company_intro_naturalness_improved": False,
                "company_introduction_operational_source_contract_present": (
                    company_intro_operational_source_contract_present
                ),
                "company_introduction_source_contract_active": False,
                "company_introduction_source_contract_improved": True,
                "company_introduction_source_contract_before_failure_count": (
                    _company_intro_source_contract_failure_count(company_intro_validation)
                ),
                "company_introduction_source_contract_after_failure_count": (
                    _company_intro_source_contract_failure_count(company_intro_validation)
                ),
                "company_introduction_unsupported_clear": True,
                "company_introduction_source_limit_clear": True,
            }
            return draft, diagnostics, editor_report, repair_applied, repair_metadata, final_controlled_realization
        branding_validation = dict(diagnostics.get("branding_source_contract_validation") or {})
        branding_contract_trigger_ids = list(branding_validation.get("repair_trigger_ids") or [])
        if (
            article_type == "branding"
            and bool(branding_validation.get("scope_match"))
            and not branding_contract_trigger_ids
            and flagged_issue_types
            and flagged_issue_types.issubset({"ending_bucket_monotony"})
        ):
            repair_metadata = {
                "skip_reason": "branding_contract_disallows_ending_monotony_retry",
                "patch_path_available": bool(flagged_spans),
                "patch_path_used": False,
                "flagged_span_count": len(flagged_spans),
                "flagged_issue_types": sorted(flagged_issue_types),
                "branding_source_contract_active": False,
                "branding_source_contract_improved": True,
                "branding_source_contract_before_failure_count": _branding_source_contract_failure_count(
                    branding_validation
                ),
                "branding_source_contract_after_failure_count": _branding_source_contract_failure_count(
                    branding_validation
                ),
                "branding_unsupported_clear": True,
            }
            return draft, diagnostics, editor_report, repair_applied, repair_metadata, final_controlled_realization
        comparative_validation = dict(diagnostics.get("comparative_review_source_contract_validation") or {})
        comparative_contract_trigger_ids = list(comparative_validation.get("repair_trigger_ids") or [])
        if (
            article_type == "comparative_review"
            and bool(comparative_validation.get("scope_match"))
            and not comparative_contract_trigger_ids
            and flagged_issue_types
            and flagged_issue_types.issubset({"ending_bucket_monotony"})
        ):
            repair_metadata = {
                "skip_reason": "comparative_review_contract_disallows_ending_monotony_retry",
                "patch_path_available": bool(flagged_spans),
                "patch_path_used": False,
                "flagged_span_count": len(flagged_spans),
                "flagged_issue_types": sorted(flagged_issue_types),
                "comparative_review_source_contract_active": False,
                "comparative_review_source_contract_improved": True,
                "comparative_review_source_contract_before_failure_count": (
                    _comparative_source_contract_failure_count(comparative_validation)
                ),
                "comparative_review_source_contract_after_failure_count": (
                    _comparative_source_contract_failure_count(comparative_validation)
                ),
                "comparative_review_unsupported_clear": True,
            }
            return draft, diagnostics, editor_report, repair_applied, repair_metadata, final_controlled_realization
        self._set_generation_progress("repair", 84, detail="不自然さを局所補修しています。")
        use_patch_path = _patch_scaffold_enabled(contract) or _patch_activation_enabled(contract, flagged_spans)
        repair_prompt = build_repair_prompt_from_diagnostics(
            contract,
            draft,
            diagnostics,
            compact_plan=compact_plan,
            flagged_spans=flagged_spans if use_patch_path else None,
        )
        repaired_raw, repair_metadata = self._call_llm(repair_prompt, article_type=article_type, max_tokens=max_tokens)
        repair_metadata.update(
            {
                "company_introduction_operational_source_contract_present": (
                    company_intro_operational_source_contract_present
                ),
                "company_introduction_source_contract_active": bool(
                    company_intro_validation.get("scope_match")
                )
                and bool(company_intro_contract_trigger_ids),
                "company_introduction_source_contract_before_failure_count": (
                    _company_intro_source_contract_failure_count(company_intro_validation)
                ),
                "company_introduction_source_contract_before_validation": (
                    _build_company_intro_source_contract_validation_snapshot(company_intro_validation)
                ),
                "patch_path_available": bool(flagged_spans),
                "patch_path_used": bool(use_patch_path),
                "patch_scope": _patch_scope_observation(
                    flagged_spans,
                    patch_path_used=bool(use_patch_path),
                ),
                "flagged_span_count": len(flagged_spans),
                "flagged_issue_types": [
                    str(item.get("issue_type") or "").strip()
                    for item in flagged_spans
                    if str(item.get("issue_type") or "").strip()
                ],
                "fingerprint_before": _fingerprint_guard_observation(editor_report),
                "compare_thin_section_headings": [
                    str(item.get("section_heading") or "").strip()
                    for item in flagged_spans
                    if str(item.get("issue_type") or "").strip() == "comparative_thin_section"
                    and str(item.get("section_heading") or "").strip()
                ],
                "controlled_realization_active": bool(controlled_realization.get("active")),
                "controlled_realization_drift_headings": list(controlled_realization.get("drift_headings") or []),
            }
        )
        flagged_headings = [
            _clean_inline_text(item.get("section_heading") or "", limit=80)
            for item in flagged_spans
            if _clean_inline_text(item.get("section_heading") or "", limit=80)
        ]
        repair_output_contract = inspect_tagged_output_contract(repaired_raw)
        repair_metadata["output_contract_parse_mode"] = str(repair_output_contract.parse_mode or "")
        repair_metadata["output_contract_complete_article"] = bool(repair_output_contract.complete_article)
        repair_metadata["output_contract_missing_sections"] = list(repair_output_contract.missing_sections or [])
        repair_metadata["output_contract_tag_names_seen"] = list(repair_output_contract.tag_names_seen or [])
        repair_candidate = _normalize_draft(contract, repair_output_contract.draft)
        repair_metadata["repair_candidate_summary"] = _draft_observation_summary(
            repair_candidate,
            {},
            {},
        )
        if (
            repair_output_contract.parse_mode == "plain_fallback"
            or not repair_output_contract.complete_article
        ):
            repair_metadata["acceptance_rejection_reason"] = "repair_output_contract_incomplete"
            return (
                draft,
                diagnostics,
                editor_report,
                repair_applied,
                repair_metadata,
                final_controlled_realization,
            )
        repaired = repair_candidate
        repaired, repaired_editor_report = _apply_surface_guards_to_draft(contract, repaired)
        repaired_diagnostics, repaired_controlled_realization = _refresh_diagnostics_state(
            contract,
            repaired,
            repaired_editor_report,
            compact_plan,
            source_pack,
        )
        repair_metadata["fingerprint_after"] = _fingerprint_guard_observation(repaired_editor_report)
        repair_metadata["repair_candidate_summary"] = _draft_observation_summary(
            repaired,
            repaired_diagnostics,
            repaired_editor_report,
        )
        if dict(repair_metadata.get("materialized_anchor_patch_reconstruction") or {}).get("applied"):
            repair_metadata["reconstructed_candidate_summary"] = dict(
                repair_metadata.get("repair_candidate_summary") or {}
            )
        scope_preserved = True
        if use_patch_path:
            scope_preserved = _repair_preserves_flagged_scope(draft, repaired, flagged_spans)
        repair_metadata["scope_preserved"] = scope_preserved
        alignment_preserved = _repair_preserves_alignment(diagnostics, repaired_diagnostics)
        local_monotony_scope_guard_active = _local_monotony_patch_scope_enabled(
            use_patch_path=use_patch_path,
            flagged_issue_types=flagged_issue_types,
        )
        ending_monotony_guard_active = local_monotony_scope_guard_active
        ending_monotony_improved = (
            _repair_improves_ending_monotony(diagnostics, repaired_diagnostics)
            if ending_monotony_guard_active
            else True
        )
        explanatory_longform_guard_active = (
            use_patch_path
            and article_type == "explanatory_article"
            and str(contract.get("length_mode") or "").strip().lower() in {"normal", "long"}
            and "explanatory_thin_section" in flagged_issue_types
        )
        explanatory_longform_improved = (
            _repair_improves_explanatory_longform(diagnostics, repaired_diagnostics)
            if explanatory_longform_guard_active
            else True
        )
        explanatory_fingerprint_guard_active = (
            use_patch_path
            and article_type == "explanatory_article"
            and _EXPLANATORY_FINGERPRINT_ISSUE_TYPE in flagged_issue_types
        )
        explanatory_fingerprint_improved = (
            _repair_improves_explanatory_fingerprint(diagnostics, repaired_diagnostics)
            if explanatory_fingerprint_guard_active
            else True
        )
        company_intro_fingerprint_guard_active = (
            use_patch_path
            and article_type == "branding"
            and str(contract.get("semantic_article_key") or "").strip().lower() == "company_introduction"
            and _COMPANY_INTRO_FINGERPRINT_ISSUE_TYPE in flagged_issue_types
        )
        company_intro_fingerprint_improved = (
            _repair_improves_company_intro_fingerprint(diagnostics, repaired_diagnostics)
            if company_intro_fingerprint_guard_active
            else True
        )
        local_monotony_scope_preserved = (
            local_monotony_scope_guard_active
            and not scope_preserved
            and _repair_preserves_local_monotony_scope(draft, repaired)
        )
        local_monotony_alignment_preserved = (
            local_monotony_scope_guard_active
            and not alignment_preserved
            and _repair_preserves_alignment(
                diagnostics,
                repaired_diagnostics,
                tolerance_by_key={
                    "must_cover_reflection_rate": 0.01,
                    "prompt_anchor_coverage": 0.15,
                    "section_focus_coverage": 0.15,
                },
            )
        )
        company_intro_local_patch_guard_active = (
            use_patch_path
            and article_type == "branding"
            and str(contract.get("semantic_article_key") or "").strip().lower() == "company_introduction"
            and bool(flagged_headings)
            and (
                flagged_issue_types.issubset({"shadow_section_drift", "heading_reanchor"})
                or (
                    _COMPANY_INTRO_FINGERPRINT_ISSUE_TYPE in flagged_issue_types
                    and flagged_issue_types.issubset(
                        {"ending_bucket_monotony", _COMPANY_INTRO_FINGERPRINT_ISSUE_TYPE}
                    )
                )
            )
        )
        local_patch_scope_preserved = (
            company_intro_local_patch_guard_active
            and not scope_preserved
            and _repair_preserves_local_patch_scope(
                draft,
                repaired,
                target_headings=flagged_headings,
                max_changed_headings=max(3, len(set(flagged_headings))),
            )
        )
        company_intro_patch_scope_decision = (
            evaluate_company_intro_patch_scope(
                contract=contract,
                current_draft=draft,
                repaired_draft=repaired,
                current_diagnostics=diagnostics,
                repaired_diagnostics=repaired_diagnostics,
                target_headings=flagged_headings,
                max_changed_headings=max(3, len(set(flagged_headings))),
            )
            if company_intro_local_patch_guard_active and not scope_preserved and not local_patch_scope_preserved
            else {"scope_match": False, "allowed": False, "reason": "not_evaluated"}
        )
        company_intro_patch_scope_preserved = bool(company_intro_patch_scope_decision.get("allowed"))
        local_patch_alignment_preserved = (
            company_intro_local_patch_guard_active
            and not alignment_preserved
            and _repair_preserves_alignment(
                diagnostics,
                repaired_diagnostics,
                tolerance_by_key={
                    "must_cover_reflection_rate": 0.01,
                    "prompt_anchor_coverage": 0.15,
                    "section_focus_coverage": 0.15,
                },
            )
        )
        effective_scope_preserved = (
            scope_preserved
            or local_monotony_scope_preserved
            or local_patch_scope_preserved
            or company_intro_patch_scope_preserved
        )
        effective_alignment_preserved = (
            alignment_preserved
            or local_monotony_alignment_preserved
            or local_patch_alignment_preserved
            or company_intro_patch_scope_preserved
        )
        scope_acceptance_path = ""
        if use_patch_path:
            if scope_preserved:
                scope_acceptance_path = "flagged_scope"
            elif local_monotony_scope_preserved:
                scope_acceptance_path = "local_monotony_scope"
            elif local_patch_scope_preserved:
                scope_acceptance_path = "local_patch_scope"
            elif company_intro_patch_scope_preserved:
                scope_acceptance_path = "company_intro_patch_scope"
        repair_metadata["alignment_preserved"] = alignment_preserved
        repair_metadata["effective_alignment_preserved"] = effective_alignment_preserved
        repair_metadata["ending_monotony_guard_active"] = ending_monotony_guard_active
        repair_metadata["ending_monotony_improved"] = ending_monotony_improved
        repair_metadata["explanatory_longform_guard_active"] = explanatory_longform_guard_active
        repair_metadata["explanatory_longform_improved"] = explanatory_longform_improved
        repair_metadata["explanatory_fingerprint_guard_active"] = explanatory_fingerprint_guard_active
        repair_metadata["explanatory_fingerprint_improved"] = explanatory_fingerprint_improved
        repair_metadata["company_intro_fingerprint_guard_active"] = company_intro_fingerprint_guard_active
        repair_metadata["company_intro_fingerprint_improved"] = company_intro_fingerprint_improved
        repair_metadata["local_monotony_scope_preserved"] = local_monotony_scope_preserved
        repair_metadata["company_intro_local_patch_guard_active"] = company_intro_local_patch_guard_active
        repair_metadata["local_patch_scope_preserved"] = local_patch_scope_preserved
        repair_metadata["company_intro_patch_scope_preserved"] = company_intro_patch_scope_preserved
        repair_metadata["company_intro_patch_scope_decision"] = dict(company_intro_patch_scope_decision)
        repair_metadata["local_patch_alignment_preserved"] = local_patch_alignment_preserved
        repair_metadata["effective_scope_preserved"] = effective_scope_preserved
        if scope_acceptance_path:
            repair_metadata["scope_acceptance_path"] = scope_acceptance_path
        if use_patch_path and not effective_scope_preserved:
            repair_metadata["scope_rejection_reason"] = "flagged_scope_drift"
        patch_scope = dict(repair_metadata.get("patch_scope") or {})
        patch_scope.update(
            {
                "scope_preserved": bool(scope_preserved),
                "local_monotony_scope_preserved": bool(local_monotony_scope_preserved),
                "local_patch_scope_preserved": bool(local_patch_scope_preserved),
                "company_intro_patch_scope_preserved": bool(company_intro_patch_scope_preserved),
                "company_intro_patch_scope_decision": dict(company_intro_patch_scope_decision),
                "effective_scope_preserved": bool(effective_scope_preserved),
                "alignment_preserved": bool(alignment_preserved),
                "local_patch_alignment_preserved": bool(local_patch_alignment_preserved),
                "effective_alignment_preserved": bool(effective_alignment_preserved),
                "scope_rejection_reason": str(repair_metadata.get("scope_rejection_reason") or ""),
                "scope_acceptance_path": str(repair_metadata.get("scope_acceptance_path") or ""),
            }
        )
        repair_metadata["patch_scope"] = patch_scope
        repair_trigger_improved = (
            float(repaired_diagnostics.get("repair_trigger_score", 1.0) or 1.0)
            <= float(diagnostics.get("repair_trigger_score", 0.0) or 0.0)
        )
        repair_metadata["repair_trigger_improved"] = repair_trigger_improved
        hidden_late_validation = dict(diagnostics.get("hidden_late_validation") or {})
        repaired_hidden_late_validation = dict(repaired_diagnostics.get("hidden_late_validation") or {})
        hidden_late_validation_active = bool(hidden_late_validation.get("scope_match")) and bool(
            hidden_late_validation.get("repair_trigger_ids")
        )
        hidden_late_validation_improved = (
            _hidden_late_validation_improved(hidden_late_validation, repaired_hidden_late_validation)
            if hidden_late_validation_active
            else True
        )
        hidden_late_forbidden_heading_clear = not bool(
            repaired_hidden_late_validation.get("visible_forbidden_heading_hits")
        )
        company_intro_repair_opener_evaluation = _evaluate_company_intro_visible_opener_drift(
            contract,
            repaired,
            compact_plan,
            repaired_diagnostics,
            repaired_controlled_realization,
        )
        company_intro_repair_opener_preserved = not bool(company_intro_repair_opener_evaluation.get("failed"))
        repair_metadata["hidden_late_validation_active"] = hidden_late_validation_active
        repair_metadata["hidden_late_validation_improved"] = bool(hidden_late_validation_improved)
        repair_metadata["hidden_late_validation_before_failure_count"] = _hidden_late_validation_failure_count(
            hidden_late_validation
        )
        repair_metadata["hidden_late_validation_after_failure_count"] = _hidden_late_validation_failure_count(
            repaired_hidden_late_validation
        )
        repair_metadata["hidden_late_validation_after_trigger_ids"] = list(
            repaired_hidden_late_validation.get("repair_trigger_ids") or []
        )
        repair_metadata["hidden_late_forbidden_heading_clear"] = hidden_late_forbidden_heading_clear
        repair_metadata["company_intro_repair_opener_preserved"] = company_intro_repair_opener_preserved
        company_intro_source_validation = dict(
            diagnostics.get("company_introduction_source_contract_validation") or {}
        )
        repaired_company_intro_source_validation = dict(
            repaired_diagnostics.get("company_introduction_source_contract_validation") or {}
        )
        company_intro_source_validation_active = bool(company_intro_source_validation.get("scope_match")) and bool(
            company_intro_source_validation.get("repair_trigger_ids")
        )
        company_intro_source_validation_improved = (
            _company_intro_source_contract_improved(
                company_intro_source_validation,
                repaired_company_intro_source_validation,
            )
            if company_intro_source_validation_active
            else True
        )
        company_intro_source_before_failure_count = _company_intro_source_contract_failure_count(
            company_intro_source_validation
        )
        company_intro_source_after_failure_count = _company_intro_source_contract_failure_count(
            repaired_company_intro_source_validation
        )
        company_intro_unsupported_clear = not bool(
            repaired_company_intro_source_validation.get("unsupported_claim_added")
        )
        company_intro_source_limit_clear = not bool(
            repaired_company_intro_source_validation.get("source_limit_visible_leakage")
        )
        repair_metadata["company_introduction_source_contract_active"] = company_intro_source_validation_active
        repair_metadata["company_introduction_source_contract_improved"] = bool(
            company_intro_source_validation_improved
        )
        repair_metadata["company_introduction_source_contract_before_failure_count"] = (
            company_intro_source_before_failure_count
        )
        repair_metadata["company_introduction_source_contract_after_failure_count"] = (
            company_intro_source_after_failure_count
        )
        repair_metadata["company_introduction_source_contract_before_validation"] = (
            _build_company_intro_source_contract_validation_snapshot(company_intro_source_validation)
        )
        repair_metadata["company_introduction_source_contract_after_validation"] = (
            _build_company_intro_source_contract_validation_snapshot(repaired_company_intro_source_validation)
        )
        repair_metadata["repair_candidate_source_slot_coverage"] = (
            _company_intro_source_slot_coverage_observation(
                contract,
                repaired_diagnostics,
                source_pack,
            )
        )
        repair_metadata["company_introduction_unsupported_clear"] = bool(company_intro_unsupported_clear)
        repair_metadata["company_introduction_source_limit_clear"] = bool(company_intro_source_limit_clear)
        company_intro_operational_source_contract_present = bool(
            contract.get("company_introduction_source_contract")
        )
        repair_metadata["company_introduction_operational_source_contract_present"] = (
            company_intro_operational_source_contract_present
        )
        company_intro_source_contract_cleared = bool(
            company_intro_operational_source_contract_present
            and company_intro_source_validation_active
            and company_intro_source_validation_improved
            and company_intro_source_after_failure_count == 0
            and company_intro_unsupported_clear
            and company_intro_source_limit_clear
            and not list(repaired_hidden_late_validation.get("repair_trigger_ids") or [])
        )
        repair_metadata["company_introduction_source_contract_cleared"] = (
            company_intro_source_contract_cleared
        )
        if company_intro_source_contract_cleared:
            repair_metadata.pop("scope_rejection_reason", None)
        case_study_validation = dict(diagnostics.get("case_study_source_contract_validation") or {})
        repaired_case_study_validation = dict(
            repaired_diagnostics.get("case_study_source_contract_validation") or {}
        )
        case_study_validation_active = bool(case_study_validation.get("scope_match")) and bool(
            case_study_validation.get("repair_trigger_ids")
        )
        case_study_validation_improved = (
            _case_study_source_contract_improved(case_study_validation, repaired_case_study_validation)
            if case_study_validation_active
            else True
        )
        case_study_unsupported_clear = not bool(
            repaired_case_study_validation.get("unsupported_metric_added")
            or repaired_case_study_validation.get("unsupported_customer_or_award_added")
        )
        repair_metadata["case_study_source_contract_active"] = case_study_validation_active
        repair_metadata["case_study_source_contract_improved"] = bool(case_study_validation_improved)
        repair_metadata["case_study_source_contract_before_failure_count"] = (
            _case_study_source_contract_failure_count(case_study_validation)
        )
        repair_metadata["case_study_source_contract_after_failure_count"] = (
            _case_study_source_contract_failure_count(repaired_case_study_validation)
        )
        repair_metadata["case_study_unsupported_clear"] = bool(case_study_unsupported_clear)
        announcement_validation = dict(diagnostics.get("announcement_source_contract_validation") or {})
        repaired_announcement_validation = dict(
            repaired_diagnostics.get("announcement_source_contract_validation") or {}
        )
        announcement_validation_active = bool(announcement_validation.get("scope_match")) and bool(
            announcement_validation.get("repair_trigger_ids")
        )
        announcement_validation_improved = (
            _announcement_source_contract_improved(announcement_validation, repaired_announcement_validation)
            if announcement_validation_active
            else True
        )
        announcement_unsupported_clear = not bool(
            repaired_announcement_validation.get("unsupported_claim_added")
        )
        repair_metadata["announcement_source_contract_active"] = announcement_validation_active
        repair_metadata["announcement_source_contract_improved"] = bool(announcement_validation_improved)
        repair_metadata["announcement_source_contract_before_failure_count"] = (
            _announcement_source_contract_failure_count(announcement_validation)
        )
        repair_metadata["announcement_source_contract_after_failure_count"] = (
            _announcement_source_contract_failure_count(repaired_announcement_validation)
        )
        repair_metadata["announcement_unsupported_clear"] = bool(announcement_unsupported_clear)
        branding_validation = dict(diagnostics.get("branding_source_contract_validation") or {})
        repaired_branding_validation = dict(
            repaired_diagnostics.get("branding_source_contract_validation") or {}
        )
        branding_validation_active = bool(branding_validation.get("scope_match")) and bool(
            branding_validation.get("repair_trigger_ids")
        )
        branding_validation_improved = (
            _branding_source_contract_improved(branding_validation, repaired_branding_validation)
            if branding_validation_active
            else True
        )
        branding_unsupported_clear = not bool(repaired_branding_validation.get("unsupported_claim_added"))
        repair_metadata["branding_source_contract_active"] = branding_validation_active
        repair_metadata["branding_source_contract_improved"] = bool(branding_validation_improved)
        repair_metadata["branding_source_contract_before_failure_count"] = (
            _branding_source_contract_failure_count(branding_validation)
        )
        repair_metadata["branding_source_contract_after_failure_count"] = (
            _branding_source_contract_failure_count(repaired_branding_validation)
        )
        repair_metadata["branding_unsupported_clear"] = bool(branding_unsupported_clear)
        comparative_validation = dict(diagnostics.get("comparative_review_source_contract_validation") or {})
        repaired_comparative_validation = dict(
            repaired_diagnostics.get("comparative_review_source_contract_validation") or {}
        )
        comparative_validation_active = bool(comparative_validation.get("scope_match")) and bool(
            comparative_validation.get("repair_trigger_ids")
        )
        comparative_validation_improved = (
            _comparative_source_contract_improved(comparative_validation, repaired_comparative_validation)
            if comparative_validation_active
            else True
        )
        comparative_unsupported_clear = not bool(
            repaired_comparative_validation.get("unsupported_price_or_plan")
            or repaired_comparative_validation.get("unsupported_result_or_vendor_claim")
        )
        repair_metadata["comparative_review_source_contract_active"] = comparative_validation_active
        repair_metadata["comparative_review_source_contract_improved"] = bool(comparative_validation_improved)
        repair_metadata["comparative_review_source_contract_before_failure_count"] = (
            _comparative_source_contract_failure_count(comparative_validation)
        )
        repair_metadata["comparative_review_source_contract_after_failure_count"] = (
            _comparative_source_contract_failure_count(repaired_comparative_validation)
        )
        repair_metadata["comparative_review_unsupported_clear"] = bool(comparative_unsupported_clear)
        company_intro_naturalness_enrichment = dict(
            diagnostics.get("company_intro_naturalness_enrichment") or {}
        )
        company_intro_naturalness_rescue_active = bool(
            company_intro_naturalness_enrichment.get("activated")
        )
        company_intro_naturalness_improved = (
            company_intro_naturalness_rescue_active
            and _repair_improves_company_intro_naturalness(diagnostics, repaired_diagnostics)
        )
        company_intro_source_reflection_guard_active = bool(
            dict(diagnostics.get("company_intro_fingerprint_repair") or {}).get("source_reflection_repair")
        )
        current_body_chars = int(diagnostics.get("body_chars", 0) or 0)
        repaired_body_chars = int(repaired_diagnostics.get("body_chars", 0) or 0)
        company_intro_source_reflection_improved = bool(
            company_intro_source_reflection_guard_active
            and not _company_intro_source_reflection_weak(repaired_diagnostics)
            and (current_body_chars <= 0 or repaired_body_chars >= int(current_body_chars * 0.9))
        )
        repair_metadata["company_intro_source_reflection_guard_active"] = (
            company_intro_source_reflection_guard_active
        )
        repair_metadata["company_intro_source_reflection_improved"] = (
            company_intro_source_reflection_improved
        )
        repair_metadata["company_intro_naturalness_rescue_active"] = (
            company_intro_naturalness_rescue_active
        )
        repair_metadata["company_intro_naturalness_improved"] = (
            bool(company_intro_naturalness_improved)
        )
        if (
            ending_monotony_guard_active
            and not ending_monotony_improved
            and not company_intro_source_contract_cleared
        ):
            repair_metadata["acceptance_rejection_reason"] = "ending_monotony_not_improved"
        if explanatory_longform_guard_active and not explanatory_longform_improved:
            repair_metadata["acceptance_rejection_reason"] = "explanatory_longform_not_improved"
        if explanatory_fingerprint_guard_active and not explanatory_fingerprint_improved:
            repair_metadata["acceptance_rejection_reason"] = "explanatory_fingerprint_not_improved"
        company_intro_fingerprint_acceptance_clear = bool(
            company_intro_fingerprint_improved
            or company_intro_source_contract_cleared
            or company_intro_source_reflection_improved
        )
        repair_metadata["company_intro_fingerprint_acceptance_clear"] = (
            company_intro_fingerprint_acceptance_clear
        )
        repair_metadata["company_intro_fingerprint_source_contract_clear"] = bool(
            company_intro_source_contract_cleared
            and company_intro_fingerprint_guard_active
            and not company_intro_fingerprint_improved
        )
        if (
            company_intro_fingerprint_guard_active
            and not company_intro_fingerprint_improved
            and not company_intro_source_contract_cleared
            and not company_intro_source_reflection_improved
        ):
            repair_metadata["acceptance_rejection_reason"] = "company_intro_fingerprint_not_improved"
        if (
            company_intro_naturalness_rescue_active
            and not company_intro_naturalness_improved
            and not company_intro_source_contract_cleared
        ):
            repair_metadata.setdefault(
                "acceptance_rejection_reason",
                "company_intro_naturalness_not_improved",
            )
        if hidden_late_validation_active and not hidden_late_forbidden_heading_clear:
            repair_metadata.setdefault(
                "acceptance_rejection_reason",
                "hidden_late_forbidden_heading_remaining",
            )
        if hidden_late_validation_active and not hidden_late_validation_improved:
            repair_metadata.setdefault(
                "acceptance_rejection_reason",
                "hidden_late_validation_not_improved",
            )
        if hidden_late_validation_active and not company_intro_repair_opener_preserved:
            repair_metadata.setdefault(
                "acceptance_rejection_reason",
                "company_intro_opener_drift_after_hidden_late_repair",
            )
        if company_intro_operational_source_contract_present and not company_intro_unsupported_clear:
            repair_metadata["acceptance_rejection_reason"] = "company_introduction_unsupported_claim_after_repair"
        if company_intro_operational_source_contract_present and not company_intro_source_limit_clear:
            repair_metadata["acceptance_rejection_reason"] = "company_introduction_source_limit_visible_after_repair"
        if (
            company_intro_source_validation_active
            and company_intro_operational_source_contract_present
            and not company_intro_source_contract_cleared
        ):
            current_rejection_reason = str(
                repair_metadata.get("acceptance_rejection_reason") or ""
            )
            if current_rejection_reason in {
                "",
                "ending_monotony_not_improved",
                "company_intro_naturalness_not_improved",
            }:
                repair_metadata["acceptance_rejection_reason"] = (
                    "company_introduction_source_contract_not_improved"
                )
        if (
            company_intro_source_validation_active
            and not company_intro_operational_source_contract_present
            and not company_intro_source_validation_improved
        ):
            repair_metadata.setdefault(
                "acceptance_rejection_reason",
                "company_introduction_source_contract_not_improved",
            )
        if case_study_validation_active and not case_study_unsupported_clear:
            repair_metadata.setdefault(
                "acceptance_rejection_reason",
                "case_study_unsupported_claim_after_repair",
            )
        if case_study_validation_active and not case_study_validation_improved:
            repair_metadata.setdefault(
                "acceptance_rejection_reason",
                "case_study_source_contract_not_improved",
            )
        if announcement_validation_active and not announcement_unsupported_clear:
            repair_metadata.setdefault(
                "acceptance_rejection_reason",
                "announcement_unsupported_claim_after_repair",
            )
        if announcement_validation_active and not announcement_validation_improved:
            repair_metadata.setdefault(
                "acceptance_rejection_reason",
                "announcement_source_contract_not_improved",
            )
        if branding_validation_active and not branding_unsupported_clear:
            repair_metadata.setdefault(
                "acceptance_rejection_reason",
                "branding_unsupported_claim_after_repair",
            )
        if branding_validation_active and not branding_validation_improved:
            repair_metadata.setdefault(
                "acceptance_rejection_reason",
                "branding_source_contract_not_improved",
            )
        if comparative_validation_active and not comparative_unsupported_clear:
            repair_metadata.setdefault(
                "acceptance_rejection_reason",
                "comparative_review_unsupported_claim_after_repair",
            )
        if comparative_validation_active and not comparative_validation_improved:
            repair_metadata.setdefault(
                "acceptance_rejection_reason",
                "comparative_review_source_contract_not_improved",
            )
        acceptance_trigger = repair_trigger_improved or explanatory_longform_improved
        if explanatory_fingerprint_guard_active:
            acceptance_trigger = bool(explanatory_fingerprint_improved)
        if company_intro_fingerprint_guard_active:
            acceptance_trigger = bool(company_intro_fingerprint_acceptance_clear)
        if company_intro_naturalness_rescue_active and not company_intro_source_contract_cleared:
            acceptance_trigger = bool(company_intro_naturalness_improved)
        if hidden_late_validation_active:
            acceptance_trigger = bool(acceptance_trigger or hidden_late_validation_improved)
            if company_intro_naturalness_rescue_active and not company_intro_source_contract_cleared:
                acceptance_trigger = bool(acceptance_trigger and company_intro_naturalness_improved)
        if company_intro_source_validation_active:
            acceptance_trigger = bool(acceptance_trigger or company_intro_source_validation_improved)
        if case_study_validation_active:
            acceptance_trigger = bool(acceptance_trigger or case_study_validation_improved)
        if announcement_validation_active:
            acceptance_trigger = bool(acceptance_trigger or announcement_validation_improved)
        if branding_validation_active:
            acceptance_trigger = bool(acceptance_trigger or branding_validation_improved)
        if comparative_validation_active:
            acceptance_trigger = bool(acceptance_trigger or comparative_validation_improved)
        ending_monotony_acceptance_clear = (
            ending_monotony_improved or company_intro_source_contract_cleared
        )
        scope_acceptance_clear = bool(
            effective_scope_preserved
            or company_intro_source_contract_cleared
            or company_intro_source_reflection_improved
        )
        alignment_acceptance_clear = effective_alignment_preserved or company_intro_source_contract_cleared
        repair_metadata["scope_acceptance_clear"] = bool(scope_acceptance_clear)
        repair_metadata["alignment_acceptance_clear"] = bool(alignment_acceptance_clear)
        repair_metadata["company_intro_scope_source_reflection_clear"] = bool(
            company_intro_source_reflection_improved and not effective_scope_preserved
        )
        repair_metadata["company_intro_alignment_source_contract_clear"] = bool(
            company_intro_source_contract_cleared and not effective_alignment_preserved
        )
        company_intro_source_acceptance_clear = (
            company_intro_source_contract_cleared
            if (
                company_intro_source_validation_active
                and company_intro_operational_source_contract_present
            )
            else company_intro_source_validation_improved
        )
        if (
            repaired.body
            and acceptance_trigger
            and alignment_acceptance_clear
            and ending_monotony_acceptance_clear
            and explanatory_longform_improved
            and explanatory_fingerprint_improved
            and company_intro_fingerprint_acceptance_clear
            and scope_acceptance_clear
            and hidden_late_forbidden_heading_clear
            and hidden_late_validation_improved
            and company_intro_repair_opener_preserved
            and company_intro_unsupported_clear
            and company_intro_source_limit_clear
            and company_intro_source_acceptance_clear
            and case_study_unsupported_clear
            and case_study_validation_improved
            and announcement_unsupported_clear
            and announcement_validation_improved
            and branding_unsupported_clear
            and branding_validation_improved
            and comparative_unsupported_clear
            and comparative_validation_improved
        ):
            draft = repaired
            diagnostics = repaired_diagnostics
            editor_report = repaired_editor_report
            repair_applied = True
            final_controlled_realization = dict(repaired_controlled_realization)
            if company_intro_naturalness_rescue_active:
                repair_metadata["acceptance_path"] = (
                    "company_intro_naturalness"
                    if company_intro_naturalness_improved and not repair_trigger_improved
                    else repair_metadata.get("acceptance_path", "")
                )
            if company_intro_source_validation_active:
                if company_intro_source_contract_cleared:
                    repair_metadata["acceptance_path"] = "company_introduction_source_contract"
                else:
                    repair_metadata["acceptance_path"] = (
                        "company_introduction_source_contract"
                        if company_intro_source_validation_improved and not repair_trigger_improved
                        else repair_metadata.get("acceptance_path", "")
                    )
            if explanatory_fingerprint_guard_active:
                repair_metadata["acceptance_path"] = (
                    "explanatory_fingerprint_flatness"
                    if explanatory_fingerprint_improved and not repair_trigger_improved
                    else repair_metadata.get("acceptance_path", "")
                )
            if company_intro_fingerprint_guard_active:
                repair_metadata["acceptance_path"] = (
                    "company_intro_fingerprint_flatness"
                    if company_intro_fingerprint_improved and not repair_trigger_improved
                    else repair_metadata.get("acceptance_path", "")
                )
            if case_study_validation_active:
                repair_metadata["acceptance_path"] = (
                    "case_study_source_contract"
                    if case_study_validation_improved and not repair_trigger_improved
                    else repair_metadata.get("acceptance_path", "")
                )
            if announcement_validation_active:
                repair_metadata["acceptance_path"] = (
                    "announcement_source_contract"
                    if announcement_validation_improved and not repair_trigger_improved
                    else repair_metadata.get("acceptance_path", "")
                )
            if branding_validation_active:
                repair_metadata["acceptance_path"] = (
                    "branding_source_contract"
                    if branding_validation_improved and not repair_trigger_improved
                    else repair_metadata.get("acceptance_path", "")
                )
            if comparative_validation_active:
                repair_metadata["acceptance_path"] = (
                    "comparative_review_source_contract"
                    if comparative_validation_improved and not repair_trigger_improved
                    else repair_metadata.get("acceptance_path", "")
                )
        return draft, diagnostics, editor_report, repair_applied, repair_metadata, final_controlled_realization

    def generate(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        contract = dict(payload or {})
        self.reset_generation_progress()
        self._set_generation_progress("contract_resolve", 10, detail="入力を確認しています。")

        input_decision = _to_plain_dict(contract.get("input_decision"))
        action = str(input_decision.get("action") or "accept").strip().lower()
        reason_code = str(input_decision.get("reason_code") or "").strip()
        needs_input_items = [_to_plain_dict(item) for item in _to_plain_list(input_decision.get("needs_input_items"))]
        if action in {"clarify", "block"}:
            return build_input_stop_result(
                contract,
                reason_code or (error_codes.INP_NEEDS_CLARIFICATION if action == "clarify" else error_codes.INP_MISSING_REQUIRED),
                needs_input_items=needs_input_items,
            )
        if (
            not _to_plain_list(contract.get("source_documents"))
            and not is_prompt_only_source_less_generation_allowed(contract)
        ):
            return build_input_stop_result(contract, error_codes.INP_MISSING_REQUIRED)

        contract = _prepare_runtime_source_contracts(contract)
        if _branding_subject_anchor_source_insufficient(contract):
            return build_input_stop_result(
                contract,
                error_codes.INP_SOURCE_CONTEXT_INSUFFICIENT,
                needs_input_items=_branding_subject_anchor_needs_input_items(),
            )
        article_type = str(contract.get("article_type") or "explanatory_article").strip().lower()
        source_pack = build_source_pack(contract)
        use_prompt_stack_experiment = _is_prompt_stack_experiment_enabled(contract)
        if _has_rejected_materialized_route_request(contract):
            return _build_pipeline_failure_result(
                contract,
                reason_code=error_codes.SYS_PIPELINE_FAILURE,
                message="Rejected materialized route flags are archived",
            )
        compact_plan = (
            []
            if use_prompt_stack_experiment
            else self._maybe_build_compact_plan(contract, source_pack)
        )
        if compact_plan:
            contract["_semantic_ledger"] = [dict(item) for item in compact_plan]
        note_target_chars = target_chars(
            str(contract.get("length_mode") or ""),
            article_type,
            source_count=len(list(source_pack.get("source_documents") or [])),
        )
        max_tokens = max(2800, min(7000, int(note_target_chars * 1.8)))
        self._set_generation_progress("source_digest", 22, detail="素材を整理しています。")
        prompt_stack_summary: Dict[str, Any] = {}

        try:
            self._set_generation_progress("single_pass_generation", 48, detail="本文を一回で生成しています。")
            if use_prompt_stack_experiment:
                try:
                    draft, llm_metadata, prompt_stack_summary = self._generate_with_experimental_prompt_stack(
                        contract,
                        source_pack,
                        article_type=article_type,
                        max_tokens=max_tokens,
                    )
                except ExperimentalPromptStackStageError as exc:
                    base_summary = dict(exc.stage_summary or {})
                    prompt_stack_summary = {
                        "enabled": True,
                        "experiment": _EXPERIMENTAL_PROMPT_STACK,
                        "used_fallback_generation": True,
                        "fallback_reason": str(exc) or "prompt_stack_failed",
                        "stages_completed": list(base_summary.get("stages_completed") or []),
                        "script_section_count": int(base_summary.get("script_section_count", 0) or 0),
                        "planner_section_count": int(base_summary.get("planner_section_count", 0) or 0),
                        "script_snapshot": dict(base_summary.get("script_snapshot") or {}),
                        "planner_snapshot": dict(base_summary.get("planner_snapshot") or {}),
                        "source_packet_snapshot": dict(base_summary.get("source_packet_snapshot") or {}),
                        "article_contract_snapshot": dict(base_summary.get("article_contract_snapshot") or {}),
                        "writer_used_fact_ids": list(base_summary.get("writer_used_fact_ids") or []),
                        "suffix_edit_window": dict(base_summary.get("suffix_edit_window") or {}),
                        "audit_result": dict(base_summary.get("audit_result") or {}),
                        "visibility_summary": {},
                        "stage_calls": dict(base_summary.get("stage_calls") or {}),
                        "support_parse_summary": dict(base_summary.get("support_parse_summary") or {}),
                    }
                    prompt_stack_summary["visibility_summary"] = _build_experimental_prompt_stack_visibility_summary(
                        prompt_stack_summary
                    )
                    draft, llm_metadata = self._generate_single_pass_draft(
                        contract,
                        source_pack,
                        article_type=article_type,
                        compact_plan=compact_plan,
                        max_tokens=max_tokens,
                    )
                except Exception as exc:
                    prompt_stack_summary = {
                        "enabled": True,
                        "experiment": _EXPERIMENTAL_PROMPT_STACK,
                        "used_fallback_generation": True,
                        "fallback_reason": str(exc) or "prompt_stack_failed",
                        "stages_completed": list(prompt_stack_summary.get("stages_completed") or []),
                        "script_section_count": int(prompt_stack_summary.get("script_section_count", 0) or 0),
                        "planner_section_count": int(prompt_stack_summary.get("planner_section_count", 0) or 0),
                        "script_snapshot": dict(prompt_stack_summary.get("script_snapshot") or {}),
                        "planner_snapshot": dict(prompt_stack_summary.get("planner_snapshot") or {}),
                        "audit_result": dict(prompt_stack_summary.get("audit_result") or {}),
                        "visibility_summary": {},
                        "stage_calls": dict(prompt_stack_summary.get("stage_calls") or {}),
                        "support_parse_summary": dict(prompt_stack_summary.get("support_parse_summary") or {}),
                    }
                    prompt_stack_summary["visibility_summary"] = _build_experimental_prompt_stack_visibility_summary(
                        prompt_stack_summary
                    )
                    draft, llm_metadata = self._generate_single_pass_draft(
                        contract,
                        source_pack,
                        article_type=article_type,
                        compact_plan=compact_plan,
                        max_tokens=max_tokens,
                    )
            else:
                draft, llm_metadata = self._generate_single_pass_draft(
                    contract,
                    source_pack,
                    article_type=article_type,
                    compact_plan=compact_plan,
                    max_tokens=max_tokens,
                )
            _require_visible_draft(draft)
            draft, editor_report = _apply_surface_guards_to_draft(contract, draft)
            _require_visible_draft(draft)
            self._set_generation_progress("light_guard", 72, detail="重複と主語の出し過ぎを点検しています。", partial_body=draft.body[:1200])
            diagnostics, controlled_realization = _refresh_diagnostics_state(
                contract,
                draft,
                editor_report,
                compact_plan,
                source_pack,
            )
            pre_repair_draft = draft
            pre_repair_editor_report = dict(editor_report)
            pre_repair_diagnostics = dict(diagnostics)
            draft, diagnostics, editor_report, repair_applied, repair_metadata, final_controlled_realization = (
                self._run_optional_repair(
                    contract=contract,
                    draft=draft,
                    diagnostics=diagnostics,
                    editor_report=editor_report,
                    compact_plan=compact_plan,
                    source_pack=source_pack,
                    article_type=article_type,
                    max_tokens=max_tokens,
                    controlled_realization=controlled_realization,
                )
            )

            draft, diagnostics, editor_report, stabilized_controlled_realization, comparative_stabilizer = (
                _maybe_stabilize_experimental_comparative_draft(
                    contract=contract,
                    draft=draft,
                    diagnostics=diagnostics,
                    editor_report=editor_report,
                    source_pack=source_pack,
                    compact_plan=compact_plan,
                )
            )
            if comparative_stabilizer.get("rewritten"):
                final_controlled_realization = dict(stabilized_controlled_realization)
            if comparative_stabilizer.get("checked"):
                repair_metadata["comparative_prompt_echo_stabilizer"] = dict(comparative_stabilizer)
            branding_final_validation = dict(diagnostics.get("branding_source_contract_validation") or {})
            if _branding_subject_anchor_final_unresolved(branding_final_validation):
                branding_anchor_failure = PipelineRuntimeError(
                    "Branding subject anchor remained unresolved after source contract validation",
                    error_codes.SYS_PIPELINE_FAILURE,
                )
                branding_anchor_failure.telemetry = {
                    "branding_subject_anchor_unresolved": {
                        "pattern": str(branding_final_validation.get("pattern") or ""),
                        "required_slots": list(branding_final_validation.get("required_slots") or []),
                        "missing_required_slots": list(
                            branding_final_validation.get("missing_required_slots") or []
                        ),
                        "brand_subject_anchor_source_available": bool(
                            branding_final_validation.get("brand_subject_anchor_source_available")
                        ),
                        "brand_subject_anchor_fronted": bool(
                            branding_final_validation.get("brand_subject_anchor_fronted")
                        ),
                        "repair_trigger_ids": list(branding_final_validation.get("repair_trigger_ids") or []),
                    }
                }
                raise branding_anchor_failure
            company_intro_opener_evaluation = _evaluate_company_intro_visible_opener_drift(
                contract,
                draft,
                compact_plan,
                diagnostics,
                final_controlled_realization,
            )
            company_intro_final_validation = dict(
                diagnostics.get("company_introduction_source_contract_validation") or {}
            )
            if _company_intro_final_hard_validation_unresolved(company_intro_final_validation):
                hard_validation_failure = PipelineRuntimeError(
                    "Company introduction hard source contract trigger remained after repair",
                    error_codes.SYS_PIPELINE_FAILURE,
                )
                hard_validation_failure.telemetry = {
                    "company_introduction_final_hard_validation": (
                        _build_company_intro_source_contract_validation_snapshot(company_intro_final_validation)
                    ),
                    **_build_company_intro_failure_payload_diagnostics(
                        diagnostics,
                        draft,
                        repair_metadata,
                    ),
                }
                raise hard_validation_failure
            if _company_intro_source_contract_repair_unresolved(repair_metadata):
                source_contract_failure = PipelineRuntimeError(
                    "Company introduction source contract remained unresolved after repair",
                    error_codes.SYS_PIPELINE_FAILURE,
                )
                source_contract_failure.telemetry = {
                    "company_introduction_source_contract_unresolved": (
                        _build_company_intro_source_contract_repair_telemetry(repair_metadata)
                    ),
                    **_build_company_intro_failure_payload_diagnostics(
                        pre_repair_diagnostics,
                        draft,
                        repair_metadata,
                    ),
                }
                raise source_contract_failure
            if _company_intro_naturalness_unresolved(pre_repair_diagnostics, repair_metadata):
                naturalness_failure = PipelineRuntimeError(
                    "Company introduction naturalness rescue remained unresolved after repair",
                    error_codes.SYS_PIPELINE_FAILURE,
                )
                company_intro_failure_diagnostics = _build_company_intro_failure_payload_diagnostics(
                    pre_repair_diagnostics,
                    draft,
                    repair_metadata,
                )
                naturalness_failure.telemetry = {
                    "company_intro_naturalness_unresolved": (
                        _build_company_intro_naturalness_unresolved_telemetry(
                            pre_repair_diagnostics,
                            repair_metadata,
                            repair_applied=repair_applied,
                            draft=draft,
                        )
                    ),
                    **company_intro_failure_diagnostics,
                }
                raise naturalness_failure
            if company_intro_opener_evaluation.get("failed"):
                opener_failure = PipelineRuntimeError(
                    "Company introduction opener drift remained visible after repair gating",
                    error_codes.SYS_PIPELINE_FAILURE,
                )
                opener_failure.telemetry = {
                    **_build_company_intro_failure_payload_diagnostics(
                        diagnostics,
                        draft,
                    ),
                    "company_intro_visible_opener_drift": {
                        key: company_intro_opener_evaluation.get(key)
                        for key in (
                            "title_history_first",
                            "title_history_first_triggered",
                            "first_section_history_first",
                            "first_section_history_first_triggered",
                            "global_focus_aligned",
                            "global_focus_rescued",
                            "global_focus_failed",
                            "opener_heading_drift",
                            "shadow_opener_heading_drift",
                            "visible_opener_heading_drift",
                            "visible_opener_heading_operational_rescued",
                            "opener_tokens_sample",
                            "drift_headings",
                            "lead_opening_opener_focus_hit",
                            "first_heading",
                            "shadow_first_heading",
                            "visible_first_heading",
                            "source_required_slots_covered",
                            "visible_required_slots_covered",
                        )
                    }
                }
                raise opener_failure
            self._set_generation_progress("output_format", 94, detail="出力を整形しています。")
            result = build_result(
                contract=contract,
                draft=draft,
                source_pack=source_pack,
                diagnostics=diagnostics,
                editor_report=editor_report,
                llm_metadata=llm_metadata,
                repair_metadata=repair_metadata,
                repair_applied=repair_applied,
            )
            pipeline_check = dict(result.get("pipeline_check") or {})
            body_generation = dict(pipeline_check.get("body_generation") or {})
            if prompt_stack_summary:
                body_generation["experimental_prompt_stack"] = prompt_stack_summary
            body_generation["repair_entry"] = _build_repair_entry_telemetry(
                contract,
                pre_repair_diagnostics,
                repair_applied=repair_applied,
                repair_metadata=repair_metadata,
            )
            case_study_validation = dict(diagnostics.get("case_study_source_contract_validation") or {})
            if case_study_validation.get("checked"):
                body_generation["case_study_source_contract_validation"] = {
                    "checked": bool(case_study_validation.get("checked")),
                    "scope_match": bool(case_study_validation.get("scope_match")),
                    "required_slots": list(case_study_validation.get("required_slots") or []),
                    "optional_slots": list(case_study_validation.get("optional_slots") or []),
                    "slot_presence": dict(case_study_validation.get("slot_presence") or {}),
                    "missing_required_slots": list(case_study_validation.get("missing_required_slots") or []),
                    "unsupported_metric_added": bool(case_study_validation.get("unsupported_metric_added")),
                    "unsupported_customer_or_award_added": bool(
                        case_study_validation.get("unsupported_customer_or_award_added")
                    ),
                    "success_story_only_drift": bool(case_study_validation.get("success_story_only_drift")),
                    "generic_advice_drift": bool(case_study_validation.get("generic_advice_drift")),
                    "wrong_article_type_drift": bool(case_study_validation.get("wrong_article_type_drift")),
                    "visible_leakage_hits": list(case_study_validation.get("visible_leakage_hits") or []),
                    "repair_trigger_ids": list(case_study_validation.get("repair_trigger_ids") or []),
                }
            announcement_validation = dict(diagnostics.get("announcement_source_contract_validation") or {})
            if announcement_validation.get("checked"):
                body_generation["announcement_source_contract_validation"] = {
                    "checked": bool(announcement_validation.get("checked")),
                    "scope_match": bool(announcement_validation.get("scope_match")),
                    "pattern": str(announcement_validation.get("pattern") or ""),
                    "required_slots": list(announcement_validation.get("required_slots") or []),
                    "optional_slots": list(announcement_validation.get("optional_slots") or []),
                    "slot_presence": dict(announcement_validation.get("slot_presence") or {}),
                    "missing_required_slots": list(announcement_validation.get("missing_required_slots") or []),
                    "target_action_buried": bool(announcement_validation.get("target_action_buried")),
                    "explanatory_drift": bool(announcement_validation.get("explanatory_drift")),
                    "help_article_drift": bool(announcement_validation.get("help_article_drift")),
                    "company_intro_drift": bool(announcement_validation.get("company_intro_drift")),
                    "wrong_article_type_drift": bool(announcement_validation.get("wrong_article_type_drift")),
                    "unsupported_claim_added": bool(announcement_validation.get("unsupported_claim_added")),
                    "visible_leakage_hits": list(announcement_validation.get("visible_leakage_hits") or []),
                    "repair_trigger_ids": list(announcement_validation.get("repair_trigger_ids") or []),
                }
            branding_validation = dict(diagnostics.get("branding_source_contract_validation") or {})
            if branding_validation.get("checked"):
                body_generation["branding_source_contract_validation"] = {
                    "checked": bool(branding_validation.get("checked")),
                    "scope_match": bool(branding_validation.get("scope_match")),
                    "pattern": str(branding_validation.get("pattern") or ""),
                    "required_slots": list(branding_validation.get("required_slots") or []),
                    "optional_slots": list(branding_validation.get("optional_slots") or []),
                    "slot_presence": dict(branding_validation.get("slot_presence") or {}),
                    "brand_subject_anchor_source_available": bool(
                        branding_validation.get("brand_subject_anchor_source_available")
                    ),
                    "brand_subject_anchor_fronted": bool(branding_validation.get("brand_subject_anchor_fronted")),
                    "missing_required_slots": list(branding_validation.get("missing_required_slots") or []),
                    "customer_touchpoint_buried": bool(branding_validation.get("customer_touchpoint_buried")),
                    "philosophy_only_drift": bool(branding_validation.get("philosophy_only_drift")),
                    "advertising_copy_drift": bool(branding_validation.get("advertising_copy_drift")),
                    "abstract_value_only": bool(branding_validation.get("abstract_value_only")),
                    "wrong_article_type_drift": bool(branding_validation.get("wrong_article_type_drift")),
                    "unsupported_claim_added": bool(branding_validation.get("unsupported_claim_added")),
                    "visible_leakage_hits": list(branding_validation.get("visible_leakage_hits") or []),
                    "repair_trigger_ids": list(branding_validation.get("repair_trigger_ids") or []),
                }
            company_intro_validation = dict(
                diagnostics.get("company_introduction_source_contract_validation") or {}
            )
            if company_intro_validation.get("checked"):
                script_packet = dict(contract.get("_company_introduction_script_packet") or {})
                if script_packet.get("checked"):
                    body_generation["company_introduction_script_packet"] = {
                        "checked": bool(script_packet.get("checked")),
                        "scope_match": bool(script_packet.get("scope_match")),
                        "pattern": str(script_packet.get("pattern") or ""),
                        "statuses": {
                            unit: str(dict(script_packet.get(unit) or {}).get("status") or "missing")
                            for unit, _slot in _COMPANY_INTRO_SCRIPT_UNITS
                        },
                        "quote_counts": {
                            unit: len(list(dict(script_packet.get(unit) or {}).get("quotes") or []))
                            for unit, _slot in _COMPANY_INTRO_SCRIPT_UNITS
                        },
                    }
                body_generation["company_introduction_source_contract_validation"] = {
                    "checked": bool(company_intro_validation.get("checked")),
                    "scope_match": bool(company_intro_validation.get("scope_match")),
                    "pattern": str(company_intro_validation.get("pattern") or ""),
                    "required_slots": list(company_intro_validation.get("required_slots") or []),
                    "optional_slots": list(company_intro_validation.get("optional_slots") or []),
                    "guard_only_slots": list(company_intro_validation.get("guard_only_slots") or []),
                    "slot_presence": dict(company_intro_validation.get("slot_presence") or {}),
                    "source_slot_presence": dict(company_intro_validation.get("source_slot_presence") or {}),
                    "missing_required_slots": list(company_intro_validation.get("missing_required_slots") or []),
                    "unbacked_required_slots": list(
                        company_intro_validation.get("unbacked_required_slots") or []
                    ),
                    "support_scope_boundary_missing_final": bool(
                        company_intro_validation.get("support_scope_boundary_missing_final")
                    ),
                    "pre_contact_decision_missing_final": bool(
                        company_intro_validation.get("pre_contact_decision_missing_final")
                    ),
                    "brochure_only_drift": bool(company_intro_validation.get("brochure_only_drift")),
                    "generic_company_copy": bool(company_intro_validation.get("generic_company_copy")),
                    "abstract_philosophy_only": bool(company_intro_validation.get("abstract_philosophy_only")),
                    "company_profile_packet_drift": bool(
                        company_intro_validation.get("company_profile_packet_drift")
                    ),
                    "wrong_article_type_drift": bool(company_intro_validation.get("wrong_article_type_drift")),
                    "unsupported_claim_added": bool(company_intro_validation.get("unsupported_claim_added")),
                    "source_limit_visible_leakage": bool(
                        company_intro_validation.get("source_limit_visible_leakage")
                    ),
                    "public_contract_present": bool(company_intro_validation.get("public_contract_present")),
                    "private_contract_present": bool(company_intro_validation.get("private_contract_present")),
                    "visible_leakage_hits": list(company_intro_validation.get("visible_leakage_hits") or []),
                    "script_packet_statuses": dict(company_intro_validation.get("script_packet_statuses") or {}),
                    "hard_trigger_ids": list(company_intro_validation.get("hard_trigger_ids") or []),
                    "degraded_trigger_ids": list(company_intro_validation.get("degraded_trigger_ids") or []),
                    "degraded_slots": list(company_intro_validation.get("degraded_slots") or []),
                    "repair_trigger_ids": list(company_intro_validation.get("repair_trigger_ids") or []),
                }
                body_generation["company_intro_observability"] = _company_intro_quality_observability(
                    contract,
                    source_pack,
                    first_draft=pre_repair_draft,
                    final_draft=draft,
                    pre_repair_diagnostics=pre_repair_diagnostics,
                    final_diagnostics=diagnostics,
                    pre_repair_editor_report=pre_repair_editor_report,
                    final_editor_report=editor_report,
                    repair_metadata=repair_metadata,
                    repair_applied=repair_applied,
                )
            comparative_validation = dict(diagnostics.get("comparative_review_source_contract_validation") or {})
            if comparative_validation.get("checked"):
                body_generation["comparative_review_source_contract_validation"] = {
                    "checked": bool(comparative_validation.get("checked")),
                    "scope_match": bool(comparative_validation.get("scope_match")),
                    "pattern": str(comparative_validation.get("pattern") or ""),
                    "required_slots": list(comparative_validation.get("required_slots") or []),
                    "optional_slots": list(comparative_validation.get("optional_slots") or []),
                    "slot_presence": dict(comparative_validation.get("slot_presence") or {}),
                    "missing_required_slots": list(comparative_validation.get("missing_required_slots") or []),
                    "ranking_drift": bool(comparative_validation.get("ranking_drift")),
                    "absolute_winner_drift": bool(comparative_validation.get("absolute_winner_drift")),
                    "unsupported_price_or_plan": bool(comparative_validation.get("unsupported_price_or_plan")),
                    "unsupported_result_or_vendor_claim": bool(
                        comparative_validation.get("unsupported_result_or_vendor_claim")
                    ),
                    "exaggerated_superiority": bool(comparative_validation.get("exaggerated_superiority")),
                    "affiliate_review_tone": bool(comparative_validation.get("affiliate_review_tone")),
                    "generic_recommendation_only": bool(comparative_validation.get("generic_recommendation_only")),
                    "missing_fit_conditions": bool(comparative_validation.get("missing_fit_conditions")),
                    "missing_tradeoff_or_caution": bool(comparative_validation.get("missing_tradeoff_or_caution")),
                    "wrong_article_type_drift": bool(comparative_validation.get("wrong_article_type_drift")),
                    "visible_leakage_hits": list(comparative_validation.get("visible_leakage_hits") or []),
                    "repair_trigger_ids": list(comparative_validation.get("repair_trigger_ids") or []),
                }
            body_generation["controlled_realization"] = {
                "active": bool(controlled_realization.get("active")),
                "shadow_section_count": int(controlled_realization.get("shadow_section_count", 0) or 0),
                "checked_section_count": int(controlled_realization.get("checked_section_count", 0) or 0),
                "initial_alignment_rate": float(controlled_realization.get("alignment_rate", 0.0) or 0.0),
                "initial_drift_count": int(controlled_realization.get("drift_count", 0) or 0),
                "initial_drift_headings": list(controlled_realization.get("drift_headings") or []),
                "final_alignment_rate": float(final_controlled_realization.get("alignment_rate", 0.0) or 0.0),
                "final_drift_count": int(final_controlled_realization.get("drift_count", 0) or 0),
                "final_drift_headings": list(final_controlled_realization.get("drift_headings") or []),
                "global_focus_aligned": bool(final_controlled_realization.get("global_focus_aligned", True)),
            }
            pipeline_check["body_generation"] = body_generation
            result["pipeline_check"] = pipeline_check
            self._set_generation_progress("completed", 100, detail="生成が完了しました。", partial_body=draft.body[:1200])
            return result
        except PipelineRuntimeError as exc:
            normalized_reason = str(getattr(exc, "reason_code", "") or error_codes.SYS_PIPELINE_FAILURE)
            if normalized_reason.startswith("INP_"):
                return build_input_stop_result(contract, normalized_reason)
            return _build_pipeline_failure_result(
                contract,
                reason_code=normalized_reason,
                message=str(exc),
                extra=getattr(exc, "telemetry", None),
            )
        except Exception as exc:
            normalized_reason = str(getattr(exc, "reason_code", "") or error_codes.SYS_PIPELINE_FAILURE)
            return _build_pipeline_failure_result(
                contract,
                reason_code=normalized_reason,
                message=str(exc),
                extra=getattr(exc, "telemetry", None),
            )
