# current_mainline_source_grounding_metric_correction_2026-04-25

## Objective

Use the live observation result from `current_mainline_source_grounding_live_observation_2026-04-25` to correct the narrow Case 4 `source_grounding:weak_reflection` false positive caused by duplicated title-like source anchor groups.

This package does not relax guard thresholds. The goal is to keep source-grounded output fail-closed when source use is truly weak, while preventing duplicated title-like source items from inflating the item denominator beyond the source-use semantics.

## Scope

- Owner file: `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
- Focused tests: `C:\tetie\notecode\note\tests\test_newalgorithm_phase06_logging_compat.py`
- Documentation: this package and `C:\tetie\WORKLOG.md`

If another product owner file becomes necessary, stop and report instead of broadening the implementation.

## Non-Goals

- No prompt changes.
- No repair count or repair trigger changes.
- No source grounding threshold or fingerprint threshold changes.
- No `quality_guard.py` changes.
- No `output_guard.py` or UI demote policy changes.
- No target length or length mode changes.
- No unconditional pass for duplicated or title-like source items.
- No success treatment for true omission.

## Hard Decision

Decision: `metric correction package needed`.

Reason: Case 4 live evidence produced two valid weak attempts with group counts `5 / 3 / 1 / 1 / 3 / 1`. The only missing group was duplicated and title-like, while the body was acceptable, leak-free, and source-aware. The existing item-based denominator can fail this shape even when deduped source-use semantics are satisfied.

Chosen correction: add a group-level auxiliary pass for this narrow denominator-inflation shape. Existing item-based metrics remain as observability.
