"""Single-pass note generation pipeline focused on orchestration."""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from note.llm_client import LLMClient
from note.newalgorithm_pipeline.editor_guard import apply_minimal_editor_guard
from note.newalgorithm_pipeline import error_codes
from note.simple_note_pipeline.postprocess import DraftSections, finalize_note_draft, parse_tagged_output
from note.simple_note_pipeline.prompt_builder import (
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


class PipelineRuntimeError(RuntimeError):
    """Runtime error with reason code."""

    def __init__(self, message: str, reason_code: str = error_codes.SYS_PIPELINE_FAILURE) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def _to_plain_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _to_plain_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _runtime_error_class(reason_code: str) -> str:
    code = str(reason_code or "").upper()
    if code.startswith("INP_"):
        return "user_input"
    if code.startswith(("POL_", "SEC_")):
        return "policy"
    if code.startswith("TRN_"):
        return "transient"
    return "system"


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


def _repair_preserves_alignment(current: Mapping[str, Any], repaired: Mapping[str, Any]) -> bool:
    tolerance_by_key = {
        "must_cover_reflection_rate": 0.01,
        "prompt_anchor_coverage": 0.05,
        "section_focus_coverage": 0.05,
    }
    for key, tolerance in tolerance_by_key.items():
        current_value = float(current.get(key) or 0.0)
        repaired_value = float(repaired.get(key) or 0.0)
        if repaired_value + tolerance < current_value:
            return False
    return True


def _compact_plan_safe_scope(contract: Mapping[str, Any]) -> bool:
    article_type = str(contract.get("article_type") or "").strip().lower()
    length_mode = str(contract.get("length_mode") or "").strip().lower()
    return (
        article_type == "explanatory_article" and length_mode in {"short", "adaptive"}
    ) or (
        article_type == "industry_analysis" and length_mode == "short"
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


def _build_flagged_spans(diagnostics: Mapping[str, Any]) -> list[Dict[str, str]]:
    flagged_spans: list[Dict[str, str]] = []
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


def _patch_scaffold_enabled(contract: Mapping[str, Any]) -> bool:
    return bool(contract.get("_flagged_span_patch_scaffold"))


def _patch_activation_enabled(contract: Mapping[str, Any], flagged_spans: list[Dict[str, str]]) -> bool:
    if not flagged_spans or not _compact_plan_safe_scope(contract):
        return False
    return all(item.get("issue_type") in {"heading_reanchor", "ending_bucket_monotony"} for item in flagged_spans)


def _normalize_draft(contract: Mapping[str, Any], draft: DraftSections) -> DraftSections:
    article_type = str(contract.get("article_type") or "").strip().lower()
    normalized_draft, note_rule_check = finalize_note_draft(draft, title_hint=resolve_title_hint(contract))
    if not note_rule_check.passed:
        raise PipelineRuntimeError(
            f"Note rule check failed: {', '.join(note_rule_check.failures)}",
            error_codes.SYS_PIPELINE_FAILURE,
        )
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
        if not _to_plain_list(contract.get("source_documents")):
            return build_input_stop_result(contract, error_codes.INP_MISSING_REQUIRED)

        article_type = str(contract.get("article_type") or "explanatory_article").strip().lower()
        source_pack = build_source_pack(contract)
        compact_plan = self._maybe_build_compact_plan(contract, source_pack)
        if compact_plan:
            contract["_semantic_ledger"] = [dict(item) for item in compact_plan]
        prompt = build_generation_prompt_from_contract(contract, source_pack, compact_plan=compact_plan)
        max_tokens = max(2800, min(7000, int(target_chars(str(contract.get("length_mode") or ""), article_type) * 1.8)))
        self._set_generation_progress("source_digest", 22, detail="素材を整理しています。")

        try:
            self._set_generation_progress("single_pass_generation", 48, detail="本文を一回で生成しています。")
            raw_text, llm_metadata = self._call_llm(prompt, article_type=article_type, max_tokens=max_tokens)
            draft = _normalize_draft(contract, parse_tagged_output(raw_text))
            draft, editor_report = _apply_editor_guard_to_draft(contract, draft)
            self._set_generation_progress("light_guard", 72, detail="重複と主語の出し過ぎを点検しています。", partial_body=draft.body[:1200])
            diagnostics = measure_diagnostics(contract, draft, editor_report=editor_report)
            diagnostics = _merge_quality_guard(
                diagnostics,
                evaluate_quality_guard(contract=contract, draft=draft, diagnostics=diagnostics, source_pack=source_pack),
            )
            diagnostics = _activate_omission_repair(contract, diagnostics)
            flagged_spans = _build_flagged_spans(diagnostics)
            diagnostics["flagged_spans"] = flagged_spans
            diagnostics["flagged_span_count"] = len(flagged_spans)

            repair_applied = False
            repair_metadata: Dict[str, Any] = {}
            if bool(diagnostics.get("repair_required")):
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
                        "patch_path_available": bool(flagged_spans),
                        "patch_path_used": bool(use_patch_path),
                        "flagged_span_count": len(flagged_spans),
                    }
                )
                repaired = _normalize_draft(contract, parse_tagged_output(repaired_raw))
                repaired, repaired_editor_report = _apply_editor_guard_to_draft(contract, repaired)
                repaired_diagnostics = measure_diagnostics(contract, repaired, editor_report=repaired_editor_report)
                repaired_diagnostics = _merge_quality_guard(
                    repaired_diagnostics,
                    evaluate_quality_guard(contract=contract, draft=repaired, diagnostics=repaired_diagnostics, source_pack=source_pack),
                )
                repaired_diagnostics = _activate_omission_repair(contract, repaired_diagnostics)
                repaired_flagged_spans = _build_flagged_spans(repaired_diagnostics)
                repaired_diagnostics["flagged_spans"] = repaired_flagged_spans
                repaired_diagnostics["flagged_span_count"] = len(repaired_flagged_spans)
                if (
                    repaired.body
                    and float(repaired_diagnostics.get("repair_trigger_score", 1.0) or 1.0)
                    <= float(diagnostics.get("repair_trigger_score", 0.0) or 0.0)
                    and _repair_preserves_alignment(diagnostics, repaired_diagnostics)
                ):
                    draft = repaired
                    diagnostics = repaired_diagnostics
                    editor_report = repaired_editor_report
                    repair_applied = True
            else:
                diagnostics["flagged_spans"] = flagged_spans
                diagnostics["flagged_span_count"] = len(flagged_spans)

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
            self._set_generation_progress("completed", 100, detail="生成が完了しました。", partial_body=draft.body[:1200])
            return result
        except PipelineRuntimeError as exc:
            return build_input_stop_result(contract, getattr(exc, "reason_code", error_codes.SYS_PIPELINE_FAILURE))
        except Exception as exc:
            normalized_reason = str(getattr(exc, "reason_code", "") or error_codes.SYS_PIPELINE_FAILURE)
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
                    "error": {"reason_code": normalized_reason, "message": str(exc)},
                },
            }
