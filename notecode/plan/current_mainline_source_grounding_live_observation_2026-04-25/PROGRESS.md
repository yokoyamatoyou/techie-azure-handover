# current_mainline_source_grounding_live_observation_2026-04-25 PROGRESS

## Current Status

- Package status: completed
- Current phase: Phase 4 hard decision / closeout
- Product code change: no
- Metric correction: not started

## Baseline

- Predecessor classification:
  - `source_grounding_observability_anchor_mismatch`
- Telemetry source:
  - `source_grounding_deduped_anchor_group_count`
  - `source_grounding_matched_anchor_group_count`
  - `source_grounding_partial_anchor_group_count`
  - `source_grounding_missing_anchor_group_count`
  - `source_grounding_duplicate_anchor_group_count`
  - `source_grounding_title_like_anchor_group_count`
  - `source_grounding_anchor_group_diagnostics`

## Live Artifact Root

- `C:\tetie\notecode\logs\current_mainline_source_grounding_live_observation_20260425-202931\`
- Summary:
  - `C:\tetie\notecode\logs\current_mainline_source_grounding_live_observation_20260425-202931\live_observation_summary.json`
- UI server:
  - started with `C:\tetie\notecode\.venv\Scripts\python.exe -m note.note_writer_app`
  - `PORT=18080`
  - `HEADLESS=1`

## Phase Ledger

| Phase | Scope | Result |
|---|---|---|
| 0 | package docs | completed |
| 1 | UI smoke | completed: initial connection failed, module launch reached `OK 200` |
| 2 | live attempts | completed: valid Case 1 x3, valid Case 4 x3 |
| 3 | evidence classification | completed |
| 4 | hard decision / closeout | completed |

## Attempt Summary

| Case | Attempt | Evidence | UI status | Runtime | Warning category | Ratio | Groups deduped / matched / partial / missing / duplicate / title-like | Visible acceptable | Classification |
|---|---:|---|---|---|---|---:|---|---|---|
| Case 1 | 1 | valid | failed | `SYS_QUALITY_WARNINGS_UNRESOLVED` | source grounding mixed | `0.4` | `5 / 2 / 1 / 2 / 0 / 0` | true | mixed |
| Case 1 | 2 | excluded | lenient collected after operation error | `SYS_PIPELINE_FAILURE` | none | n/a | n/a | false | excluded |
| Case 1 | 3 | valid | lenient collected after operation error | `OK` | fingerprint-only | `0.6` | `5 / 3 / 1 / 1 / 0 / 0` | true | control |
| Case 1 | 4 | valid | lenient collected after operation error | `OK` | fingerprint-only | `0.6` | `5 / 3 / 1 / 1 / 0 / 0` | true | control |
| Case 4 | 1 | valid | failed | `SYS_QUALITY_WARNINGS_UNRESOLVED` | source grounding mixed | `0.4444` | `5 / 3 / 1 / 1 / 3 / 1` | true | anchor-shape false positive |
| Case 4 | 2 | excluded | operation timeout before generate | n/a | none | n/a | n/a | false | excluded |
| Case 4 | 3 | valid | failed | `SYS_QUALITY_WARNINGS_UNRESOLVED` | source grounding mixed | `0.4444` | `5 / 3 / 1 / 1 / 3 / 1` | true | anchor-shape false positive |
| Case 4 | 4 | valid | lenient collected after operation error | `OK` | fingerprint-only | `0.6667` | `5 / 4 / 0 / 1 / 3 / 1` | true | control |

Notes:

- Excluded attempts are not counted as evidence because telemetry was missing or generation did not produce a fresh usable snapshot.
- Lenient collection was used only when UI operation produced or updated latest snapshots but the Selenium click/wait path ended with an operation error.
- No visible/body internal leakage was recorded in valid attempts.
- No source outside claim evidence was found in valid attempts.
- New telemetry keys were present in every valid attempt.

## Case Classification

- Case 1:
  - valid attempts: 3
  - weak attempts: 1
  - controls: 2
  - classification: `mixed`
  - evidence:
    - weak attempt body was non-empty and visibly acceptable by artifact checks.
    - group telemetry was `5 / 2 / 1 / 2 / 0 / 0`.
    - missing groups outnumbered partial / duplicate / title-like groups, so this should not be called a clean anchor-shape false positive.
- Case 4:
  - valid attempts: 3
  - weak attempts: 2
  - controls: 1
  - classification: `anchor-shape false positive`
  - evidence:
    - both weak attempts had `source_grounding_reflection_ratio=0.4444`.
    - both weak attempts had the same group shape: `5 / 3 / 1 / 1 / 3 / 1`.
    - the missing group was the duplicated title-like group around `記事依頼フォーム 導入手順と再現条件`.
    - the body was non-empty, no leakage/source outside claim was found, and the core case-study facts were visible.

## Hard Decision

- Case 1:
  - decision: `observe only`
  - reason: live weak evidence is mixed; telemetry is useful, but the single weak run is not enough to justify a metric correction package by itself.
- Case 4:
  - decision: `metric correction package needed`
  - reason: two valid live weak attempts are acceptable bodies explained by duplicate / title-like / partial anchor-group shape.
  - next package owner candidate:
    - `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
  - narrow hypothesis:
    - source-grounding reflection should be evaluated or corrected against deduped anchor groups so duplicated title-like source items do not create intermittent false fail-closed outcomes.
  - rollback boundary:
    - owner-local change only in `quality_observability_mixin.py` plus focused tests.
- Overall:
  - stop here.
  - no metric correction was implemented in this package.

## Tests / Checks

- UI smoke:
  - initial `Invoke-WebRequest http://127.0.0.1:18080/` failed because the UI was not running.
  - starting `note.note_writer_app` as a module on `PORT=18080` succeeded.
  - follow-up `Invoke-WebRequest http://127.0.0.1:18080/` returned `OK 200`.
- Product tests:
  - not run; product code was not changed.
