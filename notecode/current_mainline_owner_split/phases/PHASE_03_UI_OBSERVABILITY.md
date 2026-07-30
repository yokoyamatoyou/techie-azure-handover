# PHASE_03_UI_OBSERVABILITY

- Last Updated: 2026-03-14

## Objective

- UI 表示と runtime logging の境界を整理し、owner 単位で説明可能にする。

## In Scope

- confirm 表示
- success / stop / warning 表示
- `source_fit_status`
- runtime reason の投影
- snapshot / audit / UI journey の見え方

## Out of Scope

- input decision ロジック変更
- request builder 変更
- 本文生成改善

## Target Owners

- `note_writer_app.py`
- `current_mainline_runtime_logging.py`

## Target Files

- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\current_mainline_runtime_logging.py`
- `C:\tetie\notecode\logs\latest_ui_journey.json`
- `C:\tetie\logs\ui_journey_log.jsonl`
- `C:\tetie\notecode\logs\latest_generation_quality_report.json`

## Preconditions

- Phase02 completed
- input decision owner が確定している

## Tasks

1. UI で何を止め、何を見せるかを整理する
2. logging が何を記録し、何を記録していないかを整理する
3. UI と logging の非対称を owner ごとに説明する
4. 必要なら最小修正 owner を 1 か所に限定する

## Findings

### 事実

- UI 表示 owner は `note_writer_app.py`。
  - confirm preview の status text は `input_decision.action` を見て UI owner が固定文言で決める。
  - generation の success / warning / fail-closed 文言も UI owner が固定文言で決める。
  - UI 文言は LLM 出力本文から生成していない。
- `note_writer_app.py::_record_ui_journey_event()` は wrapper owner であり、schema shaping owner ではない。
  - 実際の JSON schema と persistence は `current_mainline_runtime_logging.py::append_ui_journey_event()` が持つ。
- confirm preview event では UI owner が `reason_code` / `needs_input_items` / `status_text` / `source_fit_status` を渡す一方、`result` は渡していない。
  - そのため `append_ui_journey_event()` の `output_summary` は空の `result` から組み立てられる。
- `current_mainline_runtime_logging.py::_build_ui_output_summary()` は `result` が空でも `runtime_reason_code` を `"OK"` に正規化する。
  - その結果、confirm stop event でも `latest_ui_journey.latest_output.runtime_reason_code` は `"OK"` になり得る。
- `append_ui_journey_event()` は top-level `runtime_reason_code` を event `reason_code` から持ち、`latest_output` は `output_summary` から持つ。
  - この 2 系統が別入力源なので、confirm stop で `journey.runtime_reason_code=INP_*` / `latest_output.runtime_reason_code=OK` の非対称が起こる。
- `source_fit_status` は UI journey の top-level key ではなく、confirm event の `extra` にだけ投影される。
  - `source_grounding_status` は current code の UI journey event に直接載せていない。
- `latest_generation_output.json` / `latest_generation_quality_report.json` / `generation_audit_log.jsonl` は generation path 専用。
  - `note_writer_app.py::_persist_latest_generation_snapshot()` は generation error / guard block / rendered success で呼ばれるが、confirm preview では呼ばれない。
  - したがって `latest_ui_journey.json` が confirm artifact、`latest_generation_output.json` が直近 generation artifact のまま、というズレは仕様として起こり得る。
- `quality_warning_only` の user-facing 表示 owner も UI owner。
  - UI owner が `result["ui_quality_warning_only"]=True` を付与し、status text を「生成が完了しました（品質警告あり）」へ変える。
  - logging owner はそれを `output_summary.ui_quality_warning_only` と event `extra.quality_warning_only` に投影する。
- logging compatibility test は current shape を固定している。
  - `test_pr03_ui_journey_log_writes_compact_latest_summary()` は `latest_ui_journey.latest_output.runtime_reason_code == "OK"` を前提にしている。
  - `test_pr03` / `test_pr05` / `test_pr06` / `test_pr06a` / `test_pr06b` により、UI journey / audit / quality projection の現行 shape が回帰で固定されている。

### 推測

- 2026-03-13 の `improvement_case` preview stop が current code とずれて見える主因は runtime owner の誤判定ではなく、confirm-only event が `latest_ui_journey.json` を上書きし、generation-only snapshot と attempt が揃っていないことにある可能性が高い。
- `latest_ui_journey.latest_output.runtime_reason_code=OK` は runtime 成功主張ではなく、「この event に generation result payload が載っていない」という logging shape の副作用である。

## Owner Decision

- UI stop / warning / success wording: `note_writer_app.py`
- confirm state invalidate / confirm required: `note_writer_app.py`
- UI journey event schema / compact latest summary / persistence: `current_mainline_runtime_logging.py`
- generation snapshot / quality report / audit persistence: `current_mainline_runtime_logging.py`
- `quality_warning_only` 判定と付与: `note_writer_app.py`
- `quality_warning_only` の投影: `current_mainline_runtime_logging.py`

## Non-Asymmetry Explanation

- `latest_ui_journey.json.runtime_reason_code`
  - event-level reason の正本
  - confirm stop なら `INP_*` が入る
- `latest_ui_journey.json.latest_output.runtime_reason_code`
  - generation result summary の投影先
  - confirm preview で `result` を渡さないため、空 summary の既定値 `"OK"` が入る
- `latest_generation_output.json`
  - generation path 専用 snapshot
  - confirm preview だけでは更新されない
- `latest_generation_quality_report.json`
  - generation result の品質 projection
  - UI status text や confirm state は持たない
- `generation_audit_log.jsonl`
  - generation attempt 単位の audit
  - confirm preview event は書かない

## Conclusion

- current code 基準では、Phase03 の主要非対称は runtime bug ではなく owner 分離に起因する observability shape の差で説明可能。
- confirm preview の stop は UI journey event にだけ反映され、generation snapshot / quality report / audit には反映されない。
- `source_fit_status=pass` と preview stop の historical artifact は、Phase02 の input decision owner ではなく、Phase03 の projection slice で説明するのが正しい。
- 今回の論点について最小修正は不要。
- 将来 confusion を減らすなら修正 owner の第一候補は `current_mainline_runtime_logging.py` だが、現行 test/compat shape を変えるため別 slice とする。

## Exit Criteria

- UI / logging の責務境界が説明可能
- 非対称が仕様か観測不足かを判断可能
- 必要なら最小修正 owner が 1 か所に限定済み

## Required Tests

- `py_compile` 対象 owner
- `pytest note\tests\test_newalgorithm_phase04_ui_wiring.py -q`
- `pytest note\tests\test_newalgorithm_phase06_logging_compat.py -q`
- 必要時のみ `pytest note\tests\test_current_mainline_ui_matrix.py -q`

## Code Bug Check

- UI 表示責務が runner や logging owner と混線していないか確認する

## Pipeline Bug Check

- confirm 表示、latest snapshot、audit、journey event の key が噛み合っているか確認する

## LLM Safety Check

- UI に露出する status / warning が LLM 出力に引きずられていないか確認する

## Retry Rule

- 同一事象の修正試行は最大 2 回

## Stop Condition

- UI wording と logging key の両方を同時に広く変える必要が出た場合は停止して slice を切り直す

## Evidence to Record

- UI 表示のスクリーン上の事実
- latest journey / audit / quality report の該当 key
- owner ごとの説明

## Evidence Recorded

- コード
  - `note_writer_app.py::_record_ui_journey_event()`
  - `note_writer_app.py::_persist_latest_generation_snapshot()`
  - `note_writer_app.py::_refresh_journey_confirm_preview()`
  - `note_writer_app.py::run_generation()`
  - `current_mainline_runtime_logging.py::_build_ui_output_summary()`
  - `current_mainline_runtime_logging.py::append_ui_journey_event()`
  - `current_mainline_runtime_logging.py::persist_latest_generation_snapshot()`
- ログ
  - `notecode/logs/latest_ui_journey.json`
  - `logs/ui_journey_log.jsonl`
  - `notecode/logs/latest_generation_output.json`
  - `notecode/logs/latest_generation_quality_report.json`
  - `notecode/logs/generation_audit_log.jsonl`
- テスト
  - `note/tests/test_newalgorithm_phase04_ui_wiring.py`
  - `note/tests/test_newalgorithm_phase06_logging_compat.py`
- 実行結果
  - `pytest note\\tests\\test_newalgorithm_phase04_ui_wiring.py -q` -> `17 passed`
  - `pytest note\\tests\\test_newalgorithm_phase06_logging_compat.py -q` -> `17 passed`

## Handoff to Next Phase

- Phase04 では build / execute / log の I/O 契約に絞る
