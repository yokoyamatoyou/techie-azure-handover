# opening_frame_redesign_2026-04-18 README

## Objective

- current package `naturalness_recovery_2026-04-07` を parked のまま維持しつつ、`opening frame ownership / role separation / current-business-first invariant` を separate redesign line として narrow に固定する
- `title / lead / first heading / first section` の責務分離を docs-only で定義し、code diff 前に evaluation boundary を固定する
- `minimal_control_layer` の placement を first design question として扱うが、exact implementation owner はまだ固定しない

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\README.md`
4. `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\TASK.md`
5. `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\PROGRESS.md`
6. `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\ROLLBACK.md`
7. `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\EXECUTION_PROMPT.md`
8. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
9. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
10. `C:\tetie\notecode\docs\opening_frame_redesign_research_synthesis_note_2026-04-18.md`
11. `C:\tetie\WORKLOG.md`

## Source Of Truth

- this package:
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\README.md`
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\TASK.md`
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\PROGRESS.md`
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\ROLLBACK.md`
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\EXECUTION_PROMPT.md`
- inherited parked boundary:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md`
- current runtime baseline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- current visible artifact baseline:
  - `C:\tetie\notecode\logs\latest_generation_output.txt`
  - `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- evidence only:
  - `C:\tetie\notecode\docs\opening_frame_redesign_research_synthesis_note_2026-04-18.md`
  - `C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\compass_artifact_wf-d9cf85b5-5c9c-4b24-b87e-d34499c64d36_text_markdown.md`
  - `C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\deep-research-report (31).md`
  - `C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\新規 テキスト ドキュメント.txt`

## Current Decision

- package category:
  - `DOCS_FIRST_NEW_PACKAGE_AFTER_PARKED_NATURALNESS_RECOVERY`
- current decision:
  - `opening frame redesign is a separate redesign line`
- package theme:
  - `opening frame ownership / role separation / current-business-first invariant`
- package position:
  - current parked package の continuation implementation ではない
  - current package reopen ではない
  - docs-first start only
- first code owner:
  - `not fixed`
- first code step:
  - `not started`
- next step:
  - `docs-first design triage`
- tentative future code candidate:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` 周辺の最小 opening-frame control surface
  - Phase 01 が legal な `1 owner / 1 hypothesis` に絞れた場合だけ future candidate として扱う
- research handling:
  - research は evidence であり source-of-truth そのものではない
- inherited parked boundary:
  - `prompt_builder.py` simplification-first wording line は failed / rollback 済み / unchanged retry 禁止
  - `pipeline.py` current-first source ordering / hint triage は failed / rollback 済み / unchanged retry 禁止
  - `pipeline.py` core_message current-first hint も unchanged retry 禁止

## Package State

- package status:
  - active
  - not_closed
- package mode:
  - docs-first design triage
- current phase:
  - Phase 00 objective freeze completed at package start
- phase 01 status:
  - not_started
- current honest status:
  - opening frame redesign の問題設定は separate line として固定した
  - exact code owner / exact minimal control placement は未確定
  - current package `naturalness_recovery_2026-04-07` は parked / not fixed のまま維持する
- next action:
  - Phase 01 で `prompt_builder` frame card / `pipeline.py` opening-frame control surface / tiny deterministic guard を code なしで比較する

## Why

- current parked package では `prompt_builder.py` と `pipeline.py` の single-owner retry がともに exhausted しており、same line を rename して戻すと do-not-retry と衝突する
- research 3 本の共通結論は wording 追加ではなく `opening frame ownership` と `title / lead / first heading / first section` の role separation に収束している
- ただし research は `minimal_control_layer` をどこへ置くかまでは未収束であり、ここを先に code owner へ確定すると別 line の docs-first start にならない
- よって current package reopen ではなく、cross-owner design question を separate redesign line として切り出すほうが source-of-truth と整合する
- first line を docs-only に止めることで、same failed retry / prompt accretion / multiple owner implementation planning への滑りを防げる

## Simplification Direction

### Keep

- current success path
- current package `naturalness_recovery_2026-04-07` の parked / not fixed judgment
- company introduction opener の `current-business-first` invariant
- docs-first / rollback-first / `1 phase = 1 narrow hypothesis = 1 owner scope`
- `minimal_control_layer` を package theme ではなく first design question として扱うこと

### Thin

- opening-frame problem setting を `title / lead / first heading / first section` に narrow に閉じる
- code owner commitment を `not fixed` のまま維持する
- next design question を control placement comparison だけへ縮める

### Remove As Default Assumption

- `prompt_builder.py` retry の rename reopen
- `pipeline.py` retry の rename reopen
- first code owner を early fix する前提
- planning / skeleton default reopen
- fixed routing table
- giant rewrite
- prompt accretion continuation
- hidden reviser accumulation

## Non-Goals

- current package `naturalness_recovery_2026-04-07` の reopen
- production code implementation
- `prompt_builder.py` simplification-first retry の rename reopen
- `pipeline.py` current-first triage の rename reopen
- `pipeline.py` core_message current-first hint の rename reopen
- prompt accretion continuation
- fixed routing table
- planning / skeleton default reopen
- giant rewrite
- current success path の置換
- hidden reviser accumulation
- first code owner の早期固定
