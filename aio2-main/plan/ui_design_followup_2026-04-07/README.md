# UI Design Follow-up 2026-04-07

最終更新: 2026-04-07  
対象: `C:\tetie\aio2-main`

## 背景

- `plan/seo_llmo_coverage_2026-04-06/` は Phase 1-9 を完走済み
- SEO / LLMO の追加監査は実装・テスト・live verify まで完了
- 次の関心事は「機能追加後の UI が、UI デザイナー視点でどこまで整理されているか」

## 現在の判断

- 情報設計は良い
- summary-first の方針も維持できている
- ただし、視覚ヒエラルキーと重要度表現はまだ改善余地がある

## 次回の目的

- 機能は増やさず、既存 UI の見せ方を改善する
- first view を過密化させない
- `score formula / legal meaning / provider meaning` は変えない
- 新規監査項目をそのまま全部強調せず、優先度順に見せる

## 優先順位 Top 5

1. `実装・設定` を `要対応 / 再分析で詳細化 / 参考` の 3 層に分ける
2. `SEO改善` タブを status 順の優先表示に変える
3. saved run で「実データなのか fallback note なのか」を明示する
4. `健康診断系` と `実装指示系` の視覚言語を分ける
5. `注意 / 要対応 / 通過 / 参考` の表現をトップから詳細まで統一する

## 主な対象ファイル

- `nicegui_app.py`
- `core/ui/panels.py`
- `core/ui/tabs/seo_tab.py`
- `core/ui/tabs/health_tab.py`
- `core/application/analysis_run_service.py`

## 非目標

- SEO / LLMO のロジック追加
- score 計算式の変更
- provider readiness の意味変更
- legal 判定基準の変更
- unrelated refactor

## 受け入れ基準

- 非開発者が `サマリー` と `やること` の後に迷わず `実装・設定` を読める
- `参考` が `注意` より強く見えない
- saved run fallback note が「旧データなので再分析推奨」と自然に理解できる
- `SEO改善` タブで「何から直すか」が 1 画面目で分かる
- live verify で `/` と `/runs/84` の両方に重大 regression がない

## 推奨の進め方

1. `C:\tetie\AGENTS.md` と `C:\tetie\aio2-main\AGENTS.md` を読む
2. `plan/seo_llmo_coverage_2026-04-06/PROGRESS.md` を読んで完走状態を確認する
3. `README.md` の Top 5 に対して、まず narrow fix の UI 案を決める
4. owner file のみで実装する
5. compile / targeted pytest / live verify を回す
6. 必要なら `WORKLOG.md` を更新する
