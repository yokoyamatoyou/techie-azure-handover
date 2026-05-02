# separate window execution prompt opening frame redesign docs first 2026-04-18

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
- C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\compass_artifact_wf-d9cf85b5-5c9c-4b24-b87e-d34499c64d36_text_markdown.md
- C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\deep-research-report (31).md
- C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\新規 テキスト ドキュメント.txt

今回の依頼種別:
- docs-first design-triage prompt
- `START_NEW_PACKAGE_OPENING_FRAME_REDESIGN_DOCS_FIRST`
- implementation prompt ではない
- current package reopen prompt ではない

今回の実施範囲:
- `naturalness_recovery_2026-04-07` package を parked のまま維持しつつ、
  separate redesign line `opening_frame_redesign` の docs-only boundary を固定する
- production code / tests / AGENTS / WORKLOG / current package docs は編集しない
- new package を start する場合も first line は docs-only とし、code diff は作らない

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
- next owner:
  - not fixed
- next narrow hypothesis:
  - not fixed

research synthesis fixed read:
- 共通点:
  - problem is `opening frame ownership`
  - `title / lead / first heading / first section` role separation が必要
  - `current-business-first` opener invariant が必要
  - prompt accretion continuation は不支持
  - broad planning default / giant rewrite first も不支持
- 差分:
  - minimal control をどこへ置くかはまだ未収束
  - `prompt_builder` frame card / variable 化
  - upstream source ordering / hint placement
  - tiny detector / guard

why this window exists:
- current package の single-owner retry は exhausted している
- しかし research は next problem setting として
  - opening owner redesign
  - role separation
  - minimal structural signal
  をかなり強く支持している
- この論点は current package の中へ戻すと do-not-retry と衝突する
- よって current package reopen ではなく、
  separate docs-first line として切る必要がある

core question:
- `opening_frame_redesign` を separate line として start するなら、
  current parked judgment と衝突せずにどの package boundary / objective / non-goals / first phase を fixed すべきか

what to decide:
1. new package を本当に `opening_frame_redesign_2026-04-18` として切るべきか
2. objective をどう最小化するか
3. non-goals をどう固定するか
4. do-not-retry boundary を current package から何を継承するか
5. first phase をなぜ `docs-first / design-triage first` にするか
6. first code owner candidate をどこに tentatively 置くか
7. `minimal_control_layer` を package 名にせず sub-question に留めるべきか

strong bias:
- current package を reopen しない
- production code を編集しない
- tests を編集しない
- stale implementation prompt を再利用しない
- `prompt_builder.py` wording simplification の rename retry をしない
- `pipeline.py` current-first hint triage の rename retry をしない
- `planning / skeleton default reopen` に戻さない
- giant rewrite proposal にしない
- prompt accretion continuation にしない
- multiple owner implementation planning に飛ばない

expected reading:
- research が支持しているのは
  - same failed owner retry ではなく
  - opening owner redesign という new problem setting
- したがって package theme は
  - `minimal_control_layer`
  ではなく
  - `opening_frame_redesign`
  が先
- `minimal_control_layer` はその package 内の first design question として扱う

expected first owner candidate:
- first docs owner candidate:
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\`
- tentative first code owner candidate after docs:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` 周辺の最小 opening-frame control surface
- 注意:
  - これは `pipeline_current_first_triage` の unchanged reopen ではない
  - docs-first line で boundary が定義できた場合だけ将来候補として書く

why this is not prompt accretion continuation:
- next line の目的は rule を増やすことではなく、
  opener ownership と role separation を再定義すること
- 共通点として収束しているのは `less prose rule, clearer owner`
- したがって next line は `add more prompt lines` ではなく
  `fix package boundary and control placement question`
  である

preferred output shape:
- docs-only package start
- recommended package path:
  - C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\
- create only if justified:
  - README.md
  - TASK.md
  - PROGRESS.md
  - ROLLBACK.md
  - EXECUTION_PROMPT.md
- if package creation is still too early:
  - docs-only stop note 1 本で止める

package objective guidance:
- opening frame の owner と role separation を定義する
- `title / lead / first heading / first section` の責務を current-business-first invariant と整合させる
- exact implementation を commit せず、
  first control placement question を narrow に切り出す

package non-goals guidance:
- current package reopen
- production code implementation
- prompt accretion continuation
- fixed routing table
- broad planning / skeleton default return
- giant rewrite
- current success path の置換

stop conditions:
- current package reopen と実質同じ内容しか書けない
- first phase が implementation へ滑る
- do-not-retry boundary を守れない
- `opening_frame_redesign` ではなく `minimal_control_layer implementation` を先に固定したくなった

final report must include:
1. 読んだ参照ルールファイル
2. 今回の実施範囲
3. new package を start するかどうか
4. start するなら objective / non-goals / do-not-retry boundary
5. first line を docs-first にした理由
6. tentative first code owner candidate
7. `minimal_control_layer` を theme 名にしなかった理由
8. 何を作成 / 更新したか
9. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
10. WEB検索を使ったかどうか
```
