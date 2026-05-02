"""Projection helpers from vNext runtime to current-compatible shapes.

Allowed dependencies:
- note.vnext.types
- note.vnext.pipeline
- stdlib
"""
from __future__ import annotations

from typing import Any, Dict, Mapping


def _to_plain_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def project_vnext_result_to_current_shape(vnext_result: Mapping[str, Any]) -> Dict[str, Any]:
    normalized = dict(vnext_result or {})
    thin_contract = _to_plain_dict(normalized.get("thin_contract"))
    return {
        "success": bool(normalized.get("success", False)),
        "title": str(normalized.get("title") or ""),
        "lead": str(normalized.get("lead") or ""),
        "body": str(normalized.get("body") or ""),
        "references": str(normalized.get("references") or ""),
        "hashtags": str(normalized.get("hashtags") or ""),
        "full_text": str(normalized.get("full_text") or ""),
        "pipeline_source": "vnext_mainline",
        "pipeline_check": {
            "input_contract": thin_contract,
            "vnext": {
                "planner_report": _to_plain_dict(normalized.get("planner_report")),
                "evaluation_report": _to_plain_dict(normalized.get("evaluation_report")),
                "repair_report": _to_plain_dict(normalized.get("repair_report")),
                "rendered_sections": list(normalized.get("rendered_sections") or []),
            },
        },
        "runtime_reason_code": "OK",
        "runtime_error_class": "",
    }


def build_vnext_shadow_projection(
    *,
    vnext_result: Mapping[str, Any],
    current_result: Mapping[str, Any],
) -> Dict[str, Any]:
    normalized_vnext = dict(vnext_result or {})
    normalized_current = dict(current_result or {})
    planner_report = _to_plain_dict(normalized_vnext.get("planner_report"))
    repair_report = _to_plain_dict(normalized_vnext.get("repair_report"))
    evaluation_report = _to_plain_dict(normalized_vnext.get("evaluation_report"))
    thin_contract = _to_plain_dict(normalized_vnext.get("thin_contract"))
    current_pipeline = _to_plain_dict(normalized_current.get("pipeline_check"))
    return {
        "enabled": True,
        "mode": "shadow",
        "success": bool(normalized_vnext.get("success", False)),
        "owner": "note.vnext.pipeline.VNextPipeline",
        "contract_summary": {
            "article_type": str(thin_contract.get("article_type") or ""),
            "semantic_subtype": str(thin_contract.get("semantic_subtype") or ""),
            "discourse_mode": str(thin_contract.get("discourse_mode") or ""),
            "evidence_style": str(thin_contract.get("evidence_style") or ""),
            "emotion_level": int(thin_contract.get("emotion_level", 0) or 0),
            "preservation_policy": str(thin_contract.get("preservation_policy") or ""),
        },
        "planner": {
            "section_count": int(planner_report.get("section_count", 0) or 0),
            "overlap_policy": _to_plain_dict(planner_report.get("overlap_policy")),
        },
        "repair": {
            "actions": list(repair_report.get("actions") or []),
            "surface_only_preservation": bool(repair_report.get("surface_only_preservation", False)),
            "mandatory_scope": list(evaluation_report.get("mandatory_scope") or []),
            "warning_first_scope": list(evaluation_report.get("warning_first_scope") or []),
        },
        "comparison": {
            "current_body_chars": len(str(normalized_current.get("body") or "")),
            "vnext_body_chars": len(str(normalized_vnext.get("body") or "")),
            "current_section_count": len(current_pipeline.get("discourse_plan", []) or []),
            "vnext_section_count": int(planner_report.get("section_count", 0) or 0),
        },
    }
