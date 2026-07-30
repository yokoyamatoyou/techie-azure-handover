# current_mainline_comparative_review_contract_activation_2026-04-26

## Objective

Fix the narrow `comparative_review` runtime contract / must-cover gap diagnosed in:

- `C:\tetie\notecode\plan\current_mainline_comparative_review_runtime_block_diagnosis_2026-04-26\`

The failing shape is:

- source facts are reflected in the body
- `source_grounding_reflection_ratio=1.0`
- comparative must-cover collapses to generic `総合`
- `must_cover_reflection_rate=0.3333`
- output guard emits `contract_alignment_must_cover_reflection_rate<0.50`

## Owner

Product owner is limited to:

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

Test owner:

- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

## Narrow Hypothesis

When explicit comparative source contract is absent, `comparative_review` should activate a bounded runtime contract from source facts plus comparison axes.

The fallback must derive reviewable slots for:

- price / plan
- approval flow
- support density
- fit conditions
- tradeoffs / cautions
- decision next step

The runtime must not depend only on generic collapsed labels like `総合`.

## Non-Goals

- Do not change thresholds.
- Do not change prompts.
- Do not change repair behavior.
- Do not broaden UI demotion.
- Do not edit `output_guard.py`.
- Do not edit `note_writer_app.py`.
- Do not edit `quality_observability_mixin.py`.
- Do not treat this as source shortage.
- Do not broaden the behavior outside `article_type=comparative_review`.

## Acceptance

- Comparative source contract activates for the diagnosed Tool A/B/C source shape.
- `source_grounding_items` receives source-backed comparative slots beyond generic `other`.
- `must_cover` does not collapse to only `総合` / generic labels.
- Existing non-comparative article types are unchanged.
- Focused and shared regressions pass.
- Focused UI rerun no longer reports `contract_alignment_must_cover_reflection_rate<0.50`; if style warnings remain, existing UX may classify as `review_required_draft`.

