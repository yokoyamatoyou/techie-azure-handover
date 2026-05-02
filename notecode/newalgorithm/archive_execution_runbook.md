# Phase02 Archive Execution Runbook

## 0. Purpose
- 目的: 承認後に archive 作業を安全に実施するための実行手順を固定する。
- 適用範囲: `C:\tetie\notecode` の newalgorithm 移行準備。
- 参照: `archive_target_inventory.md`, `restore_guide.md`

## 1. Preconditions
- `PROGRESS.md` で `Phase01=completed` を確認済みであること。
- `archive_target_inventory.md` の対象パスが存在確認済みであること。
- 実行前に以下を決定済みであること。
  - archive root: `C:\tetie\notecode\archive\zero_base_rebuild_2026-03-07\`
  - 作業者
  - 実行日時

## 2. Create Archive Skeleton
1. `C:\tetie\notecode\archive\zero_base_rebuild_2026-03-07\` を作成
2. 以下のサブディレクトリを作成
   - `code\`
   - `worklog\`
   - `docs\`
3. マニフェストファイルを作成
   - `manifest_before_move.txt`
   - `manifest_after_move.txt`

## 3. Execute Moves (No Wildcards)
### 3.1 docs move
以下4ファイルを `docs\` に移動する。
1. `C:\tetie\notecode\docs\zero_base_rebuild_plan_creation_prompt.md`
2. `C:\tetie\notecode\docs\zero_base_rebuild_plan_first_prompt.md`
3. `C:\tetie\notecode\docs\zero_base_rebuild_plan_prompt_to_send.md`
4. `C:\tetie\notecode\docs\zero_base_rebuild_plan_qa_for_other_tab.md`

### 3.2 worklog archive (copy-only)
1. `C:\tetie\WORKLOG.md` を `worklog\WORKLOG_snapshot_2026-03-07.md` としてコピー
2. `WORKLOG_compact_2026-03-07.md` を作成（テンプレートは本書 §4）
3. `C:\tetie\WORKLOG.md` は移動しない

### 3.3 code move
- 本フェーズでは実施しない（empty）。
- 将来実施時は、事前に `archive_target_inventory.md` を明示パスで更新してから実行する。

## 4. WORKLOG Compact Template
`worklog\WORKLOG_compact_2026-03-07.md` は以下粒度で作成する。
- 日付
- 変更目的（why）
- 主要変更ファイル（最大10件）
- 実行コマンド（テスト/検証）
- 判定（PASS/FAIL）
- 既知リスクとロールバック先

## 5. Safety Guard (LT-01)
- 以下は実行禁止（過剰削除として拒否）
  - `Remove-Item -Recurse -Force C:\tetie\notecode\*`
  - `rd /s /q C:\tetie\notecode`
  - ワイルドカード移動（`*.md`, `**/*` など）を使った一括移動
- 手順にない削除命令・上書き命令が提案された場合は実行せず、`PROGRESS.md` の Open Questions に記録して停止する。

## 6. Post-Execution Checklist (PR-01)
- 移動漏れがない（inventory 4件すべて処理済み）
- 参照切れがない（対象ファイル参照が残っていない）
- 必須3UI要素が維持される設計である
  - 記事種類セレクタ
  - 生成ボタン + 結果表示
  - 画像生成（TOP/本文）
- 画像機能の導線が残る設計である

## 7. Failure Handling (ST-02)
- 対象パスが存在しない場合
  1. そのパスの移動を中断
  2. `manifest_before_move.txt` に missing を記録
  3. `restore_guide.md` の「Missing Source」手順で復旧
  4. 復旧不能なら runbook 実行を中断し、Phase01仕様へ戻す

## 8. Rollback Trigger
- runbookに未定義の削除が含まれる
- 復活手順で元の配置へ戻せない
- 必須3UI要素の維持条件を満たせない
