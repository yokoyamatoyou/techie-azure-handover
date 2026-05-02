"""Manual legal helper payloads for note_writer_app Phase 04."""
from __future__ import annotations

from typing import Any, Mapping

from note.note_text_format_helpers import _to_plain_dict, _to_plain_list


def collect_current_legal_verified_texts(result: Mapping[str, Any] | None) -> list[str]:
    pipeline_check = _to_plain_dict(_to_plain_dict(result).get("pipeline_check"))
    contract = _to_plain_dict(pipeline_check.get("input_contract"))
    items: list[str] = []
    for key in ("topic", "topic_statement", "speaker_profile", "audience_profile"):
        value = str(contract.get(key) or "").strip()
        if value:
            items.append(value)
    for item in _to_plain_list(contract.get("must_cover")):
        value = str(item or "").strip()
        if value:
            items.append(value)
    for item in _to_plain_list(contract.get("source_inputs")):
        value = str(item or "").strip()
        if value:
            items.append(value)
    return items


def build_manual_legal_result_view(result: Mapping[str, Any] | None) -> dict[str, Any]:
    normalized = _to_plain_dict(result)
    checked_text = str(normalized.get("checked_text", "") or "")
    risk_level = str(normalized.get("risk_level", "none") or "none")
    issues = _to_plain_list(normalized.get("issues"))
    citation_guard = _to_plain_dict(normalized.get("citation_guard"))
    unverified_citations = _to_plain_list(citation_guard.get("unverified_citations"))

    risk_icons = {"none": "check_circle", "low": "info", "medium": "warning"}
    risk_colors = {"none": "text-green-600", "low": "text-yellow-600", "medium": "text-orange-600"}
    risk_card_classes = {
        "none": "w-full mt-4 p-4 bg-green-50",
        "low": "w-full mt-4 p-4 bg-yellow-50",
        "medium": "w-full mt-4 p-4 bg-orange-50",
    }
    if risk_level == "none":
        risk_label_text = "問題なし"
        risk_desc_text = "法的・安全面のリスクは検出されませんでした。"
    elif risk_level == "low":
        risk_label_text = "低リスク"
        risk_desc_text = f"{len(issues)}件の軽微なリスク表現が検出されました。"
    elif risk_level == "medium":
        risk_label_text = "中リスク"
        risk_desc_text = f"{len(issues)}件の注意表現が検出されました。"
    else:
        risk_label_text = "高リスク"
        risk_desc_text = f"{len(issues)}件の高リスク表現が検出されました。"

    issue_rows: list[dict[str, str]] = []
    for index, issue in enumerate(issues, 1):
        issue_dict = _to_plain_dict(issue)
        law = issue_dict.get("law", "不明")
        severity = issue_dict.get("severity", "-")
        issue_rows.append(
            {
                "title": f"#{index}【{law} / {severity}】",
                "original": str(issue_dict.get("original", "")),
                "fixed": str(issue_dict.get("fixed", "")),
                "reason": str(issue_dict.get("reason", "")),
            }
        )

    citation_guard_text = ""
    if unverified_citations:
        citation_guard_text = (
            "未検証の法令・条文・ガイドライン引用を一般表現へ置き換えました: "
            + " / ".join(str(item) for item in unverified_citations[:4])
        )

    return {
        "checked_text": checked_text,
        "risk_level": risk_level,
        "risk_icon_name": risk_icons.get(risk_level, "dangerous"),
        "risk_icon_class": risk_colors.get(risk_level, "text-red-600"),
        "risk_label_text": risk_label_text,
        "risk_desc_text": risk_desc_text,
        "risk_card_class": risk_card_classes.get(risk_level, "w-full mt-4 p-4 bg-red-50"),
        "issues_visible": bool(issues),
        "issue_rows": issue_rows,
        "citation_guard_visible": bool(unverified_citations),
        "citation_guard_text": citation_guard_text,
    }


def build_manual_legal_check_request(
    *,
    use_generated_body: bool,
    legal_input_text: Any,
    generated_body_text: Any,
    current_result: Mapping[str, Any] | None,
) -> dict[str, Any]:
    text = (generated_body_text if use_generated_body else legal_input_text) or ""
    postcheck_text = str(text).strip()
    return {
        "raw_text": text,
        "postcheck_text": postcheck_text,
        "has_text": bool(postcheck_text),
        "copied_legal_input_text": text if use_generated_body else None,
        "verified_texts": collect_current_legal_verified_texts(current_result) if use_generated_body else [],
    }


def build_manual_legal_apply_payload(
    *,
    checked_text: Any,
    title_text: Any,
    lead_text: Any,
    references_text: Any,
    hashtags_text: Any,
) -> dict[str, Any]:
    checked = str(checked_text or "").strip()
    if not checked:
        return {"has_checked_text": False, "checked_text": ""}

    note_parts = [lead_text, checked]
    if references_text:
        note_parts.append(references_text)
    full_parts = [
        title_text,
        lead_text,
        checked,
        references_text,
        hashtags_text,
    ]
    return {
        "has_checked_text": True,
        "checked_text": checked,
        "body_text": checked,
        "note_body_text": "\n\n".join(str(part) for part in note_parts if str(part).strip()),
        "full_text": "\n\n".join(str(part) for part in full_parts if str(part).strip()),
    }
