# current_mainline_source_grounding_metadata_cleanup_2026-04-26

## Objective

Fix the narrow source grounding denominator issue diagnosed in `current_mainline_explanatory_article_regression_diagnosis_2026-04-26`.

When `source_grounding_items` contains file path, upload hash, or basename-like metadata, those items are not reader-facing source facts and should not count in the source grounding reflection denominator.

## Scope

Owner:

- `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`

Focused tests:

- `C:\tetie\notecode\note\tests\test_newalgorithm_phase06_logging_compat.py`

No changes to:

- thresholds
- prompts
- repair
- UI demotion
- `output_guard.py`
- `note_writer_app.py`
- `simple_note_pipeline/pipeline.py`
- source facts themselves
- unsupported claim guards

## Hypothesis

`source_grounding_items` may contain metadata-like entries such as:

- Windows paths
- Unix-like paths
- upload filenames
- hash-like basenames
- strings without natural-language source fact content

These entries should be excluded from denominator calculation. Substantive source facts must still be counted and protected.

## Expected Outcome

- Metadata-like items are excluded from source grounding denominator.
- True source facts are not excluded.
- `source_grounding:weak_reflection` is not triggered only because metadata was mixed into `source_grounding_items`.
- `bl-explanatory-misread-metric` no longer reports false weak reflection from path/hash metadata.

## Result

- Completed on `2026-04-26 JST`.
- Product code change stayed limited to `quality_observability_mixin.py`.
- Focused tests protect metadata exclusion and true-fact preservation.
- Explanatory rerun attempts 1 and 2 both returned `publishable_success` with source grounding reflection `1.0`.
