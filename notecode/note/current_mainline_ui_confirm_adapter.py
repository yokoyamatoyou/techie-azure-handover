"""Plain-data helpers for journey confirm projection inside the UI shell."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List, Optional


def _to_plain_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _to_plain_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _normalize_string_list(
    values: Iterable[Any] | None,
    *,
    sort_values: bool = False,
) -> List[str]:
    normalized: List[str] = []
    if values is None:
        return normalized
    for item in values:
        text = str(item or "").strip()
        if text and text not in normalized:
            normalized.append(text)
    if sort_values:
        normalized.sort()
    return normalized


def _build_confirm_event_extra(
    *,
    semantic_article_key: str = "",
    decision_origin: str = "",
    confirm_gate_kind: str = "",
    source_fit_status: str = "",
    source_grounding_status: str = "",
    source_grounding_required: Optional[bool] = None,
    input_decision_action: str = "",
    allow_generate: Optional[bool] = None,
) -> Dict[str, Any]:
    extra: Dict[str, Any] = {}
    if str(semantic_article_key or "").strip():
        extra["semantic_article_key"] = str(semantic_article_key or "").strip()
    if str(decision_origin or "").strip():
        extra["decision_origin"] = str(decision_origin or "").strip()
    if str(confirm_gate_kind or "").strip():
        extra["confirm_gate_kind"] = str(confirm_gate_kind or "").strip()
    if str(source_fit_status or "").strip():
        extra["source_fit_status"] = str(source_fit_status or "").strip()
    if str(source_grounding_status or "").strip():
        extra["source_grounding_status"] = str(source_grounding_status or "").strip()
    if source_grounding_required is not None:
        extra["source_grounding_required"] = bool(source_grounding_required)
    if str(input_decision_action or "").strip():
        extra["input_decision_action"] = str(input_decision_action or "").strip()
    if allow_generate is not None:
        extra["allow_generate"] = bool(allow_generate)
    return extra


def _build_needs_input_content(items: List[Dict[str, Any]]) -> str:
    if not items:
        return ""
    missing_lines = ["- 追加で必要な補足:"]
    for item in items:
        field = str(item.get("field", "") or "")
        template = str(item.get("question_template", "") or "")
        missing_lines.append(f"- {field}: {template}")
    return "\n".join(missing_lines)


def build_journey_signature(
    *,
    purpose_key: str,
    target_key: str,
    detail_key: str = "",
    comparison_axes: Iterable[Any] | None = None,
    source_values: Iterable[Any] | None = None,
    prompt_raw: str = "",
    audience_profile: str = "",
    core_message: str = "",
    perspective_mode: str = "",
) -> str:
    payload = {
        "purpose_key": str(purpose_key or "").strip(),
        "target_key": str(target_key or "").strip(),
        "detail_key": str(detail_key or "").strip(),
        "comparison_axes": _normalize_string_list(comparison_axes),
        "sources": _normalize_string_list(source_values, sort_values=True),
        "prompt_raw": str(prompt_raw or "").strip(),
        "audience_profile": str(audience_profile or "").strip(),
        "core_message": str(core_message or "").strip(),
        "perspective_mode": str(perspective_mode or "").strip(),
    }
    normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_journey_selection_summary(
    *,
    ui_mode: str,
    purpose_key: str = "",
    purpose_label: str = "",
    target_key: str = "",
    target_label: str = "",
    detail_key: str = "",
    detail_label: str = "",
    comparison_axis_labels: Iterable[Any] | None = None,
    semantic_article_key: str = "",
    semantic_label: str = "",
    article_type_key: str = "",
    article_type_label: str = "",
    confirmed: bool = False,
) -> Dict[str, Any]:
    normalized_ui_mode = str(ui_mode or "").strip()
    is_journey_mode = normalized_ui_mode == "journey"
    return {
        "ui_mode": normalized_ui_mode,
        "purpose_key": str(purpose_key or "") if is_journey_mode else "",
        "purpose_label": str(purpose_label or "") if is_journey_mode else "",
        "target_key": str(target_key or "") if is_journey_mode else "",
        "target_label": str(target_label or "") if is_journey_mode else "",
        "detail_key": str(detail_key or "") if is_journey_mode else "",
        "detail_label": str(detail_label or "") if is_journey_mode else "",
        "comparison_axes": " / ".join(_normalize_string_list(comparison_axis_labels)),
        "semantic_article_key": str(semantic_article_key or ""),
        "semantic_label": str(semantic_label or ""),
        "article_type_key": str(article_type_key or ""),
        "article_type_label": str(article_type_label or ""),
        "confirmed": bool(confirmed),
    }


def build_invalidate_journey_confirmation(
    *,
    ui_mode: str,
    reason_text: str = "",
    semantic_article_key: str = "",
) -> Dict[str, Any]:
    status_text = ""
    source_fit_text = ""
    grounding_status_text = ""
    reason_code = ""
    error_class = ""
    event_extra: Dict[str, Any] = {}
    if str(ui_mode or "").strip() == "journey":
        status_text = str(reason_text or "").strip() or "入力が変わりました。変更した項目だけ確認してください。"
        source_fit_text = "材料のそろい具合は、入力内容を確認したあとに更新します。"
        grounding_status_text = "記事に必要な根拠は、材料がそろったあとに確認します。"
        reason_code = "INP_MISSING_REQUIRED"
        error_class = "user_input"
        event_extra = _build_confirm_event_extra(
            semantic_article_key=semantic_article_key,
            decision_origin="ui_confirm_guard",
            confirm_gate_kind="invalidated",
            allow_generate=False,
        )
    return {
        "signature": "",
        "preview": {},
        "source_fit_text": source_fit_text,
        "grounding_status_text": grounding_status_text,
        "missing_content": "",
        "status_text": status_text,
        "reason_code": reason_code,
        "error_class": error_class,
        "needs_input_items": [],
        "allow_confirm": False,
        "event_extra": event_extra,
    }


def build_journey_confirm_summary(
    *,
    purpose_label: str,
    target_label: str,
    article_type_label: str,
    semantic_label: str,
    compare_goal_label: str = "",
    comparison_labels: Iterable[Any] | None = None,
    candidate_target_labels: Iterable[Any] | None = None,
) -> str:
    lines = [
        f"- 何のための記事か: {str(purpose_label or '')}",
        f"- 書く内容: {str(target_label or '')}",
    ]
    if str(compare_goal_label or "").strip():
        lines.append(f"- 比較の見せ方: {str(compare_goal_label or '').strip()}")
    normalized_comparison_labels = _normalize_string_list(comparison_labels)
    if normalized_comparison_labels:
        lines.append(f"- 比較したい点: {' / '.join(normalized_comparison_labels)}")
    if str(article_type_label or "").strip():
        lines.append(f"- 仕上がり: {str(article_type_label or '')}")
    normalized_candidate_labels = _normalize_string_list(candidate_target_labels)
    if normalized_candidate_labels:
        lines.append(f"- 材料から見た候補: {' / '.join(normalized_candidate_labels[:3])}")
    return "\n".join(lines)


def build_journey_confirm_blocked_view(
    *,
    kind: str,
    semantic_article_key: str = "",
) -> Dict[str, Any]:
    normalized_kind = str(kind or "").strip().lower()
    if normalized_kind == "fetch_failed":
        return {
            "source_fit_text": "材料を読み取れていません。",
            "grounding_status_text": "記事に必要な根拠は、材料を読み取れたあとに確認します。",
            "missing_content": "- 取得に失敗したソースを見直してください。",
            "status_text": "読める材料をそろえてから、もう一度内容を確認してください。",
            "reason_code": "INP_SOURCE_CONTEXT_INSUFFICIENT",
            "error_class": "user_input",
            "needs_input_items": [
                {
                    "field": "source",
                    "issue_type": "fetch_failed",
                    "required_format": "取得できる URL またはファイルをそろえる",
                    "question_template": "取得できるソースをそろえてください。",
                    "example_answer": "取得できる公式ページまたは PDF に差し替えます",
                }
            ],
            "allow_confirm": False,
            "event_extra": _build_confirm_event_extra(
                semantic_article_key=semantic_article_key,
                decision_origin="ui_confirm_guard",
                confirm_gate_kind="fetch_failed",
                source_fit_status="block",
                source_grounding_status="pending_documents",
                input_decision_action="block",
                allow_generate=False,
            ),
        }
    return {
        "source_fit_text": "材料がまだありません。",
        "grounding_status_text": "記事に必要な根拠は、材料を追加したあとに確認します。",
        "missing_content": "- URL またはファイルを追加してください。",
        "status_text": "材料を追加してから、もう一度内容を確認してください。",
        "reason_code": "INP_MISSING_REQUIRED",
        "error_class": "user_input",
        "needs_input_items": [
            {
                "field": "source",
                "issue_type": "missing",
                "required_format": "URL またはファイルを 1 件以上追加する",
                "question_template": "URL またはファイルを追加してください。",
                "example_answer": "会社概要の URL または PDF を追加します",
            }
        ],
        "allow_confirm": False,
        "event_extra": _build_confirm_event_extra(
            semantic_article_key=semantic_article_key,
            decision_origin="ui_confirm_guard",
            confirm_gate_kind="no_sources",
            source_fit_status="block",
            source_grounding_status="pending_sources",
            input_decision_action="block",
            allow_generate=False,
        ),
    }


def _build_source_grounding_status_text(
    *,
    source_grounding_required: bool,
    source_grounding_status: str,
    input_decision_action: str,
) -> str:
    if not source_grounding_required or source_grounding_status == "not_required":
        return "この記事では、追加の根拠確認は不要です。"
    if source_grounding_status == "resolved":
        return "記事に必要な根拠はそろっています。"
    if source_grounding_status == "pending_documents":
        return "記事に必要な根拠は、材料を読み込んだあとに確認します。"
    if source_grounding_status == "insufficient":
        if input_decision_action == "accept":
            return "不足はありますが、今のルールではこのまま生成できます。"
        return "根拠が足りないため、補足資料を追加してください。"
    return "必要な根拠の状況を確認してください。"


def build_journey_confirm_preview_view(
    *,
    preview: Dict[str, Any],
    purpose_label: str,
    target_label: str,
    article_type_label: str,
    semantic_label: str,
    compare_goal_label: str = "",
    comparison_labels: Iterable[Any] | None = None,
    candidate_target_labels: Iterable[Any] | None = None,
) -> Dict[str, Any]:
    source_fit = _to_plain_dict(preview.get("source_fit"))
    input_decision = _to_plain_dict(preview.get("input_decision"))
    contract = _to_plain_dict(preview.get("contract")) or _to_plain_dict(preview)
    needs_input_items = [_to_plain_dict(item) for item in _to_plain_list(preview.get("needs_input_items"))[:3]]
    missing_content = _build_needs_input_content(needs_input_items)
    action = str(input_decision.get("action") or "accept")
    source_grounding_status = str(contract.get("source_grounding_status") or "")
    source_grounding_required = bool(contract.get("source_grounding_required"))
    return {
        "summary_content": build_journey_confirm_summary(
            purpose_label=purpose_label,
            target_label=target_label,
            article_type_label=article_type_label,
            semantic_label=semantic_label,
            compare_goal_label=compare_goal_label,
            comparison_labels=comparison_labels,
            candidate_target_labels=candidate_target_labels,
        ),
        "source_fit_text": str(source_fit.get("summary") or "材料の状況を確認できませんでした。"),
        "grounding_status_text": _build_source_grounding_status_text(
            source_grounding_required=source_grounding_required,
            source_grounding_status=source_grounding_status,
            input_decision_action=action,
        ),
        "missing_content": missing_content,
        "status_text": (
            "内容を確認しました。このまま生成できます。"
            if action == "accept"
            else "足りない材料があります。補ってからもう一度確認してください。"
        ),
        "reason_code": str(input_decision.get("reason_code") or "OK"),
        "error_class": "success" if action == "accept" else "user_input",
        "needs_input_items": needs_input_items,
        "allow_confirm": action == "accept",
        "event_extra": _build_confirm_event_extra(
            semantic_article_key=str(preview.get("semantic_article_key") or ""),
            decision_origin="resolved_input_contract",
            confirm_gate_kind="preview_ready",
            source_fit_status=str(source_fit.get("status") or ""),
            source_grounding_status=source_grounding_status,
            source_grounding_required=source_grounding_required,
            input_decision_action=action,
            allow_generate=action == "accept",
        ),
    }


def build_journey_confirmed_view(*, semantic_article_key: str = "") -> Dict[str, Any]:
    return {
        "status_text": "内容を確認しました。このまま生成できます。",
        "notify_text": "内容を確認しました。生成に進めます。",
        "event_extra": _build_confirm_event_extra(
            semantic_article_key=str(semantic_article_key or ""),
            decision_origin="ui_confirm_state",
            confirm_gate_kind="confirmed",
            allow_generate=True,
        ),
    }
