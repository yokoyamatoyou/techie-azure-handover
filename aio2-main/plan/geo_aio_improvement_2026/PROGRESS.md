# コトミガキ GEO/AIO改善計画 進捗管理

調査日: 2026-02-27
調査根拠: `aio2-main/WORKLOG.md` の 2026-02-27 ベストプラクティス調査結果

---

## フェーズ一覧

| Phase | タイトル | 優先 | 状態 | 主な変更ファイル |
|-------|---------|------|------|----------------|
| P01 | 緊急修正（DEBUGプリント除去 + Intent係数修正） | 🔴 高 | ✅ 完了 | `scoring_engine.py` |
| P02 | 文中E-E-A-T検出強化（日本語対応） | 🔴 高 | ✅ 完了 | `aio_analyzer.py` |
| P03 | GEO基本指標の追加（TL;DR・統計密度） | 🟠 中高 | ✅ 完了 | `aio_analyzer.py`, `core/ui/tabs/aio_tab.py` |
| P04 | スコア体系の精緻化（YMYL修正・GEO独立表示） | 🟡 中 | ✅ 完了 | `scoring_engine.py`, `core/ui/reports/executive_summary.py` |
| P05 | 多AI対応（プラットフォーム別引用予測） | 🟡 中 | ✅ 完了 | `aio_analyzer.py`, `aio_tab.py`, `aio_suggestions.py` |

---

## ステータス凡例

- ⬜ 未着手
- 🔄 作業中
- ✅ 完了
- ❌ ブロック中

---

## 完了条件（全体）

- [ ] `py -m pytest` または `python -m py_compile` で全対象ファイルがエラーなし
- [ ] `scoring_engine.py` のDEBUGプリントが0件
- [ ] AIO分析スコアのinformational補正が正方向になっている
- [ ] 日本語E-E-A-T検出が JSON-LD なしのサイトでも0点以外を返せる
- [ ] GEO関連スコア（TL;DR/統計密度）がUIに表示される
- [ ] WORKLOG.md に各Phase完了記録が追記されている

---

## 実施順序の方針

1. **P01を最初に実施**（デバッグ出力が他Phaseのテストに干渉するため）
2. P02 → P03の順（E-E-A-T検出結果をGEOスコアが参照するため）
3. P04・P05は独立しており並行可

---

## 参照ファイル

| 資料 | パス |
|------|------|
| 調査レポート（本計画の根拠） | `aio2-main/WORKLOG.md` の 2026-02-27 |
| Phase詳細 | `plan/geo_aio_improvement_2026/phase01_*.md` 〜 `phase05_*.md` |
| スコア実装 | `core/scoring_engine.py` |
| AIO分析コア | `core/aio_analyzer.py` |
| 統合エンジン | `core/engine/orchestrator.py` |
| UI表示 | `core/ui/panels.py`, `core/ui/tabs/aio_tab.py` |
