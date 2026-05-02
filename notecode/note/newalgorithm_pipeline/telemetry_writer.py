"""Telemetry writer for minimal newalgorithm pipeline."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

AUDIT_PATH = Path(__file__).resolve().parents[1] / "logs" / "newalgorithm_pipeline_audit.jsonl"
CORE_AUDIT_KEYS = (
    "timestamp",
    "status",
    "reason_code",
    "article_type",
    "media",
    "fallback_used",
    "warnings",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize_log_text(text: str, *, limit: int = 400) -> str:
    value = str(text or "")
    value = value.replace("\r", " ").replace("\n", " ").replace("\t", " ").replace("\x00", "")
    value = " ".join(value.split())
    if len(value) > limit:
        return value[:limit].rstrip() + "..."
    return value


def _sanitize_log_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _sanitize_log_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_log_value(v) for v in value]
    if isinstance(value, str):
        return _sanitize_log_text(value)
    return value


def _classify_reason_code(reason_code: str) -> str:
    code = str(reason_code or "").upper()
    if code.startswith("INP_"):
        return "error"
    if code.startswith(("SYS_", "SEC_", "POL_")):
        return "error"
    return "success"


def _ensure_compat_record(record: Dict[str, Any]) -> Dict[str, Any]:
    line = dict(record)
    reason_code = str(line.get("reason_code", "") or "OK")
    line["reason_code"] = reason_code
    line.setdefault("status", _classify_reason_code(reason_code))
    line.setdefault("article_type", str(line.get("article_type", "") or "unknown"))
    line.setdefault("media", str(line.get("media", "") or "note"))
    line.setdefault("fallback_used", bool(line.get("fallback_used", False)))
    warnings = line.get("warnings", [])
    if not isinstance(warnings, list):
        warnings = [str(warnings)]
    line["warnings"] = [str(item) for item in warnings]
    line["timestamp"] = _utc_now()
    return _sanitize_log_value(line)


def _answered_interview_question_counts(contract: Dict[str, Any]) -> Dict[str, int]:
    answers = contract.get("interview_answers", {}) or {}
    if not isinstance(answers, dict):
        return {}
    tracked_keys = ("perspective", "target", "message")
    if str(contract.get("primary_topic_source") or "").strip() == "user_prompt":
        tracked_keys = ("target",)
    answered = sum(
        1
        for key in tracked_keys
        if str(answers.get(key, "") or "").strip()
    )
    if answered <= 0:
        return {}
    return {
        "interview_answers": answered,
        "user_prompt": 0,
        "unresolved_items": 0,
        "unknown": 0,
    }


def _build_contract_alignment(contract: Dict[str, Any], quality_metrics: Dict[str, Any]) -> Dict[str, Any]:
    audience_profile = str(contract.get("audience_profile", "") or "").strip()
    topic_statement = str(contract.get("topic_statement", "") or "").strip()
    narrative_axis = str(contract.get("narrative_axis", "") or "").strip()
    speaker_profile = str(contract.get("speaker_profile", "") or "").strip()
    primary_topic_source = str(contract.get("primary_topic_source", "") or "").strip()
    prompt_instruction_items = [
        str(item or "").strip()
        for item in (contract.get("prompt_instruction_items", []) or [])
        if str(item or "").strip()
    ][:6]
    focus_bundle = dict(contract.get("focus_bundle", {}) or {})
    main_focus = str(focus_bundle.get("main_focus") or "").strip()
    support_points = [
        str(item or "").strip()
        for item in (focus_bundle.get("support_points", []) or [])
        if str(item or "").strip()
    ][:4]
    source_fact_pool = [
        str(item or "").strip()
        for item in (focus_bundle.get("source_fact_pool", []) or [])
        if str(item or "").strip()
    ][:6]
    knowledge_lenses = [
        str(item or "").strip()
        for item in (contract.get("knowledge_lenses", []) or [])
        if str(item or "").strip()
    ][:6]
    must_cover_items = [
        str(item or "").strip()
        for item in (contract.get("must_cover", []) or [])
        if str(item or "").strip()
    ][:12]
    question_source_counts = _answered_interview_question_counts(contract)
    prompt_anchor_coverage = round(float(quality_metrics.get("prompt_follow_anchor_coverage", 0.0) or 0.0), 4)
    must_cover_reflection_rate = round(float(quality_metrics.get("must_cover_reflection_ratio", 0.0) or 0.0), 4)
    source_trace_coverage = round(float(quality_metrics.get("source_grounding_reflection_ratio", 0.0) or 0.0), 4)
    section_count = max(1, int(quality_metrics.get("section_count", 0) or 0))
    section_focus_hits = int(quality_metrics.get("prompt_follow_discourse_hits", 0) or 0)
    section_focus_coverage = round(min(1.0, section_focus_hits / section_count), 4)
    allowed_pronouns = [
        str(item or "").strip()
        for item in (contract.get("allowed_pronouns", []) or [])
        if str(item or "").strip()
    ][:6]
    interview_answers = contract.get("interview_answers", {}) or {}
    answered_roles = [
        key
        for key in ("target", "perspective", "message")
        if isinstance(interview_answers, dict) and str(interview_answers.get(key, "") or "").strip()
    ]
    if primary_topic_source == "user_prompt":
        answered_roles = [key for key in answered_roles if key == "target"]
    reflected_roles = 0
    if "target" in answered_roles and audience_profile:
        reflected_roles += 1
    if "perspective" in answered_roles and (topic_statement or narrative_axis):
        reflected_roles += 1
    if "message" in answered_roles and must_cover_items:
        reflected_roles += 1
    question_reflection_rate = round(reflected_roles / max(1, len(answered_roles)), 4) if answered_roles else 0.0
    category_consistency_score = 1.0 if str(contract.get("article_type", "") or "").strip() else 0.0
    source_anchor_terms = [
        str(item or "").strip()
        for item in (quality_metrics.get("source_grounding_anchor_terms", []) or [])
        if str(item or "").strip()
    ][:12]
    alignment_score = round(
        category_consistency_score * 0.25
        + question_reflection_rate * 0.25
        + must_cover_reflection_rate * 0.25
        + prompt_anchor_coverage * 0.15
        + section_focus_coverage * 0.10,
        4,
    )
    return {
        "compatibility_source": "native_minimal",
        "alignment_score": alignment_score,
        "category_consistency_score": category_consistency_score,
        "question_reflection_rate": question_reflection_rate,
        "must_cover_reflection_rate": must_cover_reflection_rate,
        "prompt_anchor_coverage": prompt_anchor_coverage,
        "anchor_term_coverage": prompt_anchor_coverage,
        "section_focus_coverage": section_focus_coverage,
        "section_focus_hits": section_focus_hits,
        "section_focus_total": section_count,
        "speaker_consistency_score": 1.0 if speaker_profile else 0.0,
        "relationship_consistency_score": 1.0 if str(contract.get("relationship_mode", "") or "").strip() else 0.0,
        "audience_address_consistency": 1.0 if audience_profile else 0.0,
        "register_drift_index": 0.0,
        "pronoun_consistency_score": 1.0 if allowed_pronouns else 0.0,
        "source_trace_coverage": source_trace_coverage,
        "must_cover_count": len(must_cover_items),
        "must_cover_eval_count": len(must_cover_items),
        "must_cover_reflected_count": min(len(must_cover_items), int(round(must_cover_reflection_rate * len(must_cover_items)))),
        "must_cover_items": must_cover_items,
        "unresolved_count": 0,
        "question_source_coverage": 1.0 if question_source_counts else 0.0,
        "question_source_counts": question_source_counts,
        "question_source_missing_ids": [],
        "question_source_unknown_ids": [],
        "anchor_terms": [item for item in [main_focus, *support_points] if item][:6],
        "prompt_anchor_terms": [item for item in [main_focus, *support_points] if item][:6],
        "source_anchor_terms": source_anchor_terms,
        "forbidden_topic_hit_count": int(quality_metrics.get("prompt_follow_forbidden_drift_count", 0) or 0),
        "forbidden_topic_hits": [],
        "category_mismatch_detected": False,
        "speaker_profile": speaker_profile,
        "audience_profile": audience_profile,
        "topic_statement": topic_statement,
        "primary_topic_source": primary_topic_source,
        "prompt_instruction_items": prompt_instruction_items,
        "focus_bundle": {
            "main_focus": main_focus,
            "support_points": support_points,
            "goal_bias": str(focus_bundle.get("goal_bias") or "").strip(),
            "source_fact_pool": source_fact_pool,
        },
        "narrative_axis": narrative_axis,
        "knowledge_lenses": knowledge_lenses,
        "source_grounding_status": str(contract.get("source_grounding_status") or ""),
        "source_grounding_required": bool(contract.get("source_grounding_required")),
        "section_contract_issue_count": 0,
        "allowed_pronouns": allowed_pronouns,
        "detected_speaker_modes": [speaker_profile] if speaker_profile else [],
        "disallowed_pronoun_hits": [],
        "speaker_third_person_mentions": 0,
        "speaker_advice_tone_count": 0,
        "contract_alignment_reason_codes": [],
        "contract_alignment_risk": False,
    }


def build_pipeline_check(
    *,
    contract: Dict[str, Any],
    discourse_plan: List[Dict[str, str]],
    dedupe_audit: Dict[str, Any],
    editor_report: Dict[str, Any],
    legal_report: Dict[str, Any],
    retries: int,
    fallback_used: bool,
    warnings: List[str],
    style_profile: Dict[str, Any],
    quality_metrics: Dict[str, Any],
    need_question: Dict[str, Any],
    security_gate: Dict[str, Any],
    runtime: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "input_contract": contract,
        "focus_bundle": dict(contract.get("focus_bundle", {}) or {}),
        "input_decision": dict(contract.get("input_decision", {}) or {}),
        "contract_trace": {
            "ui_to_contract": {
                "article_type": str(contract.get("article_type") or ""),
                "content_goal": str(contract.get("content_goal") or ""),
                "writing_focus": str(contract.get("writing_focus") or ""),
                "tone_profile": str(contract.get("tone_profile") or ""),
                "speaker_profile": str(contract.get("speaker_profile") or ""),
                "audience_profile": str(contract.get("audience_profile") or ""),
                "core_message": str(contract.get("core_message") or ""),
                "structure": str(contract.get("structure") or "auto"),
            },
            "generation_contract": {
                "topic_statement": str(contract.get("topic_statement") or ""),
                "must_cover": list(contract.get("must_cover", []) or []),
                "source_grounding_required": bool(contract.get("source_grounding_required")),
                "source_grounding_status": str(contract.get("source_grounding_status") or ""),
                "input_decision": dict(contract.get("input_decision", {}) or {}),
            },
        },
        "io_contract": {
            "contract_resolve": {"in": ["payload"], "out": ["contract"]},
            "discourse_plan": {"in": ["contract"], "out": ["sections"]},
            "section_generation": {"in": ["sections", "topic"], "out": ["body"]},
            "dedupe": {"in": ["body", "contract"], "out": ["deduped_body", "dedupe_audit"]},
            "editor_guard": {"in": ["deduped_body"], "out": ["guarded_body", "editor_report"]},
            "resonance": {"in": ["guarded_body", "contract", "style_profile"], "out": ["resonance_body", "resonance_report"]},
            "quality_pipeline": {"in": ["resonance_body", "contract"], "out": ["quality_body", "quality_pipeline_check"]},
            "legal_postcheck": {"in": ["quality_body"], "out": ["legal_result"]},
            "output_format": {"in": ["quality_body", "topic", "article_type", "contract"], "out": ["result"]},
            "telemetry": {"in": ["all_step_outputs"], "out": ["pipeline_check"]},
        },
        "discourse_plan": discourse_plan,
        "dedupe_audit": dedupe_audit,
        "editor_report": editor_report,
        "legal_report": legal_report,
        "contract_alignment": _build_contract_alignment(contract, quality_metrics),
        "retries": int(retries),
        "fallback_used": bool(fallback_used),
        "warnings": list(warnings),
        "natural_style_profile": style_profile,
        "quality_metrics": quality_metrics,
        "need_question_decision": need_question,
        "security_gate": security_gate,
        "runtime": runtime,
    }


def append_audit_record(record: Dict[str, Any]) -> None:
    """Persist audit record with fail-open behavior."""
    try:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        line = _ensure_compat_record(record)
        with AUDIT_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except Exception:
        # telemetry persistence is fail-open by design.
        return
