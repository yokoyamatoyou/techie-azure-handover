# Next Implementation Prompt

You are working in `C:\tetie\notecode`.

Read first:

1. `C:\tetie\notecode\plan\current_mainline_comparative_review_runtime_block_diagnosis_2026-04-26\README.md`
2. `C:\tetie\notecode\plan\current_mainline_comparative_review_runtime_block_diagnosis_2026-04-26\TASK.md`
3. `C:\tetie\notecode\plan\current_mainline_comparative_review_runtime_block_diagnosis_2026-04-26\PROGRESS.md`
4. `C:\tetie\notecode\plan\current_mainline_comparative_review_runtime_block_diagnosis_2026-04-26\ROLLBACK.md`
5. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`

## Goal

Implement one narrow fix for `comparative_review` runtime contract/source grounding.

## Owner

Only edit:

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

Tests may be edited only if needed to cover this owner-local behavior.

## Narrow Hypothesis

`comparative_contract_gap`

When explicit comparative source contract is absent, runtime comparative contract/source grounding should derive reviewable comparison slots from source facts plus UI axes. It should not leave contract alignment dependent on generic collapsed labels like `総合` when the body visibly covers price / approval flow / support density / fit / tradeoff / next-step content.

## Do Not Change

- Do not change thresholds.
- Do not change prompts.
- Do not change repair policy.
- Do not broaden UI demotion.
- Do not edit `output_guard.py`.
- Do not treat the result as source shortage.
- Do not edit `note_writer_app.py` for this hypothesis.
- Do not edit `newalgorithm_pipeline/quality_observability_mixin.py` unless this package is explicitly parked and a new owner is opened.

## Acceptance Criteria

- Same comparative focused case reaches generation.
- Source grounding remains `1.0`.
- `contract_alignment_must_cover_reflection_rate<0.50` no longer fires when the body visibly covers source-backed price / approval_flow / support_density / fit / tradeoff / next-step content.
- If still fail-closed only for style/fingerprint warnings, existing UI rules may classify it as `review_required_draft` without adding a demote rule.
- Product success path remains:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## Suggested Checks

- Focused unit tests around comparative contract/source grounding in `note\tests\test_simple_note_pipeline.py`.
- Current-mainline contract/UI result adapter tests covering `must_cover_reflection_rate` and review-draft classification.
- Focused UI rerun:
  - `C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\run_log_source_ui_regression.py --case-ids bl-comparative-selection-criteria --attempts 1,2`

Stop after 3 same-phase repair attempts and report if the owner needs to change.

