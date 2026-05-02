# separate window execution prompt ui source blog contract phase01 baseline freeze 2026-04-18

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\docs\management_prompt_ui_source_blog_contract_redesign_followup_2026-04-18.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\README.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\TASK.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\PROGRESS.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\ROLLBACK.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\EXECUTION_PROMPT.md
- C:\tetie\notecode\docs\ui_source_blog_contract_archive_candidate_inventory_2026-04-18.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_ui_source_blog_contract_redesign_docs_followup_2026-04-18.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\README.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\PROGRESS.md
- C:\tetie\notecode\docs\opening_frame_redesign_research_synthesis_note_2026-04-18.md
- C:\tetie\notecode\research\新しいフォルダー (3)\00_external_ai_research_request_zero_base_ui_source_blog_algorithm_2026-04-18.md
- C:\tetie\notecode\research\新しいフォルダー (3)\08_external_ai_research_response_zero_base_ui_source_blog_algorithm_2026-04-18.md
- C:\tetie\WORKLOG.md

今回の依頼種別:
- docs-only narrow baseline freeze
- `UI_SOURCE_BLOG_CONTRACT_PHASE01_BASELINE_FREEZE`
- implementation prompt ではない
- actual archive prompt ではない

今回の実施範囲:
- `ui_source_blog_contract_redesign_2026-04-18` package の次 slice を narrow に固定する
- `UI article contract table`
- `source role baseline`
- `self-blog reuse baseline`
- `opening_frame` を `opener_mode` subproblem として位置づける
- 新規 docs note を 1 本だけ作る
- production code / tests / AGENTS / WORKLOG / current package docs は編集しない
- actual archive は行わない

current fixed judgment:
- top-level source-of-truth:
  - C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18
- inherited parked boundary:
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07
  - parked / not fixed
- reference redesign line:
  - C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18
  - reference only
- actual archive:
  - not yet
  - inventory only
- exact code owner:
  - not fixed
- first code step:
  - not started

この window が作成してよい file:
- C:\tetie\notecode\docs\ui_source_blog_contract_phase01_baseline_freeze_note_2026-04-18.md

この window がやること:
1. UI article type を minimal control axes に圧縮する
2. `fact / continuity / style_memory` の source role baseline を書く
3. self-blog reuse を `continuity reuse` と `style memory reuse` に分離して書く
4. `opening_frame` を `opener_mode` subproblem として位置づける
5. 上記を 1 本の docs note に閉じる

この window がやらないこと:
- production code edit
- test edit
- current package docs edit
- AGENTS edit
- WORKLOG edit
- implementation prompt 作成
- exact code owner fix
- actual archive 実行
- fixed routing table
- prompt accretion continuation
- giant rewrite

docs note に必ず入れること:
1. current state summary
2. minimal control axes の短い定義
3. UI article contract table
   - columns:
     - `ui_article_type`
     - `reader_task`
     - `evidence_mode`
     - `voice_distance`
     - `opener_mode`
     - `reuse_level`
4. source role baseline
   - `fact`
   - `continuity`
   - `style_memory`
   - fallback read は article-specific branch table ではなく `evidence_mode` 起点で書く
5. self-blog reuse baseline
   - past blog を default fact source にしない
   - `followup/continuity reuse` と `style memory reuse` を分ける
   - style memory には raw sentences ではなく profile summary だけを渡す
   - duplication avoidance を入れる
6. `opening_frame` position
   - `title / lead / first heading / first section` の共通 anchor は `opener_mode` から読む
   - opening-frame redesign package は subproblem reference として扱う
7. unresolved boundary
   - exact code owner はまだ fixed しない
   - exact implementation threshold や branch placement は future management step に残す

baseline writing rule:
- 長いカテゴリ別ルール集に戻さない
- minimal control axes は 5 つまでに留める
  - `reader_task`
  - `evidence_mode`
  - `voice_distance`
  - `opener_mode`
  - `reuse_level`
- self-blog reuse の activation は docs-only baseline として書く
  - exact code threshold を hard-fix しない
  - 必要なら research 由来の numeric example は `provisional` と明記する
- source selection は fixed routing table ではなく role / slot responsibility として書く

stop conditions:
- package theme が broad rewrite に膨らむ
- exact code owner を early fix したくなる
- actual archive を今やりたくなる
- self-blog reuse を default fact source にしたくなる
- current package docs を触りたくなる
- 2 file 以上を新規作成したくなる

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 今回の実施範囲
3. 作成した docs note path
4. fixed した UI article contract read
5. fixed した source role baseline
6. fixed した self-blog reuse baseline
7. exact code owner をまだ fixed していないこと
8. actual archive をしていないこと
9. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
10. WEB検索を使ったかどうか
```
