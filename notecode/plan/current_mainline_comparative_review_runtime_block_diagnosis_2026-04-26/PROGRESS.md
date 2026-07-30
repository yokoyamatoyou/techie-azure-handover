# current_mainline_comparative_review_runtime_block_diagnosis_2026-04-26 PROGRESS

## Current Status

- Package status: completed
- Current phase: closeout
- Date: 2026-04-26 JST
- Owner: docs-only diagnosis
- Product code change: no
- Prompt / threshold / repair / UI demote / output guard change: no

## Baseline

- Previous package:
  - `C:\tetie\notecode\plan\current_mainline_comparative_review_validation_harness_fix_2026-04-26\`
- Artifact root:
  - `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\`
- Diagnosis target:
  - `bl-comparative-selection-criteria`
  - attempts 1 and 2

## Attempt Table

| Attempt | Outcome | Runtime reason | Body chars | Source docs | Source grounding | Must cover | Repair | Output guard driver |
|---:|---|---|---:|---:|---:|---:|---|---|
| 1 | `input_required_block` | `SYS_QUALITY_WARNINGS_UNRESOLVED` | 1429 | 3 | 1.0 | 0.3333 | not required / not applied / not rejected | `contract_alignment_must_cover_reflection_rate<0.50` plus fingerprint/style warnings |
| 2 | `input_required_block` | `SYS_QUALITY_WARNINGS_UNRESOLVED` | 1763 | 3 | 1.0 | 0.3333 | not required / not applied / not rejected | `contract_alignment_must_cover_reflection_rate<0.50` plus fingerprint/style warnings |

## Visible Content Finding

Both bodies substantially contain the comparative review content expected from the source:

- price:
  - Tool A: monthly 5万円
  - Tool B: monthly 9万円
  - Tool C: monthly 12万円
- approval flow:
  - Tool A: single team
  - Tool B: multiple departments
  - Tool C: stricter permission/control side
- support density:
  - Tool A: email-centered support and templates
  - Tool B: CS attends onboarding
  - Tool C: dedicated CS
- fit conditions:
  - A for lighter/single-team start
  - B for cross-department review standardization
  - C for larger operation / audit / strict permissions
- tradeoffs / cautions:
  - A may be thin for cross-department or heavier control
  - B/C can be excessive depending on startup simplicity
  - price alone should not decide
- decision next step:
  - check approval breadth, support need, and control/audit requirement before choosing

No internal term leakage was observed in UI/body. No explicit outside-source claim was observed.

## UI Classification

Current UI result is `input_required_block`, but the artifact shape is a `review_required_draft` candidate.

The reason it remains `input_required_block` is current classification logic: review-draft demotion rejects guard reasons containing `contract` / `must_cover`. Since both attempts include `contract_alignment_must_cover_reflection_rate<0.50`, the UX remains fail-closed as input-required even though `needs_input_items=[]`.

This package does not recommend broadening UI demotion. The next fix should remove the inappropriate comparative contract/must-cover warning at its source.

## Historical Delta

Historical OK baseline:

- `runtime_reason_code=OK`
- `prompt_raw`: explicitly included price, approval flow, support density
- `comparison_axes`: price / approval_flow / support_density in the UI journey
- `must_cover=価格, 承認フロー, 差分`
- `must_cover_reflection_rate=1.0`
- output guard not blocked

Focused rerun after harness fix:

- `prompt_raw` empty
- UI journey comparison axis collapsed to `overall`
- runtime `comparison_axes=総合`
- `must_cover=総合, 差分, 用途別の結論`
- `must_cover_reflection_rate=0.3333`
- comparative source contract v1 exists but `scope_match=false`
- `source_contract_available=false`
- `tradeoffs_or_cautions` and `decision_next_step` are empty in source-backed slots

## Final Judgment

The block is explained by `comparative_contract_gap`.

The source facts are reflected, and the visible article has reviewable comparative substance. The hard fail is caused by contract/must-cover alignment being too generic or not derived from source facts plus UI axes in this runtime path.

## Next Owner

- Owner: `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Hypothesis: `comparative_contract_gap`

No product implementation was performed in this package.

