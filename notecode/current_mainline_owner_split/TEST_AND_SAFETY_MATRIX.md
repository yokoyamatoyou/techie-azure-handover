# Test and Safety Matrix

- Last Updated: 2026-03-14

## Mandatory Checks Common to All Phases

- `py_compile` で変更対象 owner を確認する
- `pytest` で関連回帰を確認する
- preview と generation 本体の判定差を確認する
- log と UI 表示の整合を確認する
- 事実と推測を分けて記録する

## Phase-by-Phase Test Matrix

| Phase | Main Checks | Required Logs | Required Tests |
|---|---|---|---|
| Phase01 | owner 境界の事実確認 | `latest_ui_journey.json`, `latest_generation_output.json` | 静的確認のみ |
| Phase02 | input decision / confirm / generate 判定整合 | `latest_ui_journey.json`, `generation_audit_log.jsonl` | `test_current_mainline_runner.py`, `test_current_mainline_regressions.py` |
| Phase03 | UI 表示 / runtime logging 整合 | `ui_journey_log.jsonl`, `latest_generation_quality_report.json` | `test_newalgorithm_phase04_ui_wiring.py`, `test_newalgorithm_phase06_logging_compat.py` |
| Phase04 | request build / execute / snapshot / audit 契約確認 | `latest_generation_output.json`, `generation_audit_log.jsonl` | `test_generation_request_builder.py`, `test_current_mainline_runner.py` |
| Phase05 | acceptance / rollback / handoff 確認 | current mainline 関連最新ログ一式 | 必要時に phase 横断回帰 |

## LLM Safety Checkpoints

- prompt injection を無効化できているか
- system-owned field の越権上書きがないか
- 危険断定や法務リスク表現を見落としていないか
- 過剰 gate で不必要に fail-closed していないか

## Pipeline Bug Checkpoints

- confirm preview と generation 本体が別判定になっていないか
- runtime reason と UI 表示が矛盾していないか
- snapshot / audit / latest output の key が噛み合っているか
- `source_fit`, `input_decision`, `semantic_article_key` の投影先が説明可能か

## Acceptance Evidence

- テスト結果
- ログ整合の確認結果
- owner 単位の判断根拠
- rollback 条件

## Current Accepted Baseline

- 2026-03-14 accepted suite
  - `pytest note\tests\test_generation_request_builder.py -q` -> `6 passed`
  - `pytest note\tests\test_current_mainline_runner.py -q` -> `17 passed`
  - `pytest note\tests\test_current_mainline_regressions.py -q` -> `20 passed`
  - `pytest note\tests\test_newalgorithm_phase04_ui_wiring.py -q` -> `17 passed`
  - `pytest note\tests\test_newalgorithm_phase06_logging_compat.py -q` -> `17 passed`
- docs-only close なので `py_compile` は不要
