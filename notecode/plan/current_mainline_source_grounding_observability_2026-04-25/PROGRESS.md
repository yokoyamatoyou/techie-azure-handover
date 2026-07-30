# current_mainline_source_grounding_observability_2026-04-25 PROGRESS

## Current Status

- Package status: completed
- Current phase: Phase 4 closeout
- Behavior change: no
- Owner scope:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
  - `C:\tetie\notecode\note\tests\test_newalgorithm_phase06_logging_compat.py`

## Baseline

- Predecessor diagnosis classification:
  - `source_grounding_observability_anchor_mismatch`
- Keep unchanged:
  - current success path
  - `single-pass + optional single repair 1回`
  - existing source grounding threshold
  - existing fingerprint-only demotion scope
  - existing fail-closed behavior for `source_grounding:weak_reflection`

## Telemetry Schema

Internal artifact keys to add:

- `source_grounding_deduped_anchor_group_count`
- `source_grounding_matched_anchor_group_count`
- `source_grounding_partial_anchor_group_count`
- `source_grounding_missing_anchor_group_count`
- `source_grounding_duplicate_anchor_group_count`
- `source_grounding_title_like_anchor_group_count`
- `source_grounding_anchor_group_diagnostics`

Diagnostic group shape:

```json
{
  "group_index": 1,
  "item_indices": [1],
  "duplicate_count": 1,
  "title_like": false,
  "anchor_terms": ["..."],
  "matched_terms": ["..."],
  "missing_terms": ["..."],
  "match_status": "matched|partial|missing",
  "source_excerpt": "..."
}
```

## Implementation Notes

- Existing item-based metrics must remain unchanged:
  - `source_grounding_item_count`
  - `source_grounding_reflected_count`
  - `source_grounding_reflection_ratio`
  - `source_grounding_anchor_terms`
- Group diagnostics are explainability only.
- Grouping key is normalized anchor-term signature.
- `title_like=true` when a fact is short, has no sentence punctuation, and yields at most two anchors.
- Diagnostics list is bounded.
- No prompt, generation, repair, threshold, output guard, UI demote, target length, or success/fail policy was changed.

## Implementation Summary

- Added group-level internal diagnostics to `_source_grounding_metrics()`.
- Grouping uses normalized anchor-term signatures, falling back to normalized fact text only when anchor terms are empty.
- Per-group diagnostics are bounded:
  - first 12 groups
  - first 12 item indices per group
  - first 8 anchor / matched / missing terms
  - 120 character source excerpt
- Added focused tests for:
  - duplicate / title-like / missing group observability
  - partial exact-term observability without reflected-ratio change

## Saved Artifact Diagnostic Summary

Source artifacts read from:

- `C:\tetie\notecode\logs\current_mainline_fingerprint_policy_resolution_20260425-165333\`

| Artifact | Items | Reflected | Ratio | Groups | Matched groups | Partial groups | Missing groups | Duplicate groups | Title-like groups | Interpretation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Case 1 weak | 5 | 0 | 0.0 | 5 | 0 | 3 | 2 | 0 | 0 | body is source-aware but exact anchors mostly land as partial or missing |
| Case 1 success | 5 | 3 | 0.6 | 5 | 3 | 2 | 0 | 0 | 0 | same source count, enough exact anchors reflected |
| Case 4 attempt 2 | 9 | 4 | 0.4444 | 5 | 3 | 1 | 1 | 3 | 1 | duplicate/title-like group missing and one group partial |
| Case 4 attempt 3 | 9 | 9 | 1.0 | 5 | 5 | 0 | 0 | 3 | 1 | same duplicated/title-like group matched by exact wording |

Diagnostic highlights:

- Case 1 weak:
  - partial groups include `デジタル化`, the long on-demand / scanning / support / data phrase, and `前処理から後処理まで`.
  - two groups remain missing, so the artifact is not cleanly explainable as a stale UI handoff.
- Case 1 success:
  - matched groups include `セキュリティ`, `デジタル化`, `打ち合わせ`, and `応じてNDA`.
  - the existing reflection ratio remains `0.6`.
- Case 4 attempt 2:
  - duplicate/title-like group `記事依頼フォーム 導入手順と再現条件` appears at item indices `[2, 6, 8]` and is missing.
  - the `対象読者` group is partial: `対象読者` is matched, while `依頼フォームで目的`, `レビュ当`, and `入力する形` are missing.
- Case 4 attempt 3:
  - the same duplicate/title-like group is matched via `再現条件`.
  - all five deduped groups are matched.

## Decision

- The new telemetry explains the saved Case 1 / Case 4 residuals as anchor observability / phrasing variance evidence without changing the fail-closed policy.
- This package stops at observability.
- If metric correction is needed, it should be a separate package with a hard decision; it should not be folded into this telemetry change.

## Phase Ledger

| Phase | Scope | Result |
|---|---|---|
| 0 | package docs / schema | completed |
| 1 | focused tests | completed |
| 2 | implementation | completed |
| 3 | validation | completed |
| 4 | closeout | completed |

## Tests

- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase06_logging_compat.py -q -k "source_grounding"`
  - `3 passed, 25 deselected in 2.46s`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_quality_observability_structure.py note\tests\test_newalgorithm_phase06_logging_compat.py -q`
  - `31 passed in 2.44s`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`
  - `108 passed in 15.25s`
