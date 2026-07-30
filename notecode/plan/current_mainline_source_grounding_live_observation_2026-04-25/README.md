# current_mainline_source_grounding_live_observation_2026-04-25

## Objective

Use the internal telemetry added by `current_mainline_source_grounding_observability_2026-04-25` to live-observe Case 1 / Case 4 through the real UI and classify remaining `source_grounding:weak_reflection` as:

- `true weak reflection`
- `anchor-shape false positive`
- `mixed`
- `control`

## Source

- Predecessor diagnosis:
  - `C:\tetie\notecode\plan\current_mainline_source_grounding_reflection_diagnosis_2026-04-25\`
- Telemetry implementation:
  - `C:\tetie\notecode\plan\current_mainline_source_grounding_observability_2026-04-25\PROGRESS.md`
- Fingerprint policy boundary:
  - `C:\tetie\notecode\plan\current_mainline_fingerprint_policy_resolution_2026-04-25\PROGRESS.md`

## Evidence Route

- Primary evidence:
  - real UI operation at `http://127.0.0.1:18080/`
- Allowed fallback:
  - lenient collection of fresh `latest_generation_output.json` / `latest_generation_quality_report.json` when UI click/wait is brittle but generation has started and produced a fresh snapshot.
- Supplementary only:
  - backend runner or UI-equivalent harness.

## Evidence Fields

Each attempt records:

- success / fail-closed
- runtime reason
- output guard reasons and soft warnings
- `source_grounding_reflection_ratio`
- `source_grounding_deduped_anchor_group_count`
- `source_grounding_matched_anchor_group_count`
- `source_grounding_partial_anchor_group_count`
- `source_grounding_missing_anchor_group_count`
- `source_grounding_duplicate_anchor_group_count`
- `source_grounding_title_like_anchor_group_count`
- bounded `source_grounding_anchor_group_diagnostics`
- visible acceptability
- source outside claim evidence
- visible/body internal leakage
- fingerprint-only vs source-grounding mixed warning classification

## Non-Goals

- Product code change.
- Metric correction implementation.
- Source grounding threshold change.
- Prompt addition.
- Repair trigger or repair count change.
- UI demote addition.
- Fingerprint-only demote scope expansion.
- UI display of raw internal telemetry.

## Decision

This package stops after live observation and hard decision:

- `observe only`
- `metric correction package needed`
- `runtime source-use follow-up needed`

