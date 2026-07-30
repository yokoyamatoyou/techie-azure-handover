# Current Mainline Owner Split

- Last Updated: 2026-03-17
- Scope: `C:\tetie\notecode` current mainline owner boundary and execution docs
- Source of Truth: `C:\tetie\notecode\current_mainline_owner_split\PROGRESS.md`

## Purpose

- current mainline の責務境界を owner 単位で固定する。
- runtime と品質を混同せず、仕様判断と最小修正判断を分離できる状態にする。
- 別ウインドウの担当でも、入口ファイルだけでそのまま再開できるようにする。

## Current Snapshot

- Status: completed（2026-03-14）
- Accepted current behavior:
  - `improvement_case` は `source_fit=pass` / `source_grounding_status=insufficient` でも current code 上は `input_decision=accept`
  - confirm-only event では `latest_ui_journey.runtime_reason_code` と `latest_output.runtime_reason_code` が一致しないことがある
  - generation snapshot / audit の source of truth は `pipeline_check.input_contract`
  - snapshot は full contract、audit は compact projection を維持する
  - `run_generation()` の pre-run UI reset/start transition plan、top-level exception transition plan、finally cleanup transition plan、complete terminal state transition plan は `current_mainline_ui_generation_state_adapter.py` が持ち、`note_writer_app.py` は actual widget/state mutation と trigger timing を保持する
  - `run_generation()` の success path と output guard blocked path の UI-only projection は `current_mainline_ui_result_adapter.py` が持ち、`note_writer_app.py` は widget/state mutation と logging timing を保持する
  - `run_generation()` の generation telemetry input assembly（UI journey event payload / latest snapshot kwargs）は `current_mainline_ui_generation_telemetry_adapter.py` が持ち、`note_writer_app.py` は logging / snapshot trigger timing を保持する
  - 2026-03-17 の owner-local肥大化解消 track は stop とし、残る terminal timing / actual widget-state mutation は `note_writer_app.py` に保持する
- Accepted verification baseline:
  - `test_generation_request_builder.py`
  - `test_current_mainline_runner.py`
  - `test_current_mainline_regressions.py`
  - `test_newalgorithm_phase04_ui_wiring.py`
  - `test_newalgorithm_phase06_logging_compat.py`

## Read First

- `C:\tetie\AGENTS.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\ALGORITHM.md`
- `C:\tetie\notecode_current_mainline_handoff_2026-03-17.md`
- `C:\tetie\notecode_current_mainline_handoff_2026-03-11.md`
- `C:\tetie\notecode_current_mainline_handoff_2026-03-13.md`
- `C:\tetie\notecode\docs\current_mainline_root_cause_map_2026-03-10.md`
- `C:\tetie\notecode\docs\current_mainline_tomorrow_plan_2026-03-13.md`
- `C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-03-14.md`

## Document Map

- `C:\tetie\notecode\current_mainline_owner_split\PROGRESS.md`
  - 現在地、次アクション、Phase 状態の正本
- `C:\tetie\notecode\current_mainline_owner_split\EXECUTION_RULES.md`
  - 各 Phase 共通の実行ルール、停止条件、更新ルール
- `C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md`
  - owner 境界、入出力、非責務、関連ログ・関連テストの一覧
- `C:\tetie\notecode\current_mainline_owner_split\TEST_AND_SAFETY_MATRIX.md`
  - 共通テスト、パイプライン確認、LLM 安全性確認の一覧
- `C:\tetie\notecode\current_mainline_owner_split\phases\PHASE_01_OWNER_MAP.md`
  - owner 境界の事実整理
- `C:\tetie\notecode\current_mainline_owner_split\phases\PHASE_02_INPUT_CONFIRM_DECISION.md`
  - input decision / confirm preview / generate 判定の責務整理
- `C:\tetie\notecode\current_mainline_owner_split\phases\PHASE_03_UI_OBSERVABILITY.md`
  - UI 表示と logging 境界の整理
- `C:\tetie\notecode\current_mainline_owner_split\phases\PHASE_04_PIPELINE_IO_BOUNDARY.md`
  - request build / execute / snapshot / audit の I/O 契約整理
- `C:\tetie\notecode\current_mainline_owner_split\phases\PHASE_05_ACCEPTANCE_HANDOFF.md`
  - 受入条件、rollback、handoff の固定
- `C:\tetie\notecode\vnext_current_integration\README.md`
  - owner split 完了後の vNext/current 統合移行 initiative の入口
- `C:\tetie\notecode\vnext_current_integration\PROGRESS.md`
  - vNext/current 統合移行の現在地

## Execution Order

1. `C:\tetie\notecode\current_mainline_owner_split\README.md`
2. `C:\tetie\notecode\current_mainline_owner_split\PROGRESS.md`
3. `C:\tetie\notecode\current_mainline_owner_split\EXECUTION_RULES.md`
4. `C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md`
5. `C:\tetie\notecode\current_mainline_owner_split\TEST_AND_SAFETY_MATRIX.md`
6. `C:\tetie\notecode\current_mainline_owner_split\phases\PHASE_01_OWNER_MAP.md`
7. 以降は `PROGRESS.md` の `Current Phase` に従う

## Related Files

- `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\generation_request_builder.py`
- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\current_mainline_runtime_logging.py`
- `C:\tetie\notecode\note\current_mainline_ui_generation_state_adapter.py`
- `C:\tetie\notecode\note\current_mainline_ui_generation_telemetry_adapter.py`
- `C:\tetie\notecode\note\current_mainline_input_policy.py`
- `C:\tetie\notecode\note\current_mainline_ui_result_adapter.py`
- `C:\tetie\notecode\note\current_mainline_ui_matrix.py`

## Related Logs

- `C:\tetie\notecode\logs\latest_ui_journey.json`
- `C:\tetie\logs\ui_journey_log.jsonl`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- `C:\tetie\notecode\logs\generation_audit_log.jsonl`
- `C:\tetie\notecode\logs\current_mainline_ui_short_matrix_latest.json`
- `C:\tetie\notecode\logs\current_mainline_ui_long_matrix_latest.json`

`latest_ui_journey.json` は generated artifact なので、`last_updated_at` が 2026-03-16 より前なら `latest_decision` / `latest_generation_gate` 未投影の旧 shape が残っていても current code drift とは限らない。shape の一次根拠は `current_mainline_runtime_logging.py` と `test_newalgorithm_phase06_logging_compat.py` を優先する。

## Related Tests

- `C:\tetie\notecode\note\tests\test_current_mainline_runner.py`
- `C:\tetie\notecode\note\tests\test_current_mainline_regressions.py`
- `C:\tetie\notecode\note\tests\test_current_mainline_ui_generation_state_adapter.py`
- `C:\tetie\notecode\note\tests\test_current_mainline_ui_generation_telemetry_adapter.py`
- `C:\tetie\notecode\note\tests\test_current_mainline_ui_result_adapter.py`
- `C:\tetie\notecode\note\tests\test_newalgorithm_phase04_ui_wiring.py`
- `C:\tetie\notecode\note\tests\test_newalgorithm_phase06_logging_compat.py`
- `C:\tetie\notecode\note\tests\test_generation_request_builder.py`
- `C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py`

## Source of Truth

- current phase の状態は `PROGRESS.md` を正とする。
- 各 Phase の作業内容と停止条件は該当 Phase 文書を正とする。
- 時系列の記録は `C:\tetie\WORKLOG.md` を正とする。

## Reopen Guide

- owner 境界の説明不足: Phase01 を reopen
- confirm / generate の input decision 差: Phase02 を reopen
- UI journey / latest snapshot / audit の見え方差: Phase03 を reopen
- request build / execute / snapshot / audit の field drift: Phase04 を reopen
- acceptance / handoff 導線の不足: Phase05 を reopen

新しい論点が出た場合も、最初に 1 owner だけを修正候補として明示する。
