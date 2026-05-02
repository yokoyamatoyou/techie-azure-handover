# コトミガキ 改善計画 PLAN2 — 進捗管理

作成日: 2026-02-27
前フェーズ: `plan/geo_aio_improvement_2026/` (P01〜P05 全完了)

---

## フェーズ一覧

| Phase | タイトル | 優先度 | 状態 | 主な変更ファイル |
|-------|---------|--------|------|----------------|
| P01 | バランスSliderバグ修正 + Intent alpha 復活 | 🔴 高 | ✅ 完了 | `scoring_engine.py`, `orchestrator.py` |
| P02 | メイン分析エラーUI + 空状態改善 | 🔴 高 | ✅ 完了 | `nicegui_app.py`, `core/ui/tabs/` |
| P03 | sitemap.xml メタデータ解析 | 🟡 中 | ✅ 完了 | `core/sitemap_analyzer.py`(新規), `orchestrator.py`, `executive_summary.py` |
| P04 | ビジネス目標パーソナライズ | 🟡 中 | ✅ 完了 | `nicegui_app.py`, `orchestrator.py`, `aio_suggestions.py` |
| P05 | アクセシビリティ対応 | 🟡 中 | ✅ 完了 | `core/ui/` 各ファイル |
| P06 | 内部リンク構造スコア | 🟢 低 | ✅ 完了 | `core/seo/internal_graph.py`, `orchestrator.py` |

---

## ステータス凡例

- ⬜ 未着手
- 🔄 作業中
- ✅ 完了
- ❌ ブロック中

---

## 完了条件（全体）

- [x] `py -m py_compile` で全変更ファイルがエラーなし
- [x] P01: intent=informational のサイトで統合スコアが AIO80% 寄りになる
- [x] P02: 分析失敗時にユーザー向けエラーメッセージが表示される
- [x] P03: sitemap.xml 保有サイトで「全Xページ中Y件分析」が経営サマリーに表示される
- [x] P04: ビジネス目標選択で表示される改善アクションの優先順位が変化する
- [x] P05: 主要スコアカードに aria-label が付与される
- [x] P06: 内部リンク数・孤立ページ数がサイトヘルスタブに表示される
- [x] WORKLOG.md に各Phase完了記録が追記されている

---

## 実施順序の方針

1. **P01を最初に実施** — スコア計算の根幹バグ。他の分析結果の信頼性に影響
2. **P02を次に実施** — エラー時にユーザーが詰まらないようにする
3. P03・P04 は独立しており並行可
4. P05 は小変更の集合なので隙間時間に実施可
5. P06 は P03（sitemap取得）完了後が望ましい

---

## 参照ファイル

| 資料 | パス |
|------|------|
| Phase詳細 | `plan/PLAN2/phase01_*.md` 〜 `phase06_*.md` |
| アルゴリズム仕様 | `AIO_ALGORITHM.md` |
| スコア実装 | `core/scoring_engine.py` |
| AIO分析コア | `core/aio_analyzer.py` |
| 統合エンジン | `core/engine/orchestrator.py` |
| クロール戦略 | `core/crawl_depth_strategy.py` |
| UIメイン | `nicegui_app.py` |
| UI共通 | `core/ui/panels.py` |
| AIOタブ | `core/ui/tabs/aio_tab.py` |
| 経営サマリー | `core/ui/reports/executive_summary.py` |
| 作業記録 | `WORKLOG.md` |
