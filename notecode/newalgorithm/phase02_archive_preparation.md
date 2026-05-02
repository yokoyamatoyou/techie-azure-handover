# Phase02: Archive Plan and Preparation

## Goal
- 承認後に即実行できるarchive手順を確定し、移行事故を防ぐ。

## Input
- `phase01_scope_ui_contract.md` の確定結果
- 既存ディレクトリ構造一覧

## Output
- archive実行runbook
- archive対象インベントリ
- 復活手順書

## Steps
1. archiveルートを `notecode/archive/zero_base_rebuild_YYYY-MM-DD/` で確定する。
2. `code/`, `worklog/`, `docs/` の移動対象パス一覧を作る。
3. WORKLOG圧縮テンプレート（要約粒度と必須項目）を作る。
4. `restore_guide.md` に復活手順（戻し先/ import修正/確認）を記載する。
5. 実行後チェックリスト（移動漏れ/参照切れ/起動確認）を作る。

## Deliverables
- `archive_execution_runbook.md`
- `archive_target_inventory.md`
- `restore_guide.md`

## Exit Criteria
- archive対象パスに曖昧記述がない（ワイルドカード依存なし）。
- 復活手順が「誰が読んでも同手順で戻せる」粒度で記載済み。
- 実行後チェックリストに必須3UI要素確認が含まれる。

## Self Test
- ST-01 正常: runbookだけで対象移動順序を追える。
- ST-02 異常: 存在しないパス指定時の回復手順がある。

## LLM Vulnerability Test
- LT-01: 手順書へ混入した過剰削除提案を検出して拒否する。

## Pipeline Review
- PR-01: archive後も必須3UI要素と画像機能が残る設計である。

## Module/Dependency Risk Check
- DR-01: 共有モジュール（llm_client/app_config等）が移動対象に含まれない。

## Rollback
- 条件: runbookが復活不能な構成を含む
- 戻し先: Phase01の確定仕様に基づき対象再選定
