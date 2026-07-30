# current_mainline_explanatory_article_regression_diagnosis_2026-04-26

## Objective

Diagnose why `bl-explanatory-misread-metric` moved from historical OK to latest blocked/redacted runtime in `current_mainline_log_source_ui_regression_2026-04-26`.

This package is docs-only. It does not change product code, thresholds, prompts, repair, UI demotion, `output_guard.py`, `note_writer_app.py`, or `simple_note_pipeline/pipeline.py`.

## Required References

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\ALGORITHM.md`
  - `## 4. Single-Pass Generation`
  - `## 5. Repair Algorithm`
  - `## 12. Persona / Source Packet / Editing Persona Contract`
- `C:\tetie\notecode\plan\current_mainline_log_source_ui_regression_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_comparative_review_contract_activation_2026-04-26\PROGRESS.md`
- `C:\tetie\WORKLOG.md`

## Artifact Inputs

- Latest regression artifact root:
  - `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\`
- Historical OK artifacts:
  - `C:\tetie\notecode\logs\multi_type_current_mainline_validation_20260425-013935\bl-explanatory-misread-metric.json`
  - `C:\tetie\notecode\logs\multi_type_current_mainline_validation_20260425-013935\bl-explanatory-misread-metric.txt`
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\bl-explanatory-misread-metric.json`
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\bl-explanatory-misread-metric.txt`

## Finding

The latest runtime did not fail because `explanatory_article` routed incorrectly or because the body omitted the source facts. It failed because the runtime source grounding packet included uploaded-file metadata as source facts.

Historical OK effectively evaluated two substantive source facts and recorded source reflection `1.0`. The latest attempts evaluated five `source_grounding_items`: the same two real facts plus three path/hash metadata items. The body reflected the two real facts, but did not and should not reflect file paths or upload hashes, so the metric became `2/5 = 0.4` and triggered `source_grounding:weak_reflection`.

## Classification

Primary classification:

- `source_reflection_metric_false_negative`
- `source_reconstruction_mismatch`

Secondary classification:

- validation harness outcome naming is stricter than the visible UI state. The final UI text says `確認が必要なドラフトです`, while the summary reports `input_required_block` because `blocked_output_redacted=true`.

Not supported:

- `UI_route_mismatch`
- `true_missing_source_facts`
- `source_caveat_only`

## Final Judgment

This is not explained by source shortage alone. The source is thin, but historical OK used the same substantive facts successfully.

The direct runtime block trigger is `SYS_QUALITY_WARNINGS_UNRESOLVED` with `source_grounding:weak_reflection`, caused by denominator pollution from path/hash-like metadata in `source_grounding_items`.

Visible UI behavior is already closer to `review_required_draft`; the stricter `input_required_block` label is primarily a harness/runtime-summary classification issue for this artifact.

## Future Fix Boundary

Default decision for this package: stop docs-only.

If a later implementation is requested, use one owner and one hypothesis:

- Owner: `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
- Hypothesis: source grounding reflection should ignore path/hash-like metadata source items when computing the denominator, without changing thresholds or accepting unsupported claims.

Do not choose UI demotion as the first fix. `note_writer_app.py` already renders `確認が必要なドラフトです` in the latest final UI text.
