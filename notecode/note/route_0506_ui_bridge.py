"""UI bridge for the route_0506_structured_blog_ui_v1 one-case route."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from note.route_0506_structured_blog_adapter import (
    DEFAULT_0506_ROOT,
    OPENAI_GENERATION_CANDIDATE,
    prepare_route_0506_adapter_plan,
    resolve_route_0506_genre,
    resolve_route_0506_client_mode,
    run_route_0506_local_scaffold,
)
from note.route_0506_usage_ledger import (
    ROUTE_0506_ID,
    append_usage_ledger_row,
    build_not_sent_usage_row,
    redact_secret_like_text,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_ROOT = PROJECT_ROOT / "logs"
WINDOW3_ARTIFACT_ROOT = LOG_ROOT / "route_0506_saved_source_cli_validation_20260508-234224"
UI_ROUTE_SELECTION_ENV = "NOTECODE_UI_BODY_ROUTE"

_UI_ROUTE_0506_ATTEMPTED = False

_ROUTE_0506_PROGRESS_PHASES: dict[str, tuple[int, str]] = {
    "route_0506_prepare": (35, "Route 0506 の材料を確認中..."),
    "route_0506_security_gate": (45, "Route 0506 の安全確認中..."),
    "route_0506_ui_1case": (65, "Route 0506 で本文を生成中..."),
    "route_0506_blocked": (100, "Route 0506 は安全に停止しました。"),
    "route_0506_completed": (100, "Route 0506 の本文生成が完了しました。"),
}

_ROUTE_0506_BLOCKED_CAUSE_VIEWS: dict[str, dict[str, Any]] = {
    "source_fetch_restricted": {
        "primary": "URLを直接取得できませんでした。",
        "detail": "サイト側の取得制限またはURL取得不可として扱います。API障害や通信環境とは断定しません。",
        "next_actions": [
            "本文を貼り付ける",
            "PDF/テキストをアップロードする",
            "取得可能なURLを指定する",
        ],
        "error_class": "user_input",
        "notify_color": "warning",
    },
    "source_fetch_unavailable": {
        "primary": "URLまたは資料を読み取れませんでした。",
        "detail": "取得できるソースが不足している状態として扱います。推測でAPI障害には丸めません。",
        "next_actions": [
            "URLを確認する",
            "本文を貼り付ける",
            "PDF/テキストをアップロードする",
        ],
        "error_class": "user_input",
        "notify_color": "warning",
    },
    "source_contract_insufficient": {
        "primary": "生成前に必要な材料が足りません。",
        "detail": "記事種別に必要な根拠がそろっていないため、readiness/confirmation gateで停止しました。",
        "next_actions": [
            "事例なら背景・過程・結果が分かる資料を追加する",
            "比較記事なら比較対象ごとの具体的な根拠を追加する",
            "不足箇所を本文貼付またはファイルアップロードで補う",
        ],
        "error_class": "user_input",
        "notify_color": "warning",
    },
    "security_gate": {
        "primary": "安全のため生成を止めました。",
        "detail": "任意ローカルファイル読取や危険な入力を拒否した安全停止です。",
        "next_actions": [
            "ローカルパスを直接指定せず、UIのアップロードから資料を追加する",
            "URLはhttp/httpsの取得可能なものを指定する",
            "資料内に指示文や秘密情報が混ざっていないか確認する",
        ],
        "error_class": "security",
        "notify_color": "warning",
    },
    "draft_writer_transient": {
        "primary": "上流の生成処理が一時的に失敗しました。",
        "detail": "OpenAI/DraftWriter側の一時失敗として扱います。DraftWriterの最小retry後も回復しなかった場合は安全停止します。",
        "next_actions": [
            "時間を置いて再実行する",
            "同じ入力で繰り返す場合はartifactのretry ledgerを確認する",
        ],
        "error_class": "transient",
        "notify_color": "warning",
    },
    "fetch_timeout": {
        "primary": "URL取得が時間内に終わりませんでした。",
        "detail": "fetch timeoutとして扱います。生成APIや通信環境の障害とは断定しません。",
        "next_actions": [
            "本文を貼り付ける",
            "PDF/テキストをアップロードする",
            "軽いURLまたは取得可能なURLに差し替える",
        ],
        "error_class": "user_input",
        "notify_color": "warning",
    },
    "generation_timeout": {
        "primary": "生成処理が時間内に終わりませんでした。",
        "detail": "generation timeoutとして扱います。DraftWriterの最小retry後も回復しなかった場合は安全停止します。",
        "next_actions": [
            "時間を置いて再実行する",
            "繰り返す場合はartifactのretry ledgerを確認する",
        ],
        "error_class": "transient",
        "notify_color": "warning",
    },
    "unknown_timeout": {
        "primary": "処理が時間内に終わりませんでした。",
        "detail": "fetch/generationのどちらか判別できないtimeoutです。推測でAPI障害や通信障害には丸めません。",
        "next_actions": [
            "入力資料とURLを確認する",
            "時間を置いて再実行する",
        ],
        "error_class": "system",
        "notify_color": "warning",
    },
    "quality_blocked": {
        "primary": "壊れた本文を出さないため停止しました。",
        "detail": "内部QAまたは出力ガードが、本文として表示すべきでない出力を止めました。",
        "next_actions": [
            "reason_codeを確認する",
            "資料不足か出力ガード由来かを次のnarrow ownerで切り分ける",
        ],
        "error_class": "route_0506",
        "notify_color": "negative",
    },
    "runtime_config": {
        "primary": "Route 0506 の実行設定が不足しています。",
        "detail": "OpenAI候補実行に必要な環境設定がそろっていないため、送信前に停止しました。",
        "next_actions": [
            "BLOGGEN_LLM_MODEとOPENAI_API_KEYの設定を確認する",
            "API実行が必要な場合は事前承認のうえで別windowで検証する",
        ],
        "error_class": "system",
        "notify_color": "negative",
    },
    "internal_blocked": {
        "primary": "Route 0506 の処理を安全に止めました。",
        "detail": "内部停止として扱います。reason_codeとartifactを確認してください。",
        "next_actions": [
            "artifactとreason_codeを確認する",
            "原因が一つに絞れたら次のnarrow ownerに分ける",
        ],
        "error_class": "route_0506",
        "notify_color": "negative",
    },
}


class Route0506UiBridgeError(RuntimeError):
    """Raised when the UI bridge must stop before invoking route_0506."""


def reset_route_0506_ui_onecase_lock() -> None:
    global _UI_ROUTE_0506_ATTEMPTED
    _UI_ROUTE_0506_ATTEMPTED = False


def resolve_ui_body_route_selection(route_id: str | None = None) -> str:
    selected = str(route_id or "").strip()
    if selected == "":
        return ROUTE_0506_ID
    if selected == "route_a":
        return ""
    if selected == ROUTE_0506_ID:
        return ROUTE_0506_ID
    return ""


def build_ui_selection_snapshot(
    input_contract: Mapping[str, Any],
    *,
    selected_route_id: str,
) -> dict[str, Any]:
    source_documents = input_contract.get("source_documents")
    if not isinstance(source_documents, list):
        source_documents = []
    return {
        "article_type": str(input_contract.get("article_type") or ""),
        "semantic_article_key": str(input_contract.get("semantic_article_key") or ""),
        "ui_journey": dict(input_contract.get("ui_journey") or {}),
        "selected_route_id": str(selected_route_id or ""),
        "source_mode": str(input_contract.get("source_mode") or ""),
        "source_documents_count": len(source_documents),
        "route_a_default_changed": True,
    }


def apply_route_0506_case_study_page_identity_guard(
    input_contract: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Correct category 05 title metadata from deterministic captured page identity."""
    normalized_contract = copy.deepcopy(dict(input_contract or {}))
    source_documents = normalized_contract.get("source_documents")
    if not isinstance(source_documents, list):
        source_documents = []
        normalized_contract["source_documents"] = source_documents

    is_case_study = _is_route_0506_category_05_case_study(normalized_contract)
    before_top_title = str(normalized_contract.get("title") or "").strip()
    before_doc_titles = [
        str(item.get("title") or "").strip() if isinstance(item, Mapping) else ""
        for item in source_documents
    ]
    content_hashes_before = [
        _route_0506_source_content_hash(item)
        for item in source_documents
        if isinstance(item, Mapping)
    ]
    guard: dict[str, Any] = {
        "guard_id": "category_05_case_study_page_identity_guard_v1",
        "status": "not_applicable",
        "category_id": _route_0506_category_id(normalized_contract),
        "category_05_case_study": is_case_study,
        "before_candidate_title": before_top_title or (before_doc_titles[0] if before_doc_titles else ""),
        "after_candidate_title": before_top_title or (before_doc_titles[0] if before_doc_titles else ""),
        "before_source_document_titles": before_doc_titles,
        "after_source_document_titles": list(before_doc_titles),
        "main_entity_detected": "",
        "main_entity_source": "",
        "corrected": False,
        "corrected_fields": [],
        "content_sha256_before": content_hashes_before,
        "content_sha256_after": list(content_hashes_before),
        "source_content_hash_changed": False,
        "url_refetched": False,
        "route_0506_generation": False,
    }
    if not is_case_study:
        return normalized_contract, guard
    if not source_documents:
        guard["status"] = "no_source_documents"
        return normalized_contract, guard

    main_entity = ""
    main_entity_doc_index: int | None = None
    for index, item in enumerate(source_documents):
        if not isinstance(item, dict):
            continue
        entity = _extract_case_study_company_entity(str(item.get("content") or ""))
        if entity:
            main_entity = entity
            main_entity_doc_index = index
            break
    if not main_entity:
        guard["status"] = "main_entity_not_detected"
        return normalized_contract, guard

    guard["main_entity_detected"] = main_entity
    guard["main_entity_source"] = "captured_source_body_label:社名"
    corrected_fields: list[str] = []

    corrected_titles = list(before_doc_titles)
    for index, item in enumerate(source_documents):
        if not isinstance(item, dict):
            continue
        current_title = str(item.get("title") or "").strip()
        if current_title and main_entity not in current_title:
            item["title"] = _correct_case_study_title(current_title, main_entity)
            corrected_titles[index] = str(item["title"])
            corrected_fields.append(f"source_documents[{index}].title")
        metadata = item.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
            item["metadata"] = metadata
        metadata.setdefault("page_identity_main_entity", main_entity)
        metadata.setdefault("page_identity_detection_method", "captured_source_body_label:社名")
        if current_title and main_entity not in current_title:
            metadata.setdefault("original_candidate_title", current_title)
            metadata.setdefault("corrected_candidate_title", str(item.get("title") or ""))
            metadata.setdefault("metadata_identity_guard_status", "corrected")
        else:
            metadata.setdefault("metadata_identity_guard_status", "title_already_matches")
        if main_entity_doc_index == index:
            metadata.setdefault("page_identity_primary_source", True)

    if before_top_title and main_entity not in before_top_title:
        normalized_contract["title"] = _correct_case_study_title(before_top_title, main_entity)
        corrected_fields.append("title")
    elif not before_top_title and corrected_titles:
        normalized_contract["title"] = corrected_titles[0]
        corrected_fields.append("title")

    content_hashes_after = [
        _route_0506_source_content_hash(item)
        for item in source_documents
        if isinstance(item, Mapping)
    ]
    after_top_title = str(normalized_contract.get("title") or "").strip()
    guard.update(
        {
            "status": "corrected" if corrected_fields else "title_already_matches",
            "after_candidate_title": after_top_title or (corrected_titles[0] if corrected_titles else ""),
            "after_source_document_titles": corrected_titles,
            "corrected": bool(corrected_fields),
            "corrected_fields": corrected_fields,
            "content_sha256_after": content_hashes_after,
            "source_content_hash_changed": content_hashes_before != content_hashes_after,
        }
    )
    return normalized_contract, guard


def _route_0506_category_id(input_contract: Mapping[str, Any]) -> str:
    ui_journey = input_contract.get("ui_journey")
    if isinstance(ui_journey, Mapping):
        target_key = str(ui_journey.get("target_key") or "").strip()
        if target_key:
            return target_key
    context = input_contract.get("route_0506_test_context")
    if isinstance(context, Mapping):
        category_id = str(context.get("category_id") or "").strip()
        if category_id:
            return category_id
    return ""


def _is_route_0506_category_05_case_study(input_contract: Mapping[str, Any]) -> bool:
    category_id = _route_0506_category_id(input_contract)
    article_type = str(input_contract.get("article_type") or "").strip()
    semantic_key = str(input_contract.get("semantic_article_key") or "").strip()
    return (
        category_id == "category_05_case_study"
        or (article_type == "case_study" and semantic_key == "implementation_case")
    )


def _extract_case_study_company_entity(content: str) -> str:
    lines = [line.strip() for line in str(content or "").splitlines()]
    for index, line in enumerate(lines):
        if line == "社名":
            for candidate in lines[index + 1 : index + 6]:
                entity = _normalize_case_study_company_entity(candidate)
                if entity:
                    return entity
        match = re.match(r"^社名\s+(.+)$", line)
        if match:
            entity = _normalize_case_study_company_entity(match.group(1))
            if entity:
                return entity
    return ""


def _normalize_case_study_company_entity(value: str) -> str:
    candidate = str(value or "").strip()
    if not candidate:
        return ""
    candidate = re.sub(r"\s+", "", candidate)
    if len(candidate) > 80:
        return ""
    if not any(marker in candidate for marker in ("株式会社", "有限会社", "合同会社", "学校法人", "医療法人", "社会福祉法人", "協同組合")):
        return ""
    if any(noise in candidate for noise in ("導入事例", "SmartHR", "詳しく見る", "一覧を見る")):
        return ""
    return candidate


def _correct_case_study_title(current_title: str, main_entity: str) -> str:
    title = str(current_title or "").strip()
    if not title:
        return main_entity
    if "|" in title:
        suffix = title.split("|", 1)[1].strip()
        if suffix:
            return f"{main_entity} | {suffix}"
    return main_entity


def _route_0506_source_content_hash(source_document: Mapping[str, Any]) -> str:
    content = str(source_document.get("content") or "")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def build_route_0506_progress_view(phase: str, detail: str = "") -> dict[str, Any]:
    normalized_phase = str(phase or "").strip().lower()
    percent, label = _ROUTE_0506_PROGRESS_PHASES.get(
        normalized_phase,
        (0, "Route 0506 で処理中..."),
    )
    return {
        "phase": normalized_phase,
        "percent": percent,
        "label_text": label,
        "detail": str(detail or "").strip(),
    }


def build_route_0506_user_facing_blocked_view(
    result: Mapping[str, Any],
    *,
    security_gate: Mapping[str, Any] | None = None,
    artifact_root: Path | str | None = None,
) -> dict[str, Any]:
    normalized_result = dict(result or {})
    raw_security_gate = security_gate if isinstance(security_gate, Mapping) else normalized_result.get("security_gate")
    normalized_security_gate = dict(raw_security_gate) if isinstance(raw_security_gate, Mapping) else {}
    raw_quality_report = normalized_result.get("quality_report")
    quality_report = dict(raw_quality_report) if isinstance(raw_quality_report, Mapping) else {}
    reason_code = str(
        normalized_result.get("reason_code")
        or quality_report.get("reason_code")
        or "ROUTE_0506_BLOCKED"
    )
    blocked_reason = redact_secret_like_text(
        str(
            normalized_result.get("blocked_reason_redacted")
            or normalized_result.get("blocked_reason")
            or ""
        )
    )[:1200]
    cause_key = _classify_route_0506_blocked_cause(
        reason_code=reason_code,
        blocked_reason=blocked_reason,
        security_gate=normalized_security_gate,
    )
    spec = dict(_ROUTE_0506_BLOCKED_CAUSE_VIEWS.get(cause_key) or _ROUTE_0506_BLOCKED_CAUSE_VIEWS["internal_blocked"])
    gate_reasons = _security_gate_reason_tokens(normalized_security_gate)
    artifact = str(artifact_root or normalized_result.get("artifact_root") or "").strip()

    detail_lines = [
        str(spec["detail"]),
        f"reason_code: {reason_code}",
    ]
    if blocked_reason:
        detail_lines.append(f"detail: {blocked_reason}")
    if gate_reasons:
        detail_lines.append(f"security_gate: {' / '.join(gate_reasons[:5])}")
    if artifact:
        detail_lines.append(f"artifact: {artifact}")

    next_actions = [str(item) for item in spec.get("next_actions", []) if str(item or "").strip()]
    source_error_lines = [
        "### 主表示",
        str(spec["primary"]),
        "",
        "### 詳細",
        *[f"- {line}" for line in detail_lines],
        "",
        "### 次にできること",
        *[f"- {line}" for line in next_actions],
    ]
    progress = build_route_0506_progress_view("route_0506_blocked")
    return {
        "cause_key": cause_key,
        "primary_message": str(spec["primary"]),
        "detail_message": "\n".join(detail_lines),
        "next_action": "\n".join(next_actions),
        "status_text": str(spec["primary"]),
        "source_error_content": "\n".join(source_error_lines).strip(),
        "notify_text": str(spec["primary"]),
        "notify_color": str(spec.get("notify_color") or "warning"),
        "outcome": f"blocked_route_0506_{cause_key}",
        "reason_code": reason_code,
        "error_class": str(spec.get("error_class") or "route_0506"),
        "blocked_reason_redacted": blocked_reason,
        "generation_progress_note_text": f"{progress['label_text']} reason_code={reason_code}",
        "generation_progress_note_visible": True,
    }


def _classify_route_0506_blocked_cause(
    *,
    reason_code: str,
    blocked_reason: str,
    security_gate: Mapping[str, Any],
) -> str:
    tokens = [str(reason_code or ""), str(blocked_reason or "")]
    tokens.extend(_security_gate_reason_tokens(security_gate))
    haystack = " ".join(tokens).lower()
    if ("fetch" in haystack or "source" in haystack or "url" in haystack) and "timeout" in haystack:
        return "fetch_timeout"
    if "robots" in haystack or "http_403_forbidden" in haystack or "403" in haystack or "forbidden" in haystack:
        return "source_fetch_restricted"
    if "inp_source_fetch_failed" in haystack or "fetch_failed" in haystack or "url取得不可" in haystack:
        return "source_fetch_unavailable"
    if (
        "inp_source_context_insufficient" in haystack
        or "ui_confirmation_gate_blocked" in haystack
        or "source_documents_empty_or_unusable" in haystack
        or "source_documents_required" in haystack
        or "source_documents_with_content_required" in haystack
    ):
        return "source_contract_insufficient"
    if (
        "route_0506_security_gate_blocked" in haystack
        or "local_file_locator_rejected" in haystack
        or "unsafe_url_scheme_rejected" in haystack
        or "source_prompt_injection_detected" in haystack
        or "secret_like_source_text_detected" in haystack
        or "schema_compatibility_failed" in haystack
    ):
        return "security_gate"
    if "502" in haystack or "bad gateway" in haystack or "draftwriter" in haystack:
        return "draft_writer_transient"
    if (
        "generation timeout" in haystack
        or "draft timeout" in haystack
        or "request timed out" in haystack
        or ("generation" in haystack and "timeout" in haystack)
    ):
        return "generation_timeout"
    if "timeout" in haystack or "timed out" in haystack:
        return "unknown_timeout"
    if "requires_bloggen_llm_mode_openai" in haystack or "requires_openai_api_key" in haystack:
        return "runtime_config"
    if (
        "sys_quality" in haystack
        or "qa" in haystack
        or "quality" in haystack
        or "visible_output_contract" in haystack
        or "stage_output_guard" in haystack
        or "meta-review" in haystack
        or "wrapper" in haystack
    ):
        return "quality_blocked"
    return "internal_blocked"


def _security_gate_reason_tokens(security_gate: Mapping[str, Any]) -> list[str]:
    tokens: list[str] = []
    blocked_reasons = security_gate.get("blocked_reasons")
    if isinstance(blocked_reasons, list):
        tokens.extend(str(item) for item in blocked_reasons if str(item or "").strip())
    checks = security_gate.get("checks")
    if isinstance(checks, list):
        for item in checks:
            if not isinstance(item, Mapping):
                continue
            status = str(item.get("status") or "").strip().lower()
            check_id = str(item.get("id") or "").strip()
            if check_id and status == "fail":
                tokens.append(check_id)
    return tokens


def run_route_0506_ui_onecase(
    input_contract: Mapping[str, Any],
    *,
    artifact_root: Path | str | None = None,
    route_root: Path | str = DEFAULT_0506_ROOT,
    window3_artifact_root: Path | str = WINDOW3_ARTIFACT_ROOT,
    enforce_onecase_lock: bool = True,
    client_mode: str | None = None,
) -> dict[str, Any]:
    global _UI_ROUTE_0506_ATTEMPTED
    if enforce_onecase_lock and _UI_ROUTE_0506_ATTEMPTED:
        raise Route0506UiBridgeError("route_0506_ui_onecase_already_attempted")
    if enforce_onecase_lock:
        _UI_ROUTE_0506_ATTEMPTED = True

    root = Path(artifact_root) if artifact_root is not None else LOG_ROOT / f"route_0506_ui_1case_{_now_stamp()}"
    root.mkdir(parents=True, exist_ok=True)
    normalized_input_contract, metadata_identity_guard = apply_route_0506_case_study_page_identity_guard(input_contract)
    _write_json(root / "input_contract.json", normalized_input_contract)
    _write_json(root / "metadata_identity_guard.json", metadata_identity_guard)
    resolved_client_mode = resolve_route_0506_client_mode(client_mode)
    api_send_requested = resolved_client_mode == OPENAI_GENERATION_CANDIDATE
    snapshot = build_ui_selection_snapshot(normalized_input_contract, selected_route_id=ROUTE_0506_ID)
    _write_json(root / "ui_selection_snapshot.json", snapshot)
    _write_usage_ledgers(root, client_mode=resolved_client_mode)
    preflight_plan: dict[str, Any] = {}
    try:
        preflight_plan = prepare_route_0506_adapter_plan(
            normalized_input_contract,
            artifact_root=root,
            client_mode=resolved_client_mode,
        )
        _write_json(root / "source_snapshot.json", dict(preflight_plan.get("source_snapshot") or {}))
        _write_json(root / "security_gate.json", dict(preflight_plan.get("security_gate") or {}))
    except Exception as exc:
        safe_error = redact_secret_like_text(f"{type(exc).__name__}: {exc}")[:1200]
        _write_json(root / "source_snapshot.json", {})
        _write_json(
            root / "security_gate.json",
            {
                "route_id": ROUTE_0506_ID,
                "decision": "blocked",
                "critical_unresolved": 0,
                "high_unresolved": 1,
                "medium_unresolved": 0,
                "checks": [{"id": "adapter_preflight", "status": "fail"}],
                "blocked_reasons": [safe_error],
                "artifact_root": str(root),
            },
        )

    result: dict[str, Any]
    safe_error = ""
    try:
        result = dict(
            run_route_0506_local_scaffold(
                normalized_input_contract,
                artifact_root=root,
                route_root=Path(route_root),
                run_id="route_0506_ui_1case",
                client_mode=resolved_client_mode,
            )
        )
    except Exception as exc:
        safe_error = redact_secret_like_text(f"{type(exc).__name__}: {exc}")[:1200]
        result = {
            "route_id": ROUTE_0506_ID,
            "blocked": True,
            "reason_code": "ROUTE_0506_UI_INVOCATION_FAILED",
            "blocked_reason_redacted": safe_error,
            "article_type": snapshot["article_type"],
            "semantic_article_key": snapshot["semantic_article_key"],
            "ui_journey": snapshot["ui_journey"],
            "body": "",
            "full_text": "",
            "quality_report": {"blocked": True, "reason_code": "ROUTE_0506_UI_INVOCATION_FAILED"},
            "artifact_root": str(root),
        }
        _write_json(root / "blocked.json", result)
        route_dir = root / "route_0506"
        route_dir.mkdir(parents=True, exist_ok=True)
        _write_json(route_dir / "latest_generation_output.json", result)
        (route_dir / "latest_generation_output.md").write_text("", encoding="utf-8")
        _write_json(route_dir / "latest_generation_quality_report.json", result["quality_report"])

    security_gate = _read_json(root / "security_gate.json")
    if security_gate:
        _write_json(root / "security_gate_report.json", security_gate)
    else:
        security_gate = {
            "route_id": ROUTE_0506_ID,
            "decision": "blocked",
            "critical_unresolved": 0,
            "high_unresolved": 1,
            "medium_unresolved": 0,
            "checks": [{"id": "ui_invocation", "status": "fail"}],
            "blocked_reasons": [safe_error or "security_gate_artifact_missing"],
            "artifact_root": str(root),
        }
        _write_json(root / "security_gate.json", security_gate)
        _write_json(root / "security_gate_report.json", security_gate)
        result["blocked"] = True
        result["reason_code"] = str(result.get("reason_code") or "ROUTE_0506_SECURITY_GATE_MISSING")
        _write_json(root / "blocked.json", result)

    source_snapshot = _read_json(root / "source_snapshot.json")
    mapping_report = build_mapping_collision_report(
        normalized_input_contract,
        ui_selection_snapshot=snapshot,
        source_snapshot=source_snapshot,
        window3_artifact_root=Path(window3_artifact_root),
    )
    _write_json(root / "mapping_collision_report.json", mapping_report)

    route_status = "blocked" if result.get("blocked") else "completed"
    body_char_count = len(str(result.get("body") or result.get("full_text") or ""))
    user_message_view: dict[str, Any] = {}
    if route_status == "blocked":
        result["security_gate"] = dict(security_gate)
        user_message_view = build_route_0506_user_facing_blocked_view(
            result,
            security_gate=security_gate,
            artifact_root=root,
        )
        result["user_message_view"] = user_message_view
        _write_json(root / "user_message_view.json", user_message_view)
        _write_json(root / "blocked.json", result)
        route_dir = root / "route_0506"
        route_dir.mkdir(parents=True, exist_ok=True)
        _write_json(route_dir / "latest_generation_output.json", result)
    summary = {
        "phase_window": "Window 4 current UI body generation 1case only",
        "status": route_status,
        "route_0506_status": route_status,
        "selected_route_id": ROUTE_0506_ID,
        "article_type": snapshot["article_type"],
        "semantic_article_key": snapshot["semantic_article_key"],
        "ui_journey": snapshot["ui_journey"],
        "source_mode": snapshot["source_mode"],
        "source_documents_count": snapshot["source_documents_count"],
        "genre_id": resolve_route_0506_genre(normalized_input_contract),
        "metadata_identity_guard_status": str(metadata_identity_guard.get("status") or ""),
        "metadata_identity_corrected": bool(metadata_identity_guard.get("corrected")),
        "metadata_identity_main_entity": str(metadata_identity_guard.get("main_entity_detected") or ""),
        "body_char_count": body_char_count if route_status == "completed" else 0,
        "route_a_default_changed": True,
        "route_a_regenerated": False,
        "route_a_fallback_used": False,
        "api_send": api_send_requested,
        "actual_api_call_count": None if api_send_requested else 0,
        "client_mode": resolved_client_mode,
        "model": os.getenv("OPENAI_MODEL", "gpt-5.4-mini") if api_send_requested else "",
        "reasoning_effort": os.getenv("OPENAI_REASONING_EFFORT", "high") if api_send_requested else "",
        "url_refetch": False,
        "local_file_fallback": False,
        "threshold_relaxed": False,
        "repair_acceptance_relaxed": False,
        "prompt_added_for_quality_tuning": False,
        "old_rejected_routes_used": False,
        "security_gate_status": str(security_gate.get("decision") or "blocked"),
        "mapping_collision_status": mapping_report["status"],
        "mapping_collision_suspected": bool(mapping_report["mapping_collision_suspected"]),
        "source_snapshot_hash": str(source_snapshot.get("canonical_hash") or ""),
        "window3_source_snapshot_hash": str(mapping_report.get("window3_source_snapshot_hash") or ""),
        "artifact_completeness_status": "pending",
        "artifact_missing": [],
        "artifact_root": str(root),
        "blocked_cause_key": str(user_message_view.get("cause_key") or ""),
        "user_message_primary": str(user_message_view.get("primary_message") or ""),
    }
    _write_json(root / "validation_summary.json", summary)
    _write_manual_notes(root / "manual_review_notes.md", summary, mapping_report)
    completeness = _artifact_completeness(root, blocked=(route_status == "blocked"))
    summary["artifact_completeness_status"] = completeness["status"]
    summary["artifact_missing"] = completeness["missing"]
    _write_json(root / "validation_summary.json", summary)
    _write_manual_notes(root / "manual_review_notes.md", summary, mapping_report)
    return {
        **result,
        "validation_summary": summary,
        "ui_selection_snapshot": snapshot,
        "metadata_identity_guard": metadata_identity_guard,
    }


def build_mapping_collision_report(
    input_contract: Mapping[str, Any],
    *,
    ui_selection_snapshot: Mapping[str, Any],
    source_snapshot: Mapping[str, Any],
    window3_artifact_root: Path,
) -> dict[str, Any]:
    window3_summary = _read_json(window3_artifact_root / "validation_summary.json")
    window3_source_snapshot = _read_json(window3_artifact_root / "source_snapshot.json")
    window3_input_contract = _read_json(window3_artifact_root / "input_contract.json")
    current = {
        "article_type": str(input_contract.get("article_type") or ""),
        "semantic_article_key": str(input_contract.get("semantic_article_key") or ""),
        "ui_journey": dict(input_contract.get("ui_journey") or {}),
        "audience": str(input_contract.get("audience_profile") or input_contract.get("target_reader") or ""),
        "goal": str(input_contract.get("topic_statement") or input_contract.get("core_message") or ""),
        "source_mode": str(input_contract.get("source_mode") or ""),
        "source_documents_count": len(input_contract.get("source_documents") or []),
        "source_snapshot_hash": str(source_snapshot.get("canonical_hash") or ""),
    }
    baseline_mapping = dict(window3_summary.get("mapping") or {})
    baseline = {
        "article_type": str(window3_summary.get("article_type") or baseline_mapping.get("article_type") or ""),
        "semantic_article_key": str(
            window3_summary.get("semantic_article_key") or baseline_mapping.get("semantic_article_key") or ""
        ),
        "ui_journey": dict(window3_input_contract.get("ui_journey") or baseline_mapping.get("ui_journey") or {}),
        "audience": str(window3_input_contract.get("audience_profile") or window3_input_contract.get("target_reader") or ""),
        "goal": str(window3_input_contract.get("topic_statement") or window3_input_contract.get("core_message") or ""),
        "source_mode": str(window3_summary.get("source_mode") or window3_input_contract.get("source_mode") or ""),
        "source_documents_count": int(window3_source_snapshot.get("source_count") or 0),
        "source_snapshot_hash": str(window3_source_snapshot.get("canonical_hash") or ""),
    }
    diffs = [
        {"field": key, "window3": baseline.get(key), "ui": current.get(key)}
        for key in sorted(current)
        if current.get(key) != baseline.get(key)
    ]
    return {
        "status": "suspected" if diffs else "not_suspected",
        "mapping_collision_suspected": bool(diffs),
        "selected_route_id": str(ui_selection_snapshot.get("selected_route_id") or ""),
        "window3_artifact_root": str(window3_artifact_root),
        "window3_source_snapshot_hash": baseline["source_snapshot_hash"],
        "ui_source_snapshot_hash": current["source_snapshot_hash"],
        "input_diffs": diffs,
        "quality_tuning_started": False,
    }


def _write_usage_ledgers(root: Path, *, client_mode: str) -> None:
    if client_mode == OPENAI_GENERATION_CANDIDATE:
        row = {
            "stage": "window_4_ui_1case_openai_generation_candidate",
            "artifact_root": str(root),
            "status": "requested_unmetered",
            "model": os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
            "reasoning_effort": os.getenv("OPENAI_REASONING_EFFORT", "high"),
            "actual_usage_available": False,
        }
    else:
        row = build_not_sent_usage_row(
            stage="window_4_ui_1case_local_deterministic",
            artifact_root=root,
            blocked_reason="api_send_forbidden_window_4_local_deterministic",
        )
    normalized = append_usage_ledger_row(root / "usage_ledger.jsonl", row)
    append_usage_ledger_row(root / "api_usage_ledger.jsonl", normalized)


def _artifact_completeness(root: Path, *, blocked: bool) -> dict[str, Any]:
    required = [
        root / "source_snapshot.json",
        root / "ui_selection_snapshot.json",
        root / "route_0506" / "latest_generation_output.json",
        root / "route_0506" / "latest_generation_output.md",
        root / "route_0506" / "latest_generation_quality_report.json",
        root / "security_gate_report.json",
        root / "api_usage_ledger.jsonl",
        root / "validation_summary.json",
        root / "manual_review_notes.md",
    ]
    if blocked:
        required.append(root / "blocked.json")
    missing = [str(path) for path in required if not path.exists()]
    return {"status": "complete" if not missing else "incomplete", "missing": missing}


def _write_manual_notes(path: Path, summary: Mapping[str, Any], mapping_report: Mapping[str, Any]) -> None:
    lines = [
        "# Route 0506 UI 1case Manual Review Notes",
        "",
        f"- phase/window: {summary.get('phase_window')}",
        f"- selected_route_id: {summary.get('selected_route_id')}",
        f"- route_0506_status: {summary.get('route_0506_status')}",
        f"- article_type: {summary.get('article_type')}",
        f"- semantic_article_key: {summary.get('semantic_article_key')}",
        f"- ui_journey: {json.dumps(summary.get('ui_journey') or {}, ensure_ascii=False, sort_keys=True)}",
        f"- source_snapshot_hash: {summary.get('source_snapshot_hash')}",
        f"- security_gate_status: {summary.get('security_gate_status')}",
        f"- mapping_collision_status: {summary.get('mapping_collision_status')}",
        f"- mapping_input_diff_count: {len(mapping_report.get('input_diffs') or [])}",
        f"- body_char_count: {summary.get('body_char_count')}",
        f"- client_mode: {summary.get('client_mode')}",
        f"- api_send: {str(bool(summary.get('api_send'))).lower()}",
        "- url_refetch: false",
        "- quality_tuning: not_started",
        "- japanese_blog_naturalness_note: Window 5 compare owner should review against saved Route A artifact.",
    ]
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")
