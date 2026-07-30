# current_mainline_explanatory_article_regression_diagnosis_2026-04-26 PROGRESS

## Current Status

- Package status: completed
- Current phase: Phase 4 docs closeout
- Date: `2026-04-26 JST`
- Artifact root: `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\`
- Case: `bl-explanatory-misread-metric`
- Expected article type: `explanatory_article`
- Product code change: no
- Threshold / prompt / repair / UI demote / output guard change: no
- AGENTS update: no

## Comparison Table

| Check | Historical OK | Latest attempts | Judgment |
|---|---|---|---|
| UI route / semantic key | `explanatory_article` | `explanatory_article` both attempts | no route mismatch |
| source facts | 2 substantive facts | same substantive facts plus file-path/hash metadata in runtime packet | source reconstruction not equivalent |
| `source_grounding_items` | 2 fact items | 5 items: 2 facts + 3 path/hash metadata items | denominator polluted |
| source reflection | `1.0` | `0.4 = 2/5` | metric false negative |
| must-cover | `主要な数値 / 活用場面 / 前提` | `定着状況の見方メモ / ヘルプデスク観測メモ / 主な特徴`, reflected `1.0` | not direct blocker |
| body facts | source facts present | source facts present in both bodies | not true missing source facts |
| output guard | OK | `SYS_QUALITY_WARNINGS_UNRESOLVED`, includes `source_grounding:weak_reflection` | direct runtime block trigger |
| UI visible | historical OK | final UI text says `確認が必要なドラフトです` | summary label is stricter than visible UI |
| harness summary | OK | `input_required_block` because `blocked_output_redacted=true` | harness classification mismatch |

## Direct Cause

The latest attempts included five `source_grounding_items`, but only two were substantive source facts.

Substantive facts:

- `問い合わせ件数の減少だけでは定着成功と判断できない。初回設定完了率、権限設定の再編集率、FAQ閲覧後の操作完了率を合わせて見る必要がある`
- `問い合わせは減っていても、管理者だけが設定を肩代わりしているケースがある。実務担当者の操作ログが薄いままなら定着ではなく依存の固定化が起きている`

Path/hash metadata counted as source grounding items:

- `C:\tetie\notecode\note\uploads\b0296d34e5ad47b18185d251855fa430_01.txt`
- `C:\tetie\notecode\note\uploads\b4e7920fe6374363bec490bde9124752_02.txt`
- `b0296d34e5ad47b18185d251855fa430_01`

The body reflected the two real facts, but did not reflect the file paths or hash name. That made reflection `2/5 = 0.4`, which triggered `source_grounding:weak_reflection`.

## Attempt Summary

| Attempt | Runtime reason | Body chars | Source grounding | Must-cover | Repair | Visible UI |
|---:|---|---:|---:|---:|---|---|
| 1 | `SYS_QUALITY_WARNINGS_UNRESOLVED` | 1513 | `0.4` | `1.0` | not required | `確認が必要なドラフトです` |
| 2 | `SYS_QUALITY_WARNINGS_UNRESOLVED` | 1395 | `0.4` | `1.0` | required, rejected | `確認が必要なドラフトです` |

## Classification

Primary:

- `source_reflection_metric_false_negative`
- `source_reconstruction_mismatch`

Secondary:

- validation harness outcome naming is too strict for this case because it reports `input_required_block` from `blocked_output_redacted=true`, while the final UI text is already a review-required draft message.

Not supported:

- `UI_route_mismatch`
- `true_missing_source_facts`
- `source_caveat_only`
- `repair_not_actuating` as the direct cause. Attempt 1 did not require repair; attempt 2 rejected repair, but both attempts share the same direct source reflection denominator issue.

## Source Caveat Handling

The case remains a thin-source watch, but source caveat alone does not explain the regression. Historical OK used the same substantive facts with source reflection `1.0`. The latest blocked attempts added metadata-like grounding items to the denominator.

## Next Decision

Stop as docs-only unless the user explicitly opens a future metric cleanup package.

If implementation is requested later:

- Owner: `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
- Hypothesis: source grounding reflection should ignore path/hash-like metadata source items when computing denominator, without threshold changes or unsupported-claim relaxation.

Do not choose UI demotion as the first fix. Latest visible UI already says `確認が必要なドラフトです`.

## Verification

Docs-only verification:

- Package files created:
  - `README.md`
  - `TASK.md`
  - `PROGRESS.md`
  - `ROLLBACK.md`
- `C:\tetie\WORKLOG.md` updated.
- Product code was not edited.
