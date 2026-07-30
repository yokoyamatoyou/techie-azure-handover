# current_mainline_source_grounding_reflection_diagnosis_2026-04-25 PROGRESS

## Current Status

- Package status: stopped before implementation
- Current phase: Phase 4 stop / handoff
- Behavior change: no
- Product code change: no
- Classification: `source_grounding_observability_anchor_mismatch`

## Read / Evidence Baseline

- Required source-of-truth read completed in planning:
  - `C:\tetie\AGENTS.md`
  - `C:\tetie\notecode\AGENTS.md`
  - `C:\tetie\notecode\ALGORITHM.md` sections 4, 5, 12
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
  - `C:\tetie\notecode\plan\current_mainline_fingerprint_policy_resolution_2026-04-25\PROGRESS.md`
  - predecessor package progress files
  - `C:\tetie\WORKLOG.md`
- Artifact root:
  - `C:\tetie\notecode\logs\current_mainline_fingerprint_policy_resolution_20260425-165333\`

## Policy / Data-Flow Map

- UI input source:
  - saved validations used equivalent controls: `length_mode=short` and intended speaker.
  - Case 1 speaker: `企業広報として語る`
  - Case 4 speaker: `導入支援担当として語る`
- Runtime resolved source packet:
  - Case 1 weak / success comparison uses 5 source grounding items.
  - Case 4 attempt 2 / attempt 3 use the same 9 source grounding items.
- Generated body reflection:
  - weak runs are not empty and are source-aware, but exact source-anchor matching is below threshold.
- Final quality report:
  - weak runs show `source_grounding:weak_reflection`.
  - `must_cover_reflection_rate` remains green-enough in the target weak artifacts, so this is not a broad contract-alignment failure.
- Output guard:
  - non-fingerprint warning keeps fail-closed behavior.
  - fingerprint-only demotion remains scoped to predecessor policy.
- UI adapter:
  - saved UI summaries show no stale output, no empty output, and no visible/body internal-term leakage.

## Artifact Comparison

| Case | Artifact | Runtime/UI result | Source reflection | Must-cover | Guard reasons | Classification |
|---|---|---:|---:|---:|---|---|
| Case 1 | backend strict weak run | runtime `OK`, strict guard blocked | `0/5 = 0.0` | `0.75` | fingerprint warnings + `source_grounding:weak_reflection` | `runtime source packet / final guard anchor mismatch` |
| Case 1 | UI lenient actual operation v2 | UI success | `3/5 = 0.6` | `0.75` | none | control / acceptable grounded run |
| Case 4 | UI lenient attempt 2 | UI failed | `4/9 = 0.4444` | `0.7143` | fingerprint warnings + `source_grounding:weak_reflection` | `runtime source packet / final guard anchor mismatch` with phrasing variance |
| Case 4 | UI lenient attempt 3 | UI success | `9/9 = 1.0` | `0.7143` | fingerprint-only warnings, demoted | control / acceptable grounded run |

## Anchor Evidence

- Case 1 weak run:
  - body reflects business content such as data digitization, printing/scanning, consultation entry points, process/support scope.
  - current anchor matcher records misses because each long source item requires at least two exact anchor terms and the generated body often paraphrases or keeps only one exact term.
  - examples of partial matches that still count as misses:
    - item 1 matched `デジタル化` only
    - item 2 matched only a long combined phrase around on-demand printing / scanning / operations support
    - item 3 matched `前処理から後処理まで` only
    - items 4 and 5 had no exact two-term match in the weak run
- Case 1 success run:
  - matched `3/5`.
  - exact anchors included `セキュリティ`, `デジタル化`, `打ち合わせ`, `応じてNDA`, `正確なアンケート帳票`, `入力データ`.
- Case 4 attempt 2:
  - source packet equality with attempt 3 confirmed by artifact inspection.
  - matched `4/9`; duplicates and title-like items made the denominator high.
  - missed duplicated/title-like anchors such as `記事依頼フォーム 導入手順と再現条件`.
  - missed exact phrase groups such as `依頼フォームで目的 ... 入力する形` even though the body describes the same form setup and required fields.
- Case 4 attempt 3:
  - matched `9/9`.
  - generated wording happened to preserve exact anchors including `再現条件`, `依頼フォームで目的`, `対象読者`, `レビュ当`, and `入力する形`.

## Classification Decision

- Primary bucket:
  - `runtime source packet / final guard anchor mismatch`
- Secondary factor:
  - generation phrasing variance, especially in Case 4 where the same source packet can produce `4/9` or `9/9`.
- Not primary:
  - `UI handoff artifact mismatch`
  - `stale / wrong contract evaluation`
  - `fingerprint policy residual`
- Reason:
  - input controls were equivalent, UI artifacts were fresh, body was non-empty, leakage was absent, and the weak signal tracks exact anchor matching rather than the broader source-aware body quality.

## Next Owner Recommendation

- Do not implement inside this package.
- If continuing, open a separate follow-up with owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
- Narrow hypothesis:
  - Add source-grounding observability for deduped, matched, and missing anchor groups derived from the runtime source packet. The goal is to distinguish true omission from anchor false positive without weakening fail-closed behavior.
- Why this owner:
  - `source_grounding:weak_reflection` is emitted from source grounding metrics and contextual naturalness reporting in quality observability.
  - The observed residual is in metric explainability / anchor matching, not UI display, output-guard policy, prompt text, repair count, or target length.
- Why this is not threshold relaxation:
  - The follow-up would keep the existing blocking behavior and add evidence needed to decide whether a future correction is source-use or metric-shape related.

## Phase Ledger

| Phase | Scope | Behavior change | Result |
|---|---|---|---|
| 0 | package docs | no | README / TASK / PROGRESS / ROLLBACK created |
| 1 | policy / data-flow map | no | source-use to UI display map documented |
| 2 | artifact comparison | no | Case 1 / Case 4 weak and success artifacts classified |
| 3 | next owner decision | no | likely owner narrowed to `quality_observability_mixin.py` |
| 4 | stop / handoff | no | implementation deferred to separate package |

## Tests

- Product tests not run because this is a docs-only diagnosis package.
- No product code was changed.
