"""Security gate scaffold for route_0506_structured_blog_ui_v1."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from note.route_0506_usage_ledger import ROUTE_0506_ID, redact_secret_like_text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APPROVED_LOG_ROOT = PROJECT_ROOT / "logs"
APPROVED_UPLOAD_ROOT = PROJECT_ROOT / "note" / "uploads"
APPROVED_UPLOAD_EXTENSIONS = frozenset({".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg", ".webp"})

_LOCAL_PATH_RE = re.compile(
    r"^(?:[A-Za-z]:[\\/]|\\\\|/|file:|\.{1,2}[\\/])",
    re.IGNORECASE,
)
_PROMPT_INJECTION_RE = re.compile(
    r"(ignore (?:all )?(?:previous|system) instructions|"
    r"reveal (?:the )?(?:system prompt|api key|secret)|"
    r"execute this|run this command|developer message)",
    re.IGNORECASE,
)
_FACT_ID_RE = re.compile(r"^F[0-9]{3,}$")


def is_local_file_locator(value: str) -> bool:
    text = str(value or "").strip()
    return bool(text and _LOCAL_PATH_RE.search(text))


def normalize_uploaded_file_locator(
    value: str,
    *,
    approved_upload_root: Path | str | None = None,
) -> str:
    text = str(value or "").strip()
    if not text or text.lower().startswith("file:"):
        return ""
    try:
        path = Path(text).resolve()
        upload_root = Path(approved_upload_root or APPROVED_UPLOAD_ROOT).resolve()
    except (OSError, RuntimeError, TypeError, ValueError):
        return ""
    try:
        in_upload_root = path.is_relative_to(upload_root)
    except AttributeError:  # pragma: no cover - Python <3.9 fallback.
        try:
            path.relative_to(upload_root)
            in_upload_root = True
        except ValueError:
            in_upload_root = False
    if not in_upload_root or path == upload_root:
        return ""
    if path.suffix.lower() not in APPROVED_UPLOAD_EXTENSIONS:
        return ""
    return f"notecode_uploaded_file/{path.name}"


def is_approved_uploaded_file_locator(
    value: str,
    *,
    approved_upload_root: Path | str | None = None,
) -> bool:
    return bool(normalize_uploaded_file_locator(value, approved_upload_root=approved_upload_root))


def is_unsafe_url_label(value: str) -> bool:
    text = str(value or "").strip()
    parsed = urlparse(text)
    if not parsed.scheme:
        return False
    return parsed.scheme.lower() not in {"http", "https"}


def validate_artifact_root(
    artifact_root: Path | str,
    *,
    approved_root: Path | str = APPROVED_LOG_ROOT,
) -> tuple[bool, str]:
    root = Path(artifact_root).resolve()
    approved = Path(approved_root).resolve()
    try:
        return root.is_relative_to(approved), ""
    except AttributeError:  # pragma: no cover - Python <3.9 fallback.
        try:
            root.relative_to(approved)
            return True, ""
        except ValueError:
            return False, "artifact_root_outside_approved_root"


def _source_documents(input_contract: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    docs = input_contract.get("source_documents")
    if not isinstance(docs, list):
        return []
    return [item for item in docs if isinstance(item, Mapping)]


def evaluate_route_0506_security_gate(
    input_contract: Mapping[str, Any],
    *,
    artifact_root: Path | str,
    approved_root: Path | str = APPROVED_LOG_ROOT,
    schema_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blocked_reasons: list[str] = []
    high_unresolved = 0
    critical_unresolved = 0

    root_ok, root_reason = validate_artifact_root(artifact_root, approved_root=approved_root)
    checks.append({"id": "artifact_root_containment", "status": "pass" if root_ok else "fail"})
    if not root_ok:
        critical_unresolved += 1
        blocked_reasons.append(root_reason or "artifact_root_outside_approved_root")

    docs = _source_documents(input_contract)
    source_ok = bool(
        docs
        and any(str(item.get("content") or item.get("text") or item.get("extracted_text") or "").strip() for item in docs)
    )
    checks.append({"id": "source_documents_present", "status": "pass" if source_ok else "fail"})
    if not source_ok:
        high_unresolved += 1
        blocked_reasons.append("source_documents_empty_or_unusable")

    locator_values = _iter_source_locator_values(docs)
    uploaded_locator_hits = [
        value for value in locator_values if is_local_file_locator(value) and is_approved_uploaded_file_locator(value)
    ]
    local_locator_hits = [
        value
        for value in locator_values
        if is_local_file_locator(value) and not is_approved_uploaded_file_locator(value)
    ]
    checks.append(
        {
            "id": "uploaded_file_locator_allowed",
            "status": "pass",
            "count": len(uploaded_locator_hits),
        }
    )
    checks.append({"id": "local_file_locator_rejected", "status": "fail" if local_locator_hits else "pass"})
    if local_locator_hits:
        high_unresolved += 1
        blocked_reasons.append("local_file_locator_rejected")

    unsafe_url_hits = [value for value in locator_values if not is_local_file_locator(value) and is_unsafe_url_label(value)]
    checks.append({"id": "unsafe_url_scheme_rejected", "status": "fail" if unsafe_url_hits else "pass"})
    if unsafe_url_hits:
        high_unresolved += 1
        blocked_reasons.append("unsafe_url_scheme_rejected")

    source_text = "\n".join(
        str(item.get("content") or item.get("text") or item.get("extracted_text") or "") for item in docs
    )
    injection_hit = bool(_PROMPT_INJECTION_RE.search(source_text))
    checks.append({"id": "source_prompt_injection_scan", "status": "fail" if injection_hit else "pass"})
    if injection_hit:
        high_unresolved += 1
        blocked_reasons.append("source_prompt_injection_detected")

    secret_redacted = redact_secret_like_text(source_text) != source_text
    checks.append({"id": "source_secret_like_text_scan", "status": "fail" if secret_redacted else "pass"})
    if secret_redacted:
        high_unresolved += 1
        blocked_reasons.append("secret_like_source_text_detected")

    schema_status = str(dict(schema_report or {}).get("status") or "not_checked")
    if schema_status == "fail":
        high_unresolved += 1
        blocked_reasons.append("schema_compatibility_failed")
    checks.append({"id": "schema_compatibility", "status": schema_status})

    decision = "pass" if critical_unresolved == 0 and high_unresolved == 0 else "blocked"
    return {
        "route_id": ROUTE_0506_ID,
        "decision": decision,
        "critical_unresolved": critical_unresolved,
        "high_unresolved": high_unresolved,
        "medium_unresolved": 0,
        "checks": checks,
        "blocked_reasons": sorted(set(blocked_reasons)),
        "artifact_root": str(artifact_root),
    }


def _iter_source_locator_values(docs: Iterable[Mapping[str, Any]]) -> list[str]:
    values: list[str] = []
    for item in docs:
        for key in ("locator", "url", "canonical_url", "path", "file_path", "filename"):
            text = str(item.get(key) or "").strip()
            if text:
                values.append(text)
    return values


def validate_source_card_schema_compatibility(payload: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    facts = payload.get("facts")
    if not isinstance(facts, list) or not facts:
        errors.append({"path": "facts", "reason": "facts_required"})
    else:
        for index, fact in enumerate(facts):
            if not isinstance(fact, Mapping):
                errors.append({"path": f"facts[{index}]", "reason": "fact_must_be_object"})
                continue
            fact_id = str(fact.get("fact_id") or "")
            if not _FACT_ID_RE.fullmatch(fact_id):
                errors.append({"path": f"facts[{index}].fact_id", "reason": "fact_id_format"})
            importance = fact.get("importance")
            if not isinstance(importance, int) or importance < 1 or importance > 5:
                errors.append({"path": f"facts[{index}].importance", "reason": "importance_range_1_5"})

    return {
        "status": "pass" if not errors else "fail",
        "stage": "source_card_extraction",
        "checked": True,
        "errors": errors,
    }


def write_security_gate_artifact(path: Path | str, report: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dict(report), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
