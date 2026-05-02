# sentence final monotony quality guard triage note 2026-04-17

## Read Files

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_quality_guard_triage_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_validation_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_repair_lane_followup_note_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_validation_20260417-155957\summary.json`

## Scope

- first owner only:
  - `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- question:
  - should explanatory short monotony-only cases with `ending:bucket_monotony` be promoted to `repair_required=true` before `pipeline.py` repair lane entry
- out of scope:
  - `pipeline.py`
  - `prompt_builder.py`
  - route / planning / source-of-truth updates

## Current Trigger Read Before Diff

- base gate remained `repair_trigger_score >= 0.58`
- existing dedicated monotony promotion existed only for:
  - `semantic_article_key == company_introduction`
  - `ending_bucket_max_run >= 5`
  - `ending_bucket_monotony_score >= 0.68`
- explanatory short monotony-only case had no dedicated promotion line
- result:
  - `ending:bucket_monotony` soft warning could appear
  - later repair lane could be patch-path-capable
  - but `repair_required` still stayed false upstream

## Why Case A Stayed False

- live-like explanatory case was stopping in `quality_guard.py`, not in `pipeline.py`
- saved rerun reference:
  - `ending_bucket_max_run = 26`
  - `ending_bucket_monotony_score = 0.5417`
  - `repair_trigger_score = 0.4556`
  - `repair_required = false`
- latest rerun reference:
  - `ending_bucket_max_run = 11`
  - `ending_bucket_monotony_score = 0.2558`
  - `repair_trigger_score = 0.4258`
  - `repair_required = false`
- exact reason:
  - current promotions covered company intro structure, comparative thin sections, rhythm flatness cluster, sentence integrity, single-sentence paragraph excess, proposition density, lead cliché, uniform paragraph rhythm, and company-intro-only ending monotony
  - explanatory short monotony-only case matched none of them

## Decision

- selected candidate:
  - candidate A
  - narrow explanatory short monotony-only promotion in `quality_guard.py`
- rejected candidate:
  - candidate B
  - `patch_path_candidate` is not available at this owner boundary, so composing the trigger around it would require re-coupling to `pipeline.py`

## Changed Conditions

- new promotion applies only when all of the following hold:
  - `article_type == explanatory_article`
  - `length_mode == short`
  - `ending_bucket_max_run >= 12`
  - `ending_bucket_monotony_score >= 0.5`
  - `repeated_opening_count == 0`
  - `duplicate_paragraph_count == 0`
  - `sentence_integrity_warning_count == 0`
  - no existing single-sentence paragraph promotion condition
  - `proposition_informative_ratio >= 0.32`
  - `proposition_low_info_ratio <= 0.5`
  - `lead_cliche_detected == false`
  - `uniform_paragraph_rhythm == false`
- promotion floor:
  - `repair_trigger_score = max(current_score, 0.58)`

## Guard Preservation

- company intro monotony promotion is unchanged
- global threshold is unchanged
- no broadening to all article types
- no reuse of company intro branch for explanatory cases
- mixed-issue cases still use their existing promotions because the new line explicitly excludes sentence-integrity, proposition-density, lead-cliche, uniform-paragraph, repeated-opening, duplicate-paragraph, and single-sentence-paragraph paths

## Tests

- focused owner-local:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -k "short_rhythm_flatness_cluster or company_intro_ending_bucket_monotony or sentence_integrity_warning or single_sentence_paragraph_excess or explanatory" -q`
  - `6 passed, 13 deselected`
- owner-local full:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
  - `19 passed`
- neighbor check:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`
  - `117 passed`
- shared checks:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
  - `83 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "not st08b4_industry_analysis_title_and_lead_do_not_echo_prompt" -q`
  - `233 passed, 1 deselected`

## Touched Files

- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_quality_guard_triage_note_2026-04-17.md`

## New Focused Tests

- explanatory short strong monotony-only case promotes to `repair_required=true`
- weaker explanatory ending bucket monotony case stays below gate

## Non-Updated Files

- AGENTS: not updated
- WORKLOG: not updated
- current planning package docs: not updated

## Next Step

- next prompt:
  - live re-validation
- reason:
  - upstream trigger owner is now aligned with the previously confirmed `pipeline.py` acceptance lane
