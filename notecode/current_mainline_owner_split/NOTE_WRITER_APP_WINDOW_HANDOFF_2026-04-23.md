# `note_writer_app.py` 別ウインドウ用手引き

- 目的: `note\note_writer_app.py` が肥大化している**実際の中身**を、実装者・別 Chat ウインドウに渡すための地図。
- 行番号は 2026-04-23 時点。Git で変わるため「近傍検索（シンボル名）」を併用すること。
- 正本の責務境界: `C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md`
- アルゴリズム: `C:\tetie\notecode\ALGORITHM.md`（触る前に該当節を確認）

## 1. 規模の事実

| 指標 | 目安 |
|------|------|
| 全体 | 約 9,200 行 |
| トップレベル `def` / `class` / `async def` | 約 157 個 |
| 最大の単一ブロック | `@ui.page("/")` → `main_page()`（**約 4,300 行超**。末尾付近に手動リーガル UI 等も含む） |

肥大の主因は **NiceGUI の declarative UI が `main_page` 内に縦に積み上がっていること**に加え、**runner / adapter の薄いラッパー**と**ソース／画像／品質系のヘルパー**が同ファイルに同居している点である。

## 2. ファイル先頭（おおよそ L1–L675）

- **ロギング**: `setup_app_logging`、JSON formatter、NiceGUI 切断ノイズの filter。
- **import 集**: `current_mainline_runner`、各種 `current_mainline_ui_*_adapter`、`image_*`、`blog_image_auto`、`runtime_logging` ラッパ名、他多数。
- **定数・パス**: `UPLOAD_DIR` / `STATIC_DIR`、`latest_generation_*` / `generation_audit` の**プロジェクト直下 logs と workspace 直下 logs の二重定義**（互換ミラー）、`HUB_URL` 等。
- **HTML サニタイザ**、静的ファイル `app.add_static_files("/static", ...)`。
- **データ構造**: `SourceItem`、`AppState`（ソース、面接回答、画像生成状態、ジャーニー confirm 用フィールド等）。
- **マルチクライアント**: `_CLIENT_STATES`、client key、タイマ登録/解放、`_StateProxy` / `_GeneratorProxy`（legacy generator と mainline `MinimalPipeline` の遅延生成）。

## 3. 入力・ジャーニー・記事型まわり（おおよそ L676–L1590）

- 記事型・プロンプト辞書の合成、**ジャーニー目的/ターゲット**の正規化。
- **ソースモード**: ラベル解決、ゼロソース可否、**入力面の組み立て** `_build_source_mode_input_surface`、オマカセ用 `_build_omakase_surface_state`、公開済み記事候補 `_load_current_published_post_candidates`。
- **生成前ゲート表示** `_build_generate_gate_surface`、インライン告知 `_build_announcement_inline_error`。
- 記事型ラベル→キー、writer role / core message、**一人称方針**、面接由来の正規化（topic / narrative / knowledge lenses）。
- 操作 ID、**UI 利用ログ** `_log_ui_usage`、理由コード分類、フェッチ失敗整形、403 URL、ソース通知、遅延表示文言。
- **PDF アシスト**: 候補探索、ingest、リセット。
- **あいまいさダイアログ** `_is_ambiguity_confirmed` / `_open_ambiguity_dialog`。

## 4. サブ UI コンテナ（おおよそ L1591–L1972）

- `sources_container` — ソース一覧と操作（refresh パターン）。
- `custom_genres_container`、ジャンル編集/削除、記事型セレクト連動。
- `_open_privacy_blur_dialog` — ぼかし等（`image_editing` 利用）。
- `generated_images_container` — 生成画像プレビュー帯。
- スクロール/コピー小物。

## 5. current mainline 周辺の「中核ブロック」（おおよそ L1973–L3594）

`OWNER_MAP` で外部オーナーに分けた**契約解決・runner・ログ schema**は別モジュールだが、**UI 用の引数整形・遷移プラン・telemetry 用 dict の組み立て**がここに大量にある。

- 品質レポート走査: `_iter_quality_phase_reports`、fingerprint 抽出、**output guard 評価** `_evaluate_generation_output_guard`。
- **ログ薄ラッパー**: `_build_latest_quality_report_payload`、`_append_generation_audit_record`、`_append_ui_journey_event`、`_record_ui_journey_event`、`_persist_latest_generation_snapshot`（中身は `current_mainline_runtime_logging` へ委譲する形が中心）。
- **adapter 直呼び出しの薄ラッパ**群: 成功/ブロック/各種エラー/確認必須/フェッチ失敗/invalid type/guard retry 等の「view dict」組み立て、生成 prerun/exception/cleanup/complete プラン、ゲート extra、ビジー表示等（関数名に `_build_current_mainline_*` が連続）。
- **入力系**: `_build_current_mainline_input_contract_kwargs`、生成リクエスト準備、面接 state、必須入力ウィザード、**質問 item の UI 用フィルタ**、selection payload、フェッチ要約、guard retry、output guard ブロック、**完了/例外/クリーンアップ/レンダ用 payload** の apply。
- **非同期本線**: `_execute_current_mainline_generation_with_context`（`run.io_bound` + `execute_current_mainline_generation` + プロンプト文脈付与）。
- **失敗時スナップショ fail-open**: `_persist_current_mainline_generation_snapshot_fail_open`。
- **画像プロンプト**: `_build_generated_image_prompt_value`、`_run_current_mainline_image_prompt_step`（`image_prompt_helpers` の pattern 適用含む）。
- **生成後オートリーガル**: `_resolve_current_mainline_auto_legal_postcheck`。

## 6. ソース操作・起動時掃除・アップロード（おおよそ L3599–L3750）

- `_add_source` / `_remove_source` / `_restore_recent_uploaded_sources` / `_cleanup_old_upload_files` — **モジュール import 時に古い upload を掃除**する副作用あり（L3697 付近）。
- `_handle_upload` — NiceGUI イベントからファイル保存・ソース登録（10MB 上限、拡張子ホワイトリスト）。

## 7. グローバル UI アセット（おおよそ L3752–L4794）

- `app.colors(...)` でテーマ色。
- **1 本目 `ui.add_head_html`（L3763 付近〜）**: フォント link、favicon、**大規模埋め込み CSS**（`.icon`、カード、ステップ、生成結果、法的 UI 用クラス等）。**~900 行規模のスタイル**が文字列内に存在。
- **2 本目 `ui.add_head_html`（L4730 付近）**: ステップ追従バー用 **インライン JavaScript**（scroll spy、`.step-card-*` / `.sticky-s*` 前提）。

## 8. `main_page()`（おおよそ L4798–L9171）

- エントリ: `@ui.page("/")`。**クライアント毎**にタイマ掃除・state/generator 確保、disconnect 時 `_release_client_scope`。
- `OPENAI_API_KEY` 未設定時のエラー面。
- ブランド/レイアウト、ステップトラッキング用 UI、**面接・ソース・生成・プレビュー・画像・リーガル**など、アプリの可視面の**大半がこの関数のネスト内**にある。
- **手動リーガルポストチェック**（`run_legal_postcheck`、結果レンダ、本文への反映）等はファイル末尾近く（L9000 台）に**ローカル関数として定義**されているブロックを含む。
- 以降 `run_app`（ポート探索、headless、`ui.run`）。

## 9. 既に分離されているもの（同ファイル内に残る import のみ参照）

次は**別モジュール正本**。**このファイルの行数を膨らませないための抜粋**として扱うこと。

- `note.image_prompt_helpers` — パターン定数、プロンプト組み立て、分割。
- `note.note_text_format_helpers` — URL/ハッシュタグ/プレーンテキスト整形等。
- `note.proposition_density_helpers` — 主張密度関連。
- `note.generation_exception_helpers` — 例外分類、guard retry 文言。
- `current_mainline_ui_*_adapter` / `current_mainline_ui_confirm_adapter` — confirm/success/blocked 等の**プレーンデータ**。
- `current_mainline_runtime_logging` — ファイル書き込みと schema 寄りの正本（`note_writer_app` 側はタイミングと引数が主題）。

## 10. 触る前の最短検索キーワード

| やりたいこと | このファイル内の手掛かり例 |
|-------------|---------------------------|
| 生成ボタン〜進捗 | `_prepare_current_mainline_*` / `run_generation`（`main_page` 内） |
| 契約・runner の**判断** | 原則 `current_mainline_runner` / `input_contract` へ。本ファイルは payload |
| ログファイル名・パス | ファイル先頭の `LATEST_*_PATH` / `GENERATION_AUDIT_*` |
| 画像自動・プロンプト | `_run_current_mainline_image_prompt_step`、先頭 `blog_image` / `image_config` import |
| スタイル変更 | `ui.add_head_html` 内の `<style>`（2 箇所目は JS） |
| 手動リーガル | `main_page` 後半 `run_legal_check` 付近 |

## 11. AGENTS / WORKLOG

- 本ファイルの分割・正本昇格を行う場合は、`C:\tetie\notecode\AGENTS.md` の **accretion 禁止**と `OWNER_MAP` の境界に従い、`C:\tetie\WORKLOG.md` へ**一行でも**記録を検討する。
