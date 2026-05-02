# AGENTS

まず `C:\tetie\AGENTS.md` を先に確認し、全体方針と参照順を把握してから本ファイルを読むことを推奨します。

このファイルは、後日変更しやすいように構成と運用ルールをまとめたガイドです。

## 目的
- UI/アルゴリズム/レポートの変更点を整理し、再現性を確保する
- Streamlit → NiceGUI 移行後の入口を明確化する

## ディレクトリ構造（主要）
※ .venv / build / dist / obf_dist / obfuscated_src は省略。
```
aio2-main/
    - assets/
        - favicon.svg
    - core/
        - application/          # [NEW] NiceGUI向け分析実行・履歴保存のアプリケーション層
            - analysis_run_service.py  # 分析実行/履歴保存/result_path/snapshot JSON
            - csv_export_service.py    # 履歴一覧CSV/優先アクションCSV
        - engine/               # [NEW] 分析エンジンのコア
            - base_analyzer.py  # 共通初期化・ユーティリティ
            - orchestrator.py   # SEOAIOAnalyzer（current engine owner）
            - site_health_engine.py  # サイトヘルス統合
        - legal_checks/         # [NEW] 法務・コンプライアンス分析
            - commercial_transaction.py  # 特商法
            - consumer_protection.py     # 消費者保護（視認性/弁護士コメント）
            - premiums_labeling.py       # 景表法
            - stealth_marketing.py       # ステマ規制
            - visibility_checker.py      # 視認性チェック
        - monitoring/           # [NEW] monitoring JSON persistence
            - history_store.py  # outputs/monitoring の読み書き
        - site_health/          # [NEW] サイト健全性（UX/技術）
            - accessibility_checker.py   # アクセシビリティ
            - ogp_checker.py             # SNS最適化
            - security_checker.py        # セキュリティ
            - advice_generator.py        # パーソナライズ助言
        - storage/
            - database.py       # 履歴DB保存
        - structured_data/      # [NEW] 構造化データ支援
            - checker.py         # 構造化データ簡易チェック
        - aio_analyzer.py       # AIO定量スコア算出・Entity Linking (Modified 2026-01-29)
        - aio_suggestions.py    # プラットフォーム別アドバイス生成
        - citation_generator.py # [NEW] 引用スニペット抽出・マークアップ生成
        - constants.py          # 定数・ラベル定義
        - industry_detector.py  # 業界自動判定
        - knowledge_graph.py    # 知識グラフ連携・エンティティ正規化 (Modified 2026-01-29)
        - wikidata_client.py    # [NEW] Wikidata QID連携・キャッシュ
        - model_selector.py     # LLMモデル選択
        - platform_detector.py  # [NEW] プラットフォーム(CMS)自動検知
        - robots_analyzer.py    # AIクローラー適合性/SSR/マルチモーダル分析
        - scoring_engine.py     # 統合スコア計算
        - sitemap_analyzer.py   # [NEW] sitemap.xml メタデータ解析（URL/lastmod）
        - scraper.py            # Webスクレイピング/robots.txtチェック
        - term_glossary.py      # [NEW] 専門用語グロッサリー
        - token_tracker.py      # トークン使用量追跡
        - visualization.py      # 可視化ヘルパー
        - ui/                   # [NEW] UIコンポーネント
            - panel_context.py  # panels向け dependency context
            - tabs/             # [NEW] タブ別表示ロジック
                - aio_tab.py
                - seo_tab.py
                - health_tab.py
                - industry_tab.py
                - simulation_tab.py
                - comparison_tab.py
            - reports/
                - executive_summary.py
            - detail_panels.py  # 法務チェック深掘り表示
            - panels.py         # UIパネル描画（分割）
        - evidence_pipeline.py # [NEW] 証拠収集・正規化・重複統合パイプライン
    - outputs/
        - monitoring/
        - reports/
    - PDFreport/
        - sections/                  # [NEW] PDFセクション描画
        - high_quality_pdf_generator.py  # PDF生成
        - improved_commentary_generator.py  # [NEW] AI解説文改善
        - site_health_pdf.py             # [NEW] サイトヘルスページ生成
        - pdf_data_mapper.py             # 分析データ→PDF形式変換
        - reporting.py
    - nicegui_app.py       # UIメイン (NiceGUI)
    - seo_aio_engine.py    # 後方互換プロキシ（engine移行済み）
    - run_app.py           # EXE化用エントリポイント
    - simple_start.bat     # 簡易起動スクリプト
    - requirements.txt
    - WORKLOG.md
```

## エントリポイント
- UI起動: `nicegui_app.py`
- EXE起動: `run_app.py`
- バッチ起動: `simple_start.bat`

## 起動方法
- `simple_start.bat`
- `python run_app.py`
- `python nicegui_app.py`

## UI構成（NiceGUI）
- `/` : enterprise dashboard
    - 上部: brand header + 新規分析カード
    - 中段: KPI 3 件まで
    - 下段: 検索 / ソート / 履歴一覧CSV を持つ history data table
    - 主導線: run 保存後に `/runs/{run_id}` へ移動
- `/runs/{run_id}` : saved detail workspace
    - 上部: URL / AI認識 / SEO / 総合優先度 / 最優先3件 / 前回比
    - 本文: `概要 / AI認識改善 / SEO改善 / 履歴 / 技術補足`
    - fixed/reference 情報は expansion 内へ後退
- `/report/print` : 削除済み。route / renderer / export service とも current flow には存在しない

## アルゴリズム図・人間向けREADME
- **現在のアルゴリズムの流れ図・モジュール一覧**: `Notebook/README.md`（人間向け説明）
- アルゴリズムのみのコピーは `Notebook/core/` にあり、UI・履歴DB・レポート描画は含まない（54ファイル）。本番はルートの `core/` を参照。

## スコア/アルゴリズム関連
- SEO/AIOのコア計算: `core/engine/orchestrator.py`（`seo_aio_engine.py` は後方互換プロキシ）
- NiceGUIの分析実行・履歴保存・saved detail rehydrate: `core/application/analysis_run_service.py`
- CSV出力の責務境界: `core/application/csv_export_service.py`
- monitoring JSON保存: `core/monitoring/history_store.py`
- UI依存注入の境界: `core/ui/panel_context.py` / `core/ui/panels.py`
- AIO定量スコア: `core/aio_analyzer.py` (※NLPコア: SudachiPy Mode A/B/C)
- **Entity Linking**: `core/aio_analyzer.py` の `calculate_entity_linking()`
  - Sudachi品詞判定（pos[1]=='固有名詞'）ベースで100万語+対応
  - カテゴリ別重み付け（人名/地名/組織）: `core/knowledge_graph.py`
  - 補完辞書（ChatGPT, E-E-A-T等の新語）: `SUPPLEMENTARY_ENTITIES`
  - 表記ゆれ検出・正規化: `normalize_entity()`, `group_entities_by_normalized()`
  - **Wikidata QID連携（任意）**: Top3のみAPI検索＋30日キャッシュ（`ENABLE_WIKIDATA`, `WIKIDATA_TOP_K`）
- 統合スコア: `core/scoring_engine.py`
- 定性アドバイス: `core/aio_suggestions.py`
- 詳細仕様: `C:\tetie\aio2-main\ALGORITHM.md`
  - LLMリライトは構造化サマリー（見出し/箇条書き/FAQ/表）を併用して精度を上げる
  - LLM温度は0.3（再現性優先）

## プラットフォーム対応
- **対応プラットフォーム**: WordPress, Wix, Shopify, Amazonマーケットプレイス, 楽天市場, Yahoo!ショッピング, その他CMS/サイト作成サービス
- **プラットフォーム別アドバイス**: `core/aio_suggestions.py` に各プラットフォーム向けの技術アドバイスを実装
- **プラットフォーム検出**: `core/platform_detector.py` で自動検知
- **更新元データ**: `core/platform_guidance.py` を単一情報源（SSOT）として運用
  - `verified_at`（最終確認日）と `source_links`（公式ドキュメントURL）を保持する
  - 更新周期の目安: 月1回（または主要プラットフォームの仕様変更を検知したタイミング）
  - 更新時は `WORKLOG.md` に「確認対象・差分・確認日」を必ず記録する
- **ECプラットフォーム特化機能**:
  - 楽天市場・Yahoo!ショッピング向け特商法リンク検出強化 (`core/legal_checks/commercial_transaction.py`)
  - 左カラム・ナビゲーション領域の特商法リンク検出に対応
  - プラットフォーム固有のDOM構造（leftContents, shopinfo, SearchHeader, storeDesign等）に対応

## 法務チェック機能
- **法務チェック深掘り分析**: `core/evidence_pipeline.py` による証拠収集・正規化・重複統合
- **対応法規**: 特商法、景表法、ステマ規制、視認性チェック
- **深掘り表示**: `core/ui/detail_panels.py` で重要度別（重要/注意/参考）に分類表示

## AI予測機能
- **引用スニペット生成**: `core/citation_generator.py` で高精度な引用候補抽出とJSON-LD speakableマークアップ生成
- **UI表示**: 「引用候補」タブでスニペットカードを表示（AI回答シミュレーションは削除）

## エクスポート
- 履歴一覧CSV: `core/application/csv_export_service.py::export_history_csv`
- 優先アクションCSV: `core/application/csv_export_service.py::export_priority_actions_csv`
- spreadsheet formula injection 対策: `sanitize_csv_cell`
- PDF / print route と export service は current flow から削除済み

## 変更ルール（推奨）
- UI変更は `nicegui_app.py` を起点に実施
- スコア式の変更は `C:\tetie\aio2-main\ALGORITHM.md` と同時更新
- エラー表示は日本語で簡潔に（英語は注釈）
- ニールセンの10原則（Nielsen 10 Heuristics）をUI変更時に確認

## 現状整理・改善方針（2026-02-02）
- **plan/CURRENT_AND_NEXT_IMPROVEMENTS.md**: 改修計画の解像度評価と「次の改修」候補を1か所にまとめた入口。業界分析に結合HTMLを渡す、PDF入力保証と空セクション文言、ロール別タブ、review Phase 2–5 の扱いを記載。履歴参照: `archive/20260207/aio2-main/STATUS_AND_IMPROVEMENTS.md`（リーガル/PDF/UI/ユーザー属性の詳細）。

## 変更履歴
- **2026/03/30**: `現状 / 改善方法` 優先の narrow fix を追加
  - 作業ウィンドウのタブを `現状 / 改善方法 / 詳細 / 内部診断` に整理し、`固定の参考情報` を主画面から除去
  - 具体候補が未生成の箇所では汎用テンプレートへ逃がさず、当該URLに対する不足と次アクションだけを表示
  - `nicegui_app.py` の `ui.timer` を非DOMの async loop に置き換え、`parent slot deleted` 系の UI ログノイズを抑える方向へ調整
- **2026/03/30**: overview-first の追加調整を実施
  - `ろごSV.svg` を static 側へ反映し、`TECHIE / コトミガキ` のブランドヘッダーを簡潔な構成へ整理
  - 主画面の常設説明を削減し、`現状` / `改善方法` を優先。補足説明は info アイコンのツールチップへ退避
  - `core/ui/panels.py` と `core/ui/reports/executive_summary.py` の見出し説明を圧縮し、`根拠` 呼称を `詳細` へ変更
- **2026/03/30**: ブランド表示と言語統一の narrow fix を追加
  - `nicegui_app.py` のトップを `TECHIE / コトミガキ` の日本語中心ヘッダーへ変更し、ロゴの余白と役割説明を強化
  - `core/ui/reports/executive_summary.py` と `core/ui/panels.py` で `今回の分析結果 / あなた向けの改善提案 / 固定の参考情報` の境界が一目で分かる見出しへ整理
  - 印刷版でも `あなた向けの改善提案` を先に読めるように順番とラベルを調整
- **2026/03/30**: SaaSレイアウト整理と固定説明の後退を実施
  - `nicegui_app.py` を `入力コントロール → 要約ストリップ → 作業ウィンドウ` の縦構成へ再編し、詳細設定/競合入力を折りたたみ化
  - 分析完了後に要約へ自動スクロールするよう変更し、初回判断を先に出す導線へ調整
  - `core/ui/panels.py` で `内部診断・補足` と `参考テンプレート` を分離し、URL固有でないテンプレートを改善プラン本体から退避
  - `core/ui/tabs/aio_tab.py` で `penalty_multiplier=1.0` 時の式表示を抑制し、provider詳細を expansion 化
  - `core/ui/tabs/health_tab.py` の `llms.txt` ベストプラクティスを折りたたみ化
  - `/report/print` の shell owner を `core/ui/reports/print_report.py` に寄せた
- **2026/03/29**: アルゴリズム監査に基づく UI 再編と文言整合を実施
  - `core/scoring_engine.py` の YMYLペナルティ条件を `is_ymyl_context and AIO E-E-A-T < 4.0` に整理
  - `nicegui_app.py` を SaaS 風の 3役割レイアウトへ再編（入力 / 要約 / 作業）
  - `core/ui/panels.py` で URL固有所見と一般説明・システム補足を分離
  - `core/ui/tabs/aio_tab.py` の重み表示を現行11指標に揃えた
- **2026/03/25**: `/report/print` の live 印刷確認に基づく narrow fix を追加
  - `core/ui/reports/executive_summary.py` の先頭 `まずやること` カードを印刷向けに短文化し、1ページ目で `自社理解 / 結論 / 初手` が完結するよう調整
  - `core/ui/panels.py` の印刷 CSS に `summary-top-action` / `status-card` の keep-together を追加し、先頭アクションカードと小さな法務カードの途中改ページを抑制
  - `core/ui/components.py` の `create_status_card()` に `status-card` クラスを付与
  - headless Edge で live UI と `/report/print` を再確認し、注意/法務/補足/技術詳細が 2ページ目以降へ後退していることを確認
- **2026/03/25**: 印刷/共有レポートの読み順 narrow fix を追加
  - `core/ui/reports/executive_summary.py` で `このサイトをどう理解したか` / `今回の結論` / `まずやること` を先頭に整理
  - `core/ui/panels.py` で `前回比較` を `補足情報` に後退し、`根拠・技術詳細` と `改善提案` の境界を明示
  - `report_panel()` の冒頭を `今回の結論` → `今すぐやること（Top3）` の順に整理し、`1ページ目/2ページ目` のUI都合ラベルを廃止
- **2026/03/25**: live UI の情報設計 narrow fix を追加
  - `core/ui/panels.py` で注意点を先頭 `callout` に集約し、判定メモを `補足情報（判定条件・システムメモ）` に後退
  - `report_panel()` のセクション順を非エンジニア向け優先に整理し、`根拠を見る` / `専門詳細` のラベルで専門情報の境界を明示
  - `nicegui_app.py` の `印刷用ページ` 導線を `secondary-btn` に変更し、本文導線より強く見えすぎないよう調整
- **2026/03/25**: UI/印刷 narrow fix を実施
  - `nicegui_app.py` / `core/ui/panels.py` で通知・補助説明・操作導線の文言を整理し、`印刷用ページ` 導線に統一
  - `/report/print` の印刷 CSS で重い装飾を無効化し、長い詳細セクションは分割可、短い通知/メトリクスのみ keep-together に変更
- **2026/02/02**: 現状確認（STATUS_AND_IMPROVEMENTS.md）: リーガル/PDF/UI/ユーザー属性の整理と改善方針を追記。
- **2026/02/02**: リーガル検出強化/PDFブランク対策/UIロール出し分けを実装（WORKLOG参照）。
- **2026/02/01**: UI修正/PDF拡張/階層クロール/プログレスバー修正
  - `ui.html()` に `sanitize=False` 追加（NiceGUI 2.x対応）
  - PDF生成器を7ページ構成に拡張（fpdf2）
  - 履歴タブ表示確認、DB保存・比較機能は動作確認済み
  - プログレスバー修正: 完了時100%を1.5秒間表示してからリセット
  - 階層クロール実装: priority_pages（プライバシーポリシー/会社概要等）を実際に取得
  - 法務チェック: メインHTML + 優先ページHTMLを結合して検出精度向上
- **2026/01/30**: Wikidata連携/構造化サマリー/差分強調
  - `core/wikidata_client.py` を追加し、QID連携をTop3＋キャッシュに限定
  - `core/engine/orchestrator.py` で構造化サマリーを生成しLLMリライトに渡す
  - UI/PDFでBefore/Afterの視覚強調を追加
- **2026/01/29**: Entity Recognition 改善
  - `core/aio_analyzer.py`: Sudachi品詞判定ベースのEntity Linking実装
  - `core/knowledge_graph.py`: カテゴリ重み付け、補完辞書、正規化機能追加
  - 計画ファイル: `plans/refactor2/`
- **2026/01/24**: リライト案カードの分割を抑制
  - `PDFreport/sections/report_sections.py` で1カード表示を優先
- **2026/01/24**: PDFセクション描画の分割
  - `PDFreport/sections/` に意思決定サマリ/即時改善/改善提案を移動
- **2026/01/24**: FAQ検出ロジックの分離
  - `core/faq_detection.py` を追加し、`seo_aio_engine.py` からFAQ関数群を移動
- **2026/01/24**: UIセレクトの展開方向と文字サイズを調整
  - `nicegui_app.py` のセレクトを下方向表示 + 小さめフォントに変更
- **2026/01/24**: PDFリライト案カードの可読性を改善
  - `PDFreport/high_quality_pdf_generator.py` のリライト案を見出し付きに整形
- **2026/01/24**: 進捗ログの未定義を修正
  - `seo_aio_engine.py` に `progress_log` を追加
- **2026/01/24**: 解析開始時刻の未定義を修正
  - `seo_aio_engine.py` で `analysis_started_at` を初期化
- **2026/01/24**: 進捗コールバックの未定義を修正
  - `seo_aio_engine.py` に `update_progress` の安全ラッパーを追加
- 変更履歴は `WORKLOG.md` に追記
- **2026/01/22**: 楽天市場・Yahoo!ショッピング対応
  - プラットフォーム選択肢に追加
  - 特商法リンク検出の強化（左カラム・ナビ対応）
  - プラットフォーム別アドバイスの追加
