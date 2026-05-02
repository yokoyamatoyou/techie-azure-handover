# separate window execution prompt opening frame redesign package docs start 2026-04-18

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\management_stop_report_after_failed_pipeline_current_first_triage_2026-04-18.md
- C:\tetie\notecode\docs\parked_package_prompt_naturalness_recovery_2026-04-18.md
- C:\tetie\notecode\docs\management_prompt_keep_naturalness_recovery_parked_2026-04-18.md
- C:\tetie\notecode\docs\opening_frame_redesign_research_synthesis_note_2026-04-18.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_opening_frame_redesign_docs_first_2026-04-18.md
- C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\compass_artifact_wf-d9cf85b5-5c9c-4b24-b87e-d34499c64d36_text_markdown.md
- C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\deep-research-report (31).md
- C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\新規 テキスト ドキュメント.txt

今回の依頼種別:
- docs-first package creation prompt
- `START_OPENING_FRAME_REDESIGN_PACKAGE_DOCS`
- implementation prompt ではない
- current package reopen prompt ではない

今回の実施範囲:
- new package
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\`
  を docs-only で作成する
- 作成対象は
  - `README.md`
  - `TASK.md`
  - `PROGRESS.md`
  - `ROLLBACK.md`
  - `EXECUTION_PROMPT.md`
  の 5 本だけに限定する
- production code / tests / AGENTS / WORKLOG / current package docs は編集しない
- current package `naturalness_recovery_2026-04-07` は parked のまま維持する

current fixed judgment:
- current package:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07`
- package state:
  - `parked / not fixed`
- current success path:
  - keep
- failed / rollback 済み / unchanged retry 禁止:
  - `prompt_builder.py` simplification-first wording line
  - `pipeline.py` current-first source ordering / hint triage
  - `pipeline.py` core_message current-first hint
- current package reopen:
  - しない

new package fixed theme:
- package name:
  - `opening_frame_redesign_2026-04-18`
- package theme:
  - `opening frame ownership / role separation / current-business-first invariant`
- package position:
  - current parked package の continuation implementation ではない
  - separate redesign line の docs-first start

why this package is legal:
- research 3本の共通結論は
  - `opening frame ownership`
  - `title / lead / first heading / first section` role separation
  - `current-business-first` opener invariant
  - `prompt accretion continuation` 不支持
  に収束している
- これは current package の failed single-owner retry と同じ問いではなく、
  cross-owner design question として別 line に切るほうが source-of-truth と整合する

what this window must create:
1. `README.md`
   - objective
   - read order
   - source-of-truth
   - current decision
   - package state
   - why
   - simplification direction
   - non-goals
2. `TASK.md`
   - global rules
   - current locked outcome
   - gates
   - stop gate
   - docs-first phase map
   - refined execution order
3. `PROGRESS.md`
   - current goal
   - current status
   - hypothesis framing
   - owner scope
   - attempts used
   - next phase
4. `ROLLBACK.md`
   - baseline
   - rollback rule
   - do-not-retry hypotheses inherited from current package
   - package-specific stop boundary
5. `EXECUTION_PROMPT.md`
   - next startup canonical prompt path
   - docs-first first step only

new package objective guidance:
- code diff を始める前に
  `opening frame ownership` の問題設定を narrow に固定する
- `title / lead / first heading / first section` の責務を分ける
- `company introduction` の `current-business-first` invariant を package-level に固定する
- `minimal_control_layer` の placement を design question として扱う
- exact implementation owner はまだ固定しない

new package non-goals guidance:
- current package `naturalness_recovery_2026-04-07` の reopen
- production code 実装
- `prompt_builder.py` retry の rename reopen
- `pipeline.py` retry の rename reopen
- prompt accretion continuation
- fixed routing table
- planning / skeleton default reopen
- giant rewrite
- current success path の置換
- hidden reviser accumulation

important writing constraints:
- `pipeline.py` を first code owner に確定しない
- `prompt_builder.py` を first code owner に確定しない
- owner は `not fixed yet` と書く
- tentative candidate が必要なら
  - `newalgorithm_pipeline/pipeline.py` 周辺の最小 opening-frame control surface
  を候補として触れるだけに留める
- `minimal_control_layer` は package theme ではなく first design question として置く
- research は evidence であり source-of-truth そのものではないと明記する

recommended package read order:
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

expected current decision wording:
- package category:
  - `DOCS_FIRST_NEW_PACKAGE_AFTER_PARKED_NATURALNESS_RECOVERY`
- current decision:
  - `opening frame redesign is a separate redesign line`
- first code owner:
  - `not fixed`
- first code step:
  - `not started`
- next step:
  - `docs-first design triage`

expected first phase shape:
- Phase 00:
  - objective:
    - define opener ownership problem and evaluation boundary
  - owner:
    - package docs only
  - exit:
    - objective / non-goals / do-not-retry / evaluation set が固定される
- Phase 01:
  - objective:
    - compare minimal control placement candidates without code
  - owner:
    - docs only
  - candidates:
    - `prompt_builder` frame card
    - `pipeline.py` opening-frame control surface
    - tiny deterministic guard
  - exit:
    - legal `1 owner / 1 hypothesis` candidate が 1 本に絞られる

gates guidance:
- entry gate:
  - new package が current parked package と役割衝突していない
  - do-not-retry boundary が継承されている
- pass gate:
  - docs 5 本が互いに整合している
  - current package parked judgment と衝突しない
  - next step が implementation に滑っていない
- stop gate:
  - current package reopen と実質同じ文書しか書けない
  - code owner を early fix したくなった
  - package objective が broad redesign に膨らんだ

rollback guidance:
- rollback 対象は new package docs だけ
- current package docs は触らない
- code diff がないので production rollback は不要

WEB search policy:
- 原則不要
- local docs / local research / local source-of-truth だけで足りるなら使わない
- 足りない場合のみ 1 回だけ許可
- 使った場合は query と採用理由を短く示す

final report must include:
1. 読んだ参照ルールファイル
2. 今回の実施範囲
3. 作成した package path
4. 作成した docs 5 本
5. new package objective
6. non-goals
7. do-not-retry / parked boundary の継承内容
8. first code owner を fixed していないこと
9. WEB検索を使ったかどうか
10. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
