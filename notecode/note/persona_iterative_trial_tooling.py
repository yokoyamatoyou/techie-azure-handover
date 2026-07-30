"""Tooling helpers for the persona iterative trial initiative."""

from __future__ import annotations

import ast
import json
import shutil
from dataclasses import asdict, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from note.current_mainline_persona_trial import (
    INITIATIVE_ID,
    build_persona_trial_telemetry,
    enrich_persona_trial_contract,
    iter_persona_trial_family_specs,
)
from note.current_mainline_runner import build_current_mainline_input_contract
from note.current_mainline_ui_matrix import UISweepCase, run_ui_sweep_cases

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UI_LIVE_FIXTURE_PATH = (
    PROJECT_ROOT / "新しいフォルダー" / "新しいフォルダー (5)" / "ui_live_genre_sweep_test.py"
)
DEFAULT_RUN_ROOT = (
    PROJECT_ROOT / "新しいフォルダー" / "新しいフォルダー (5)" / "persona_iterative_trial_window_run"
)
DEFAULT_UI_ACCEPTANCE_CASE_ROOT = (
    PROJECT_ROOT / "新しいフォルダー" / "新しいフォルダー (5)" / "ui_live_genre_sweep" / "cases"
)
_LOOP_PHASES: Sequence[str] = ("baseline_1", "baseline_2", "narrow_change", "rerun_1", "rerun_2")

_CASE_ROUTE_BY_GENRE: Dict[str, Dict[str, Any]] = {
    "explanatory_article": {"ui_journey": {"purpose_key": "explain", "target_key": "concept"}},
    "daily_story": {"ui_journey": {"purpose_key": "daily", "target_key": "day_to_day"}},
    "branding": {"ui_journey": {"purpose_key": "introduce", "target_key": "company"}},
    "announcement": {"ui_journey": {"purpose_key": "announce", "target_key": "standard"}},
    "case_study": {"ui_journey": {"purpose_key": "case", "target_key": "implementation"}},
    "industry_analysis": {"ui_journey": {"purpose_key": "explain", "target_key": "industry"}},
    "comparative_review": {"ui_journey": {"purpose_key": "compare", "target_key": "tool_service"}},
}


def _reverse_label_map(mapping: Mapping[str, str]) -> Dict[str, str]:
    return {
        str(label): str(key)
        for key, label in mapping.items()
        if str(key or "").strip() and str(label or "").strip()
    }


def _load_ui_label_maps() -> Dict[str, Dict[str, str]]:
    from note import note_writer_app as ui_mod

    return {
        "content_goal": _reverse_label_map(ui_mod.CONTENT_GOAL_LABELS),
        "tone_profile": _reverse_label_map(ui_mod.TONE_PROFILE_LABELS),
        "writing_focus": _reverse_label_map(ui_mod.WRITING_FOCUS_LABELS),
        "length_mode": _reverse_label_map(ui_mod.LENGTH_MODE_LABELS),
        "self_reference": _reverse_label_map(ui_mod.SELF_REFERENCE_POLICY_LABELS),
    }


def load_ui_live_case_definitions(path: str | Path = DEFAULT_UI_LIVE_FIXTURE_PATH) -> List[Dict[str, Any]]:
    fixture_path = Path(path)
    if not fixture_path.exists() and fixture_path == DEFAULT_UI_LIVE_FIXTURE_PATH:
        archived_fixture_path = (
            PROJECT_ROOT.parent
            / "archive"
            / "cleanup_20260501_1043_phase2"
            / "notecode"
            / "新しいフォルダー"
            / "新しいフォルダー (5)"
            / "ui_live_genre_sweep_test.py"
        )
        if archived_fixture_path.exists():
            fixture_path = archived_fixture_path
    module = ast.parse(fixture_path.read_text(encoding="utf-8"), filename=str(fixture_path))
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "CASES":
                payload = ast.literal_eval(node.value)
                return [dict(item) for item in list(payload or []) if isinstance(item, dict)]
    raise ValueError(f"CASES assignment not found: {fixture_path}")


def _build_source_document(case_id: str, entry: Mapping[str, Any]) -> Dict[str, Any]:
    name = str(entry.get("name") or "source.txt").strip() or "source.txt"
    return {
        "title": name,
        "content": str(entry.get("content") or "").strip(),
        "locator": f"fixture://persona-trial/{case_id}/{name}",
        "source_type": "text",
        "notices": [],
    }


def _first_sentence(text: Any, *, limit: int = 96) -> str:
    raw = " ".join(str(text or "").split()).strip()
    if not raw:
        return ""
    for marker in ("。", "！", "？", ".", "!", "?"):
        position = raw.find(marker)
        if position >= 0:
            return raw[: position + 1][:limit]
    return raw[:limit]


def _derive_user_prompt_text(entry: Mapping[str, Any]) -> str:
    purpose = str(entry.get("purpose_label") or "").strip()
    target = str(entry.get("target_label") or "").strip()
    audience = str(entry.get("audience") or "").strip()
    core_message = str(entry.get("core_message") or "").strip()
    first_source = ""
    for source_entry in list(entry.get("source_docs") or []):
        if not isinstance(source_entry, Mapping):
            continue
        first_source = _first_sentence(source_entry.get("content") or "")
        if first_source:
            break
    if core_message:
        return core_message
    base = " ".join(part for part in (purpose, target) if part)
    if audience and base:
        return f"{audience}向けに、{base}。{first_source}".strip()
    if base:
        return f"{base}。{first_source}".strip()
    if first_source:
        return first_source
    return str(entry.get("case_id") or "persona-iterative-trial").strip()


def build_persona_trial_cases(
    case_definitions: Sequence[Mapping[str, Any]] | None = None,
) -> List[UISweepCase]:
    label_maps = _load_ui_label_maps()
    definitions = list(case_definitions or load_ui_live_case_definitions())
    cases: List[UISweepCase] = []
    for entry in definitions:
        case_id = str(entry.get("case_id") or "").strip()
        article_type = str(entry.get("genre") or "").strip()
        if not case_id or not article_type:
            continue
        detail_settings = dict(entry.get("detail_settings") or {})
        ui_route = dict(_CASE_ROUTE_BY_GENRE.get(article_type, {}))
        ui_journey = dict(ui_route.get("ui_journey") or {})
        if article_type == "comparative_review":
            compare_axes = [str(item or "").strip() for item in list(entry.get("compare_axes") or []) if str(item or "").strip()]
            if compare_axes:
                ui_journey["comparison_axes"] = list(compare_axes)
        source_documents = [
            _build_source_document(case_id, item)
            for item in list(entry.get("source_docs") or [])
            if isinstance(item, Mapping)
        ]
        source_values = [str(item.get("locator") or "").strip() for item in source_documents if str(item.get("locator") or "").strip()]
        cases.append(
            UISweepCase(
                case_id=case_id,
                article_type=article_type,
                user_prompt_text=_derive_user_prompt_text(entry),
                audience_profile_input=str(entry.get("audience") or "").strip(),
                content_goal_key=label_maps["content_goal"].get(
                    str(detail_settings.get("content_goal_label") or ""),
                    "auto",
                ),
                writing_focus_key=label_maps["writing_focus"].get(
                    str(detail_settings.get("writing_focus_label") or ""),
                    "auto",
                ),
                tone_profile_key=label_maps["tone_profile"].get(
                    str(detail_settings.get("tone_profile_label") or ""),
                    "auto",
                ),
                length_mode_key=label_maps["length_mode"].get(
                    str(detail_settings.get("length_mode_label") or ""),
                    "short",
                ),
                speaker_profile_input=str(entry.get("writer_label") or "").strip(),
                core_message_input=str(entry.get("core_message") or "").strip(),
                self_reference_policy_key=label_maps["self_reference"].get(
                    str(detail_settings.get("self_reference_label") or ""),
                    "auto",
                ),
                allow_experience=False,
                source_values=source_values,
                source_documents=source_documents,
                source_mode="grounded",
                ui_journey=ui_journey,
                comparison_axes=list(ui_journey.get("comparison_axes") or []),
                note="persona iterative trial live fixture mirror",
            )
        )
    return cases


def select_persona_trial_cases(
    case_ids: Sequence[str] | None = None,
    *,
    cases: Sequence[UISweepCase] | None = None,
) -> List[UISweepCase]:
    selected_cases = list(cases or build_persona_trial_cases())
    if not case_ids:
        return selected_cases
    requested_ids = [str(case_id or "").strip() for case_id in case_ids if str(case_id or "").strip()]
    case_by_id = {case.case_id: case for case in selected_cases}
    missing_ids = [case_id for case_id in requested_ids if case_id not in case_by_id]
    if missing_ids:
        raise ValueError(f"unknown persona trial case ids: {', '.join(missing_ids)}")
    return [case_by_id[case_id] for case_id in requested_ids]


def build_trial_case_records(
    cases: Sequence[UISweepCase],
    *,
    max_loops: int = 5,
    changed_owner: str = "",
    expected_benefit: str = "",
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for case in cases:
        baseline_config_id = f"{case.case_id}-baseline"
        for index in range(1, min(max_loops, len(_LOOP_PHASES)) + 1):
            phase = _LOOP_PHASES[index - 1]
            records.append(
                {
                    "case_id": case.case_id,
                    "article_type": case.article_type,
                    "trial_loop_index": index,
                    "phase": phase,
                    "baseline_config_id": baseline_config_id,
                    "changed_owner": changed_owner if phase == "narrow_change" else "",
                    "expected_benefit": expected_benefit if phase == "narrow_change" else "",
                    "keep_or_rollback": "pending" if phase != "narrow_change" else "",
                    "stable_success": False,
                    "exhausted": False,
                    "accepted": None,
                }
            )
    return records


def build_persona_matrix_payload() -> List[Dict[str, Any]]:
    return iter_persona_trial_family_specs()


def build_source_packet_notes(cases: Sequence[UISweepCase]) -> List[Dict[str, Any]]:
    notes: List[Dict[str, Any]] = []
    for case in cases:
        contract = build_current_mainline_input_contract(
            source_values=list(case.source_values),
            source_documents=list(case.source_documents),
            article_type=case.article_type,
            user_prompt_text=case.user_prompt_text,
            content_goal_key=case.content_goal_key,
            writing_focus_key=case.writing_focus_key,
            structure_key="auto",
            length_mode_key=case.length_mode_key,
            tone_profile_key=case.tone_profile_key,
            perspective_key="auto",
            allow_experience=bool(case.allow_experience),
            interview_answers=dict(case.interview_answers),
            speaker_profile_input=case.speaker_profile_input,
            audience_profile_input=case.audience_profile_input,
            core_message_input=case.core_message_input,
            self_reference_policy_key=case.self_reference_policy_key,
            strict_saas_mode=case.strict_saas_mode,
            ui_journey=dict(case.ui_journey) if case.ui_journey else None,
            comparison_axes=list(case.comparison_axes),
            body_generation_experiment=case.body_generation_experiment,
            source_mode=case.source_mode,
            industry_hint=case.industry_hint,
            source_trace=list(case.source_trace),
        )
        contract = enrich_persona_trial_contract(contract)
        source_packet = dict(contract.get("_source_packet") or {})
        notes.append(
            {
                "case_id": case.case_id,
                "article_type": case.article_type,
                "audience_profile": case.audience_profile_input,
                "source_fact_count": len(list(source_packet.get("source_facts") or [])),
                "reader_friction": list(source_packet.get("reader_friction") or []),
                "must_cover": list(source_packet.get("must_cover") or []),
                "late_return": str(source_packet.get("late_return") or ""),
                "forbidden_expansion": list(source_packet.get("forbidden_expansion") or []),
            }
        )
    return notes


def build_persona_trial_input_contract(case: UISweepCase) -> Dict[str, Any]:
    return enrich_persona_trial_contract(
        build_current_mainline_input_contract(
            source_values=list(case.source_values),
            source_documents=list(case.source_documents),
            article_type=case.article_type,
            user_prompt_text=case.user_prompt_text,
            content_goal_key=case.content_goal_key,
            writing_focus_key=case.writing_focus_key,
            structure_key="auto",
            length_mode_key=case.length_mode_key,
            tone_profile_key=case.tone_profile_key,
            perspective_key="auto",
            allow_experience=bool(case.allow_experience),
            interview_answers=dict(case.interview_answers),
            speaker_profile_input=case.speaker_profile_input,
            audience_profile_input=case.audience_profile_input,
            core_message_input=case.core_message_input,
            self_reference_policy_key=case.self_reference_policy_key,
            strict_saas_mode=case.strict_saas_mode,
            ui_journey=dict(case.ui_journey) if case.ui_journey else None,
            comparison_axes=list(case.comparison_axes),
            body_generation_experiment=case.body_generation_experiment,
            source_mode=case.source_mode,
            industry_hint=case.industry_hint,
            source_trace=list(case.source_trace),
        )
    )


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, Mapping) else {}


def _write_markdown_if_missing(path: Path, text: str) -> None:
    if path.exists():
        return
    _write_text(path, text)


def _append_markdown_entry(path: Path, heading: str, lines: Sequence[str]) -> None:
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    if content and not content.endswith("\n"):
        content += "\n"
    if content:
        content += "\n"
    content += f"## {heading}\n"
    for line in lines:
        content += f"- {line}\n"
    _write_text(path, content)


def _record_key(record: Mapping[str, Any]) -> tuple[str, int, str]:
    return (
        str(record.get("case_id") or ""),
        int(record.get("trial_loop_index") or 0),
        str(record.get("phase") or ""),
    )


def _merge_trial_case_records(
    template_records: Sequence[Mapping[str, Any]],
    existing_records: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    existing_by_key = {_record_key(record): dict(record) for record in existing_records}
    merged_records: List[Dict[str, Any]] = []
    seen_keys: set[tuple[str, int, str]] = set()
    for template in template_records:
        key = _record_key(template)
        seen_keys.add(key)
        merged = dict(template)
        existing = existing_by_key.get(key)
        if existing:
            merged.update(existing)
            merged["case_id"] = template["case_id"]
            merged["trial_loop_index"] = template["trial_loop_index"]
            merged["phase"] = template["phase"]
            merged["article_type"] = template["article_type"]
            merged["baseline_config_id"] = template["baseline_config_id"]
        merged_records.append(merged)
    for record in existing_records:
        key = _record_key(record)
        if key in seen_keys:
            continue
        merged_records.append(dict(record))
    return merged_records


def load_trial_manifest(run_root: str | Path = DEFAULT_RUN_ROOT) -> Dict[str, Any]:
    return _read_json(Path(run_root) / "case_manifest.json")


def _write_trial_manifest(
    *,
    run_root: str | Path,
    selected_cases: Sequence[UISweepCase],
    records: Sequence[Mapping[str, Any]],
    existing_manifest: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    artifact_root = Path(run_root)
    existing = dict(existing_manifest or {})
    created_at = str(existing.get("created_at") or existing.get("timestamp") or datetime.now().isoformat())
    payload = {
        "initiative_id": INITIATIVE_ID,
        "timestamp": datetime.now().isoformat(),
        "created_at": created_at,
        "case_count": len(selected_cases),
        "records": [dict(record) for record in records],
        "cases": [asdict(case) for case in selected_cases],
    }
    _write_json(artifact_root / "case_manifest.json", payload)
    return payload


def _record_phase_name(loop_index: int) -> str:
    if loop_index < 1 or loop_index > len(_LOOP_PHASES):
        raise ValueError(f"loop index out of range: {loop_index}")
    return str(_LOOP_PHASES[loop_index - 1])


def _find_trial_record(
    records: Sequence[Mapping[str, Any]],
    *,
    case_id: str,
    loop_index: int,
) -> Dict[str, Any]:
    phase_name = _record_phase_name(loop_index)
    for record in records:
        if (
            str(record.get("case_id") or "") == case_id
            and int(record.get("trial_loop_index") or 0) == int(loop_index)
            and str(record.get("phase") or "") == phase_name
        ):
            return dict(record)
    raise ValueError(f"trial record not found: {case_id} loop {loop_index} ({phase_name})")


def _replace_trial_record(
    records: Sequence[Mapping[str, Any]],
    *,
    case_id: str,
    loop_index: int,
    replacement: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    phase_name = _record_phase_name(loop_index)
    updated_records: List[Dict[str, Any]] = []
    matched = False
    for record in records:
        if (
            str(record.get("case_id") or "") == case_id
            and int(record.get("trial_loop_index") or 0) == int(loop_index)
            and str(record.get("phase") or "") == phase_name
        ):
            updated_records.append(dict(replacement))
            matched = True
            continue
        updated_records.append(dict(record))
    if not matched:
        raise ValueError(f"trial record not found: {case_id} loop {loop_index} ({phase_name})")
    return updated_records


def _cases_from_manifest_payload(manifest: Mapping[str, Any] | None) -> List[UISweepCase]:
    cases_payload = list((manifest or {}).get("cases") or [])
    restored_cases: List[UISweepCase] = []
    for item in cases_payload:
        if not isinstance(item, Mapping):
            continue
        restored_cases.append(UISweepCase(**dict(item)))
    return restored_cases


def _write_json(path: Path, payload: Mapping[str, Any] | Sequence[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _render_trial_plan(
    *,
    cases: Sequence[UISweepCase],
    records: Sequence[Mapping[str, Any]],
) -> str:
    lines = [
        f"# {INITIATIVE_ID}",
        "",
        "## scope",
        "- Hybrid mode: mirror diagnostics + Selenium UI acceptance",
        "- current mainline only",
        "- single-pass + optional single repair 1回",
        "- mirror baseline 2 runs -> strict UI anchor -> 1 narrow change -> mirror reruns -> strict UI keep/rollback",
        "- default audience is invalid for trial acceptance",
        "- authoritative acceptance comes from ui_live_genre_sweep_test.py artifacts",
        "",
        "## article types",
    ]
    for case in cases:
        lines.append(f"- {case.article_type}: {case.case_id}")
    lines.extend(
        [
            "",
            "## loop manifest",
        ]
    )
    for record in records:
        lines.append(
            f"- {record['case_id']} loop {record['trial_loop_index']}: {record['phase']} "
            f"(baseline_config_id={record['baseline_config_id']})"
        )
    return "\n".join(lines).strip() + "\n"


def _render_persona_matrix(matrix_rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "# persona matrix",
        "",
        "| article_type | semantic_key | family_key | late_return |",
        "| --- | --- | --- | --- |",
    ]
    for row in matrix_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("article_type") or ""),
                    str(row.get("semantic_article_key") or ""),
                    str(row.get("family_key") or ""),
                    str(row.get("late_return") or ""),
                ]
            )
            + " |"
        )
    return "\n".join(lines).strip() + "\n"


def _render_source_packet_notes(notes: Sequence[Mapping[str, Any]]) -> str:
    lines = ["# source packet notes", ""]
    for note in notes:
        lines.extend(
            [
                f"## {note.get('case_id')}",
                f"- article_type: {note.get('article_type')}",
                f"- audience: {note.get('audience_profile')}",
                f"- source_fact_count: {note.get('source_fact_count')}",
                f"- reader_friction: {json.dumps(list(note.get('reader_friction') or []), ensure_ascii=False)}",
                f"- must_cover: {json.dumps(list(note.get('must_cover') or []), ensure_ascii=False)}",
                f"- late_return: {note.get('late_return')}",
                f"- forbidden_expansion: {json.dumps(list(note.get('forbidden_expansion') or []), ensure_ascii=False)}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def initialize_trial_artifact_dir(
    *,
    run_root: str | Path = DEFAULT_RUN_ROOT,
    cases: Sequence[UISweepCase] | None = None,
    max_loops: int = 5,
    changed_owner: str = "",
    expected_benefit: str = "",
    preserve_existing: bool = True,
) -> Dict[str, Any]:
    artifact_root = Path(run_root)
    selected_cases = list(cases or build_persona_trial_cases())
    template_records = build_trial_case_records(
        selected_cases,
        max_loops=max_loops,
        changed_owner=changed_owner,
        expected_benefit=expected_benefit,
    )
    existing_manifest = load_trial_manifest(artifact_root) if preserve_existing else {}
    existing_records = list(existing_manifest.get("records") or []) if existing_manifest else []
    records = _merge_trial_case_records(template_records, existing_records) if existing_records else list(template_records)
    persona_matrix = build_persona_matrix_payload()
    source_packet_notes = build_source_packet_notes(selected_cases)

    _write_text(
        artifact_root / "trial_plan.md",
        _render_trial_plan(cases=selected_cases, records=records),
    )
    _write_markdown_if_missing(
        artifact_root / "change_log.md",
        "# change log\n\n- initialized\n",
    )
    _write_markdown_if_missing(
        artifact_root / "search_log.md",
        "# search log\n\n- no web evidence recorded\n",
    )
    _write_markdown_if_missing(
        artifact_root / "rollback_log.md",
        "# rollback log\n\n- no rollback recorded\n",
    )
    _write_text(
        artifact_root / "persona_matrix.md",
        _render_persona_matrix(persona_matrix),
    )
    _write_text(
        artifact_root / "source_packet_notes.md",
        _render_source_packet_notes(source_packet_notes),
    )
    manifest_payload = _write_trial_manifest(
        run_root=artifact_root,
        selected_cases=selected_cases,
        records=records,
        existing_manifest=existing_manifest,
    )

    for case in selected_cases:
        case_dir = artifact_root / "cases" / case.case_id
        _write_markdown_if_missing(case_dir / "strict_review_notes.md", f"# {case.case_id} strict review notes\n\n- pending\n")
        _write_markdown_if_missing(case_dir / "pass_fail.md", f"# {case.case_id} pass/fail\n\n- pending\n")

    return {
        "artifact_root": str(artifact_root),
        "records": records,
        "case_ids": [case.case_id for case in selected_cases],
        "preserved_existing": bool(existing_manifest),
        "manifest": manifest_payload,
    }


def append_trial_change_log_entry(
    *,
    run_root: str | Path = DEFAULT_RUN_ROOT,
    article_type: str,
    changed_owner: str,
    files_changed: Sequence[str],
    reason: str,
    expected_benefit: str,
    result_after_check: str = "",
    keep_or_rollback: str = "pending",
    timestamp: str | None = None,
) -> str:
    entry_time = str(timestamp or datetime.now().isoformat())
    lines = [
        f"timestamp: {entry_time}",
        f"article_type: {article_type}",
        f"changed_owner: {changed_owner}",
        f"files_changed: {json.dumps(list(files_changed), ensure_ascii=False)}",
        f"reason: {reason}",
        f"expected_benefit: {expected_benefit}",
        f"result_after_next_2run_check: {result_after_check or 'pending'}",
        f"keep_or_rollback: {keep_or_rollback}",
    ]
    path = Path(run_root) / "change_log.md"
    _append_markdown_entry(path, f"{entry_time} {article_type}", lines)
    return str(path)


def append_trial_search_log_entry(
    *,
    run_root: str | Path = DEFAULT_RUN_ROOT,
    article_type: str,
    query: str,
    rationale: str,
    sources_used: Sequence[str] | None = None,
    timestamp: str | None = None,
) -> str:
    entry_time = str(timestamp or datetime.now().isoformat())
    lines = [
        f"timestamp: {entry_time}",
        f"article_type: {article_type}",
        f"query: {query}",
        f"rationale: {rationale}",
        f"sources_used: {json.dumps(list(sources_used or []), ensure_ascii=False)}",
    ]
    path = Path(run_root) / "search_log.md"
    _append_markdown_entry(path, f"{entry_time} {article_type}", lines)
    return str(path)


def append_trial_rollback_log_entry(
    *,
    run_root: str | Path = DEFAULT_RUN_ROOT,
    article_type: str,
    files_changed: Sequence[str],
    reason: str,
    evidence: str,
    timestamp: str | None = None,
) -> str:
    entry_time = str(timestamp or datetime.now().isoformat())
    lines = [
        f"timestamp: {entry_time}",
        f"article_type: {article_type}",
        f"files_changed: {json.dumps(list(files_changed), ensure_ascii=False)}",
        f"reason: {reason}",
        f"evidence: {evidence}",
    ]
    path = Path(run_root) / "rollback_log.md"
    _append_markdown_entry(path, f"{entry_time} {article_type}", lines)
    return str(path)


def _derive_persona_trial_from_result(
    case: UISweepCase,
    loop_result: Mapping[str, Any],
) -> Dict[str, Any]:
    pipeline_check = dict(loop_result.get("pipeline_check") or {})
    persona_trial = dict(pipeline_check.get("persona_trial") or {})
    if persona_trial:
        return persona_trial
    input_contract = dict(pipeline_check.get("input_contract") or {})
    if not input_contract:
        input_contract = build_persona_trial_input_contract(case)
    return build_persona_trial_telemetry(input_contract, result={"pipeline_check": pipeline_check})


def run_persona_trial_case_mirror(
    *,
    case_id: str,
    live: bool = False,
    run_root: str | Path = DEFAULT_RUN_ROOT,
    loop_index: int,
    cases: Sequence[UISweepCase] | None = None,
    persist_manifest: bool = True,
) -> Dict[str, Any]:
    selected_case = select_persona_trial_cases([case_id], cases=cases)[0]
    case_artifact_dir = Path(run_root) / "cases" / selected_case.case_id / f"loop_{loop_index:02d}"
    mirror_case = replace(selected_case, case_id=f"{selected_case.case_id}-loop{loop_index}")
    payload = run_ui_sweep_cases([mirror_case], live=live, artifact_dir=case_artifact_dir)
    loop_result = dict(list(payload.get("results") or [{}])[0] or {})
    persona_trial = _derive_persona_trial_from_result(selected_case, loop_result)
    accepted = bool(loop_result.get("short_gate", {}).get("passed", False)) and bool(
        persona_trial.get("audience_valid_for_trial", False)
    )
    mirror_result = {
        "case_id": selected_case.case_id,
        "article_type": selected_case.article_type,
        "trial_loop_index": int(loop_index),
        "phase": _record_phase_name(loop_index),
        "accepted": accepted,
        "persona_trial": persona_trial,
        "artifact_dir": str(case_artifact_dir),
        "artifact_path": str(loop_result.get("artifact_path") or ""),
        "artifact_text_path": str(loop_result.get("artifact_text_path") or ""),
        "short_gate": dict(loop_result.get("short_gate") or {}),
        "quality_read": dict(loop_result.get("quality_read") or {}),
        "contract_summary": dict(loop_result.get("contract_summary") or {}),
        "runtime_summary": dict(loop_result.get("runtime_summary") or {}),
        "reason_code": str(loop_result.get("reason_code") or ""),
        "success": bool(loop_result.get("success", False)),
        "last_updated_at": datetime.now().isoformat(),
        "execution_mode": "live" if live else "offline",
    }
    if persist_manifest:
        manifest = load_trial_manifest(run_root)
        records = list(manifest.get("records") or [])
        record = _find_trial_record(records, case_id=selected_case.case_id, loop_index=loop_index)
        record.update(mirror_result)
        updated_records = _replace_trial_record(
            records,
            case_id=selected_case.case_id,
            loop_index=loop_index,
            replacement=record,
        )
        _write_trial_manifest(
            run_root=run_root,
            selected_cases=select_persona_trial_cases(cases=cases),
            records=updated_records,
            existing_manifest=manifest,
        )
    return {
        "payload": payload,
        "result": mirror_result,
    }


def snapshot_ui_acceptance_artifacts(
    *,
    case_id: str,
    loop_index: int,
    run_root: str | Path = DEFAULT_RUN_ROOT,
    ui_case_root: str | Path = DEFAULT_UI_ACCEPTANCE_CASE_ROOT,
    accepted: bool | None = None,
    dominant_failure: str = "",
    strict_review_summary: str = "",
    pass_fail_reason: str = "",
) -> Dict[str, Any]:
    source_dir = Path(ui_case_root) / case_id
    if not source_dir.exists():
        raise FileNotFoundError(f"ui acceptance artifact source not found: {source_dir}")
    loop_dir = Path(run_root) / "cases" / case_id / f"loop_{loop_index:02d}"
    snapshot_dir = loop_dir / "ui_acceptance"
    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)
    shutil.copytree(source_dir, snapshot_dir)

    ui_output_path = snapshot_dir / "ui_output.json"
    quality_report_path = snapshot_dir / "latest_generation_quality_report.json"
    snapshot_summary = {
        "case_id": case_id,
        "loop_index": int(loop_index),
        "phase": _record_phase_name(loop_index),
        "source_dir": str(source_dir),
        "snapshot_dir": str(snapshot_dir),
        "ui_output_present": ui_output_path.exists(),
        "quality_report_present": quality_report_path.exists(),
        "accepted": accepted,
        "dominant_failure": dominant_failure,
        "strict_review_summary": strict_review_summary,
        "pass_fail_reason": pass_fail_reason,
        "last_updated_at": datetime.now().isoformat(),
    }

    manifest = load_trial_manifest(run_root)
    records = list(manifest.get("records") or [])
    record = _find_trial_record(records, case_id=case_id, loop_index=loop_index)
    record["ui_acceptance"] = dict(snapshot_summary)
    if accepted is not None:
        record["accepted"] = bool(accepted)
    if dominant_failure:
        record["dominant_failure"] = dominant_failure
    if strict_review_summary:
        record["strict_review_summary"] = strict_review_summary
    updated_records = _replace_trial_record(
        records,
        case_id=case_id,
        loop_index=loop_index,
        replacement=record,
    )
    selected_cases = _cases_from_manifest_payload(manifest) or build_persona_trial_cases()
    _write_trial_manifest(
        run_root=run_root,
        selected_cases=selected_cases,
        records=updated_records,
        existing_manifest=manifest,
    )

    review_lines = [
        f"phase: {_record_phase_name(loop_index)}",
        f"source_artifact: {source_dir}",
        f"snapshot: {snapshot_dir}",
        f"ui_output_present: {str(ui_output_path.exists()).lower()}",
        f"quality_report_present: {str(quality_report_path.exists()).lower()}",
        f"accepted: {accepted if accepted is not None else 'pending'}",
        f"dominant_failure: {dominant_failure or 'pending'}",
        f"summary: {strict_review_summary or 'pending'}",
    ]
    pass_fail_lines = [
        f"phase: {_record_phase_name(loop_index)}",
        f"accepted: {accepted if accepted is not None else 'pending'}",
        f"reason: {pass_fail_reason or strict_review_summary or 'pending'}",
        f"snapshot: {snapshot_dir}",
    ]
    case_dir = Path(run_root) / "cases" / case_id
    _append_markdown_entry(
        case_dir / "strict_review_notes.md",
        f"{snapshot_summary['last_updated_at']} loop {loop_index}",
        review_lines,
    )
    _append_markdown_entry(
        case_dir / "pass_fail.md",
        f"{snapshot_summary['last_updated_at']} loop {loop_index}",
        pass_fail_lines,
    )
    return snapshot_summary


def run_persona_iterative_trial(
    *,
    live: bool = False,
    run_root: str | Path = DEFAULT_RUN_ROOT,
    max_loops: int = 5,
) -> Dict[str, Any]:
    cases = build_persona_trial_cases()
    init_payload = initialize_trial_artifact_dir(
        run_root=run_root,
        cases=cases,
        max_loops=max_loops,
    )
    results: List[Dict[str, Any]] = []
    for case in cases:
        for loop_index in range(1, min(max_loops, 5) + 1):
            run_payload = run_persona_trial_case_mirror(
                case_id=case.case_id,
                live=live,
                run_root=run_root,
                loop_index=loop_index,
                cases=cases,
                persist_manifest=True,
            )
            results.append(dict(run_payload["result"]))
    _write_json(Path(run_root) / "loop_results.json", {"results": results})
    return {
        **init_payload,
        "live": live,
        "loop_results": results,
    }
