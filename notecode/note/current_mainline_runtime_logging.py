from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

from note.published_post_inventory import (
    append_published_post_inventory_entry,
    build_published_post_inventory_entry,
)

PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT_DIR = Path(__file__).resolve().parents[2]
LATEST_GENERATION_TEXT_PATH = PROJECT_ROOT_DIR / "logs" / "latest_generation_output.txt"
LATEST_GENERATION_JSON_PATH = PROJECT_ROOT_DIR / "logs" / "latest_generation_output.json"
LATEST_GENERATION_QUALITY_REPORT_PATH = PROJECT_ROOT_DIR / "logs" / "latest_generation_quality_report.json"
LATEST_GENERATION_TEXT_PATH_WORKSPACE = WORKSPACE_ROOT_DIR / "logs" / "latest_generation_output.txt"
LATEST_GENERATION_JSON_PATH_WORKSPACE = WORKSPACE_ROOT_DIR / "logs" / "latest_generation_output.json"
LATEST_GENERATION_QUALITY_REPORT_PATH_WORKSPACE = WORKSPACE_ROOT_DIR / "logs" / "latest_generation_quality_report.json"
GENERATION_AUDIT_JSONL_PATH = PROJECT_ROOT_DIR / "logs" / "generation_audit_log.jsonl"
GENERATION_AUDIT_JSONL_PATH_WORKSPACE = WORKSPACE_ROOT_DIR / "logs" / "generation_audit_log.jsonl"
LATEST_UI_JOURNEY_PATH = PROJECT_ROOT_DIR / "logs" / "latest_ui_journey.json"
LATEST_UI_JOURNEY_PATH_WORKSPACE = WORKSPACE_ROOT_DIR / "logs" / "latest_ui_journey.json"
UI_JOURNEY_JSONL_PATH = PROJECT_ROOT_DIR / "logs" / "ui_journey_log.jsonl"
UI_JOURNEY_JSONL_PATH_WORKSPACE = WORKSPACE_ROOT_DIR / "logs" / "ui_journey_log.jsonl"

logger = logging.getLogger(__name__)

_UI_JOURNEY_LOG_MAX_BYTES = 512 * 1024
_UI_JOURNEY_LOG_KEEP_LINES = 400
_UI_JOURNEY_MAX_EVENTS = 40
_UI_JOURNEY_CACHE_MAX_ATTEMPTS = 8
_UI_JOURNEY_CACHE: Dict[str, Dict[str, Any]] = {}

_ALGORITHM_STAGE_OWNERS: Dict[str, str] = {
    "contract_resolve": "note.newalgorithm_pipeline.input_contract.resolve_input_contract",
    "source_digest": "note.simple_note_pipeline.rendering.build_source_pack",
    "single_pass_generation": "note.simple_note_pipeline.pipeline.MinimalPipeline.generate",
    "light_guard": "note.simple_note_pipeline.quality_guard.measure_diagnostics",
    "repair": "note.simple_note_pipeline.prompt_builder.build_repair_prompt_from_diagnostics",
    "discourse_plan": "note.newalgorithm_pipeline.discourse_planner.build_discourse_plan",
    "section_generation": "note.newalgorithm_pipeline.section_generator.generate_sections",
    "dedupe": "note.newalgorithm_pipeline.dedupe_adapter.run_semantic_dedupe",
    "editor_guard": "note.newalgorithm_pipeline.editor_guard.apply_minimal_editor_guard",
    "resonance": "human_resonance.pipeline.HumanResonancePipeline.process",
    "quality_pipeline": "human_resonance2.quality_pipeline.QualityPipeline.process",
    "legal_postcheck": "note.newalgorithm_pipeline.legal_postcheck.run_legal_postcheck",
    "output_format": "note.newalgorithm_pipeline.output_formatter.format_output",
    "telemetry": "note.newalgorithm_pipeline.telemetry_writer.build_pipeline_check",
}


def _to_plain_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _to_plain_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _safe_round_float(value: Any, digits: int = 4, default: float = 0.0) -> float:
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return default


def _sanitize_log_text(value: Any, limit: int = 160) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").replace("\t", " ").replace("\x00", "")
    text = " ".join(text.split())
    if len(text) > limit:
        return text[:limit] + "..."
    return text


def _stable_text_hash(value: Any) -> str:
    normalized = _sanitize_log_text(value, limit=400)
    if not normalized:
        return ""
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]


def _build_source_target_summary(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if re.match(r"^https?://", raw, re.IGNORECASE):
        parsed = urlparse(raw)
        host = (parsed.netloc or "").lower()
        tail = Path(parsed.path or "").name[:24]
        if host and tail:
            return f"{host}/{tail}"
        return host or _sanitize_log_text(raw, limit=48)
    source_path = Path(raw)
    file_name = source_path.name[:32]
    suffix = source_path.suffix.lower()
    if file_name:
        return file_name
    if suffix:
        return f"file:{suffix}"
    return _sanitize_log_text(raw, limit=48)


def _build_source_ui_summary(source_items: Any) -> Dict[str, Any]:
    items = _to_plain_list(source_items)
    source_types: Dict[str, int] = {}
    targets: List[str] = []
    for item in items:
        source_type = ""
        value = ""
        if isinstance(item, dict):
            source_type = str(item.get("source_type", "") or "")
            value = str(item.get("value", "") or item.get("locator", "") or "")
        else:
            source_type = str(getattr(item, "source_type", "") or "")
            value = str(getattr(item, "value", "") or getattr(item, "locator", "") or "")
        normalized_type = source_type or "unknown"
        source_types[normalized_type] = int(source_types.get(normalized_type, 0)) + 1
        summarized = _build_source_target_summary(value)
        if summarized and summarized not in targets and len(targets) < 5:
            targets.append(summarized)
    return {
        "source_count": len(items),
        "source_types": source_types,
        "source_targets": targets,
    }


def _build_ui_input_summary(user_prompt_text: str, source_items: Any) -> Dict[str, Any]:
    prompt = str(user_prompt_text or "").strip()
    summary = {
        "prompt_chars": len(prompt),
        "prompt_hash": _stable_text_hash(prompt),
        "prompt_excerpt": _sanitize_log_text(prompt, limit=180),
    }
    summary.update(_build_source_ui_summary(source_items))
    return summary


def _build_ui_selection_summary(selections: Dict[str, Any]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    for key, value in _to_plain_dict(selections).items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, bool):
            summary[str(key)] = value
            continue
        summary[str(key)] = _sanitize_log_text(value, limit=64)
    return summary


def _build_ui_output_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    normalized = _to_plain_dict(result)
    full_text = str(normalized.get("full_text", "") or "")
    return {
        "title": _sanitize_log_text(normalized.get("title", ""), limit=96),
        "title_chars": len(str(normalized.get("title", "") or "")),
        "lead_chars": len(str(normalized.get("lead", "") or "")),
        "body_chars": len(str(normalized.get("body", "") or "")),
        "full_text_chars": len(full_text),
        "linkedin_chars": len(str(normalized.get("linkedin_text", "") or "")),
        "runtime_reason_code": str(
            normalized.get("runtime_reason_code") or normalized.get("reason_code") or "OK"
        ),
        "blocked_output_redacted": bool(normalized.get("blocked_output_redacted", False)),
        "ui_transient_retry_count": int(normalized.get("ui_transient_retry_count", 0) or 0),
        "ui_guard_retry_count": int(normalized.get("ui_guard_retry_count", 0) or 0),
        "ui_quality_warning_only": bool(normalized.get("ui_quality_warning_only", False)),
    }


def _build_ui_latest_decision_summary(event_payload: Dict[str, Any]) -> Dict[str, Any]:
    event_name = str(event_payload.get("event") or "").strip()
    phase = str(event_payload.get("phase") or "").strip()
    if phase != "confirm" and not event_name.startswith("journey_confirm"):
        return {}

    extra = _to_plain_dict(event_payload.get("extra"))
    selection_summary = _to_plain_dict(event_payload.get("selection_summary"))
    latest_decision: Dict[str, Any] = {
        "reason_code": str(event_payload.get("runtime_reason_code") or ""),
        "error_class": str(event_payload.get("runtime_error_class") or ""),
        "status_text": str(event_payload.get("status_text") or ""),
        "needs_input_fields": _to_plain_list(event_payload.get("needs_input_fields"))[:5],
        "semantic_article_key": str(
            extra.get("semantic_article_key") or selection_summary.get("semantic_article_key") or ""
        ),
        "decision_origin": str(extra.get("decision_origin") or ""),
        "confirm_gate_kind": str(extra.get("confirm_gate_kind") or ""),
        "source_fit_status": str(extra.get("source_fit_status") or ""),
        "source_grounding_status": str(extra.get("source_grounding_status") or ""),
        "source_grounding_required": bool(extra.get("source_grounding_required", False)),
        "input_decision_action": str(extra.get("input_decision_action") or ""),
    }
    if "allow_generate" in extra:
        latest_decision["allow_generate"] = bool(extra.get("allow_generate"))
    return latest_decision


def _copy_optional_str(target: Dict[str, Any], key: str, value: Any) -> None:
    text = str(value or "").strip()
    if text:
        target[key] = text


def _copy_optional_bool(target: Dict[str, Any], key: str, source: Dict[str, Any]) -> None:
    if key in source:
        target[key] = bool(source.get(key))


def _copy_optional_int(target: Dict[str, Any], key: str, source: Dict[str, Any]) -> None:
    if key not in source:
        return
    try:
        target[key] = int(source.get(key) or 0)
    except (TypeError, ValueError):
        return


def _build_ui_latest_generation_gate_summary(event_payload: Dict[str, Any]) -> Dict[str, Any]:
    event_name = str(event_payload.get("event") or "").strip()
    extra = _to_plain_dict(event_payload.get("extra"))
    generation_gate_kind = str(extra.get("generation_gate_kind") or "").strip()
    if not event_name.startswith("generation_") or not generation_gate_kind:
        return {}

    selection_summary = _to_plain_dict(event_payload.get("selection_summary"))
    latest_generation_gate: Dict[str, Any] = {
        "event": event_name,
        "phase": str(event_payload.get("phase") or "").strip(),
        "reason_code": str(event_payload.get("runtime_reason_code") or ""),
        "error_class": str(event_payload.get("runtime_error_class") or ""),
        "status_text": str(event_payload.get("status_text") or ""),
        "needs_input_fields": _to_plain_list(event_payload.get("needs_input_fields"))[:5],
        "article_type": str(event_payload.get("article_type") or ""),
        "semantic_article_key": str(
            extra.get("semantic_article_key") or selection_summary.get("semantic_article_key") or ""
        ),
        "decision_origin": str(extra.get("decision_origin") or ""),
        "generation_gate_kind": generation_gate_kind,
        "required_action": str(extra.get("required_action") or ""),
    }
    _copy_optional_bool(latest_generation_gate, "allow_generate", extra)
    if "selection_confirmed" in extra:
        latest_generation_gate["selection_confirmed"] = bool(extra.get("selection_confirmed"))
    elif "confirmed" in selection_summary:
        latest_generation_gate["selection_confirmed"] = bool(selection_summary.get("confirmed"))
    _copy_optional_bool(latest_generation_gate, "confirmed_signature_present", extra)
    _copy_optional_str(latest_generation_gate, "confirmation_state", extra.get("confirmation_state"))
    _copy_optional_str(latest_generation_gate, "required_step", extra.get("required_step"))
    _copy_optional_int(latest_generation_gate, "required_journey_stage", extra)
    _copy_optional_str(
        latest_generation_gate,
        "selected_article_type_label",
        extra.get("selected_article_type_label"),
    )
    _copy_optional_str(
        latest_generation_gate,
        "resolved_article_type",
        extra.get("resolved_article_type"),
    )
    _copy_optional_str(
        latest_generation_gate,
        "article_type_resolution_state",
        extra.get("article_type_resolution_state"),
    )
    _copy_optional_int(latest_generation_gate, "term_count", extra)
    return latest_generation_gate


def _trim_jsonl_file(target: Path) -> None:
    try:
        if not target.exists() or target.stat().st_size <= _UI_JOURNEY_LOG_MAX_BYTES:
            return
        lines = target.read_text(encoding="utf-8").splitlines()
        if len(lines) <= _UI_JOURNEY_LOG_KEEP_LINES:
            return
        trimmed = "\n".join(lines[-_UI_JOURNEY_LOG_KEEP_LINES :]) + "\n"
        target.write_text(trimmed, encoding="utf-8")
    except Exception as exc:
        logger.warning("Failed to trim ui journey log path=%s: %s", target, exc)


def append_ui_journey_event(
    *,
    attempt_id: str,
    event: str,
    article_type: str = "",
    phase: str = "",
    user_prompt_text: str = "",
    source_items: Any = None,
    selections: Dict[str, Any] | None = None,
    result: Dict[str, Any] | None = None,
    reason_code: str = "",
    error_class: str = "",
    status_text: str = "",
    needs_input_items: List[Any] | None = None,
    extra: Dict[str, Any] | None = None,
) -> int:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    normalized_reason = str(reason_code or _to_plain_dict(result).get("runtime_reason_code") or "OK")
    normalized_error_class = str(error_class or _classify_reason_code(normalized_reason))
    input_summary = _build_ui_input_summary(user_prompt_text, source_items)
    selection_summary = _build_ui_selection_summary(_to_plain_dict(selections))
    output_summary = _build_ui_output_summary(_to_plain_dict(result))
    needs_input_fields = []
    for item in _to_plain_list(needs_input_items):
        if isinstance(item, dict):
            field = str(item.get("field", "") or "")
        else:
            field = str(getattr(item, "field", "") or "")
        if field and field not in needs_input_fields:
            needs_input_fields.append(field)
    compact_extra = {}
    for key, value in _to_plain_dict(extra).items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, (int, float, bool)):
            compact_extra[str(key)] = value
        else:
            compact_extra[str(key)] = _sanitize_log_text(value, limit=96)

    event_payload = {
        "timestamp": timestamp,
        "attempt_id": str(attempt_id or ""),
        "event": str(event or "").strip() or "unknown",
        "phase": str(phase or "").strip(),
        "article_type": str(article_type or "unknown"),
        "status": "success" if normalized_reason == "OK" else "error",
        "runtime_reason_code": normalized_reason,
        "runtime_error_class": normalized_error_class,
        "status_text": _sanitize_log_text(status_text, limit=120),
        "needs_input_fields": needs_input_fields[:5],
        "input_summary": input_summary,
        "selection_summary": selection_summary,
        "output_summary": output_summary,
        "extra": compact_extra,
    }

    payload = json.dumps(event_payload, ensure_ascii=False)
    success_count = 0
    for target in (UI_JOURNEY_JSONL_PATH, UI_JOURNEY_JSONL_PATH_WORKSPACE):
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            _trim_jsonl_file(target)
            with target.open("a", encoding="utf-8") as f:
                f.write(payload + "\n")
            _trim_jsonl_file(target)
            success_count += 1
        except Exception as exc:
            logger.warning("Failed to append ui journey event path=%s: %s", target, exc)

    journey = _UI_JOURNEY_CACHE.get(attempt_id)
    if journey is None:
        journey = {
            "attempt_id": str(attempt_id or ""),
            "article_type": str(article_type or "unknown"),
            "started_at": timestamp,
            "last_updated_at": timestamp,
            "input_summary": input_summary,
            "selection_summary": selection_summary,
            "events": [],
            "latest_output": {},
            "latest_decision": {},
            "latest_generation_gate": {},
            "runtime_reason_code": normalized_reason,
            "runtime_error_class": normalized_error_class,
            "needs_input_fields": [],
        }
        _UI_JOURNEY_CACHE[attempt_id] = journey
    journey["article_type"] = str(article_type or journey.get("article_type", "unknown"))
    journey["last_updated_at"] = timestamp
    if input_summary.get("prompt_chars") or input_summary.get("source_count"):
        journey["input_summary"] = input_summary
    if selection_summary:
        journey["selection_summary"] = selection_summary
    if output_summary.get("title_chars") or output_summary.get("body_chars") or output_summary.get("runtime_reason_code"):
        journey["latest_output"] = output_summary
    journey["runtime_reason_code"] = normalized_reason
    journey["runtime_error_class"] = normalized_error_class
    journey["needs_input_fields"] = needs_input_fields[:5]
    events = _to_plain_list(journey.get("events"))
    event_copy = dict(event_payload)
    event_copy["extra"] = compact_extra
    events.append(event_copy)
    journey["events"] = events[-_UI_JOURNEY_MAX_EVENTS:]
    latest_decision = _build_ui_latest_decision_summary(event_copy)
    if latest_decision:
        journey["latest_decision"] = latest_decision
    latest_generation_gate = _build_ui_latest_generation_gate_summary(event_copy)
    if latest_generation_gate:
        journey["latest_generation_gate"] = latest_generation_gate

    if len(_UI_JOURNEY_CACHE) > _UI_JOURNEY_CACHE_MAX_ATTEMPTS:
        oldest_attempts = sorted(
            _UI_JOURNEY_CACHE.items(),
            key=lambda item: str(item[1].get("last_updated_at", "")),
        )[:-_UI_JOURNEY_CACHE_MAX_ATTEMPTS]
        for stale_attempt_id, _ in oldest_attempts:
            _UI_JOURNEY_CACHE.pop(stale_attempt_id, None)

    latest_payload = {
        "log_compat_version": "ui-journey-v1",
        "attempt_id": str(attempt_id or ""),
        "article_type": journey.get("article_type", "unknown"),
        "started_at": journey.get("started_at", timestamp),
        "last_updated_at": timestamp,
        "runtime_reason_code": normalized_reason,
        "runtime_error_class": normalized_error_class,
        "needs_input_fields": needs_input_fields[:5],
        "input_summary": journey.get("input_summary", {}),
        "selection_summary": journey.get("selection_summary", {}),
        "latest_output": journey.get("latest_output", {}),
        "latest_decision": journey.get("latest_decision", {}),
        "latest_generation_gate": journey.get("latest_generation_gate", {}),
        "events": journey.get("events", []),
    }
    for target in (LATEST_UI_JOURNEY_PATH, LATEST_UI_JOURNEY_PATH_WORKSPACE):
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(latest_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to save latest ui journey path=%s: %s", target, exc)

    return success_count


def _count_sentences(text: str) -> int:
    source = (text or "").strip()
    if not source:
        return 0
    return len([s for s in re.split(r"(?<=[。！？])\s*", source) if s.strip()])


def _classify_reason_code(reason_code: str) -> str:
    code = str(reason_code or "").strip().upper()
    if not code or code == "OK":
        return "success"
    if code.startswith("INP_"):
        return "user_input"
    if code.startswith(("POL_", "SEC_")):
        return "policy"
    if code.startswith("TRN_"):
        return "transient"
    return "system"


_PROPOSITION_LOW_SIGNAL_PATTERN = re.compile(
    r"(?:"
    r"重要(?:です|だ)|"
    r"大切(?:です|だ)|"
    r"必要(?:です|だ)|"
    r"求められ(?:ます|る)|"
    r"期待できます|"
    r"と言(?:え|える)(?:ます|でしょう)?|"
    r"かもしれません|"
    r"ではないでしょうか|"
    r"と考えます|"
    r"につながります|"
    r"ことができます|"
    r"が挙げられます|"
    r"がポイントです"
    r")"
)
_PROPOSITION_CONCRETE_SIGNAL_PATTERN = re.compile(
    r"(?:"
    r"\d|%|％|年|月|日|時|分|秒|円|人|社|件|回|"
    r"「|」|『|』|https?://|"
    r"追加|更新|公開|開始|終了|廃止|改善|変更|対応|提供|導入|移行|修正|発表|告知"
    r")"
)
_PROPOSITION_TOKEN_PATTERN = re.compile(r"[一-龥]{2,}|[ァ-ヴー]{3,}|[A-Za-z]{3,}")
_PROPOSITION_STOP_TOKENS = {
    "こと",
    "もの",
    "ため",
    "よう",
    "それ",
    "これ",
    "今回",
    "記事",
    "内容",
    "情報",
    "視点",
    "読者",
    "自分",
    "相手",
    "必要",
    "重要",
    "可能",
    "状況",
    "場合",
}

def _build_proposition_density_target_text(result: Dict[str, Any]) -> str:
    lead = str(result.get("lead", "") or "").strip()
    body = str(result.get("body", "") or "").strip()
    if lead or body:
        return "\n\n".join(part for part in (lead, body) if part)
    return str(result.get("full_text", "") or "").strip()


def _extract_proposition_sentences(text: str) -> List[str]:
    source = (text or "").strip()
    if not source:
        return []

    kept_lines: List[str] = []
    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if re.match(r"^(?:[-*]|[0-9]+[.)])\s+", line):
            line = re.sub(r"^(?:[-*]|[0-9]+[.)])\s+", "", line, count=1).strip()
        if line:
            kept_lines.append(line)
    if not kept_lines:
        return []

    merged = " ".join(kept_lines).strip()
    if not merged:
        return []

    raw_sentences = [s.strip() for s in re.split(r"(?<=[。！？!?])\s*", merged) if s.strip()]
    return raw_sentences or [merged]


def _count_proposition_content_terms(sentence: str) -> int:
    tokens = []
    for token in _PROPOSITION_TOKEN_PATTERN.findall(sentence or ""):
        normalized = token.strip().lower()
        if normalized and normalized not in _PROPOSITION_STOP_TOKENS:
            tokens.append(normalized)
    return len(set(tokens))


def _classify_proposition_sentence(sentence: str) -> str:
    normalized = re.sub(r"\s+", "", str(sentence or ""))
    if not normalized:
        return "skip"

    length = len(normalized)
    concrete_signal = bool(_PROPOSITION_CONCRETE_SIGNAL_PATTERN.search(normalized))
    low_signal = bool(_PROPOSITION_LOW_SIGNAL_PATTERN.search(normalized))
    content_terms = _count_proposition_content_terms(normalized)

    if concrete_signal:
        return "informative"
    if content_terms >= 3 and length >= 22:
        return "informative"
    if low_signal and content_terms <= 2:
        return "low"
    if content_terms <= 1 and length < 30:
        return "low"
    if length <= 10:
        return "low"
    if content_terms >= 2 and length >= 16:
        return "medium"
    return "low"


def _analyze_proposition_density(text: str) -> Dict[str, Any]:
    sentences = _extract_proposition_sentences(text)
    if not sentences:
        return {
            "sentence_count": 0,
            "informative_count": 0,
            "medium_count": 0,
            "low_info_count": 0,
            "informative_ratio": 0.0,
            "low_info_ratio": 0.0,
            "low_info_examples": [],
        }

    informative_count = 0
    medium_count = 0
    low_info_count = 0
    low_info_examples: List[str] = []
    for sentence in sentences:
        label = _classify_proposition_sentence(sentence)
        if label == "informative":
            informative_count += 1
        elif label == "medium":
            medium_count += 1
        elif label == "low":
            low_info_count += 1
            if len(low_info_examples) < 4:
                low_info_examples.append(sentence[:96])

    sentence_count = len(sentences)
    return {
        "sentence_count": sentence_count,
        "informative_count": informative_count,
        "medium_count": medium_count,
        "low_info_count": low_info_count,
        "informative_ratio": _safe_round_float(informative_count / max(1, sentence_count), 4, 0.0),
        "low_info_ratio": _safe_round_float(low_info_count / max(1, sentence_count), 4, 0.0),
        "low_info_examples": low_info_examples,
    }


def _iter_quality_phase_reports(quality: Dict[str, Any]) -> List[Dict[str, Any]]:
    flattened: List[Dict[str, Any]] = []
    for report in _to_plain_list(quality.get("reports")):
        if not isinstance(report, dict):
            continue
        nested = _to_plain_list(report.get("phase_reports"))
        if nested:
            flattened.extend([phase for phase in nested if isinstance(phase, dict)])
            continue
        if report.get("phase"):
            flattened.append(report)
    return flattened


def _extract_fingerprint_phase_report(quality: Dict[str, Any]) -> Dict[str, Any]:
    for phase_report in _iter_quality_phase_reports(quality):
        if str(phase_report.get("phase", "") or "") != "fingerprint":
            continue
        return {
            "flat_zone_flags": _to_plain_list(phase_report.get("flat_zone_flags")),
            "overall_unpredictability": _safe_round_float(phase_report.get("overall_unpredictability"), 4, 0.0),
            "correction_hints": _to_plain_list(phase_report.get("correction_hints")),
            "fingerprint_correction_applied": bool(phase_report.get("fingerprint_correction_applied", False)),
            "nominalization_rate": _safe_round_float(phase_report.get("nominalization_rate"), 4, 0.0),
            "sentence_ending_entropy": _safe_round_float(phase_report.get("sentence_ending_entropy"), 4, 0.0),
            "sentence_ending_fine_entropy": _safe_round_float(
                phase_report.get("sentence_ending_fine_entropy"),
                4,
                0.0,
            ),
            "subject_explicit_rate": _safe_round_float(phase_report.get("subject_explicit_rate"), 4, 0.0),
            "mtld": _safe_round_float(phase_report.get("mtld"), 4, 0.0),
        }
    return {}


def collect_runtime_config_snapshot(result: Dict[str, Any]) -> Dict[str, Any]:
    cfg_path = PROJECT_ROOT_DIR / "config.json"
    cfg_data: Dict[str, Any] = {}
    config_mtime = ""
    try:
        if cfg_path.exists():
            cfg_data = json.loads(cfg_path.read_text(encoding="utf-8"))
            config_mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(cfg_path.stat().st_mtime))
    except Exception as exc:
        logger.warning("Failed to read config snapshot: %s", exc)
        cfg_data = {}

    llm_cfg = _to_plain_dict(cfg_data.get("llm"))
    quality_cfg = _to_plain_dict(cfg_data.get("quality_pipeline"))
    section_cfg = _to_plain_dict(cfg_data.get("section_generation"))
    post_cfg = _to_plain_dict(cfg_data.get("postprocess"))
    repair_cfg = _to_plain_dict(post_cfg.get("repair_only"))
    runtime_pipeline = _to_plain_dict(result.get("pipeline_check"))
    runtime_input_contract = _to_plain_dict(runtime_pipeline.get("input_contract"))
    runtime_quality = _to_plain_dict(result.get("quality_pipeline_check"))
    runtime_llm = _to_plain_dict(result.get("llm_check"))
    if not runtime_llm:
        runtime_llm = _to_plain_dict(_to_plain_dict(runtime_pipeline.get("section_generation")).get("llm_check"))
    task_models_snapshot = _to_plain_dict(llm_cfg.get("task_models"))
    runtime_model_source = str(runtime_llm.get("model_source") or "").strip()
    runtime_selected_model = str(
        runtime_llm.get("selected_model") or runtime_llm.get("primary_model") or ""
    ).strip()
    if runtime_model_source.startswith("task_models.") and runtime_selected_model:
        runtime_task_key = runtime_model_source.removeprefix("task_models.").strip()
        if runtime_task_key:
            task_models_snapshot[runtime_task_key] = runtime_selected_model
    strict_saas_mode = str(
        runtime_input_contract.get("strict_saas_mode")
        or result.get("strict_saas_mode")
        or cfg_data.get("strict_saas_mode")
        or ""
    ).strip()

    return {
        "config_path": str(cfg_path),
        "config_last_modified": config_mtime,
        "generation_mode": cfg_data.get("generation_mode", "zero_base_v2"),
        "strict_saas_mode": strict_saas_mode,
        "llm": {
            "model_name": llm_cfg.get("model_name", ""),
            "fallback_model": llm_cfg.get("fallback_model", ""),
            "reasoning_effort": llm_cfg.get("reasoning_effort", ""),
            "timeout": llm_cfg.get("timeout"),
            "top_p": llm_cfg.get("top_p"),
            "presence_penalty": llm_cfg.get("presence_penalty"),
            "frequency_penalty": llm_cfg.get("frequency_penalty"),
            "disable_temperature_model_prefixes": _to_plain_list(llm_cfg.get("disable_temperature_model_prefixes")),
            "disable_top_p_model_prefixes": _to_plain_list(llm_cfg.get("disable_top_p_model_prefixes")),
            "disable_penalty_model_prefixes": _to_plain_list(llm_cfg.get("disable_penalty_model_prefixes")),
            "task_models": task_models_snapshot,
        },
        "quality_pipeline": {
            "enabled": bool(quality_cfg.get("enabled", False)),
            "mode": quality_cfg.get("mode", "off"),
            "fingerprint_enabled": quality_cfg.get("fingerprint_enabled"),
            "resonance_tuning_enabled": bool(quality_cfg.get("resonance_tuning_enabled", False)),
            "phase01_lexical_enabled": bool(quality_cfg.get("phase01_lexical_enabled", False)),
            "phase02_burstiness_enabled": bool(quality_cfg.get("phase02_burstiness_enabled", False)),
            "phase03_nominalization_enabled": bool(quality_cfg.get("phase03_nominalization_enabled", False)),
            "phase04_style_drift_enabled": bool(quality_cfg.get("phase04_style_drift_enabled", False)),
            "phase05_layout_guard_enabled": bool(quality_cfg.get("phase05_layout_guard_enabled", False)),
            "phase06_orchestrator_enabled": bool(quality_cfg.get("phase06_orchestrator_enabled", False)),
            "phase07_rollout_enabled": bool(quality_cfg.get("phase07_rollout_enabled", False)),
        },
        "section_generation": {
            "novelty_gate": _to_plain_dict(section_cfg.get("novelty_gate")),
            "context_overlap": _to_plain_dict(section_cfg.get("context_overlap")),
            "hard_soft_thresholds": _to_plain_dict(section_cfg.get("hard_soft_thresholds")),
        },
        "postprocess": {"repair_only": repair_cfg},
        "runtime_checks": {
            "llm_check": runtime_llm,
            "pipeline_section_generation": _to_plain_dict(runtime_pipeline.get("section_generation")),
            "pipeline_postprocess": _to_plain_dict(runtime_pipeline.get("postprocess")),
            "quality_pipeline": {
                "enabled": runtime_quality.get("enabled"),
                "mode": runtime_quality.get("mode"),
                "fingerprint_enabled": runtime_quality.get("fingerprint_enabled"),
                "fail_open": runtime_quality.get("fail_open"),
            },
            "strict_saas_mode": strict_saas_mode,
        },
    }


def _is_missing_alignment_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _derive_interview_answer_source_counts(input_contract: Dict[str, Any]) -> Dict[str, int]:
    interview_answers = _to_plain_dict(input_contract.get("interview_answers"))
    answered_count = sum(
        1
        for key in ("perspective", "target", "message")
        if str(interview_answers.get(key, "") or "").strip()
    )
    if answered_count <= 0:
        return {}
    return {"interview_answers": answered_count, "user_prompt": 0, "unresolved_items": 0, "unknown": 0}


def build_pipeline_contract_alignment(pipeline: Dict[str, Any]) -> Dict[str, Any]:
    contract_alignment = _to_plain_dict(pipeline.get("contract_alignment"))
    input_contract = _to_plain_dict(pipeline.get("input_contract"))
    quality_metrics = _to_plain_dict(pipeline.get("quality_metrics"))
    merged = dict(contract_alignment)
    has_native_alignment = bool(contract_alignment)
    merged.setdefault("compatibility_source", "native" if contract_alignment else "input_contract_fallback")

    audience_profile = str(merged.get("audience_profile") or input_contract.get("audience_profile") or "").strip()
    topic_statement = str(merged.get("topic_statement") or input_contract.get("topic_statement") or "").strip()
    narrative_axis = str(merged.get("narrative_axis") or input_contract.get("narrative_axis") or "").strip()
    knowledge_lenses = _to_plain_list(merged.get("knowledge_lenses"))
    if not knowledge_lenses:
        knowledge_lenses = _to_plain_list(input_contract.get("knowledge_lenses"))[:6]
    must_cover_items = _to_plain_list(merged.get("must_cover_items"))
    if not must_cover_items:
        must_cover_items = _to_plain_list(input_contract.get("must_cover"))[:12]
    question_source_counts = _to_plain_dict(merged.get("question_source_counts"))
    if not question_source_counts:
        question_source_counts = _derive_interview_answer_source_counts(input_contract)

    merged["audience_profile"] = audience_profile
    merged["topic_statement"] = topic_statement
    merged["narrative_axis"] = narrative_axis
    merged["knowledge_lenses"] = knowledge_lenses[:6]
    merged["must_cover_items"] = must_cover_items[:12]
    merged["question_source_counts"] = question_source_counts

    if _is_missing_alignment_value(merged.get("category_consistency_score")):
        merged["category_consistency_score"] = 1.0 if str(input_contract.get("article_type") or "").strip() else 0.0
    if _is_missing_alignment_value(merged.get("must_cover_reflection_rate")):
        merged["must_cover_reflection_rate"] = _safe_round_float(quality_metrics.get("must_cover_reflection_ratio"), 4, 0.0)
    if _is_missing_alignment_value(merged.get("prompt_anchor_coverage")):
        merged["prompt_anchor_coverage"] = _safe_round_float(quality_metrics.get("prompt_follow_anchor_coverage"), 4, 1.0)
    if _is_missing_alignment_value(merged.get("anchor_term_coverage")):
        merged["anchor_term_coverage"] = _safe_round_float(quality_metrics.get("prompt_follow_anchor_coverage"), 4, 1.0)
    if _is_missing_alignment_value(merged.get("section_focus_coverage")):
        section_count = max(1, int(quality_metrics.get("section_count", 0) or 0))
        discourse_hits = int(quality_metrics.get("prompt_follow_discourse_hits", 0) or 0)
        merged["section_focus_coverage"] = round(min(1.0, discourse_hits / section_count), 4)
    if _is_missing_alignment_value(merged.get("speaker_consistency_score")):
        merged["speaker_consistency_score"] = 1.0 if has_native_alignment else (
            1.0 if str(input_contract.get("speaker_profile") or "").strip() else 0.0
        )
    if _is_missing_alignment_value(merged.get("pronoun_consistency_score")):
        merged["pronoun_consistency_score"] = 1.0 if has_native_alignment or _to_plain_list(input_contract.get("allowed_pronouns")) else 0.0
    if _is_missing_alignment_value(merged.get("relationship_consistency_score")):
        merged["relationship_consistency_score"] = 1.0 if has_native_alignment else (
            1.0 if str(input_contract.get("relationship_mode") or "").strip() else 0.0
        )
    if _is_missing_alignment_value(merged.get("audience_address_consistency")):
        merged["audience_address_consistency"] = 1.0 if audience_profile else 0.0
    if _is_missing_alignment_value(merged.get("source_trace_coverage")):
        merged["source_trace_coverage"] = 1.0 if _to_plain_list(input_contract.get("source_inputs")) else 0.0

    if _is_missing_alignment_value(merged.get("question_reflection_rate")):
        interview_answers = _to_plain_dict(input_contract.get("interview_answers"))
        answered_roles = [key for key in ("target", "perspective", "message") if str(interview_answers.get(key, "") or "").strip()]
        reflected_count = 0
        if "target" in answered_roles and audience_profile:
            reflected_count += 1
        if "perspective" in answered_roles and (topic_statement or narrative_axis):
            reflected_count += 1
        if "message" in answered_roles and must_cover_items:
            reflected_count += 1
        merged["question_reflection_rate"] = round(reflected_count / max(1, len(answered_roles)), 4) if answered_roles else 0.0

    if _is_missing_alignment_value(merged.get("alignment_score")):
        merged["alignment_score"] = round(
            _safe_round_float(merged.get("category_consistency_score"), 4, 0.0) * 0.25
            + _safe_round_float(merged.get("question_reflection_rate"), 4, 0.0) * 0.25
            + _safe_round_float(merged.get("must_cover_reflection_rate"), 4, 0.0) * 0.25
            + _safe_round_float(merged.get("prompt_anchor_coverage"), 4, 1.0) * 0.15
            + _safe_round_float(merged.get("section_focus_coverage"), 4, 1.0) * 0.10,
            4,
        )

    return merged


def build_algorithm_trace_snapshot(pipeline: Dict[str, Any]) -> Dict[str, Any]:
    normalized_pipeline = _to_plain_dict(pipeline)
    io_contract = _to_plain_dict(normalized_pipeline.get("io_contract"))
    discourse_plan = _to_plain_list(normalized_pipeline.get("discourse_plan"))
    quality_metrics = _to_plain_dict(normalized_pipeline.get("quality_metrics"))
    input_contract = _to_plain_dict(normalized_pipeline.get("input_contract"))
    need_question = _to_plain_dict(normalized_pipeline.get("need_question_decision"))
    section_generation = _to_plain_dict(normalized_pipeline.get("section_generation"))
    dedupe_audit = _to_plain_dict(normalized_pipeline.get("dedupe_audit"))
    editor_report = _to_plain_dict(normalized_pipeline.get("editor_report"))
    final_quality_eval = _to_plain_dict(normalized_pipeline.get("final_quality_eval"))
    stage_order = [str(stage) for stage in io_contract.keys()]
    stages: List[Dict[str, Any]] = []
    for stage_name, io_shape in io_contract.items():
        normalized_io = _to_plain_dict(io_shape)
        summary: Dict[str, Any] = {}
        if stage_name == "contract_resolve":
            summary = {
                "article_type": str(input_contract.get("article_type") or ""),
                "source_count": int(input_contract.get("source_count", 0) or len(_to_plain_list(input_contract.get("source_inputs")))),
                "should_ask": bool(need_question.get("ask", need_question.get("should_ask", False))),
            }
        elif stage_name == "discourse_plan":
            summary = {
                "section_count": len(discourse_plan),
                "intent_sequence": [
                    str(item.get("intent") or item.get("objective") or "")
                    for item in discourse_plan
                    if isinstance(item, dict)
                ],
                "heading_sequence": [
                    str(item.get("heading") or "")
                    for item in discourse_plan
                    if isinstance(item, dict) and str(item.get("heading") or "").strip()
                ],
            }
        elif stage_name == "section_generation":
            summary = {
                "retry_count": int(section_generation.get("retry_count", 0) or 0),
                "fallback_used": bool(section_generation.get("fallback_used", False)),
                "section_char_counts": _to_plain_list(section_generation.get("section_char_counts"))[:8],
            }
        elif stage_name == "dedupe":
            duplicate_pairs = int(dedupe_audit.get("duplicate_pairs", 0) or 0)
            sentence_count = int(dedupe_audit.get("sentence_count", 0) or 0)
            summary = {
                "removed_duplicate_count": duplicate_pairs,
                "preserved_sentence_count": max(0, sentence_count - duplicate_pairs),
                "provider_mode": str(dedupe_audit.get("resolved_provider_mode") or dedupe_audit.get("provider_mode") or ""),
                "embedding_used": bool(dedupe_audit.get("embedding_used", False)),
                "embedding_skipped_reason": str(dedupe_audit.get("embedding_skipped_reason") or ""),
                "fail_open": bool(dedupe_audit.get("fail_open", False)),
            }
        elif stage_name == "editor_guard":
            summary = {
                "sentence_integrity_repair_count": int(editor_report.get("sentence_integrity_repair_count", 0) or 0),
                "sentence_integrity_warning_count": int(editor_report.get("sentence_integrity_warning_count", 0) or 0),
                "repair_kinds": [
                    str(item.get("kind") or "")
                    for item in _to_plain_list(editor_report.get("repair_actions"))
                    if isinstance(item, dict) and bool(item.get("applied", False)) and str(item.get("kind") or "").strip()
                ][:8],
            }
        elif stage_name == "quality_pipeline":
            summary = {
                "soft_warning_count": int(final_quality_eval.get("soft_warning_count", 0) or 0),
                "topic_echo_body_only_ratio": _safe_round_float(quality_metrics.get("topic_echo_body_only_ratio"), 4, 0.0),
                "case_result_condition_sentence_count": int(quality_metrics.get("case_result_condition_sentence_count", 0) or 0),
                "comparative_axis_shift_count": int(quality_metrics.get("comparative_axis_shift_count", 0) or 0),
            }
        stages.append(
            {
                "stage": str(stage_name),
                "owner": _ALGORITHM_STAGE_OWNERS.get(str(stage_name), ""),
                "inputs": _to_plain_list(normalized_io.get("in")),
                "outputs": _to_plain_list(normalized_io.get("out")),
                "summary": summary,
            }
        )
    return {
        "stage_order": stage_order,
        "stages": stages,
        "discourse_section_count": len(discourse_plan),
        "discourse_headings": [
            str(item.get("heading") or "")
            for item in discourse_plan
            if isinstance(item, dict) and str(item.get("heading") or "").strip()
        ],
        "quality_metric_keys": sorted(str(key) for key in quality_metrics.keys())[:24],
    }


def _extract_existing_output_guard(result: Dict[str, Any]) -> Dict[str, Any]:
    direct_guard = _to_plain_dict(result.get("output_guard"))
    if direct_guard:
        return direct_guard
    pipeline = _to_plain_dict(result.get("pipeline_check"))
    return _to_plain_dict(pipeline.get("output_guard"))


def collect_failed_parameters(result: Dict[str, Any]) -> Dict[str, Any]:
    pipeline = _to_plain_dict(result.get("pipeline_check"))
    quality = _to_plain_dict(result.get("quality_pipeline_check"))
    output_guard_inputs = _to_plain_dict(pipeline.get("output_guard_inputs"))
    native_contract_alignment = _to_plain_dict(output_guard_inputs.get("contract_alignment"))
    contract_alignment = native_contract_alignment or build_pipeline_contract_alignment(pipeline)
    input_contract = _to_plain_dict(pipeline.get("input_contract"))
    existing_output_guard = _extract_existing_output_guard(result)

    retry_failures: List[Dict[str, Any]] = []
    for item in _to_plain_list(pipeline.get("retry_telemetry")):
        if not isinstance(item, dict):
            continue
        redundant = bool(item.get("redundant"))
        low_novelty = bool(item.get("low_novelty"))
        if redundant or low_novelty:
            retry_failures.append(
                {
                    "attempt": item.get("attempt"),
                    "redundant": redundant,
                    "low_novelty": low_novelty,
                    "novelty_ratio": _safe_round_float(item.get("novelty_ratio"), 4, 1.0),
                    "novelty_threshold": _safe_round_float(item.get("novelty_threshold"), 4, 0.0),
                    "overlap_term_ratio": _safe_round_float(item.get("overlap_term_ratio"), 4, 0.0),
                    "overlap_terms_count": int(item.get("overlap_terms_count", 0) or 0),
                }
            )

    hard_soft_eval = _to_plain_dict(output_guard_inputs.get("hard_soft_eval")) or _to_plain_dict(pipeline.get("hard_soft_eval"))
    final_quality_eval = _to_plain_dict(output_guard_inputs.get("final_quality_eval")) or _to_plain_dict(pipeline.get("final_quality_eval"))
    repair_only_report = _to_plain_dict(pipeline.get("repair_only_report"))
    contextual_naturalness = _to_plain_dict(output_guard_inputs.get("contextual_naturalness_report")) or _to_plain_dict(pipeline.get("contextual_naturalness_report"))
    proposition_density = _to_plain_dict(output_guard_inputs.get("proposition_density"))
    if not proposition_density:
        proposition_density = _analyze_proposition_density(_build_proposition_density_target_text(result))
    proposition_sentence_count = int(proposition_density.get("sentence_count", 0) or 0)
    proposition_informative_ratio = _safe_round_float(proposition_density.get("informative_ratio"), 4, 0.0)
    proposition_low_info_ratio = _safe_round_float(proposition_density.get("low_info_ratio"), 4, 0.0)
    hard_soft_metrics = _to_plain_dict(hard_soft_eval.get("metrics"))
    semantic_layout = _to_plain_dict(contextual_naturalness.get("semantic_layout"))
    semantic_issue_count = int(contextual_naturalness.get("semantic_issue_count", semantic_layout.get("semantic_issue_count", 0)) or 0)
    instructional_fragment_count = max(
        int(contextual_naturalness.get("instructional_fragment_count", 0) or 0),
        int(hard_soft_metrics.get("instructional_fragment_count", 0) or 0),
    )
    fingerprint_phase_report = _extract_fingerprint_phase_report(quality)

    quality_mode_resolution: Dict[str, Any] = {}
    for quality_report in _to_plain_list(quality.get("reports")):
        if isinstance(quality_report, dict):
            mode_resolution = _to_plain_dict(quality_report.get("mode_resolution"))
            if mode_resolution:
                quality_mode_resolution = mode_resolution
                break

    alignment_score = _safe_round_float(contract_alignment.get("alignment_score"), 4, 0.0)
    must_cover_reflection_rate = _safe_round_float(contract_alignment.get("must_cover_reflection_rate"), 4, 0.0)
    prompt_anchor_coverage = _safe_round_float(contract_alignment.get("prompt_anchor_coverage"), 4, 1.0)
    anchor_term_coverage = _safe_round_float(contract_alignment.get("anchor_term_coverage"), 4, 1.0)
    section_focus_coverage = _safe_round_float(contract_alignment.get("section_focus_coverage"), 4, 1.0)
    section_focus_total = int(contract_alignment.get("section_focus_total", 0) or 0)
    anchor_terms = _to_plain_list(contract_alignment.get("anchor_terms"))
    forbidden_topic_hits = _to_plain_list(contract_alignment.get("forbidden_topic_hits"))
    forbidden_topic_hit_count = int(contract_alignment.get("forbidden_topic_hit_count", 0) or 0)
    if not forbidden_topic_hit_count and forbidden_topic_hits:
        forbidden_topic_hit_count = len(forbidden_topic_hits)
    default_speaker_score = 1.0 if str(contract_alignment.get("speaker_profile") or input_contract.get("speaker_profile") or "").strip() else 0.0
    speaker_consistency_score = _safe_round_float(contract_alignment.get("speaker_consistency_score"), 4, default_speaker_score)
    pronoun_consistency_score = _safe_round_float(contract_alignment.get("pronoun_consistency_score"), 4, 1.0)
    relationship_consistency_score = _safe_round_float(contract_alignment.get("relationship_consistency_score"), 4, 1.0)
    category_mismatch_detected = bool(contract_alignment.get("category_mismatch_detected", False))
    contract_alignment_risk = bool(
        bool(contract_alignment.get("contract_alignment_risk", False))
        or category_mismatch_detected
        or forbidden_topic_hit_count > 0
        or int(contract_alignment.get("section_contract_issue_count", 0) or 0) > 0
    )

    hard_failed = bool(hard_soft_eval.get("hard_failed", False))
    hard_fail_reasons = _to_plain_list(hard_soft_eval.get("hard_fail_reasons"))
    final_hard_failed = bool(final_quality_eval.get("hard_failed", False))
    if final_hard_failed and not hard_failed:
        hard_failed = True
        hard_fail_reasons.append("final_quality_eval_hard_failed")
    if bool(result.get("hard_failed", False)) and not hard_failed:
        hard_failed = True
        hard_fail_reasons.append("result_hard_failed")
    for reason in _to_plain_list(result.get("hard_fail_reasons")):
        if reason not in hard_fail_reasons:
            hard_fail_reasons.append(reason)
    guard_blocked = bool(existing_output_guard.get("blocked", False))
    guard_reason_code = str(existing_output_guard.get("reason_code") or "").strip()
    guard_error_class = str(existing_output_guard.get("error_class") or "").strip()
    guard_reasons = [
        str(reason).strip()
        for reason in _to_plain_list(existing_output_guard.get("reasons"))
        if str(reason or "").strip()
    ]
    guard_soft_warnings = [
        str(reason).strip()
        for reason in _to_plain_list(existing_output_guard.get("soft_warnings"))
        if str(reason or "").strip()
    ]
    if guard_blocked:
        hard_failed = True
        if guard_reason_code and guard_reason_code not in hard_fail_reasons:
            hard_fail_reasons.append(guard_reason_code)
        for reason in guard_reasons:
            if reason not in hard_fail_reasons:
                hard_fail_reasons.append(reason)

    grammar_before = _to_plain_dict(repair_only_report.get("before"))
    grammar_after = _to_plain_dict(repair_only_report.get("after"))
    repair_error = str(repair_only_report.get("error", "") or "")
    runtime_reason_code = str(result.get("runtime_reason_code") or result.get("reason_code") or "OK")
    runtime_error_class = str(result.get("runtime_error_class") or _classify_reason_code(runtime_reason_code))
    result_failed = not bool(result.get("success", True))
    pipeline_soft_warnings = [
        str(reason).strip()
        for reason in _to_plain_list(final_quality_eval.get("soft_warnings"))
        if str(reason or "").strip()
    ]
    final_soft_warnings = guard_soft_warnings or pipeline_soft_warnings
    final_soft_warning_count = int(
        existing_output_guard.get("soft_warning_count")
        or final_quality_eval.get("soft_warning_count")
        or len(final_soft_warnings)
        or 0
    )
    if final_soft_warnings and final_soft_warning_count < len(final_soft_warnings):
        final_soft_warning_count = len(final_soft_warnings)

    has_failure = bool(
        result_failed
        or runtime_reason_code != "OK"
        or retry_failures
        or hard_failed
        or hard_fail_reasons
        or guard_blocked
    )

    return {
        "has_failure": has_failure,
        "runtime_reason_code": runtime_reason_code,
        "runtime_error_class": runtime_error_class,
        "retry_failures": retry_failures,
        "hard_soft_eval": {
            "mode": hard_soft_eval.get("mode", "off"),
            "hard_failed": hard_failed,
            "hard_fail_reasons": hard_fail_reasons,
            "soft_warnings": _to_plain_list(hard_soft_eval.get("soft_warnings")),
            "metrics": _to_plain_dict(hard_soft_eval.get("metrics")),
        },
        "repair_only_report": {
            "mode": repair_only_report.get("mode", "off"),
            "applied": bool(repair_only_report.get("applied", False)),
            "guard_rejected": bool(repair_only_report.get("guard_rejected", False)),
            "would_call_llm": bool(repair_only_report.get("would_call_llm", False)),
            "error": repair_error,
            "before_violations_per_1k": _safe_round_float(grammar_before.get("violations_per_1k_chars"), 4, 0.0),
            "after_violations_per_1k": _safe_round_float(grammar_after.get("violations_per_1k_chars"), 4, 0.0),
        },
        "contextual_naturalness_report": {
            "passed": bool(contextual_naturalness.get("passed", True)),
            "issue_count": int(contextual_naturalness.get("issue_count", 0) or 0),
            "soft_issue_count": int(contextual_naturalness.get("soft_issue_count", 0) or 0),
            "instructional_fragment_count": instructional_fragment_count,
            "sentence_count": int(contextual_naturalness.get("sentence_count", 0) or 0),
            "connective_opening_ratio": _safe_round_float(contextual_naturalness.get("connective_opening_ratio"), 4, 0.0),
            "topic_opening_ratio": _safe_round_float(contextual_naturalness.get("topic_opening_ratio"), 4, 0.0),
            "ellipsis_opening_ratio": _safe_round_float(contextual_naturalness.get("ellipsis_opening_ratio"), 4, 0.0),
            "awkward_ending_count": int(contextual_naturalness.get("awkward_ending_count", 0) or 0),
            "awkward_ending_ratio": _safe_round_float(contextual_naturalness.get("awkward_ending_ratio"), 4, 0.0),
            "ai_template_ending_count": int(contextual_naturalness.get("ai_template_ending_count", 0) or 0),
            "ai_template_ending_ratio": _safe_round_float(contextual_naturalness.get("ai_template_ending_ratio"), 4, 0.0),
            "connector_collision_count": int(contextual_naturalness.get("connector_collision_count", 0) or 0),
            "semantic_issue_count": semantic_issue_count,
            "semantic_layout": {
                "section_count": int(semantic_layout.get("section_count", 0) or 0),
                "heading_alignment_mean": _safe_round_float(semantic_layout.get("heading_alignment_mean"), 4, 0.0),
                "heading_alignment_min": _safe_round_float(semantic_layout.get("heading_alignment_min"), 4, 0.0),
                "heading_alignment_low_count": int(semantic_layout.get("heading_alignment_low_count", 0) or 0),
                "transition_jaccard_mean": _safe_round_float(semantic_layout.get("transition_jaccard_mean"), 4, 0.0),
                "transition_jaccard_min": _safe_round_float(semantic_layout.get("transition_jaccard_min"), 4, 0.0),
                "transition_low_count": int(semantic_layout.get("transition_low_count", 0) or 0),
                "abrupt_opening_count": int(semantic_layout.get("abrupt_opening_count", 0) or 0),
                "abrupt_opening_ratio": _safe_round_float(semantic_layout.get("abrupt_opening_ratio"), 4, 0.0),
                "heading_repetition_count": int(semantic_layout.get("heading_repetition_count", 0) or 0),
            },
        },
        "proposition_density": {
            "sentence_count": proposition_sentence_count,
            "informative_count": int(proposition_density.get("informative_count", 0) or 0),
            "medium_count": int(proposition_density.get("medium_count", 0) or 0),
            "low_info_count": int(proposition_density.get("low_info_count", 0) or 0),
            "informative_ratio": proposition_informative_ratio,
            "low_info_ratio": proposition_low_info_ratio,
            "low_info_examples": _to_plain_list(proposition_density.get("low_info_examples"))[:4],
        },
        "instructional_fragment_count": instructional_fragment_count,
        "output_guard": {
            "blocked": guard_blocked,
            "reason_code": guard_reason_code,
            "error_class": guard_error_class,
            "reasons": guard_reasons,
            "soft_warnings": guard_soft_warnings,
            "soft_warning_count": max(
                int(existing_output_guard.get("soft_warning_count", 0) or 0),
                len(guard_soft_warnings),
            ),
            "manual_instructional_hits": _to_plain_list(existing_output_guard.get("manual_instructional_hits"))[:6],
            "needs_input_items": _to_plain_list(existing_output_guard.get("needs_input_items"))[:6],
        },
        "contract_alignment": {
            "alignment_score": alignment_score,
            "category_consistency_score": _safe_round_float(contract_alignment.get("category_consistency_score"), 4, 0.0),
            "question_reflection_rate": _safe_round_float(contract_alignment.get("question_reflection_rate"), 4, 0.0),
            "must_cover_reflection_rate": _safe_round_float(contract_alignment.get("must_cover_reflection_rate"), 4, 0.0),
            "category_mismatch_detected": category_mismatch_detected,
            "prompt_anchor_coverage": prompt_anchor_coverage,
            "anchor_term_coverage": anchor_term_coverage,
            "section_focus_coverage": section_focus_coverage,
            "section_focus_hits": int(contract_alignment.get("section_focus_hits", 0) or 0),
            "section_focus_total": section_focus_total,
            "forbidden_topic_hit_count": forbidden_topic_hit_count,
            "forbidden_topic_hits": forbidden_topic_hits[:12],
            "must_cover_count": int(contract_alignment.get("must_cover_count", 0) or 0),
            "must_cover_items": _to_plain_list(contract_alignment.get("must_cover_items")),
            "unresolved_count": int(contract_alignment.get("unresolved_count", 0) or 0),
            "question_source_coverage": _safe_round_float(contract_alignment.get("question_source_coverage"), 4, 0.0),
            "question_source_counts": _to_plain_dict(contract_alignment.get("question_source_counts")),
            "question_source_missing_ids": _to_plain_list(contract_alignment.get("question_source_missing_ids")),
            "question_source_unknown_ids": _to_plain_list(contract_alignment.get("question_source_unknown_ids")),
            "anchor_terms": anchor_terms[:14],
            "prompt_anchor_terms": _to_plain_list(contract_alignment.get("prompt_anchor_terms"))[:12],
            "source_anchor_terms": _to_plain_list(contract_alignment.get("source_anchor_terms"))[:12],
            "speaker_consistency_score": speaker_consistency_score,
            "relationship_consistency_score": relationship_consistency_score,
            "audience_address_consistency": _safe_round_float(contract_alignment.get("audience_address_consistency"), 4, 0.0),
            "register_drift_index": _safe_round_float(contract_alignment.get("register_drift_index"), 4, 0.0),
            "pronoun_consistency_score": pronoun_consistency_score,
            "source_trace_coverage": _safe_round_float(contract_alignment.get("source_trace_coverage"), 4, 0.0),
            "section_contract_issue_count": int(contract_alignment.get("section_contract_issue_count", 0) or 0),
            "allowed_pronouns": _to_plain_list(contract_alignment.get("allowed_pronouns"))[:6],
            "detected_speaker_modes": _to_plain_list(contract_alignment.get("detected_speaker_modes"))[:6],
            "disallowed_pronoun_hits": _to_plain_list(contract_alignment.get("disallowed_pronoun_hits"))[:6],
            "speaker_third_person_mentions": int(contract_alignment.get("speaker_third_person_mentions", 0) or 0),
            "speaker_advice_tone_count": int(contract_alignment.get("speaker_advice_tone_count", 0) or 0),
            "contract_alignment_reason_codes": _to_plain_list(contract_alignment.get("contract_alignment_reason_codes"))[:8],
            "contract_alignment_risk": contract_alignment_risk,
        },
        "quality_mode_resolution": quality_mode_resolution,
        "fingerprint_phase": fingerprint_phase_report,
        "final_quality_eval": {
            "evaluated": bool(final_quality_eval.get("evaluated", False) or existing_output_guard),
            "mode": str(final_quality_eval.get("mode", "off") or "off"),
            "hard_failed": bool(final_hard_failed or guard_blocked),
            "hard_fail_reasons": hard_fail_reasons,
            "soft_warnings": final_soft_warnings,
            "soft_warning_count": final_soft_warning_count,
            "semantic_issue_count": int(final_quality_eval.get("semantic_issue_count", 0) or 0),
            "instructional_fragment_count": int(final_quality_eval.get("instructional_fragment_count", 0) or 0),
        },
    }


def build_latest_quality_report_payload(
    *,
    timestamp: str,
    attempt_id: str,
    result: Dict[str, Any],
    config_snapshot: Dict[str, Any],
    failed_parameters: Dict[str, Any],
) -> Dict[str, Any]:
    full_text = str(result.get("full_text", "") or "")
    hard_soft = _to_plain_dict(failed_parameters.get("hard_soft_eval"))
    hard_soft_metrics = _to_plain_dict(hard_soft.get("metrics"))
    naturalness = _to_plain_dict(failed_parameters.get("contextual_naturalness_report"))
    proposition_density = _to_plain_dict(failed_parameters.get("proposition_density"))
    fingerprint = _to_plain_dict(failed_parameters.get("fingerprint_phase"))
    pipeline_check = _to_plain_dict(result.get("pipeline_check"))
    newalgorithm_metrics = _to_plain_dict(pipeline_check.get("quality_metrics"))
    fallback_unpredictability = _safe_round_float(fingerprint.get("overall_unpredictability"), 4, 0.0)
    metrics = {
        "chars": len(full_text),
        "sentence_count": _count_sentences(full_text),
        "connective_opening_ratio": _safe_round_float(naturalness.get("connective_opening_ratio"), 4, 0.0),
        "overall_unpredictability": _safe_round_float(hard_soft_metrics.get("unpredictability"), 4, fallback_unpredictability),
        "sentence_ending_entropy": _safe_round_float(fingerprint.get("sentence_ending_entropy"), 4, 0.0),
        "sentence_ending_fine_entropy": _safe_round_float(fingerprint.get("sentence_ending_fine_entropy"), 4, 0.0),
        "subject_explicit_rate": _safe_round_float(fingerprint.get("subject_explicit_rate"), 4, _safe_round_float(newalgorithm_metrics.get("explicit_subject_ratio"), 4, 0.0)),
        "nominalization_rate": _safe_round_float(fingerprint.get("nominalization_rate"), 4, 0.0),
        "flat_zone_count": int(hard_soft_metrics.get("flat_zone_count", len(_to_plain_list(fingerprint.get("flat_zone_flags")))) or 0),
        "semantic_issue_count": int(naturalness.get("semantic_issue_count", 0) or 0),
        "proposition_sentence_count": int(proposition_density.get("sentence_count", 0) or 0),
        "proposition_informative_ratio": _safe_round_float(proposition_density.get("informative_ratio"), 4, 0.0),
        "proposition_low_info_ratio": _safe_round_float(proposition_density.get("low_info_ratio"), 4, 0.0),
        "topic_echo_ratio": _safe_round_float(newalgorithm_metrics.get("topic_echo_ratio"), 4, 0.0),
        "topic_echo_body_only_ratio": _safe_round_float(newalgorithm_metrics.get("topic_echo_body_only_ratio"), 4, 0.0),
        "topic_echo_heading_adjusted_ratio": _safe_round_float(newalgorithm_metrics.get("topic_echo_heading_adjusted_ratio"), 4, 0.0),
        "topic_echo_long_span_count": int(newalgorithm_metrics.get("topic_echo_long_span_count", 0) or 0),
        "paragraph_break_semantic_score": _safe_round_float(newalgorithm_metrics.get("paragraph_break_semantic_score"), 4, 0.0),
        "paragraph_duplication_risk_count": int(newalgorithm_metrics.get("paragraph_duplication_risk_count", 0) or 0),
        "paragraph_heading_echo_count": int(newalgorithm_metrics.get("paragraph_heading_echo_count", 0) or 0),
        "section_opening_repetition_count": int(newalgorithm_metrics.get("section_opening_repetition_count", 0) or 0),
        "sentence_integrity_warning_count": int(newalgorithm_metrics.get("sentence_integrity_warning_count", 0) or 0),
        "prompt_follow_anchor_coverage": _safe_round_float(newalgorithm_metrics.get("prompt_follow_anchor_coverage"), 4, 0.0),
        "prompt_follow_must_cover_hits": int(newalgorithm_metrics.get("prompt_follow_must_cover_hits", 0) or 0),
        "must_cover_reflection_ratio": _safe_round_float(newalgorithm_metrics.get("must_cover_reflection_ratio"), 4, 0.0),
        "prompt_context_reflection_ratio": _safe_round_float(newalgorithm_metrics.get("prompt_context_reflection_ratio"), 4, 0.0),
        "dx_context_reflection_ratio": _safe_round_float(newalgorithm_metrics.get("dx_context_reflection_ratio"), 4, 0.0),
        "prompt_follow_forbidden_drift_count": int(newalgorithm_metrics.get("prompt_follow_forbidden_drift_count", 0) or 0),
        "bridge_phrase_count": int(newalgorithm_metrics.get("bridge_phrase_count", 0) or 0),
        "reader_emotion_proxy_count": int(newalgorithm_metrics.get("reader_emotion_proxy_count", 0) or 0),
        "fact_slot_coverage": _safe_round_float(newalgorithm_metrics.get("fact_slot_coverage"), 4, 0.0),
        "fact_slot_reuse_count": int(newalgorithm_metrics.get("fact_slot_reuse_count", 0) or 0),
        "source_grounding_reflection_ratio": _safe_round_float(newalgorithm_metrics.get("source_grounding_reflection_ratio"), 4, 0.0),
        "announcement_action_sentence_count": int(newalgorithm_metrics.get("announcement_action_sentence_count", 0) or 0),
        "announcement_invalid_modal_pattern_count": int(newalgorithm_metrics.get("announcement_invalid_modal_pattern_count", 0) or 0),
        "case_result_abstract_summary_count": int(newalgorithm_metrics.get("case_result_abstract_summary_count", 0) or 0),
        "case_result_change_sentence_count": int(newalgorithm_metrics.get("case_result_change_sentence_count", 0) or 0),
        "case_result_condition_sentence_count": int(newalgorithm_metrics.get("case_result_condition_sentence_count", 0) or 0),
        "comparative_fit_sentence_count": int(newalgorithm_metrics.get("comparative_fit_sentence_count", 0) or 0),
        "comparative_absolute_winner_claim_count": int(newalgorithm_metrics.get("comparative_absolute_winner_claim_count", 0) or 0),
        "comparative_axis_shift_count": int(newalgorithm_metrics.get("comparative_axis_shift_count", 0) or 0),
        "example_specificity_count": int(newalgorithm_metrics.get("example_specificity_count", 0) or 0),
        "abstract_example_fallback_count": int(newalgorithm_metrics.get("abstract_example_fallback_count", 0) or 0),
        "unverified_legal_citation_count": int(newalgorithm_metrics.get("unverified_legal_citation_count", 0) or 0),
    }
    return {
        "timestamp": timestamp,
        "attempt_id": attempt_id,
        "source_file": str(LATEST_GENERATION_TEXT_PATH),
        "metrics": metrics,
        "newalgorithm_metrics": newalgorithm_metrics,
        "output_guard": _to_plain_dict(failed_parameters.get("output_guard")),
        "legacy_metrics": {
            "hard_soft_metrics": hard_soft_metrics,
            "contextual_naturalness_report": naturalness,
            "proposition_density": proposition_density,
            "fingerprint_phase": fingerprint,
        },
        "failure_parameters": failed_parameters,
        "quality_mode_resolution": _to_plain_dict(failed_parameters.get("quality_mode_resolution")),
        "final_quality_eval": _to_plain_dict(failed_parameters.get("final_quality_eval")),
        "config_snapshot": config_snapshot,
        "log_events": {},
    }


def append_generation_audit_record(record: Dict[str, Any]) -> int:
    def _sanitize_log_value(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): _sanitize_log_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_sanitize_log_value(v) for v in value]
        if isinstance(value, str):
            text = value.replace("\r", " ").replace("\n", " ").replace("\t", " ").replace("\x00", "")
            text = " ".join(text.split())
            return text[:500] + "..." if len(text) > 500 else text
        return value

    normalized = _to_plain_dict(record)
    reason_code = str(normalized.get("runtime_reason_code") or normalized.get("reason_code") or "OK")
    normalized.setdefault("reason_code", reason_code)
    normalized.setdefault("runtime_reason_code", reason_code)
    normalized.setdefault("runtime_error_class", _classify_reason_code(reason_code))
    normalized.setdefault("status", "success" if reason_code == "OK" else "error")
    normalized.setdefault("article_type", str(normalized.get("article_type", "") or "unknown"))
    normalized.setdefault("media", str(normalized.get("media", "") or "note"))
    normalized.setdefault("warnings", _to_plain_list(normalized.get("warnings")))
    payload = json.dumps(_sanitize_log_value(normalized), ensure_ascii=False)
    success_count = 0
    for target in (GENERATION_AUDIT_JSONL_PATH, GENERATION_AUDIT_JSONL_PATH_WORKSPACE):
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as f:
                f.write(payload + "\n")
            success_count += 1
        except Exception as exc:
            logger.warning("Failed to append generation audit record path=%s: %s", target, exc)
    return success_count


def persist_latest_generation_snapshot(
    *,
    result: Dict[str, Any],
    attempt_id: str,
    article_type: str,
    writing_focus_key: str,
    perspective_key: str,
    prompt_raw: str,
    system_hint_items: List[str] | None,
    retry_memo: List[str] | None,
    strict_saas_mode: str,
    source_count: int,
    tone_profile_key: str = "auto",
    blocked: bool = False,
) -> None:
    full_text = (result.get("full_text", "") or "").strip()
    runtime_reason_code = str(result.get("runtime_reason_code", "") or result.get("reason_code", "") or "")
    pipeline_check = _to_plain_dict(result.get("pipeline_check"))
    pipeline_error = _to_plain_dict(pipeline_check.get("error"))
    should_persist_empty_failure_snapshot = (
        runtime_reason_code == "SYS_PIPELINE_FAILURE"
        and (bool(pipeline_error) or not bool(result.get("success", True)))
    )
    if not full_text and not blocked and not should_persist_empty_failure_snapshot:
        return
    stored_full_text = "[BLOCKED_OUTPUT_REDACTED]" if blocked else full_text

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    review_points = result.get("review_points") or []
    if not isinstance(review_points, list):
        review_points = []
    review_points = [str(point) for point in review_points if str(point).strip()]
    config_snapshot = collect_runtime_config_snapshot(result)
    failed_parameters = collect_failed_parameters(result)
    retry_failures = _to_plain_list(failed_parameters.get("retry_failures"))
    hard_soft_report = _to_plain_dict(failed_parameters.get("hard_soft_eval"))
    naturalness_report = _to_plain_dict(failed_parameters.get("contextual_naturalness_report"))
    proposition_density = _to_plain_dict(failed_parameters.get("proposition_density"))
    semantic_layout = _to_plain_dict(naturalness_report.get("semantic_layout"))
    algorithm_trace = build_algorithm_trace_snapshot(pipeline_check)
    contract_alignment = build_pipeline_contract_alignment(pipeline_check)
    input_contract = _to_plain_dict(pipeline_check.get("input_contract"))
    alignment_score = _safe_round_float(
        result.get("zero_base_alignment_score"),
        4,
        _safe_round_float(contract_alignment.get("alignment_score"), 4, 0.0),
    )
    question_generation_owner = str(
        result.get("question_generation_owner")
        or input_contract.get("question_generation_owner")
        or ""
    ).strip()
    semantic_article_key = str(input_contract.get("semantic_article_key") or "").strip()
    ui_journey = _to_plain_dict(input_contract.get("ui_journey"))
    source_fit = _to_plain_dict(input_contract.get("source_fit"))
    question_source_counts = _to_plain_dict(contract_alignment.get("question_source_counts"))
    runtime_error_class = str(result.get("runtime_error_class", "") or _classify_reason_code(runtime_reason_code))
    needs_input_items = _to_plain_list(result.get("needs_input_items"))
    normalized_prompt_raw = str(prompt_raw or result.get("prompt_raw") or result.get("user_prompt") or "").strip()
    normalized_system_hint_items = [
        str(item).strip() for item in (system_hint_items or result.get("system_hint_items") or []) if str(item or "").strip()
    ]
    normalized_retry_memo = [
        str(item).strip() for item in (retry_memo or result.get("retry_memo") or []) if str(item or "").strip()
    ]
    normalized_strict_saas_mode = str(
        strict_saas_mode
        or input_contract.get("strict_saas_mode")
        or config_snapshot.get("strict_saas_mode")
        or ""
    ).strip()

    text_payload = (
        f"# Latest Generation Output\n"
        f"timestamp: {timestamp}\n"
        f"attempt_id: {attempt_id}\n"
        f"article_type: {article_type}\n"
        f"writing_focus: {writing_focus_key}\n"
        f"perspective: {perspective_key}\n"
        f"tone_profile: {tone_profile_key}\n"
        f"source_count: {source_count}\n"
        f"blocked_output_redacted: {bool(blocked)}\n"
        f"strict_saas_mode: {normalized_strict_saas_mode or '-'}\n"
        f"question_generation_owner: {question_generation_owner or '-'}\n"
        f"semantic_article_key: {semantic_article_key or '-'}\n"
        f"source_fit_status: {str(source_fit.get('status') or '-')}\n"
        f"prompt_raw: {normalized_prompt_raw}\n"
        f"system_hint_items: {' / '.join(normalized_system_hint_items[:5]) if normalized_system_hint_items else '-'}\n"
        f"retry_memo: {' / '.join(normalized_retry_memo[:5]) if normalized_retry_memo else '-'}\n"
        f"review_points: {' / '.join(review_points[:5]) if review_points else '-'}\n\n"
        f"generation_mode: {config_snapshot.get('generation_mode', 'zero_base_v2')}\n"
        f"runtime_error_class: {runtime_error_class or '-'}\n"
        f"runtime_reason_code: {runtime_reason_code or '-'}\n"
        f"needs_input_items: {len(needs_input_items)}\n"
        f"retry_failures: {len(retry_failures)}\n"
        f"hard_failed: {bool(hard_soft_report.get('hard_failed', False))}\n"
        f"soft_issue_count: {naturalness_report.get('soft_issue_count', 0)}\n\n"
        f"semantic_issue_count: {naturalness_report.get('semantic_issue_count', 0)}\n"
        f"contract_alignment_score: {alignment_score}\n"
        f"prompt_anchor_coverage: {contract_alignment.get('prompt_anchor_coverage', 0.0)}\n"
        f"anchor_term_coverage: {contract_alignment.get('anchor_term_coverage', 0.0)}\n"
        f"section_focus_coverage: {contract_alignment.get('section_focus_coverage', 0.0)}\n"
        f"heading_alignment_mean: {semantic_layout.get('heading_alignment_mean', 0.0)}\n"
        f"transition_jaccard_mean: {semantic_layout.get('transition_jaccard_mean', 0.0)}\n"
        f"abrupt_opening_ratio: {semantic_layout.get('abrupt_opening_ratio', 0.0)}\n\n"
        f"awkward_endings: {naturalness_report.get('awkward_ending_count', 0)}\n"
        f"ai_template_endings: {naturalness_report.get('ai_template_ending_count', 0)}\n"
        f"ai_template_ending_ratio: {naturalness_report.get('ai_template_ending_ratio', 0.0)}\n"
        f"ellipsis_opening_ratio: {naturalness_report.get('ellipsis_opening_ratio', 0.0)}\n\n"
        f"proposition_sentence_count: {proposition_density.get('sentence_count', 0)}\n"
        f"proposition_informative_ratio: {proposition_density.get('informative_ratio', 0.0)}\n"
        f"proposition_low_info_ratio: {proposition_density.get('low_info_ratio', 0.0)}\n\n"
        f"{stored_full_text}\n"
    )

    json_payload = {
        "log_compat_version": "phase06-quasi-strict-v1",
        "timestamp": timestamp,
        "attempt_id": attempt_id,
        "article_type": article_type,
        "writing_focus": writing_focus_key,
        "perspective": perspective_key,
        "tone_profile": tone_profile_key,
        "source_count": source_count,
        "strict_saas_mode": normalized_strict_saas_mode,
        "question_generation_owner": question_generation_owner,
        "semantic_article_key": semantic_article_key,
        "ui_journey": ui_journey,
        "source_fit": source_fit,
        "user_prompt": normalized_prompt_raw,
        "prompt_raw": normalized_prompt_raw,
        "system_hint_items": normalized_system_hint_items,
        "retry_memo": normalized_retry_memo,
        "title": result.get("title", ""),
        "lead": result.get("lead", ""),
        "body": result.get("body", ""),
        "references": result.get("references", ""),
        "hashtags": result.get("hashtags", ""),
        "full_text": stored_full_text,
        "blocked_output_redacted": bool(blocked),
        "linkedin_text": result.get("linkedin_text", ""),
        "runtime_error_class": runtime_error_class,
        "runtime_reason_code": runtime_reason_code,
        "needs_input_items": needs_input_items,
        "review_points": review_points,
        "input_contract": input_contract,
        "pipeline_check": pipeline_check,
        "algorithm_trace": algorithm_trace,
        "pipeline_check_linkedin": _to_plain_dict(result.get("pipeline_check_linkedin")),
        "quality_pipeline_check": _to_plain_dict(result.get("quality_pipeline_check")),
        "llm_check": _to_plain_dict(result.get("llm_check")),
        "zero_base_question_sources": _to_plain_dict(result.get("zero_base_question_sources")),
        "zero_base_contract_alignment": contract_alignment,
        "contract_alignment_score": alignment_score,
        "config_snapshot": config_snapshot,
        "failed_parameters": failed_parameters,
        "compatibility": {
            "mode": "quasi_strict",
            "core_keys": [
                "timestamp",
                "attempt_id",
                "article_type",
                "title",
                "lead",
                "body",
                "references",
                "hashtags",
                "full_text",
                "runtime_reason_code",
            ],
        },
    }
    quality_payload = build_latest_quality_report_payload(
        timestamp=timestamp,
        attempt_id=attempt_id,
        result=result,
        config_snapshot=config_snapshot,
        failed_parameters=failed_parameters,
    )

    targets = [
        (LATEST_GENERATION_TEXT_PATH, text_payload),
        (LATEST_GENERATION_TEXT_PATH_WORKSPACE, text_payload),
        (LATEST_GENERATION_JSON_PATH, json.dumps(json_payload, ensure_ascii=False, indent=2)),
        (LATEST_GENERATION_JSON_PATH_WORKSPACE, json.dumps(json_payload, ensure_ascii=False, indent=2)),
        (LATEST_GENERATION_QUALITY_REPORT_PATH, json.dumps(quality_payload, ensure_ascii=False, indent=2)),
        (LATEST_GENERATION_QUALITY_REPORT_PATH_WORKSPACE, json.dumps(quality_payload, ensure_ascii=False, indent=2)),
    ]
    written_targets = 0
    failed_target_paths: List[str] = []
    for target_path, content in targets:
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
            written_targets += 1
        except Exception as exc:
            failed_target_paths.append(str(target_path))
            logger.warning("Failed to save generation snapshot path=%s id=%s: %s", target_path, attempt_id, exc)

    audit_written_count = append_generation_audit_record(
        {
            "timestamp": timestamp,
            "attempt_id": attempt_id,
            "article_type": article_type,
            "writing_focus": writing_focus_key,
            "perspective": perspective_key,
            "tone_profile": tone_profile_key,
            "source_count": source_count,
            "review_points": review_points[:5],
            "runtime_error_class": runtime_error_class,
            "runtime_reason_code": runtime_reason_code,
            "needs_input_items": needs_input_items[:5],
            "input_contract": {
                "length_mode_requested": str(input_contract.get("length_mode_requested", "") or ""),
                "length_mode": str(input_contract.get("length_mode", "") or ""),
                "audience_profile": str(input_contract.get("audience_profile", "") or ""),
                "topic_statement": str(input_contract.get("topic_statement", "") or ""),
                "prompt_raw": normalized_prompt_raw,
                "strict_saas_mode": normalized_strict_saas_mode,
                "question_generation_owner": question_generation_owner,
                "semantic_article_key": semantic_article_key,
                "comparison_axes": _to_plain_list(input_contract.get("comparison_axes"))[:2],
                "ui_journey": {
                    "purpose_key": str(ui_journey.get("purpose_key") or ""),
                    "target_key": str(ui_journey.get("target_key") or ""),
                    "detail_key": str(ui_journey.get("detail_key") or ""),
                },
                "source_fit_status": str(source_fit.get("status") or ""),
            },
            "output_metrics": {
                "title_chars": len(str(result.get("title", "") or "")),
                "lead_chars": len(str(result.get("lead", "") or "")),
                "body_chars": len(str(result.get("body", "") or "")),
                "full_text_chars": len(full_text),
                "linkedin_chars": len(str(result.get("linkedin_text", "") or "")),
                "proposition_sentence_count": int(proposition_density.get("sentence_count", 0) or 0),
                "proposition_informative_ratio": _safe_round_float(proposition_density.get("informative_ratio"), 4, 0.0),
                "proposition_low_info_ratio": _safe_round_float(proposition_density.get("low_info_ratio"), 4, 0.0),
            },
            "contract_alignment": {
                "alignment_score": alignment_score,
                "category_consistency_score": _safe_round_float(contract_alignment.get("category_consistency_score"), 4, 0.0),
                "question_reflection_rate": _safe_round_float(contract_alignment.get("question_reflection_rate"), 4, 0.0),
                "must_cover_reflection_rate": _safe_round_float(contract_alignment.get("must_cover_reflection_rate"), 4, 0.0),
                "prompt_anchor_coverage": _safe_round_float(contract_alignment.get("prompt_anchor_coverage"), 4, 1.0),
                "anchor_term_coverage": _safe_round_float(contract_alignment.get("anchor_term_coverage"), 4, 1.0),
                "section_focus_coverage": _safe_round_float(contract_alignment.get("section_focus_coverage"), 4, 1.0),
                "speaker_consistency_score": _safe_round_float(contract_alignment.get("speaker_consistency_score"), 4, 0.0),
                "audience_address_consistency": _safe_round_float(contract_alignment.get("audience_address_consistency"), 4, 0.0),
                "register_drift_index": _safe_round_float(contract_alignment.get("register_drift_index"), 4, 0.0),
                "pronoun_consistency_score": _safe_round_float(contract_alignment.get("pronoun_consistency_score"), 4, 0.0),
                "source_trace_coverage": _safe_round_float(contract_alignment.get("source_trace_coverage"), 4, 0.0),
                "must_cover_items": _to_plain_list(contract_alignment.get("must_cover_items"))[:12],
                "audience_profile": str(contract_alignment.get("audience_profile", "") or ""),
                "topic_statement": str(contract_alignment.get("topic_statement", "") or ""),
                "question_source_counts": question_source_counts,
            },
            "algorithm_trace": {
                "stage_order": list(algorithm_trace.get("stage_order") or []),
                "discourse_section_count": int(algorithm_trace.get("discourse_section_count", 0) or 0),
            },
            "editor_guard": {
                "repair_count": int(_to_plain_dict(pipeline_check.get("editor_report")).get("sentence_integrity_repair_count", 0) or 0),
                "warning_count": int(_to_plain_dict(pipeline_check.get("editor_report")).get("sentence_integrity_warning_count", 0) or 0),
                "repair_kinds": [
                    str(item.get("kind") or "")
                    for item in _to_plain_list(_to_plain_dict(pipeline_check.get("editor_report")).get("repair_actions"))
                    if isinstance(item, dict) and bool(item.get("applied", False)) and str(item.get("kind") or "").strip()
                ][:8],
            },
            "config_snapshot": config_snapshot,
            "failed_parameters": failed_parameters,
        }
    )
    published_inventory_written_count = 0
    if bool(result.get("success")) and not bool(blocked):
        published_inventory_written_count = append_published_post_inventory_entry(
            build_published_post_inventory_entry(
                attempt_id=attempt_id,
                timestamp=timestamp,
                result=result,
                input_contract=input_contract,
                article_type=article_type,
            )
        )
    if written_targets == 0:
        logger.warning("No snapshot files were saved id=%s", attempt_id)
    if audit_written_count == 0:
        logger.warning("No generation audit records were appended id=%s", attempt_id)
    if bool(result.get("success")) and not bool(blocked) and published_inventory_written_count == 0:
        logger.warning("No published post inventory records were appended id=%s", attempt_id)

    logger.info(
        "Latest generation snapshot processed id=%s written_targets=%s audit_written_targets=%s published_inventory_written_targets=%s",
        attempt_id,
        written_targets,
        audit_written_count,
        published_inventory_written_count,
    )
    if failed_target_paths:
        logger.warning("Snapshot save had partial failures id=%s failed_paths=%s", attempt_id, failed_target_paths)
