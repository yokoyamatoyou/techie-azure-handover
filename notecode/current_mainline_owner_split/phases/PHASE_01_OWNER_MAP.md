# PHASE_01_OWNER_MAP

- Last Updated: 2026-03-14

## Objective

- current mainline の主要 5 owner の責務境界を事実ベースで固定する。

## In Scope

- owner ごとの主責務、非責務、入出力、呼び出し方向
- 関連ログ、関連テスト、正本の確認

## Out of Scope

- コード修正
- UI 文言変更
- 品質改善

## Target Owners

- `input_contract.py`
- `current_mainline_runner.py`
- `generation_request_builder.py`
- `note_writer_app.py`
- `current_mainline_runtime_logging.py`

## Target Files

- `C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md`
- `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\generation_request_builder.py`
- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\current_mainline_runtime_logging.py`

## Preconditions

- `README.md`, `PROGRESS.md`, `EXECUTION_RULES.md`, `TEST_AND_SAFETY_MATRIX.md` が存在する
- current mainline handoff と `WORKLOG.md` の 2026-03-13 / 2026-03-14 記録を読了済み

## Tasks

1. 主要 5 owner の主責務と非責務を `OWNER_MAP.md` に記載する
2. 呼び出し元 / 呼び出し先を owner 単位で確認する
3. 各 owner に対応するログとテストを紐付ける
4. 境界リスクを `Open Boundary Risks` に記録する

## Exit Criteria

- `OWNER_MAP.md` の 5 owner 行が埋まっている
- `Cross-Owner Call Map` が埋まっている
- `Source of Truth by Concern` が埋まっている
- 主要な非責務が明記されている

## Required Tests

- 静的確認のみ
- 必要に応じて既存ログと既存テストの導線を確認する

## Code Bug Check

- owner を跨いだ責務重複の記載漏れがないか確認する
- 非責務が曖昧な行がないか確認する

## Pipeline Bug Check

- preview, generate, logging の経路が `Cross-Owner Call Map` と矛盾していないか確認する

## LLM Safety Check

- LLM 安全性チェックの owner がどこにあるかを明示し、未記載領域を残さない

## Retry Rule

- 同一事象の整理失敗は最大 2 回まで修正する

## Stop Condition

- owner 境界の正本が 2 つ以上あると判明した場合は停止して報告する
- 呼び出し方向に矛盾があり解消できない場合は停止して報告する

## Evidence to Record

- 参照したコード
- 参照したログ
- owner ごとの責務・非責務

## Handoff to Next Phase

- Phase02 では `input_contract.py` と `current_mainline_runner.py` の判定責務に絞って進む

