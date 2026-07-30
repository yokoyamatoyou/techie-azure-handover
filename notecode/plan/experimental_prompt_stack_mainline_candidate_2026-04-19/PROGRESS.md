# experimental_prompt_stack_mainline_candidate_2026-04-19 PROGRESS

## Current Goal

- `experimental_prompt_stack` を current mainline 候補として進める
- immediate target は `historical compare / success visibility / promotion gate hardening`

## Current Status

- status:
  - active
  - implementation lane
- current baseline:
  - `body_generation_experiment` propagation enabled
  - prompt stack upgraded to `SOURCE_PACKET -> ARTICLE_CONTRACT -> writer -> suffix editor -> audit`
  - suffix edit and audit telemetry available
  - success visibility summary projected to current mainline result / UI matrix artifact
  - historical compare summary projected to UI matrix payload / artifact
  - promotion gate summary projected without default flip
- current default:
  - still not promoted to mainline default
- current retry budget:
  - next slice starts at `0/3`

## Completed Slice

- propagation / stack refactor / targeted test alignment completed
- success visibility completed
- historical compare completed
- promotion gate surface completed
- changed files:
  - `C:\tetie\notecode\note\generation_request_builder.py`
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\current_mainline_ui_matrix.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\tests\test_generation_request_builder.py`
  - `C:\tetie\notecode\note\tests\test_current_mainline_runner.py`
  - `C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py`
  - `C:\tetie\notecode\note\tests\test_current_mainline_genre_sweep.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- latest narrow additions:
  - `C:\tetie\notecode\note\current_mainline_ui_matrix.py`
  - `C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py`

## Verified Tests

- passed:
  - `python -m pytest C:\tetie\notecode\note\tests\test_generation_request_builder.py -q`
  - `python -m pytest C:\tetie\notecode\note\tests\test_current_mainline_runner.py C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py C:\tetie\notecode\note\tests\test_current_mainline_genre_sweep.py C:\tetie\notecode\note\tests\test_simple_note_pipeline.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_generation_request_builder.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_ui_matrix.py note\tests\test_current_mainline_genre_sweep.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py::test_simple_note_pipeline_experimental_prompt_stack_runs_support_planner_writer_editor_sequence note\tests\test_current_mainline_ui_matrix.py::test_build_current_mainline_payload_keeps_body_generation_experiment note\tests\test_current_mainline_ui_matrix.py::test_run_ui_sweep_cases_projects_body_generation_summary_to_saved_artifact note\tests\test_current_mainline_ui_matrix.py::test_run_ui_sweep_cases_builds_historical_compare_and_promotion_gate_summary -q`

## 2026-04-19 Promotion Evidence Verification

- touched file:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- narrow fix:
  - suffix editor が返す multiline JSON-like payload の parse を lenient にし、`experimental_prompt_stack` の suffix edit が silent drop されないようにした
  - owner-local failure `test_simple_note_pipeline_experimental_prompt_stack_runs_support_planner_writer_editor_sequence` はこの fix で解消した
- historical compare read:
  - `prompt_only_probe_2026-04-03_same_source.json` は `INP_MISSING_REQUIRED` の input-contract block
  - `prompt_only_probe_2026-04-03_same_source_force_accept.json` も override 後に同じ block が継続する
  - `direct_gpt54_prompt_only_same_source_2026-04-03.json` は content-generation reference として読める
- visible baseline read:
  - `latest_generation_output.txt` は `2026-04-15 00:25:07` / `gen-4692e32c`
  - current visible artifact は `blocked_output_redacted: True`
  - runtime reason は `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - `latest_generation_quality_report.json` の output guard は `soft_warning_count = 6`
  - soft warnings は `fingerprint:bigram_mono_low / vocab_repetition / nominalization_rate_high / sentence_ending_entropy_low / syntactic_complexity_low / comma_overuse`
- shared checks:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
  - result: fail
  - remaining failure:
    - `note\tests\test_newalgorithm_phase03_pipeline.py::test_st08b4_industry_analysis_title_and_lead_do_not_echo_prompt`
  - read:
    - this is owner outside current slice and was already a known unrelated shared-check failure
- promotion decision:
  - `default_flip_allowed` remains `false`
  - Phase 2 decision is `gate fail`
  - default route stays unchanged
  - reason:
    - `shared_checks_pass` is still unmet
    - latest visible baseline is still blocked by unresolved quality warnings
    - latest visible artifact is not sufficient promotion evidence for the candidate default route
- next exact slice:
  - keep `experimental_prompt_stack` opt-in only
  - separate owner must clear `test_st08b4_industry_analysis_title_and_lead_do_not_echo_prompt`
  - after shared checks pass, regenerate a fresh candidate-visible artifact and rerun promotion evidence verification before any default flip

## 2026-04-20 Fresh Artifact Promotion Evidence Rerun

- touched file:
  - `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\PROGRESS.md`
- fresh evidence generation:
  - live rerun 1 artifact:
    - `C:\tetie\notecode\logs\experimental_prompt_stack_promotion_evidence_20260420-071610\fresh_candidate_summary.json`
    - case: `ui-short-branding-company-grounded-experimental-promotion-evidence`
    - runtime: `success = true` / `runtime_reason_code = OK` / `output_guard.blocked = false` / `soft_warning_count = 2`
    - route metadata: `body_generation_experiment = experimental_prompt_stack` / `pipeline_source = newalgorithm_mainline` / `semantic_article_key = company_introduction`
    - experimental route readout: `run_state = fallback` / `used_fallback_generation = true` / `fallback_reason = support_parse_failed` / `compare_ready = false` / `audit_result = {}` / `writer_of_record = blank`
  - live rerun 2 artifact:
    - `C:\tetie\notecode\logs\experimental_prompt_stack_promotion_evidence_20260420-071836\fresh_candidate_summary.json`
    - case: `explanatory-prompt-stack-evidence`
    - runtime: `success = true` / `runtime_reason_code = OK` / `output_guard.blocked = false` / `soft_warning_count = 3`
    - route metadata: `body_generation_experiment = experimental_prompt_stack` / `pipeline_source = newalgorithm_mainline` / `semantic_article_key = explanatory_article`
    - experimental route readout: `run_state = fallback` / `used_fallback_generation = true` / `fallback_reason = support_parse_failed` / `compare_ready = false` / `audit_result = {}` / `writer_of_record = blank`
- stale baseline separation:
  - stale docs baseline was `latest_generation_output.txt` = `2026-04-15 00:25:07` / `gen-4692e32c`
  - fresh latest baseline is `latest_generation_output.txt` = `2026-04-20 07:18:36` / `cand-20260420-071836`
  - fresh `latest_generation_quality_report.json` now reads `quality_gate = passed` / `output_guard.blocked = false` / `soft_warning_count = 3` / `reason_code = OK`
- historical compare read:
  - `latest_generation_quality_report.json` is now a fresh 2026-04-20 baseline rather than the stale 2026-04-15 baseline used in prior docs
  - `prompt_only_probe_2026-04-03_same_source.json` and `prompt_only_probe_2026-04-03_same_source_force_accept.json` remain `INP_MISSING_REQUIRED` input-contract blocks
  - `direct_gpt54_prompt_only_same_source_2026-04-03.json` remains the prompt-only content-generation reference
  - `historical_compare_readable = true` and `historical_compare_distinguishes_failures = true` in the fresh rerun artifacts
- promotion decision:
  - `default_flip_allowed` remains `false`
  - default route stays unchanged
  - measured gate result is `fail`
  - exact measured blocker:
    - live `experimental_prompt_stack` reruns propagated the opt-in flag, but both candidate reruns fell back before `support -> planner -> writer -> editor -> audit` completed
    - measured failure is `success_visibility_ready = false`
    - exact reason is `support_parse_failed`, so `compare_ready = false`, `audit_verdict = ""`, and `writer_of_record` cannot be established from candidate telemetry
  - external shared blocker remains separate:
    - `note\tests\test_newalgorithm_phase03_pipeline.py::test_st08b4_industry_analysis_title_and_lead_do_not_echo_prompt`
    - record it as `external shared blocker`, not `candidate route regression`
    - even if measured gate were recovered, `shared_checks_pass` would still remain unmet until this external blocker is cleared
- self-test:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py::test_simple_note_pipeline_experimental_prompt_stack_runs_support_planner_writer_editor_sequence note\tests\test_current_mainline_ui_matrix.py::test_build_current_mainline_payload_keeps_body_generation_experiment note\tests\test_current_mainline_ui_matrix.py::test_run_ui_sweep_cases_projects_body_generation_summary_to_saved_artifact note\tests\test_current_mainline_ui_matrix.py::test_run_ui_sweep_cases_builds_historical_compare_and_promotion_gate_summary -q`
  - result: pass
- next exact slice:
  - keep `experimental_prompt_stack` opt-in only
  - do not enter `st08b4` repair
  - narrow next owner-local slice is `support` stage live parse stability for `experimental_prompt_stack`
  - after `support_parse_failed` is removed and `compare_ready = true` becomes visible again, rerun fresh promotion evidence before any default flip

## 2026-04-20 Support Parse Stability Recovery

- touched files:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
  - `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\PROGRESS.md`
- narrow fix:
  - support stage に owner-local lenient parser を追加し、strict JSON 以外でも `section_briefs` alias を復元できるようにした
  - live support output の揺れとして確認できた
    - `sections`
    - `section_goal` / `section_purpose`
    - `fact_anchor = ["F1"]`
    - `section_focus` 欠落
    を `heading / section_focus / fact_anchor` へ narrow normalize する
  - `support_parse_failed` fallback 時に `support_parse_summary` を stage summary へ残し、`parse_mode / payload_source / section_briefs_source / detected_keys / raw_preview` を owner-local telemetry として可視化した
  - `requested_experiment_unsupported` / `route_branch` は今回の primary blocker ではなく、support parse stability slice とは分離したままにした
- owner-local tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py::test_simple_note_pipeline_experimental_prompt_stack_runs_support_planner_writer_editor_sequence note\tests\test_simple_note_pipeline.py::test_simple_note_pipeline_experimental_prompt_stack_falls_back_to_regular_generation_when_support_parse_fails note\tests\test_simple_note_pipeline.py::test_parse_support_script_recovers_fenced_json_with_section_aliases note\tests\test_simple_note_pipeline.py::test_parse_support_script_recovers_key_value_section_briefs_when_json_is_broken note\tests\test_simple_note_pipeline.py::test_parse_support_script_uses_heading_when_section_focus_is_omitted -q`
  - result: pass
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
  - result: pass
- fresh evidence generation:
  - artifact:
    - `C:\tetie\notecode\logs\experimental_prompt_stack_promotion_evidence_20260420-091225\fresh_candidate_summary.json`
  - case `ui-short-branding-company-grounded-experimental-promotion-evidence`:
    - `run_state = completed`
    - `completed_stages = ["support", "planner", "writer", "editor", "audit"]`
    - `audit_verdict = WARN`
    - `compare_ready = true`
    - `fallback_reason = ""`
    - `writer_of_record = simple_note_pipeline`
    - `support_parse_summary.section_briefs_source = section_briefs`
  - case `explanatory-prompt-stack-evidence`:
    - `run_state = completed`
    - `completed_stages = ["support", "planner", "writer", "editor", "audit"]`
    - `audit_verdict = WARN`
    - `compare_ready = true`
    - `fallback_reason = ""`
    - `writer_of_record = simple_note_pipeline`
    - `support_parse_summary.section_briefs_source = section_briefs`
- latest baseline read:
  - `latest_generation_output.txt` now reflects the explanatory rerun and includes `## 先にそろえるべき設定の前提` / `## 判断を迷わせないための軸` / `## 実務でどう使うか`
  - `latest_generation_quality_report.json` remains `runtime_reason_code = OK` / `output_guard.blocked = false` / `soft_warning_count = 3`
- promotion decision:
  - measured `support_parse_failed` blocker is cleared
  - `success_visibility_ready = true`
  - `historical_compare.compare_ready = true`
  - `default_flip_allowed` remains `false`
  - exact remaining blocker is still external shared blocker:
    - `note\tests\test_newalgorithm_phase03_pipeline.py::test_st08b4_industry_analysis_title_and_lead_do_not_echo_prompt`
  - current candidate route is now promotion-evaluable, but default flip stays out of scope until shared checks are cleared by the separate owner
- next exact slice:
  - keep `experimental_prompt_stack` opt-in only
  - do not enter `default flip`
  - do not enter `st08b4` repair
  - next owner outside this slice must resolve the external shared blocker, then rerun promotion gate if default-route judgement is still needed

## Next Slice Order

1. `experimental_prompt_stack` は opt-in のまま維持する
2. external shared blocker を別 owner のまま解消する
3. shared checks pass 後に promotion gate を再判定する
4. default route は gate pass まで維持する

## Blockers

- repo is not git root
- default route promotion はまだ block 中
- mainline 昇格には targeted tests / shared checks の追加確認が必要
- measured candidate blocker:
  - `support_parse_failed` is cleared in fresh evidence
  - candidate route telemetry is now established (`run_state = completed` / `compare_ready = true` / `writer_of_record = simple_note_pipeline`)
  - remaining measured blocker is not candidate-local parse failure but external shared checks / default-flip gate
- external shared blocker:
  - `note\tests\test_newalgorithm_phase03_pipeline.py::test_st08b4_industry_analysis_title_and_lead_do_not_echo_prompt`

## Current Readout

- historical compare:
  - `prompt_only_probe_2026-04-03_same_source.json` は `INP_MISSING_REQUIRED` の input-contract block
  - `prompt_only_probe_2026-04-03_same_source_force_accept.json` も同じ block が継続
  - `direct_gpt54_prompt_only_same_source_2026-04-03.json` は content-generation reference
  - `latest_generation_quality_report.json` は `2026-04-20 07:18:36` / `cand-20260420-071836` の fresh baseline quality reference
- promotion gate:
  - fresh latest baseline は `runtime_reason_code = OK` / `output_guard.blocked = false` / `soft_warning_count = 3`
  - measured surface は `experiment propagation / historical compare readable / compare_ready = true` を確認できる
  - `experimental_prompt_stack` candidate route は 2 case とも `run_state = completed` / `audit_verdict = WARN` / `compare_reason = compare_with_audit_warning`
  - `default_flip_allowed` はまだ `false`
  - reason:
    - external `shared_checks_pass` が未解消
    - current slice では `default flip` に入らない

## Handoff Rule

- context が増えたら clean slice boundary で止める
- 止めるときは this file に
  - completed slice
  - passed tests
  - next exact slice
  - unresolved blocker
  を追記して次ウインドウへ渡す
