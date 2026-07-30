from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = Path(__file__).resolve().parent

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(TOOLS_ROOT))

from note.current_mainline_ui_matrix import SHORT_SWEEP_CASES, UISweepCase, run_ui_sweep_cases  # noqa: E402
from run_stepwise_three_article_gate import FIXED_CASE_IDS, STEP_OPTIMIZED_PROMPTS  # noqa: E402

PROMPT_ONLY_PERSONA_LINES: List[str] = [
    "日本語の note / ブログ記事を自然に仕上げる編集者として書いてください。",
    "宣伝カード調や説明カード調に寄せすぎず、読者が無理なく読める読み物にしてください。",
    "文末を揃えすぎず、段落の長さも揃えすぎず、改行の呼吸を均一にしすぎないでください。",
    "一人称は必要なところだけ使い、主語を省略しすぎて誰の判断か曖昧にしないでください。",
    "後半を言い換え反復にせず、『整理できます / つながります / 見えてきます』型の説明カード調を避けてください。",
    "source にない実績や数値は足さないでください。",
]
PROMPT_ONLY_COMPANY_LINE = (
    "会社自身を指すときは社名を機械的に繰り返さず、必要な箇所では『私たちは』を自然に使ってください。"
)


def _build_prompt_only_self_reference_line(policy_key: str) -> str:
    normalized = str(policy_key or "").strip().lower()
    if normalized == "watashi":
        return "書き手自身を指すときは『私』を優先し、段落冒頭で反復しないでください。"
    if normalized == "watashitachi":
        return "自分たちを指すときは『私たち』を優先し、段落冒頭で反復しないでください。"
    if normalized == "tousha":
        return "自社を指すときは『当社』を優先し、段落冒頭で反復しないでください。"
    if normalized == "heisha":
        return "自社を指すときは『弊社』を優先し、段落冒頭で反復しないでください。"
    if normalized == "minimal":
        return "一人称はなるべく使わず、必要なところだけ自然に置いてください。"
    return ""


def _selected_cases(case_set: str) -> List[UISweepCase]:
    if case_set == "fixed3":
        allowed = set(FIXED_CASE_IDS)
        return [case for case in SHORT_SWEEP_CASES if case.case_id in allowed]
    return list(SHORT_SWEEP_CASES)


def _build_prompt_only_text(case: UISweepCase) -> str:
    lines = [case.user_prompt_text, *PROMPT_ONLY_PERSONA_LINES]
    self_reference_line = _build_prompt_only_self_reference_line(case.self_reference_policy_key)
    if self_reference_line:
        lines.append(self_reference_line)
    elif case.article_type == "branding":
        lines.append(PROMPT_ONLY_COMPANY_LINE)
    return "\n".join(line for line in lines if str(line).strip()).strip()


def _build_mode_cases(mode: str, *, selected_cases: Iterable[UISweepCase]) -> List[UISweepCase]:
    built: List[UISweepCase] = []
    for base in selected_cases:
        prompt_text = base.user_prompt_text
        note_suffix = mode
        if mode == "algorithm":
            prompt_text = STEP_OPTIMIZED_PROMPTS.get(base.case_id, base.user_prompt_text)
            note_suffix = "algorithm-step-optimized" if base.case_id in STEP_OPTIMIZED_PROMPTS else "algorithm-current"
        elif mode == "prompt_only":
            prompt_text = _build_prompt_only_text(base)
            note_suffix = "prompt-only-persona"
        built.append(
            UISweepCase(
                case_id=base.case_id,
                article_type=base.article_type,
                user_prompt_text=prompt_text,
                audience_profile_input=base.audience_profile_input,
                content_goal_key=base.content_goal_key,
                writing_focus_key=base.writing_focus_key,
                tone_profile_key=base.tone_profile_key,
                length_mode_key=base.length_mode_key,
                speaker_profile_input=base.speaker_profile_input,
                core_message_input=base.core_message_input,
                self_reference_policy_key=base.self_reference_policy_key,
                allow_experience=base.allow_experience,
                source_values=list(base.source_values),
                source_documents=deepcopy(base.source_documents),
                interview_answers=deepcopy(base.interview_answers),
                strict_saas_mode=base.strict_saas_mode,
                body_generation_experiment=base.body_generation_experiment,
                ui_journey=deepcopy(base.ui_journey),
                comparison_axes=list(base.comparison_axes),
                note=f"{base.note} / {note_suffix}".strip(" /"),
            )
        )
    return built


def _case_summary(item: Mapping[str, Any]) -> Dict[str, Any]:
    rubric = dict(item.get("rubric") or {})
    quality_read = dict(item.get("quality_read") or {})
    contract_summary = dict(item.get("contract_summary") or {})
    runtime_summary = dict(item.get("runtime_summary") or {})
    rubric_axes = dict(rubric.get("axis_scores") or {})
    human_ai_axis = dict(rubric_axes.get("human_visible_ai_feel") or {})
    final_quality_eval = dict(quality_read.get("final_quality_eval") or {})
    return {
        "case_id": str(item.get("case_id") or ""),
        "rubric_total": int(rubric.get("total_score", 0) or 0),
        "ai_feel": str(quality_read.get("human_visible_ai_feel") or human_ai_axis.get("reason") or ""),
        "soft_warning_count": int(final_quality_eval.get("soft_warning_count", 0) or 0),
        "prompt_anchor_coverage": contract_summary.get("prompt_anchor_coverage"),
        "must_cover_reflection_rate": contract_summary.get("must_cover_reflection_rate"),
        "source_trace_coverage": contract_summary.get("source_trace_coverage"),
        "patch_path_used": runtime_summary.get("patch_path_used"),
        "repair_applied": runtime_summary.get("repair_applied"),
        "artifact_path": str(item.get("artifact_path") or ""),
        "artifact_text_path": str(item.get("artifact_text_path") or ""),
    }


def _mode_summary(payload: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "summary_path": str(payload.get("saved_to") or ""),
        "matrix_status": str(payload.get("matrix_status") or ""),
        "cases": [_case_summary(item) for item in list(payload.get("results") or [])],
    }


def _rank_tuple(case_summary: Mapping[str, Any]) -> tuple:
    return (
        int(case_summary.get("rubric_total", 0) or 0),
        -int(case_summary.get("soft_warning_count", 0) or 0),
        float(case_summary.get("must_cover_reflection_rate") or 0.0),
        float(case_summary.get("source_trace_coverage") or 0.0),
        float(case_summary.get("prompt_anchor_coverage") or 0.0),
    )


def _build_winners(
    mode_cases: Mapping[str, List[Mapping[str, Any]]],
    *,
    selected_cases: Iterable[UISweepCase],
) -> List[Dict[str, Any]]:
    case_ids = [case.case_id for case in selected_cases]
    winners: List[Dict[str, Any]] = []
    for case_id in case_ids:
        ranked = []
        for mode_name, items in mode_cases.items():
            matched = next((item for item in items if str(item.get("case_id") or "") == case_id), None)
            if matched is None:
                continue
            ranked.append((mode_name, matched))
        if not ranked:
            continue
        ranked.sort(key=lambda pair: _rank_tuple(pair[1]), reverse=True)
        top_score = _rank_tuple(ranked[0][1])
        top_modes = [mode_name for mode_name, item in ranked if _rank_tuple(item) == top_score]
        winners.append(
            {
                "case_id": case_id,
                "winner": top_modes[0] if len(top_modes) == 1 else "tie",
                "ranking": [mode_name for mode_name, _ in ranked],
            }
        )
    return winners


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_production_baseline_summary() -> Dict[str, Any]:
    latest_output = _load_json(PROJECT_ROOT / "logs" / "latest_generation_output.json")
    latest_quality = _load_json(PROJECT_ROOT / "logs" / "latest_generation_quality_report.json")
    contract_alignment = dict(latest_quality.get("failure_parameters", {}).get("contract_alignment") or {})
    output_guard = dict(latest_quality.get("output_guard") or {})
    metrics = dict(latest_quality.get("newalgorithm_metrics") or {})
    return {
        "attempt_id": str(latest_output.get("attempt_id") or latest_quality.get("attempt_id") or ""),
        "article_type": str(latest_output.get("article_type") or ""),
        "semantic_article_key": str(latest_output.get("semantic_article_key") or ""),
        "title": str(latest_output.get("title") or ""),
        "ai_feel": "flat_or_repetitive" if int(output_guard.get("soft_warning_count", 0) or 0) > 0 else "",
        "soft_warning_count": int(output_guard.get("soft_warning_count", 0) or 0),
        "prompt_anchor_coverage": contract_alignment.get("prompt_anchor_coverage"),
        "must_cover_reflection_rate": contract_alignment.get("must_cover_reflection_rate"),
        "source_trace_coverage": contract_alignment.get("source_trace_coverage"),
        "ending_bucket_max_run": metrics.get("ending_bucket_max_run"),
        "ending_bucket_monotony_score": metrics.get("ending_bucket_monotony_score"),
        "flat_zone_count": latest_quality.get("metrics", {}).get("flat_zone_count"),
        "repair_applied": latest_quality.get("failure_parameters", {}).get("repair_only_report", {}).get("applied"),
        "patch_path_used": latest_quality.get("failure_parameters", {}).get("repair_only_report", {}).get("would_call_llm"),
        "source_file": str(latest_quality.get("source_file") or ""),
    }


def _write_payload(root: Path, payload: Mapping[str, Any]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "combined_summary.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run minimum hybrid vs prompt-only 10-case compare matrix.")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--label", default="baseline31")
    parser.add_argument("--case-set", choices=("short10", "fixed3"), default="short10")
    parser.add_argument("--artifact-root", default="")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    selected_cases = _selected_cases(args.case_set)
    artifact_root = (
        Path(args.artifact_root)
        if args.artifact_root
        else PROJECT_ROOT / "logs" / "codex_minimum_hybrid_compare_matrix" / f"{timestamp}-{args.case_set}-{args.label}"
    )

    mode_payloads: Dict[str, Dict[str, Any]] = {}
    for mode_name in ("generic", "algorithm", "prompt_only"):
        mode_dir = artifact_root / mode_name
        payload = run_ui_sweep_cases(
            _build_mode_cases(mode_name, selected_cases=selected_cases),
            live=bool(args.live),
            artifact_dir=mode_dir,
        )
        payload["generated_at"] = datetime.now().isoformat(timespec="seconds")
        payload["saved_to"] = str(mode_dir / "summary.json")
        mode_dir.mkdir(parents=True, exist_ok=True)
        (mode_dir / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        mode_payloads[mode_name] = payload

    mode_summaries = {name: _mode_summary(payload) for name, payload in mode_payloads.items()}
    mode_cases = {name: list(summary.get("cases") or []) for name, summary in mode_summaries.items()}
    combined = {
        "artifact_root": str(artifact_root),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "live": bool(args.live),
        "case_set": args.case_set,
        "case_ids": [case.case_id for case in selected_cases],
        "compare_entry_count": sum(len(items) for items in mode_cases.values()),
        "production_reference_count": 1,
        "entry_count": sum(len(items) for items in mode_cases.values()) + 1,
        "modes": mode_summaries,
        "production_like_baseline": _build_production_baseline_summary(),
        "winners": _build_winners(mode_cases, selected_cases=selected_cases),
    }
    combined_path = _write_payload(artifact_root, combined)
    combined["combined_summary_path"] = str(combined_path)
    print(json.dumps(combined, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
