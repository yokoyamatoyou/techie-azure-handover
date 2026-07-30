# current_mainline_comparative_review_runtime_block_diagnosis_2026-04-26

## Objective

Diagnose the post-harness-fix `comparative_review` runtime block for `bl-comparative-selection-criteria`.

The previous package fixed the UI harness failure. The focused rerun reached generation for attempts 1 and 2, but both attempts fail-closed as:

- outcome: `input_required_block`
- runtime reason: `SYS_QUALITY_WARNINGS_UNRESOLVED`
- body exists
- source docs: 3

This package is docs-only. It does not change product code, prompts, thresholds, repair behavior, UI demotion behavior, `output_guard.py`, or source adequacy policy.

## Artifact References

- Previous package:
  - `C:\tetie\notecode\plan\current_mainline_comparative_review_validation_harness_fix_2026-04-26\PROGRESS.md`
- Focused rerun root:
  - `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\`
- Comparative attempt artifacts:
  - `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\ui_live\bl-comparative-selection-criteria\attempt_1\`
  - `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\ui_live\bl-comparative-selection-criteria\attempt_2\`
- Historical OK baseline:
  - `C:\tetie\notecode\logs\multi_type_current_mainline_validation_20260425-013935\bl-comparative-selection-criteria.json`

## Diagnosis Summary

Both focused attempts produced grounded comparative bodies. The visible body substantially covers:

- price
- approval flow
- support density
- fit conditions
- tradeoffs / cautions
- decision next step

No UI/body internal-term leakage was observed. No explicit outside-source claim was observed. `needs_input_items` is empty.

The block is not explained by source shortage. The 3 thin source docs are reflected, and `source_grounding_reflection_ratio=1.0` for both attempts. The immediate runtime block is the contract/metric shape:

- `must_cover_reflection_rate=0.3333`
- `contract_alignment_must_cover_reflection_rate<0.50`
- `SYS_QUALITY_WARNINGS_UNRESOLVED`

## Attempt Diagnosis Table

| Attempt | Outcome | Body | Source grounding | Must cover | Repair | Classification judgment |
|---:|---|---:|---:|---:|---|---|
| 1 | `input_required_block` / `SYS_QUALITY_WARNINGS_UNRESOLVED` | 1429 chars | 1.0 | 0.3333 | not required / not applied / not rejected | review-draft candidate, but blocked by contract/must_cover reason |
| 2 | `input_required_block` / `SYS_QUALITY_WARNINGS_UNRESOLVED` | 1763 chars | 1.0 | 0.3333 | not required / not applied / not rejected | review-draft candidate, but blocked by contract/must_cover reason |

## UI Classification Judgment

`input_required_block` is misleading for this artifact shape.

Reasons:

- The generated body exists.
- Source facts are reflected.
- `needs_input_items` is empty.
- No route mismatch was observed.
- No internal leakage or explicit outside-source claim was observed.

The artifact shape is closer to `review_required_draft`, but current UI classification intentionally keeps it as `input_required_block` because review-draft classification blocks any guard reason containing `contract` / `must_cover`.

Do not fix this by broadening UI demotion. The next owner should address why comparative runtime contract/must-cover alignment is generic or under-detected.

## Historical Delta

Old comparative source contract v1 live validation was `OK`:

- prompt/axes included price, approval flow, and support density.
- `must_cover=価格, 承認フロー, 差分`.
- `must_cover_reflection_rate=1.0`.
- output guard was not blocked.

Focused rerun after harness fix differs:

- `prompt_raw` is empty.
- UI axis collapsed to `overall` / `総合`.
- `must_cover=総合, 差分, 用途別の結論`.
- lexical `must_cover_reflection_rate` drops to `0.3333`.
- comparative source contract v1 exists but `scope_match=false` and `source_contract_available=false`.
- `tradeoffs_or_cautions` and `decision_next_step` are not source-backed slots in the runtime contract, even though the visible body contains reviewable caution and next-step content.

## Final Classification

Primary classification:

- `comparative_contract_gap`

Secondary observations:

- `review_draft_classification_too_strict` is visible, but it is not the next owner because the strictness is triggered by a legitimate contract/must-cover warning family.
- `source_reflection_metric_false_negative` may be involved, but source grounding itself is not false negative in this run because source grounding is 1.0.
- `repair_not_actuating` is not primary because repair was not required/applied/rejected for both attempts.
- `source_caveat` remains historical context only; do not resolve by treating this as source shortage.

## Next Owner

- Owner: `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Narrow hypothesis: `comparative_contract_gap`

The next implementation should make comparative_review runtime contract/source grounding derive reviewable comparison slots from source facts plus UI axes when explicit comparative source contract is absent.

