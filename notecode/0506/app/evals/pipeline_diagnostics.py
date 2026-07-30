from __future__ import annotations

from typing import Any

from app.evals.hardening import verify_claim_traceability
from app.services.pipeline_runner import BlogPipelineResult
from app.services.stylometry import analyze_text, ending_bucket, split_sentences


def build_pipeline_diagnostics(
    result: BlogPipelineResult,
    observer_report: dict[str, Any],
    source_readiness: list[dict[str, Any]],
) -> dict[str, Any]:
    quality = result.quality_check["quality_check"]
    draft_metrics = analyze_text(result.draft)
    final_metrics = quality["stylometry"]
    brief = result.article_brief["article_brief"]
    draft_call = _stage_call(observer_report, "draft_writer")
    opening_call = _stage_call(observer_report, "opening_editor")
    global_call = _stage_call(observer_report, "global_consistency_editor")
    style_call = _stage_call(observer_report, "style_editor")
    structural_call = _stage_call(observer_report, "structural_editor")
    traceability_problems = verify_claim_traceability(result.knowledge_pack, result.article_brief)
    editor_outputs_present = all(
        bool(str(text).strip())
        for text in (
            result.opening_edited_draft,
            result.global_consistency_edited_draft,
            result.edited_draft,
            result.structural_edited_draft,
        )
    )
    observed_editor_calls = bool(opening_call and global_call and style_call and structural_call)

    checks = {
        "editing_persona_fired": _pass(
            bool((observed_editor_calls or editor_outputs_present) and brief.get("style_profile_id") and brief.get("editor_profile_id")),
            "opening, global consistency, style, and structural editing completed with configured persona refs",
            details={
                "observed_external_editor_calls": observed_editor_calls,
                "deterministic_editor_outputs_present": editor_outputs_present,
            },
        ),
        "structured_source_passed_to_generation": _pass(
            bool(draft_call and draft_call["payload_summary"].get("structured_claims_passed")),
            "draft_writer received article_brief plus article_knowledge_pack confirmed claims",
            note="raw source packets are intentionally not passed to draft_writer",
        ),
        "passed_source_is_appropriate": _pass(
            _source_readiness_ok(source_readiness)
            and not traceability_problems
            and len(result.knowledge_pack["article_knowledge_pack"]["confirmed_facts"]) >= 8,
            "sources are readable, unblocked, traceable, and produce enough confirmed claims",
            details={
                "source_count": len(source_readiness),
                "total_extracted_chars": sum(item["extracted_text_chars"] for item in source_readiness),
                "traceability_problems": traceability_problems,
            },
        ),
        "generation_persona_output_is_appropriate": _pass(
            _text_generation_ok(result.draft, result.final_article, brief, quality),
            "draft/final keep narrator, avoid third-party leakage, and finish without QA issues",
            details={
                "draft_sentence_count": draft_metrics["sentence_count"],
                "draft_max_sentence_length": draft_metrics["max_sentence_length"],
                "final_sentence_count": final_metrics["sentence_count"],
                "final_max_sentence_length": final_metrics["max_sentence_length"],
                "quality_issue_types": [issue["type"] for issue in quality["issues"]],
                "manual_red_flags": _manual_red_flags(result.final_article),
            },
        ),
    }
    return {
        "overall_pass": all(item["pass"] for item in checks.values()),
        "checks": checks,
        "observer_checks": observer_report["checks"],
        "stage_order": observer_report["stages"],
    }


def _stage_call(observer_report: dict[str, Any], stage_name: str) -> dict[str, Any] | None:
    for call in observer_report.get("calls", []):
        if call["stage_name"] == stage_name:
            return call
    return None


def _source_readiness_ok(source_readiness: list[dict[str, Any]]) -> bool:
    if not source_readiness:
        return False
    if any(not item["can_proceed"] for item in source_readiness):
        return False
    if any(item["extraction_confidence"] == "low" for item in source_readiness):
        return False
    return sum(item["extracted_text_chars"] for item in source_readiness) >= 1200


def _text_generation_ok(
    draft: str,
    final_article: str,
    brief: dict[str, Any],
    quality: dict[str, Any],
) -> bool:
    narrator = brief["narrator"]
    forbidden_terms = brief.get("forbidden_viewpoint_terms", [])
    if narrator not in draft or narrator not in final_article:
        return False
    if any(term in final_article for term in forbidden_terms):
        return False
    if quality["issues"]:
        return False
    return not _manual_red_flags(final_article)


def _manual_red_flags(text: str) -> list[str]:
    flags = []
    fragments = ("前処理から後処理まで。", "RPAとデータエントリの。", "データに関する課題を解決し、。")
    if any(fragment in text for fragment in fragments):
        flags.append("fragment_like_sentence")
    if _has_bare_short_noun_sentence(text):
        flags.append("bare_short_noun_sentence")
    if "私で4代目" in text:
        flags.append("source_voice_leakage")
    if "HPをご覧" in text:
        flags.append("source_page_greeting_leakage")
    return flags


def _has_bare_short_noun_sentence(text: str) -> bool:
    for sentence in split_sentences(text):
        stripped = sentence.rstrip("。！？!?")
        if len(stripped) <= 18 and ending_bucket(sentence) == "名詞止め":
            if not stripped.startswith("#"):
                return True
    return False


def _pass(
    passed: bool,
    reason: str,
    note: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {"pass": passed, "reason": reason}
    if note:
        result["note"] = note
    if details:
        result["details"] = details
    return result
