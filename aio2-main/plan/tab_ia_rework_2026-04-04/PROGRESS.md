# tab_ia_rework_2026-04-04 PROGRESS

## Current Goal

- `aio2-main` の分析後 UI を 5 タブ構成へ再編し、live / saved / snapshot を同じ情報設計で揃える

## Current Status

- Package status: planning
- Current phase: Phase 0 baseline inventory 固定
- Status: not started
- Next action:
  - `analysis_run_service.py` の snapshot 契約を先に拡張する
  - その後 `panels.py` の live / saved 両方を同じ 5 タブへ差し替える

## Core Decisions

- 上位タブは `サマリー / やること / 文章改善 / 実装・設定 / 履歴と比較`
- provider 状態は `実装・設定` のみ
- FAQ 内容案は `文章改善`
- FAQPage / schema / llms.txt は `実装・設定`
- `C:\tetie\zip` は参照のみ

## Risks

- snapshot 保存粒度を増やさないまま UI だけ変えると、saved workspace が再び薄くなる
- `文章改善` と `実装・設定` の境界を曖昧にすると再度重複する
- provider detail を 1 画面に寄せる際、説明文が増えすぎると逆に読みにくくなる
