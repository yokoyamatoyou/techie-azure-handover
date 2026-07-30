以下をそのまま Codex に渡してください。

---

参照ルールファイル:
- `C:\tetie\AGENTS.md`
- `C:\tetie\aio2-main\AGENTS.md`
- `C:\tetie\aio2-main\ALGORITHM.md`
- `C:\tetie\aio2-main\WORKLOG.md`
- `C:\tetie\aio2-main\plan\CURRENT_AND_NEXT_IMPROVEMENTS.md`
- `C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\PROGRESS.md`
- `C:\tetie\aio2-main\plan\ui_design_followup_2026-04-07\README.md`

前提:
- `plan/seo_llmo_coverage_2026-04-06/` は Phase 1-9 完走済み
- SEO / LLMO coverage のロジック追加は今回の対象外
- 今回は UI デザイナー視点の整理を行う
- `score formula / legal meaning / provider meaning` は変えない
- `C:\tetie\zip` は変更しない

今回の実施範囲:
- `実装・設定` の情報階層を 3 層に再整理する
- `SEO改善` タブを status 順の優先表示にする
- saved run fallback note と実データ表示の区別を分かりやすくする
- `健康診断系` と `実装指示系` の視覚言語を分ける
- status 表現をトップから詳細まで統一する

開始時に必ず読むファイル:
1. `C:\tetie\AGENTS.md`
2. `C:\tetie\aio2-main\AGENTS.md`
3. `C:\tetie\aio2-main\WORKLOG.md`
4. `C:\tetie\aio2-main\plan\CURRENT_AND_NEXT_IMPROVEMENTS.md`
5. `C:\tetie\aio2-main\plan\seo_llmo_coverage_2026-04-06\PROGRESS.md`
6. `C:\tetie\aio2-main\plan\ui_design_followup_2026-04-07\README.md`

実行方針:
- まず local context のみで narrow fix を設計する
- owner file を越える refactor はしない
- first view を過密化させない
- summary-first を維持する
- 実装前に現状 UI 構造を確認し、変更意図を短く述べる
- 実装後は compile / targeted pytest / live verify を行う
- live verify は `http://127.0.0.1:8081/` と `http://127.0.0.1:8081/runs/84` の両方で行う

主な対象ファイル:
- `nicegui_app.py`
- `core/ui/panels.py`
- `core/ui/tabs/seo_tab.py`
- `core/ui/tabs/health_tab.py`
- `core/application/analysis_run_service.py`

最低限の受け入れ条件:
- `参考` が `注意` より強く見えない
- `SEO改善` タブで `要対応` が先頭に来る
- `実装・設定` で「今やること」と「参考」が混ざって見えない
- saved run の fallback note が旧データ由来だと分かる
- compile / targeted pytest / live verify が green

最終報告で必ず示すこと:
- 参照ルールファイル
- 今回の実施範囲
- 実施内容
- テスト結果
- live verify 結果
- 失敗回数
- 次アクション
- AGENTS/WORKLOG更新の要否

---
