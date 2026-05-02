# Phase02 Restore Guide

## 0. Purpose
- archive作業後に、対象ファイルを同じ手順で復元できるようにする。
- 対象: `archive_execution_runbook.md` で移動/退避した docs/worklog。

## 1. Restore Inputs
- archive root: `C:\tetie\notecode\archive\zero_base_rebuild_2026-03-07\`
- inventory: `archive_target_inventory.md`
- runbook logs:
  - `manifest_before_move.txt`
  - `manifest_after_move.txt`

## 2. Restore Procedure (docs)
1. 復元元を確認
   - `C:\tetie\notecode\archive\zero_base_rebuild_2026-03-07\docs\`
2. 復元先を確認
   - `C:\tetie\notecode\docs\`
3. 以下4ファイルを個別に戻す（順序固定）
   1. `zero_base_rebuild_plan_creation_prompt.md`
   2. `zero_base_rebuild_plan_first_prompt.md`
   3. `zero_base_rebuild_plan_prompt_to_send.md`
   4. `zero_base_rebuild_plan_qa_for_other_tab.md`
4. 各ファイルごとに存在確認（復元元/復元先）を記録

## 3. Restore Procedure (worklog)
1. `C:\tetie\WORKLOG.md` が存在することを確認
2. `worklog\WORKLOG_snapshot_2026-03-07.md` と比較し、差分の有無を確認
3. `WORKLOG_compact_2026-03-07.md` を参照用として保持（削除しない）

## 4. Missing Source Recovery (ST-02)
- 症状: 復元元ファイルがない
- 手順:
  1. `manifest_before_move.txt` を確認し、実行前存在を再確認
  2. `manifest_after_move.txt` を確認し、移動先の誤りを特定
  3. 誤配置先から手動で戻す
  4. それでも見つからない場合は `WORKLOG_snapshot_2026-03-07.md` の記録を使い、復旧対象を再取得する
  5. 復旧不能時は Phase01時点の仕様状態へ戻す判断を実施する

## 5. Import/Reference Check
- docs参照切れ確認
  - `C:\tetie\notecode\docs\` 配下で zero_base_rebuild 関連参照が解決する
- 共有モジュールは復元不要（本フェーズで移動していない）
  - `C:\tetie\notecode\note\llm_client.py`
  - `C:\tetie\notecode\core\app_config.py`
  - `C:\tetie\notecode\note\note_writer_app.py`
  - `C:\tetie\notecode\note\article_generator.py`

## 6. Final Verification (PR-01)
- 必須3UI要素の設計維持を確認
  - 記事種類セレクタ
  - 生成ボタン + 結果表示
  - 画像生成（TOP/本文）
- 画像導線（プロンプト生成と画像生成ボタン）が設計上残っていることを確認
