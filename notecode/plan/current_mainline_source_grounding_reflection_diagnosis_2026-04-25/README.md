# current_mainline_source_grounding_reflection_diagnosis_2026-04-25 README

## Objective

- Diagnose the intermittent `source_grounding:weak_reflection` residual left after completed package `current_mainline_fingerprint_policy_resolution_2026-04-25`.
- Keep fingerprint-only residual closed as scoped soft warning / observability. Do not reopen fingerprint policy.
- Classify Case 1 / Case 4 saved artifacts by evidence before any implementation.

## Source Of Truth

- Global current package:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- Completed predecessor:
  - `C:\tetie\notecode\plan\current_mainline_fingerprint_policy_resolution_2026-04-25\`
- Primary artifact root:
  - `C:\tetie\notecode\logs\current_mainline_fingerprint_policy_resolution_20260425-165333\`
- Current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## Non-Goals

- Do not demote `source_grounding:weak_reflection` to warning-only.
- Do not relax `quality_guard.py`, fingerprint thresholds, source grounding thresholds, target chars, or length mode.
- Do not add prompt wording, repair triggers, repair attempts, or route branches.
- Do not broaden fingerprint-only demotion scope.
- Do not change `note_writer_app.py`, `output_guard.py`, `prompt_builder.py`, or `pipeline.py` as a workaround.
- Do not expose runtime/internal terms in body or UI.
- Do not reopen pre-2026-04-02 archive, completed reference packages, or frozen architecture package.

## Data-Flow Map

| Layer | Evidence to inspect | Current finding |
|---|---|---|
| UI input source | UI selected article type, semantic key, speaker, length mode, source inputs | Equivalent controls were used in saved validation: `short` length and intended speaker for both cases. |
| Runtime resolved source packet | `input_contract.source_grounding_items`, `must_cover`, source docs count | Case 1 has 5 source items; Case 4 attempt 2 and attempt 3 share the same 9 source items. |
| Generated body reflection | body excerpt, matched anchors, missing anchors | Weak runs contain source-aware bodies but miss exact anchor groups required by the current metric. |
| Final quality report | `source_grounding_reflection_ratio`, `source_trace_coverage`, `must_cover_reflection_rate`, soft warnings | `must_cover` can be green while source trace is red, so the two signals are not interchangeable. |
| Output guard blocking reason | strict guard reasons and fingerprint-only demotion eligibility | Runs containing `source_grounding:weak_reflection` remain blocked; Case 4 attempt 3 demotes only because warnings are fingerprint-only. |
| UI adapter display | UI status, stale/empty result, visible/body leakage | Saved UI artifacts show no stale result, no empty result, and no internal-term leakage. |

## Artifact Classification

| Artifact | Primary classification | Evidence |
|---|---|---|
| Case 1 weak run | `runtime source packet / final guard anchor mismatch` | Strict guard had `source_grounding:weak_reflection`, `source_ref=0.0`, `must_cover=0.75`, 5 source items, body was visibly source-aware. Anchor matching recorded `0/5` because long source snippets were reflected by paraphrase or partial terms only. |
| Case 1 success run | control / acceptable grounded run | Same 5 source items, `source_ref=0.6`, `must_cover=0.75`, no output guard reasons, UI success, fresh non-empty artifact. |
| Case 4 attempt 2 | `runtime source packet / final guard anchor mismatch` with generation phrasing variance | Same 9 source items as attempt 3, `source_ref=0.4444`, `must_cover=0.7143`, blocked. Core case-study facts are present, but exact anchors such as `再現条件` and `依頼フォームで目的` are missed in enough duplicated/title-like source items to fall below 0.5. |
| Case 4 attempt 3 | control / acceptable grounded run | Same 9 source items, `source_ref=1.0`, `must_cover=0.7143`, UI success. Remaining warnings were fingerprint-only and eligible for predecessor policy. |

## Decision

- Root classification for this package: `source_grounding_observability_anchor_mismatch`.
- This is not primarily a UI handoff artifact mismatch: equivalent controls, fresh outputs, no stale result, no empty result, and no leakage were already observed.
- This is not a threshold problem to solve by relaxation. The current metric is detecting exact source-anchor reflection, while some bodies reflect source meaning through paraphrase or a subset of long source fragments.
- No implementation is performed in this package.

## Next Owner If Continuing

- Candidate owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
- Narrow follow-up hypothesis:
  - Source-grounding observability should expose deduped, matched, and missing anchor groups from the runtime source packet, so true omission and anchor false positives can be distinguished without weakening the fail-closed guard.
- Not first owners:
  - `note_writer_app.py`
  - `output_guard.py`
  - `prompt_builder.py`
  - `simple_note_pipeline\pipeline.py`
