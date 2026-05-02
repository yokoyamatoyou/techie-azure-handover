# separate window execution prompt ui source blog contract redesign docs start 2026-04-18

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\README.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\TASK.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\PROGRESS.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\ROLLBACK.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\EXECUTION_PROMPT.md
- C:\tetie\notecode\research\新しいフォルダー (3)\00_external_ai_research_request_zero_base_ui_source_blog_algorithm_2026-04-18.md
- C:\tetie\notecode\research\新しいフォルダー (3)\08_external_ai_research_response_zero_base_ui_source_blog_algorithm_2026-04-18.md
- C:\tetie\notecode\research\新しいフォルダー (3)\01_opening_frame_redesign_README_copy_2026-04-18.md
- C:\tetie\notecode\research\新しいフォルダー (3)\06_software_and_runtime_summary_copy_2026-04-18.md
- C:\tetie\notecode\research\新しいフォルダー (3)\07_issue_and_work_summary_copy_2026-04-18.md
- C:\tetie\WORKLOG.md

今回の依頼種別:
- docs-only execution prompt
- `START_UI_SOURCE_BLOG_CONTRACT_REDESIGN_DOCS`
- implementation prompt ではない

今回の実施範囲:
- new package
  - `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\`
  を docs-only で作成する
- 作成対象:
  - `README.md`
  - `TASK.md`
  - `PROGRESS.md`
  - `ROLLBACK.md`
  - `EXECUTION_PROMPT.md`
- 追加で docs-only archive inventory を 1 本だけ作る
  - recommended path:
    - `C:\tetie\notecode\docs\archive_candidate_inventory_2026-04-18.md`
- production code / tests / AGENTS / WORKLOG / current package docs は編集しない
- actual archive は行わない

この再構築の目的:
- UI の記事種類と日本語ブログの責務を揃える
- source を role 分離する
- 自分の過去ブログ reuse を `fact` と `style_memory` に分けて設計する
- prompt accretion や局所 patch accumulation をやめる

新 package の固定テーマ:
- `ui article contract`
- `source role separation`
- `self-blog reuse policy`
- `minimal control axes for Japanese blog generation`

この作業のルール:
- プロンプトとモジュールの複雑化・肥大化は禁止
- 新規追加は可
  - ただし境界整理と rollback clarity に寄与する場合だけ
- 各作業は slice ごとに完了させる
- 各 slice 完了後に自己テストする
- エラー時は local self-fix を優先し、必要なら WEB検索も使って 3 回まで修正する
- 3 回失敗したら停止して user report

slice plan:
1. slice 1:
  - package docs 5 本を作成
2. slice 1 self-test:
  - 5 本の source-of-truth / package category / non-goals / do-not-retry / next step が整合しているか確認
3. slice 2:
  - archive candidate inventory note を作成
4. slice 2 self-test:
  - inventory が runtime code を actual archive 対象にしていないか確認
5. stop:
  - actual archive や code diff には進まない

new package objective guidance:
- UI article type を long prompt rule ではなく `article contract` に変換する
- source を `fact / continuity / style_memory` に分ける
- self-blog reuse を `continuity reuse` と `style memory reuse` に分ける
- 日本語ブログの自然さを、少数の control axes で説明できるようにする
- current packages の局所 retry を再開しない

recommended minimal control axes:
- `reader_task`
- `evidence_mode`
- `voice_distance`
- `opener_mode`
- `reuse_level`

new package non-goals:
- current package reopen
- opening_frame line の implementation 継続
- prompt accretion continuation
- fixed routing table
- category hardcode の増殖
- giant rewrite
- hidden reviser accumulation
- actual archive 実行

deadcode archive policy for this task:
- 今回やるのは inventory only
- archive candidate は docs / prompts / rolled-back experiment notes を優先
- production runtime code は candidate には書いてよいが `actual archive pending` と明記する
- current source-of-truth packages は archive candidate にしない

important package writing constraints:
- `naturalness_recovery_2026-04-07` は parked / not fixed として維持する
- `opening_frame_redesign_2026-04-18` は historical redesign line として参照のみ
- new package は UI/source/blog contract の上位問題設定に限定する
- exact code owner は `not fixed` と書く
- first code step は `not started`
- first implementation prompt を作らない

recommended package path:
- `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\`

recommended package docs structure:
- `README.md`
  - objective / read order / source-of-truth / current decision / package state / why / simplification direction / non-goals
- `TASK.md`
  - global rules / locked outcome / gates / stop gate / phase map / retry discipline
- `PROGRESS.md`
  - current goal / current status / hypothesis framing / owner scope / next phase
- `ROLLBACK.md`
  - baseline / rollback rule / inherited do-not-retry / archive policy / stop boundary
- `EXECUTION_PROMPT.md`
  - next startup canonical prompt path / docs-first next step only

recommended archive inventory contents:
- `archive-safe-now`
  - current prompt ではない historical docs / prompts
- `archive-later-after-confirmation`
  - production に近いが参照切れ確認が必要なもの
- `do-not-archive`
  - current source-of-truth
  - current runtime
  - current mainline 参照ファイル

WEB search policy:
- 原則不要
- local docs / local research / local source-of-truth だけで足りるなら使わない
- self-test で blocker が出た場合のみ WEB検索を使ってよい
- ただし 3 回失敗したら停止して報告する

final report must include:
1. 読んだ参照ルールファイル
2. 今回の実施範囲
3. 作成した package path
4. 作成した docs 5 本
5. archive inventory note path
6. package objective / non-goals
7. deadcode archive policy
8. self-test 内容と結果
9. WEB検索を使ったかどうか
10. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
