# management prompt ui source blog contract redesign rebuild 2026-04-18

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
- C:\tetie\notecode\docs\opening_frame_redesign_research_synthesis_note_2026-04-18.md
- C:\tetie\notecode\docs\opening_frame_minimal_control_comparison_note_2026-04-18.md
- C:\tetie\notecode\docs\opening_frame_pipeline_control_surface_triage_note_2026-04-18.md
- C:\tetie\notecode\research\新しいフォルダー (3)\00_external_ai_research_request_zero_base_ui_source_blog_algorithm_2026-04-18.md
- C:\tetie\notecode\research\新しいフォルダー (3)\08_external_ai_research_response_zero_base_ui_source_blog_algorithm_2026-04-18.md
- C:\tetie\WORKLOG.md

今回の依頼種別:
- management prompt
- `UI_SOURCE_BLOG_CONTRACT_REDESIGN_REBUILD`
- implementation prompt ではない
- current package reopen prompt ではない

今回の目的:
- 開発体制を `局所 symptom 修正` から `UI / source / self-blog reuse 契約` の docs-first 再設計へ切り替える
- 指示ウインドウとして、新しい docs-only line を定義し、作業ウインドウへ narrow な開始 prompt を 1 本だけ渡す
- current packages を壊さず、deadcode archive は inventory-only までに留める

current fixed read:
- `naturalness_recovery_2026-04-07` は parked / not fixed
- `opening_frame_redesign_2026-04-18` は docs-first line だが、さらに上位の `UI -> source -> blog contract` 再設計が必要になった
- external research response は
  - article contract
  - source role separation
  - self-blog reuse policy
  - opener frame
  - writer / guard boundary
  の再分離を支持している

このウインドウの役割:
- new top-level redesign line が必要かを管理判断する
- package objective / non-goals / archive policy を固定する
- 作業ウインドウ用 prompt を 1 本だけ作る
- production code には進まない

今回の実施範囲:
1. `UI article contract redesign` が new package として必要かを判断する
2. 必要なら package theme / non-goals / do-not-retry inheritance を fixed する
3. deadcode archive policy を fixed する
4. 作業ウインドウ用の docs-only 開始 prompt を 1 本だけ作る

今回のルール:
- プロンプトとモジュールの複雑化・肥大化は禁止
- 新規追加は可
  - ただし境界を明確化し、既存複雑性を増やさない場合だけ
- 各作業は slice ごとに閉じる
- 各 slice 完了後に自己テストする
- エラー時は local self-fix を優先し、必要なら WEB検索も使って 3 回まで修正する
- 3 回失敗したら停止して user report

deadcode archive policy:
- 今やるのは actual archive ではなく `archive candidate inventory` まで
- 先に archive してよい候補:
  - rollback 済みで current prompt ではない docs
  - historical implementation prompts
  - experiment notes のうち source-of-truth ではないもの
- 今 archive しないもの:
  - production runtime code
  - current source-of-truth packages
  - current mainline に参照される file
- 目的:
  - mainline を痩せさせる前に、archive safety を docs で確定する

判定すべきこと:
1. new package を切るか
2. package 名を何にするか
3. objective を何にするか
4. non-goals を何にするか
5. deadcode archive をどこまでやるか
6. 作業ウインドウの first slice を何にするか

期待する結論:
- new package:
  - `ui_source_blog_contract_redesign_2026-04-18`
- first line:
  - docs-only
- first work slices:
  - package docs 5 本
  - archive candidate inventory note 1 本
- actual archive:
  - not yet

このウインドウでやらないこと:
- production code 実装
- tests 実装
- current package reopen
- opening_frame line の implementation prompt 作成
- actual archive 実行
- broad rewrite

stop conditions:
- current package reopen と実質同じ判断しか出ない
- package theme が広すぎて docs-first に閉じない
- actual archive を今やりたくなった
- 複数 worker 向けの実装 prompt を作りたくなった

最終成果物:
- current state summary
- new package judgment
- deadcode archive policy judgment
- 作業ウインドウ向け prompt path

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 今回の実施範囲
3. new package を切るかどうか
4. package 名 / objective / non-goals
5. deadcode archive policy
6. 作成した作業ウインドウ prompt
7. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
8. WEB検索を使ったかどうか
```
