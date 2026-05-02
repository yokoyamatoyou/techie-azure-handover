# コトメイク新アルゴリズム実装計画（Phase分割）

## 0. 目的と適用範囲
- 目的: `notecode` の文章生成パイプラインをゼロベースで再設計し、現行UIの形を維持したまま、生成品質・安全性・保守性を改善する。
- UI方針: 画面レイアウトは維持。不要機能はニールセン10原則・ヒックの法則に従い削除または一時非表示。
- 本計画の成果物: フェーズ別実装手順、自己テスト、LLM脆弱性テスト、依存関係脆弱性確認、ロールバック条件。

## 1. 固定仕様（確定済み）
- 記事タイプ（表示名 / 内部キー）
  - 解説 `explanatory_article`
  - 日常 `daily_story`
  - ブランド `branding`
  - お知らせ `announcement`
  - 事例 `case_study`
  - 業界分析 `industry_analysis`
  - 比較レビュー `comparative_review`
- `daily_story` のSEO差分は `input_contract` 正規化で `style_compact_for_seo=true` を明示（UI入力項目は増やさない）。
- 最小UIの必須3要素
  - 記事種類セレクタ
  - 記事生成実行（生成ボタン + 結果表示）
  - 画像生成（TOP/本文向け）
- 旧依存UIは原則削除。影響不明かつ移行リスク高は1リリースのみ非表示。
- UI整理の運用: 先に現行UIを維持して新アルゴリズムを安定化し、その後に実ログ根拠で不要項目を削除する。
- 生成後リーガル導線は「自動実行 + 任意再実行」。
- ログ互換性は準厳密互換（主要キー維持 + 追加キーで拡張）。

## 2. 実行順序
1. Phase01: スコープ固定・UI項目対応表・契約定義
2. Phase02: 承認後archive整理手順の確定と実行準備
3. Phase03: 新生成パイプライン最小実装
4. Phase04: UI接続（3要素中心）と不要UI整理
5. Phase05: 編集1層 + 生成後リーガル + 安全試験
6. Phase06: 監査/ログ互換 + 依存脆弱性確認
7. Phase07: 受入試験・移行判定・ロールバック確定

## 2.1 実行プロトコル（他AI向け）
- 各Phaseは `Input -> Steps -> Deliverables -> Exit Criteria -> Tests -> Rollback` の順で実行する。
- Exit Criteria を満たさない限り次Phaseへ進まない。
- 不明点が出た場合は実装を止め、`PROGRESS.md` の `Open Questions` に追加する。
- 変更時は同日に `C:\tetie\WORKLOG.md` へ追記する。

## 3. 品質ゲート（全Phase共通）
- 自己テスト: 実装範囲の正常系/異常系を最低1件ずつ実行。
- LLM脆弱性テスト: プロンプト注入、越権命令、危険出力誘導を検証。
- パイプライン精査: 入力契約から出力ログまでのデータ流れを確認。
- モジュール/依存脆弱性: 依存棚卸し、既知脆弱性、復元手順を点検。
- ロールバック条件: 各Phaseで「戻す条件」と「戻し先」を明記。

## 4. 生成パイプラインの目標構成
- `input_contract.py`: 入力正規化（article_type, media, style flags）
- `discourse_planner.py`: 記事タイプ別構成計画
- `section_generator.py`: セクション生成
- `dedupe_adapter.py`: semantic_dedupe呼び出し
- `editor_guard.py`: 軽量編集1層（重複/文法/AIぽさ）
- `legal_postcheck.py`: 生成後リーガル（自動 + 任意再実行）
- `output_formatter.py`: 出力整形
- `telemetry_writer.py`: 既存互換ログ出力

## 5. 承認後archive整理（必須章）
- 実装着手前に以下を順序実行:
  1. archive先ディレクトリ作成（`notecode/archive/zero_base_rebuild_YYYY-MM-DD/`）
  2. archive対象コードを `code/` に移動（構造維持）
  3. WORKLOGを圧縮し `worklog/` に退避
  4. 復活手順メモを `restore_guide.md` として保存
  5. 移動漏れ・import参照切れを検証
- 実行後確認:
  - 必須3UI要素が動作
  - 新パイプラインの最小生成が通る
  - 主要ログキーが維持される

## 6. ドキュメント導線
- 実行管理: `PROGRESS.md`
- フェーズ詳細: `phase01_*.md` 〜 `phase07_*.md`
- 判定記録: 各phaseの「テスト結果」節に記載
- 初期テンプレート:
  - `ui_mapping_table.md`
  - `article_type_matrix.md`
  - `input_contract_draft.md`
