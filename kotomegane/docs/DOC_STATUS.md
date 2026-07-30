# Document Status

## Recommended Read Order

1. `AGENTS.md`
   - この repo の運用入口
2. `docs/CURRENT_STATE_2026-03-30.md`
   - 現在の実装状態
3. `docs/DOC_STATUS.md`
   - 文書の位置づけ
4. `docs/SAAS_IMPLEMENTATION_PLAN_2026-04-03.md`
   - `kotomegane` 単体の SaaS 実装計画
5. `docs/LLM_BATCH_AND_CACHE_RULES_2026-04-05.md`
   - LLM Batch / prompt cache / provider差分の運用ルール
6. `docs/DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md`
   - `kotomegane` のデザイン適用計画
7. `docs/UI_VALUE_REDESIGN_PLAN_2026-04-10.md`
   - URL の意味づけ、価値訴求、他社参考を含む UI 改修計画
8. `docs/UI_REDUCTION_IMPLEMENTATION_PLAN_2026-04-14.md`
   - first view の削減、色統一、文言置換、overflow 対策の実装用 plan
9. `docs/COMPETITIVE_VALUE_VISUALIZATION_PLAN_2026-04-24.md`
   - 既存アルゴリズムを変えず、競合比較・引用元影響・負け質問を低認知負荷で見せるための実装 plan
10. `docs/UI_UX_REFACTOR_PLAN_2026-05-23.md`
   - 非エンジニア視点の UI/UX 診断 issue を細かい owner package に分ける実装計画
11. `docs/SCHEDULE_UI_CHANGE_2026-05-23.md`
   - 自動定期分析の曜日チェックボックス化、旧UI挙動、複数質問/複数曜日登録、3質問実行時の guardrail 挙動の現在仕様
12. `docs/OPENAI_RUNTIME_NOTES.md`
   - OpenAI runtime note
13. `README.md`
   - セットアップ / 起動

## Current Source Of Truth

### Repo Operation

- `AGENTS.md`
  - 運用入口
- `docs/CURRENT_STATE_2026-03-30.md`
  - 実装現在値
- `README.md`
  - セットアップ / 起動

### Product Plan

- `docs/SAAS_IMPLEMENTATION_PLAN_2026-04-03.md`
  - `kotomegane` 単体の実装計画
- `docs/LLM_BATCH_AND_CACHE_RULES_2026-04-05.md`
  - Batch、prompt cache、provider差分の current rule
- `docs/DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md`
  - `kotomegane` のデザイン適用計画
- `docs/UI_VALUE_REDESIGN_PLAN_2026-04-10.md`
  - URL の意味づけ、主結果の価値説明、内部処理の退避方針を含む改修計画
- `docs/UI_REDUCTION_IMPLEMENTATION_PLAN_2026-04-14.md`
  - first view の削減、suite 色統一、input/result copy 更新、overflow hardening の実装 plan
- `docs/COMPETITIVE_VALUE_VISUALIZATION_PLAN_2026-04-24.md`
  - 共通ヘッダを維持し、新アルゴリズムなしで競合比較・引用元影響・負け質問を可視化する実装 plan
- `docs/UI_UX_REFACTOR_PLAN_2026-05-23.md`
  - UI/UX 診断 issue を owner package、実装順、検証条件へ分解する current implementation plan
- `docs/SCHEDULE_UI_CHANGE_2026-05-23.md`
  - 自動定期分析の曜日 UI、保存仕様、3質問実行時の guardrail current rule

### Session Notes

- `docs/session_notes/**`
  - 次回再開 prompt、作業メモ、時点依存の session 用資料

### Cross Product Reference

- `docs/cross_product/TECHIE_SUITE_PLATFORM_PLAN_2026-04-05.md`
  - Azure移行、3製品共通基盤、価格未確定の扱い
- `docs/cross_product/UI_UNIFICATION_PLAN_2026-03-31.md`
  - 3製品を同一 SaaS 群として見せる UI 方針
- `C:\tetie\techie-hub\DESIGN_SYSTEM_PLAN_2026-04-01.md`
  - TECHIE 共通デザイン正本

### External Handover

- `external_engineer_handover_2026-04-05/`
  - 外部エンジニア向けの最小共有パッケージ

## Reference Documents

- `docs/FEATURE_SUMMARY_2026-04-03.md`
  - 現行機能の要約
- `docs/OPENAI_RUNTIME_NOTES.md`
  - OpenAI 起点の runtime note
  - provider横断の current rule は `LLM_BATCH_AND_CACHE_RULES_2026-04-05.md` を優先
- `deep-research-report (11).md`
  - 参考仕様
  - 現行コードと完全一致する前提では使わない
- `C:\tetie\kotomegane\Saa S基盤設計.docx`
  - Azure / SaaS 基盤の元資料
  - markdown 正本は `docs/cross_product/TECHIE_SUITE_PLATFORM_PLAN_2026-04-05.md`

## Legacy Documents

- `archive/2026-03-30-ai-traffic-analytics/**`
  - 旧アプリ仕様、旧コード、旧マニュアル

## Outdated External Entry

- `C:\tetie\AGENTS.md`
  - 全体入口としては有効
  - ただし `kotomegane` の説明が旧 AI トラフィック解析のまま
  - `kotomegane` 作業ではこの repo の `AGENTS.md` を優先する

## Current Documentation Rule

- docx は参考に留め、運用判断は markdown に寄せる
- `Batch / prompt cache / provider差分` は `docs/LLM_BATCH_AND_CACHE_RULES_2026-04-05.md` に集約する
- `docs/` 直下には `kotomegane` 本体の正本を残す
- セッション用メモは `docs/session_notes/` に寄せる
- Azure移行と横断資料は `docs/cross_product/` に寄せる
- 料金プランは検討中のため、正式 source of truth をまだ置かない


