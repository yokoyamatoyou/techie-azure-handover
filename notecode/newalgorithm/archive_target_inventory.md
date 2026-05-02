# Phase02 Archive Target Inventory

## Scope
- 対象サービス: `C:\tetie\notecode`
- archiveルート（確定）: `C:\tetie\notecode\archive\zero_base_rebuild_2026-03-07\`
- このインベントリは **ワイルドカード不使用** の明示パスのみを扱う。

## Move Targets (docs)
- `C:\tetie\notecode\docs\zero_base_rebuild_plan_creation_prompt.md`
  - -> `C:\tetie\notecode\archive\zero_base_rebuild_2026-03-07\docs\zero_base_rebuild_plan_creation_prompt.md`
- `C:\tetie\notecode\docs\zero_base_rebuild_plan_first_prompt.md`
  - -> `C:\tetie\notecode\archive\zero_base_rebuild_2026-03-07\docs\zero_base_rebuild_plan_first_prompt.md`
- `C:\tetie\notecode\docs\zero_base_rebuild_plan_prompt_to_send.md`
  - -> `C:\tetie\notecode\archive\zero_base_rebuild_2026-03-07\docs\zero_base_rebuild_plan_prompt_to_send.md`
- `C:\tetie\notecode\docs\zero_base_rebuild_plan_qa_for_other_tab.md`
  - -> `C:\tetie\notecode\archive\zero_base_rebuild_2026-03-07\docs\zero_base_rebuild_plan_qa_for_other_tab.md`

## Move Targets (worklog)
- source: `C:\tetie\WORKLOG.md`
  - copy -> `C:\tetie\notecode\archive\zero_base_rebuild_2026-03-07\worklog\WORKLOG_snapshot_2026-03-07.md`
  - summary -> `C:\tetie\notecode\archive\zero_base_rebuild_2026-03-07\worklog\WORKLOG_compact_2026-03-07.md`
  - 補足: 全体運用のため `C:\tetie\WORKLOG.md` 自体は移動しない（copy-only）。

## Move Targets (code)
- 本フェーズで移動対象なし（empty）。
- 理由: 実行時importに関わるランタイムコードの切断リスクを避けるため、Phase03以降の疎通確認後に再評価する。

## Explicit Exclusion (DR-01)
- 以下は共有モジュールのため移動対象に含めない。
  - `C:\tetie\notecode\note\llm_client.py`
  - `C:\tetie\notecode\core\app_config.py`
  - `C:\tetie\notecode\note\note_writer_app.py`
  - `C:\tetie\notecode\note\article_generator.py`
  - `C:\tetie\notecode\note\image_prompt_mixin.py`
  - `C:\tetie\notecode\note\image_editing.py`

## Post-Execution Required Checks (PR-01)
- 必須3UI要素が残っていること
  - 記事種類セレクタ
  - 生成ボタン + 結果表示
  - 画像生成（TOP/本文）
- 画像機能（TOP/本文向けプロンプト生成、画像生成ボタン）が機能すること
