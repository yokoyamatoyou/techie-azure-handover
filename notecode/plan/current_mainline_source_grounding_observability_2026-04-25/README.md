# current_mainline_source_grounding_observability_2026-04-25 README

## Objective

- Improve only source grounding explainability after `current_mainline_source_grounding_reflection_diagnosis_2026-04-25`.
- Keep product behavior unchanged: generation, prompt, repair, thresholds, output guard policy, UI demotion, target length, and success/fail state must not change.
- Let saved artifacts distinguish true weak reflection from exact-anchor mismatch / phrasing variance.

## Source Of Truth

- Global current package:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- Predecessor diagnosis:
  - `C:\tetie\notecode\plan\current_mainline_source_grounding_reflection_diagnosis_2026-04-25\`
- Current owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
- Focused tests:
  - `C:\tetie\notecode\note\tests\test_newalgorithm_phase06_logging_compat.py`

## Non-Goals

- Do not demote `source_grounding:weak_reflection`.
- Do not relax source grounding / fingerprint / quality thresholds.
- Do not change repair count, repair triggers, prompts, target chars, length mode, source packet thickness, or UI display.
- Do not change `note_writer_app.py`, `output_guard.py`, `prompt_builder.py`, or pipeline behavior.
- Do not expose raw diagnostics to reader-facing body or UI.

## Telemetry Schema

The following keys are internal artifact telemetry only:

- `source_grounding_deduped_anchor_group_count`
- `source_grounding_matched_anchor_group_count`
- `source_grounding_partial_anchor_group_count`
- `source_grounding_missing_anchor_group_count`
- `source_grounding_duplicate_anchor_group_count`
- `source_grounding_title_like_anchor_group_count`
- `source_grounding_anchor_group_diagnostics`

Each diagnostic group is bounded and may contain:

- `group_index`
- `item_indices`
- `duplicate_count`
- `title_like`
- `anchor_terms`
- `matched_terms`
- `missing_terms`
- `match_status`
- `source_excerpt`

## Decision

- Add explainability only. Existing `source_grounding_reflected_count` and `source_grounding_reflection_ratio` remain item-based and unchanged.
- Grouping is based on normalized anchor-term signature.
- Title-like groups are short facts with no sentence punctuation and at most two anchors.
- Diagnostics are bounded to avoid artifact bloat.
