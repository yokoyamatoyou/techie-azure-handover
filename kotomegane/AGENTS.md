# コトメガネ AGENTS

このファイルは `C:\tetie\kotomegane` の現行運用入口です。  
現在の `コトメガネ` は、旧来の AI トラフィック解析アプリではなく、`LLMO Prompt Loop PoC` を実装するための PoC リポジトリです。

このファイルの役割は **ガイド / 参照順 / 更新ルール** の提示に限定します。  
`docs/` 直下は `コトメガネ本体` の正本を優先し、セッション用メモは `docs/session_notes/`、横断資料は `docs/cross_product/` に分離します。

## Current Work Guide

- 現行 snapshot / handoff: `C:\tetie\kotomegane\WORKLOG.md`
- 現行アルゴリズムと責務分担: `C:\tetie\kotomegane\ALGORITHM.md`
- 現行の SaaS 実装計画: `C:\tetie\kotomegane\docs\SAAS_IMPLEMENTATION_PLAN_2026-04-03.md`
- LLM Batch / prompt cache 運用方針: `C:\tetie\kotomegane\docs\LLM_BATCH_AND_CACHE_RULES_2026-04-05.md`
- `kotomegane` の実装正本: `C:\tetie\kotomegane\docs\DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md`
- OpenAI runtime 前提: `C:\tetie\kotomegane\docs\OPENAI_RUNTIME_NOTES.md`
- `AGENTS.md` には詳細な phase 手順や長い TODO を蓄積しない。実行順、停止条件、完了条件は plan doc 側へ集約する

## 目的

- サービス名は `コトメガネ`
- 目的は、キーワードを複数回実行し、LLM 検索応答を分析する可視化 PoC を最短で見せること
- 既定モデルは `gpt-5.4-nano`
- OpenAI Responses API と `web_search` を使う
- prompt caching を前提に運用する
- PoC 期間中のみコストを算出する
- コスト換算は `1 USD = 160 JPY`
- 将来のために `Gemini` `Claude` の UI 枠は用意してよいが、現時点では形のみで実装しない

## Read Order

1. `C:\tetie\kotomegane\AGENTS.md`
2. `C:\tetie\kotomegane\WORKLOG.md`
3. `C:\tetie\kotomegane\ALGORITHM.md`
4. `C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md`
5. `C:\tetie\kotomegane\docs\DOC_STATUS.md`
6. `C:\tetie\kotomegane\docs\SAAS_IMPLEMENTATION_PLAN_2026-04-03.md`
7. `C:\tetie\kotomegane\docs\LLM_BATCH_AND_CACHE_RULES_2026-04-05.md`
8. `C:\tetie\kotomegane\docs\DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md`
9. `C:\tetie\kotomegane\docs\OPENAI_RUNTIME_NOTES.md`
10. `C:\tetie\kotomegane\TASK.md`
11. `C:\tetie\kotomegane\README.md`
12. `C:\tetie\kotomegane\deep-research-report (11).md`

## Source Of Truth

- 運用ルール: `AGENTS.md`
- current snapshot / handoff: `WORKLOG.md`
- 現行アルゴリズム: `ALGORITHM.md`
- 現在の状態: `docs/CURRENT_STATE_2026-03-30.md`
- ドキュメントの位置づけ: `docs/DOC_STATUS.md`
- SaaS 実装計画: `docs/SAAS_IMPLEMENTATION_PLAN_2026-04-03.md`
- LLM Batch / prompt cache 運用方針: `docs/LLM_BATCH_AND_CACHE_RULES_2026-04-05.md`
- `kotomegane` 実装正本: `docs/DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md`
- セッション用メモ: `docs/session_notes/**`
- 横断資料: `docs/cross_product/**`
- 現在タスク: `TASK.md`
- セットアップと起動: `README.md`
- OpenAI 前提: `docs/OPENAI_RUNTIME_NOTES.md`
- 実装コード: `app.py`, `llmo_client.py`, `analysis_lib.py`, `storage.py`, `config.py`
- 設定ファイル: `config/llmo_poc_settings.json`

## Reference Only

- `deep-research-report (11).md`
  - 参考仕様。PoC の元案として扱う。
  - 実装の現在値とずれる可能性があるため、実行時の正本にしない。

## Legacy

- `archive/**`
  - 旧 AI トラフィック解析アプリ一式。
  - 現行 PoC では参照専用。

## UI / Branding Rules

- ロゴ: `assets/logo_mark.svg` を共通ブランドマークとして使い、サービス名はテキストで並べる
- 補助の旧ロゴ資産: `assets/kotomegane-logo.svg`
- 配色基準: `スクリーンショット 2026-03-30 194437.png`
- 画面トーン: クリーム背景、濃いブラウンのバー、オレンジ強調
- 既定ポート: `8083`
- `C:\tetie\techie-hub\start.bat` から起動できる状態を維持する

## Runtime Rules

- Python 仮想環境は `.venv`
- セットアップは `setup.ps1`
- 起動は `run.ps1`
- API キーは `.env` の `OPENAI_API_KEY`
- prompt cache 系設定は config から制御する
- `n` は UI で変更できる状態を保つ

## Documentation Rule

- 現行状態が変わったら `docs/CURRENT_STATE_*.md` と `README.md` を先に更新する
- snapshot / handoff が変わったら `WORKLOG.md` を更新する
- 実行フローや責務が変わったら `ALGORITHM.md` を更新する
- 詳細な実行順、phase、停止条件は `AGENTS.md` に増やさず、plan doc に書く
- `docs/` 直下には `kotomegane` 本体の正本を残し、補助資料は `session_notes/` と `cross_product/` に寄せる
- 参考仕様だけ変えず、実装と手順を先に合わせる
- `C:\tetie\AGENTS.md` は全体入口だが、`kotomegane` の現況は古い場合がある。作業時は本ファイルを優先する
