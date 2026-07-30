# ux_heuristic_audit_followup_2026-04-13 EXECUTION PROMPT

## autonomous_start_prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\aio2-main\AGENTS.md
- C:\tetie\aio2-main\ALGORITHM.md
- C:\tetie\aio2-main\WORKLOG.md
- C:\tetie\aio2-main\plan\CURRENT_AND_NEXT_IMPROVEMENTS.md
- C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\README.md
- C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\TASK.md
- C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\PROGRESS.md
- C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\README.md
- C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\TASK.md
- C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\PROGRESS.md
- C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\ROLLBACK.md
- C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\EXECUTION_PROMPT.md

今回の実施範囲:
- 2026-04-13 の UX / マーケティング監査で見つかった P1/P2 を phase 単位で解消する
- `analysis logic / score meaning / legal meaning` は変更しない
- 別ウインドウで 1 phase ずつ進め、自己テストが green のときだけ次 phase へ進む
- 完了時は Codex 自身も視認で UI 原則チェックを行い、文字サイズ、文字のはみ出し、折り返し崩れ、色コントラスト、focus 可視性、モバイル崩れまで確認する

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\aio2-main\AGENTS.md
3. C:\tetie\aio2-main\ALGORITHM.md
4. C:\tetie\aio2-main\WORKLOG.md
5. C:\tetie\aio2-main\plan\CURRENT_AND_NEXT_IMPROVEMENTS.md
6. C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\README.md
7. C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\TASK.md
8. C:\tetie\aio2-main\plan\ux_commercial_readiness_2026-04-05\PROGRESS.md
9. C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\README.md
10. C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\TASK.md
11. C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\PROGRESS.md
12. C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\ROLLBACK.md
13. C:\tetie\aio2-main\plan\ux_heuristic_audit_followup_2026-04-13\EXECUTION_PROMPT.md

最初にやること:
1. `PROGRESS.md` の `Current phase` と `Phase Ledger` を読む
2. `TASK.md` で current phase の owner / objective / required checks を確認する
3. 対象 owner file だけを読む
4. phase を 1 つだけ進める
5. 自己テストを行う
6. `PROGRESS.md` を更新する
7. gate green なら次 phase へ進む
8. gate red なら同一 phase 内で最大 3 回まで修正する

実装優先順:
1. Phase 1 baseline and success lock
2. Phase 2 input guardrails
3. Phase 3 analysis control recovery
4. Phase 4 dashboard value proposition
5. Phase 5 workspace IA simplification
6. Phase 6 implementation/reference split
7. Phase 7 verification and closeout

shared checks:
- C:\tetie\aio2-main\.venv\Scripts\python.exe -m py_compile nicegui_app.py core\ui\dashboard.py core\ui\panels.py core\application\analysis_run_service.py
- C:\tetie\aio2-main\.venv\Scripts\pytest.exe -q tests\test_dashboard_ui.py tests\test_characterization_ui.py tests\test_analysis_run_service.py tests\test_executive_summary.py

live verify:
- C:\tetie\techie-hub\start.bat force
- http://127.0.0.1:8081/
- http://127.0.0.1:8081/runs/84

各 phase 完了時の自己テスト:
1. compile を実行する
2. 対象 pytest を実行する
3. live route を開いて desktop と mobile 相当で確認する
4. Codex 自身が視認で次を確認する
   - 文字サイズが小さすぎないか
   - タイトル、ボタン、タブ、チップ、入力欄の文字がはみ出していないか
   - 折り返しや省略で意味が壊れていないか
   - テキストと背景の色コントラストが弱すぎないか
   - focus ring や hover が見えるか
   - CTA の優先順位が視覚的に分かるか
   - desktop / mobile で card や table が崩れていないか
   - `保存済みワークスペース` と `履歴` の主導線が迷わないか
5. 問題があれば同一 phase 内で修正してから再テストする
6. pass したら `PROGRESS.md` に evidence を残す

phase ごとの狙い:
- Phase 2:
  - main URL / competitor URL の事前エラー防止
- Phase 3:
  - cancel または stay-on-page / auto-open control の導入
- Phase 4:
  - dashboard 上段を価値訴求面に置き換える
- Phase 5:
  - saved workspace の primary navigation を軽くする
- Phase 6:
  - `実装・設定` の actionable / reference を分ける

重要制約:
- score や判定意味を変えない
- reference 情報は削除ではなく後退配置で扱う
- `履歴と比較` と `FAQ` は残す
- cancel 実装が analysis core を巻き込むなら、先に `自動で開かない` など narrow fix を入れてよい

自律進行ルール:
- 各 phase は `実装 -> 自己テスト -> 視認チェック -> PROGRESS 更新` の順で進める
- gate green なら user に聞かず次 phase へ自動で進む
- ただし stop condition に触れた場合だけ停止して user に報告する
- unrelated refactor や scope 拡張はしない
- visual regression を見つけた場合は、その phase の未完了として扱う

失敗時ルール:
- まず local context だけで narrow fix を試す
- それでも仕様が確定しない場合のみ Web 検索を使う
- Web 検索は同一 failure につき最大 3 回
- query / source / tried fix / result を `PROGRESS.md` Failure Log に残す
- local repair 3 回 + Web 検索を含む修正試行 3 回でも可決できなければ停止する
- 停止時は failure summary、試した修正、残る原因、ユーザー判断が必要な点を report する

最終報告で必ず示すこと:
- 参照ルールファイル
- 今回の実施範囲
- current phase
- 実施内容
- テスト結果
- 視認チェック結果
- failure 回数
- web search 回数
- 次アクション
- AGENTS / WORKLOG 更新の要否
```
