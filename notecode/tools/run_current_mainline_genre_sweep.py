from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(PROJECT_ROOT))

from note.current_mainline_ui_matrix import UISweepCase, run_ui_sweep_cases  # noqa: E402

DEFAULT_CASEBOOK_PATH = (
    PROJECT_ROOT / "note" / "tests" / "fixtures" / "current_mainline_genre_sweep_casebook_2026-03-30.json"
)
DEFAULT_ARTIFACT_ROOT = PROJECT_ROOT / "logs" / "current_mainline_ui_runs"
PHASE_CASEBOOK_KEYS: Dict[str, str] = {
    "baseline": "baseline_cases",
    "acceptance": "baseline_cases",
    "stabilization": "stabilization_cases",
    "experimental": "experimental_cases",
}
REVIEW_CHECKLIST: List[str] = [
    "同一内容が複数回出ていないか",
    "lead / body に prompt echo がないか",
    "句読点や改行が平板すぎず、人間の呼吸に見えるか",
    "1段落1〜4文の範囲で息継ぎがあるか",
    "主語の出し方が過剰でも不足でもないか",
    "同じ書き出し / 文末 / 接続が続きすぎていないか",
    "各見出しが別の役割を持ち、内容追従性が落ちていないか",
    "source がある場合に具体性が薄まりすぎていないか",
]


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _normalize_string_list(values: Iterable[Any] | None) -> List[str]:
    normalized: List[str] = []
    for value in values or []:
        text = str(value or "").strip()
        if text:
            normalized.append(text)
    return normalized


def _build_case_from_entry(entry: Mapping[str, Any]) -> UISweepCase:
    return UISweepCase(
        case_id=str(entry.get("case_id") or "").strip(),
        article_type=str(entry.get("article_type") or "").strip(),
        user_prompt_text=str(entry.get("user_prompt_text") or "").strip(),
        audience_profile_input=str(entry.get("audience_profile_input") or "").strip(),
        content_goal_key=str(entry.get("content_goal_key") or "auto"),
        writing_focus_key=str(entry.get("writing_focus_key") or "auto"),
        tone_profile_key=str(entry.get("tone_profile_key") or "auto"),
        length_mode_key=str(entry.get("length_mode_key") or "adaptive"),
        speaker_profile_input=str(entry.get("speaker_profile_input") or "").strip(),
        core_message_input=str(entry.get("core_message_input") or "").strip(),
        allow_experience=bool(entry.get("allow_experience", False)),
        source_values=list(entry.get("source_values") or []),
        source_documents=list(entry.get("source_documents") or []),
        interview_answers=dict(entry.get("interview_answers") or {}),
        strict_saas_mode=str(entry.get("strict_saas_mode") or "medium"),
        body_generation_experiment=str(entry.get("body_generation_experiment") or "").strip().lower(),
        ui_journey=dict(entry.get("ui_journey") or {}),
        comparison_axes=list(entry.get("comparison_axes") or []),
        note=str(entry.get("note") or "").strip(),
    )


def _filter_case_entries(
    entries: Sequence[Mapping[str, Any]],
    *,
    genres: Sequence[str] | None = None,
    case_ids: Sequence[str] | None = None,
) -> List[Dict[str, Any]]:
    genre_filter = {str(item or "").strip() for item in genres or [] if str(item or "").strip()}
    case_filter = {str(item or "").strip() for item in case_ids or [] if str(item or "").strip()}
    filtered: List[Dict[str, Any]] = []
    for entry in entries:
        normalized = dict(entry)
        genre = str(normalized.get("genre") or normalized.get("article_type") or "").strip()
        case_id = str(normalized.get("case_id") or "").strip()
        if genre_filter and genre not in genre_filter:
            continue
        if case_filter and case_id not in case_filter:
            continue
        filtered.append(normalized)
    return filtered


def _build_phase_case_entries(
    casebook: Mapping[str, Any],
    *,
    phase: str,
    genres: Sequence[str] | None = None,
    case_ids: Sequence[str] | None = None,
) -> List[Dict[str, Any]]:
    if phase == "genre-rerun":
        pool = list(casebook.get("baseline_cases") or []) + list(casebook.get("stabilization_cases") or [])
    else:
        casebook_key = PHASE_CASEBOOK_KEYS[phase]
        pool = list(casebook.get(casebook_key) or [])
    return _filter_case_entries(pool, genres=genres, case_ids=case_ids)


def _extract_metric(item: Mapping[str, Any], key: str) -> Any:
    pipeline_check = dict(item.get("pipeline_check") or {})
    quality_metrics = dict(pipeline_check.get("quality_metrics") or {})
    if key in quality_metrics:
        return quality_metrics.get(key)
    final_quality_eval = dict(
        pipeline_check.get("final_quality_eval")
        or dict(pipeline_check.get("failed_parameters") or {}).get("final_quality_eval")
        or {}
    )
    if key == "soft_warning_count":
        return final_quality_eval.get("soft_warning_count")
    return None


def _metric_snapshot(item: Mapping[str, Any]) -> Dict[str, Any]:
    prompt_echo_hits = list(item.get("prompt_echo_hits") or [])
    runtime_summary = dict(item.get("runtime_summary") or {})
    return {
        "rubric_total": int(dict(item.get("rubric") or {}).get("total_score", 0) or 0),
        "short_gate_passed": bool(dict(item.get("short_gate") or {}).get("passed", False)),
        "prompt_echo_hits": len(prompt_echo_hits),
        "paragraph_length_cv": _extract_metric(item, "paragraph_length_cv"),
        "paragraph_count": _extract_metric(item, "paragraph_count"),
        "paragraph_sentence_count_cv": _extract_metric(item, "paragraph_sentence_count_cv"),
        "single_sentence_paragraph_ratio": _extract_metric(item, "single_sentence_paragraph_ratio"),
        "soft_warning_count": _extract_metric(item, "soft_warning_count"),
        "sentence_integrity_warning_count": _extract_metric(item, "sentence_integrity_warning_count"),
        "comparative_axis_shift_count": _extract_metric(item, "comparative_axis_shift_count"),
        "announcement_invalid_modal_pattern_count": _extract_metric(item, "announcement_invalid_modal_pattern_count"),
        "runtime_same_model_retry_count": int(runtime_summary.get("same_model_retry_count", 0) or 0),
        "runtime_model_fallback_attempted": bool(runtime_summary.get("model_fallback_attempted", False)),
        "artifact_text_path": str(item.get("artifact_text_path") or ""),
    }


def _mean(values: Sequence[float]) -> float | None:
    usable = [float(value) for value in values]
    if not usable:
        return None
    return round(sum(usable) / len(usable), 4)


def _build_genre_summary(results: Sequence[Mapping[str, Any]], entry_map: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    by_genre: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for item in results:
        entry = dict(entry_map.get(str(item.get("case_id") or ""), {}))
        genre = str(entry.get("genre") or item.get("selections", {}).get("article_type_key") or "")
        by_genre[genre].append(item)

    summary: Dict[str, Any] = {}
    for genre, items in sorted(by_genre.items()):
        rubric_scores = [int(dict(item.get("rubric") or {}).get("total_score", 0) or 0) for item in items]
        paragraph_length_cvs = [
            value
            for value in (_extract_metric(item, "paragraph_length_cv") for item in items)
            if isinstance(value, (int, float))
        ]
        paragraph_sentence_cvs = [
            value
            for value in (_extract_metric(item, "paragraph_sentence_count_cv") for item in items)
            if isinstance(value, (int, float))
        ]
        summary[genre] = {
            "case_ids": [str(item.get("case_id") or "") for item in items],
            "pass_count": sum(1 for item in items if bool(dict(item.get("short_gate") or {}).get("passed", False))),
            "case_count": len(items),
            "rubric_mean_total": _mean(rubric_scores),
            "rubric_min_total": min(rubric_scores) if rubric_scores else None,
            "prompt_echo_case_ids": [
                str(item.get("case_id") or "")
                for item in items
                if list(item.get("prompt_echo_hits") or [])
            ],
            "sentence_integrity_case_ids": [
                str(item.get("case_id") or "")
                for item in items
                if int(_extract_metric(item, "sentence_integrity_warning_count") or 0) > 0
            ],
            "comparative_axis_shift_case_ids": [
                str(item.get("case_id") or "")
                for item in items
                if int(_extract_metric(item, "comparative_axis_shift_count") or 0) > 0
            ],
            "announcement_modal_issue_case_ids": [
                str(item.get("case_id") or "")
                for item in items
                if int(_extract_metric(item, "announcement_invalid_modal_pattern_count") or 0) > 0
            ],
            "paragraph_length_cv_mean": _mean(paragraph_length_cvs),
            "paragraph_sentence_count_cv_mean": _mean(paragraph_sentence_cvs),
        }
    return summary


def _build_issue_ledger(results: Sequence[Mapping[str, Any]], entry_map: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    genre_summary = _build_genre_summary(results, entry_map)
    ledger = {"genres": {}}
    for genre, summary in genre_summary.items():
        ledger["genres"][genre] = {
            "case_ids": list(summary["case_ids"]),
            "status": "needs_manual_review",
            "recurring_issues": [],
            "watch_metrics": {
                "prompt_echo_case_ids": list(summary["prompt_echo_case_ids"]),
                "sentence_integrity_case_ids": list(summary["sentence_integrity_case_ids"]),
                "comparative_axis_shift_case_ids": list(summary["comparative_axis_shift_case_ids"]),
                "announcement_modal_issue_case_ids": list(summary["announcement_modal_issue_case_ids"]),
            },
            "recommended_first_owner": "note/simple_note_pipeline/*",
        }
    return ledger


def _build_case_manifest(entries: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    source_mode_counts: Dict[str, int] = defaultdict(int)
    genre_counts: Dict[str, int] = defaultdict(int)
    route_keys: List[str] = []
    for entry in entries:
        source_mode_counts[str(entry.get("source_mode") or "unknown")] += 1
        genre = str(entry.get("genre") or entry.get("article_type") or "")
        genre_counts[genre] += 1
        route = dict(entry.get("ui_journey") or {})
        route_keys.append(f"{route.get('purpose_key', '')}/{route.get('target_key', '')}".strip("/"))
    return {
        "case_count": len(entries),
        "genre_counts": dict(sorted(genre_counts.items())),
        "source_mode_counts": dict(sorted(source_mode_counts.items())),
        "route_keys": sorted({item for item in route_keys if item}),
        "case_ids": [str(entry.get("case_id") or "") for entry in entries],
    }


def _build_manual_review_template(
    *,
    phase: str,
    results: Sequence[Mapping[str, Any]],
    entry_map: Mapping[str, Mapping[str, Any]],
) -> str:
    lines: List[str] = [
        f"# manual review ({phase})",
        "",
        "## genre summary notes",
        "- recurring issues:",
        "- kept state regression:",
        "- owner-local fix candidates:",
        "",
    ]
    for item in results:
        case_id = str(item.get("case_id") or "")
        entry = dict(entry_map.get(case_id, {}))
        review_focus = _normalize_string_list(entry.get("review_focus"))
        lines.extend(
            [
                f"## {case_id}",
                f"- genre: {entry.get('genre') or entry.get('article_type')}",
                f"- theme: {entry.get('theme_label') or ''}",
                f"- source_mode: {entry.get('source_mode') or ''}",
                f"- artifact: {item.get('artifact_text_path') or ''}",
                f"- metrics: {json.dumps(_metric_snapshot(item), ensure_ascii=False)}",
                f"- review_focus: {', '.join(review_focus) if review_focus else '(none)'}",
                "- checklist:",
            ]
        )
        for checklist_item in REVIEW_CHECKLIST:
            lines.append(f"  - {checklist_item}")
        lines.extend(
            [
                "- notes:",
                "- verdict:",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def _build_placeholder_markdown(title: str, intro: str) -> str:
    return f"# {title}\n\n{intro}\n\n- none\n"


def _default_artifact_dir(phase: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return DEFAULT_ARTIFACT_ROOT / f"codex-genre-sweep-{timestamp}-{phase}"


def execute_phase(
    *,
    phase: str,
    casebook_path: Path,
    artifact_dir: Path,
    live: bool,
    genres: Sequence[str] | None = None,
    case_ids: Sequence[str] | None = None,
) -> Dict[str, Any]:
    casebook = _load_json(casebook_path)
    selected_entries = _build_phase_case_entries(
        casebook,
        phase=phase,
        genres=genres,
        case_ids=case_ids,
    )
    selected_cases = [_build_case_from_entry(entry) for entry in selected_entries]
    payload = run_ui_sweep_cases(selected_cases, live=live, artifact_dir=artifact_dir)
    entry_map = {str(entry.get("case_id") or ""): entry for entry in selected_entries}
    payload["phase"] = phase
    payload["generated_at"] = datetime.now().isoformat(timespec="seconds")
    payload["casebook_path"] = str(casebook_path)
    payload["case_manifest"] = _build_case_manifest(selected_entries)
    payload["genre_summary"] = _build_genre_summary(payload["results"], entry_map)

    matrix_payload = {
        "phase": phase,
        "casebook_path": str(casebook_path),
        "case_manifest": payload["case_manifest"],
        "cases": selected_entries,
    }
    _write_json(artifact_dir / "matrix.json", matrix_payload)
    _write_json(artifact_dir / "summary.json", payload)
    _write_json(artifact_dir / "genre_issue_ledger.json", _build_issue_ledger(payload["results"], entry_map))
    _write_text(
        artifact_dir / "manual_review.md",
        _build_manual_review_template(phase=phase, results=payload["results"], entry_map=entry_map),
    )
    placeholder_files = {
        "rollback_log.md": _build_placeholder_markdown(
            "rollback log",
            "Rollback を行った場合だけ理由と reverse patch 対象を書く。",
        ),
        "research_notes.md": _build_placeholder_markdown(
            "research notes",
            "Primary source の URL と current algorithm への示唆だけを書く。",
        ),
    }
    for filename, content in placeholder_files.items():
        path = artifact_dir / filename
        if not path.exists():
            _write_text(path, content)
    return payload


def _parse_csv_arg(value: str) -> List[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run current mainline genre sweep.")
    parser.add_argument(
        "--phase",
        choices=("baseline", "genre-rerun", "acceptance", "stabilization", "experimental"),
        required=True,
    )
    parser.add_argument("--live", action="store_true", help="Use live OpenAI execution.")
    parser.add_argument("--casebook", type=str, default=str(DEFAULT_CASEBOOK_PATH))
    parser.add_argument("--artifact-dir", type=str, default="")
    parser.add_argument("--genres", type=str, default="", help="Comma-separated genre keys.")
    parser.add_argument("--case-ids", type=str, default="", help="Comma-separated case ids.")
    args = parser.parse_args()

    casebook_path = Path(args.casebook)
    artifact_dir = Path(args.artifact_dir) if args.artifact_dir else _default_artifact_dir(args.phase)
    genres = _parse_csv_arg(args.genres)
    case_ids = _parse_csv_arg(args.case_ids)

    payload = execute_phase(
        phase=args.phase,
        casebook_path=casebook_path,
        artifact_dir=artifact_dir,
        live=bool(args.live),
        genres=genres,
        case_ids=case_ids,
    )
    print(f"phase={payload['phase']} live={payload['live']} cases={len(payload['results'])}")
    print(f"artifact_dir={artifact_dir}")
    battery_summary = dict(payload.get("battery_summary") or {})
    print(
        "short_gate_passed="
        f"{battery_summary.get('short_gate_passed_count', 0)}/{battery_summary.get('case_count', 0)}"
    )
    print(f"rubric_mean_total={battery_summary.get('rubric_mean_total')}")
    for genre, summary in sorted(dict(payload.get("genre_summary") or {}).items()):
        print(
            f"- {genre}: pass={summary.get('pass_count')}/{summary.get('case_count')} "
            f"rubric_mean_total={summary.get('rubric_mean_total')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
