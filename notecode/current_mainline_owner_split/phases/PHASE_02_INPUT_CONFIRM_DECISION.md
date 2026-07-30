# PHASE_02_INPUT_CONFIRM_DECISION

- Last Updated: 2026-03-14

## Objective

- input decision、confirm preview、generation 本体の判定責務を owner 単位で固定する。

## In Scope

- `reason_code`
- `allow_generate`
- `needs_input`
- `source_fit`
- confirm preview と generation 本体の判定順

## Out of Scope

- UI 表示改善
- logging key の追加変更
- 本文品質改善

## Target Owners

- `input_contract.py`
- `current_mainline_runner.py`

## Target Files

- `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\logs\latest_ui_journey.json`
- `C:\tetie\logs\ui_journey_log.jsonl`

## Preconditions

- Phase01 completed
- owner map が確定している

## Tasks

1. source 要件の定義位置を確認する
2. `source_fit.status` が保証する範囲を確認する
3. `INP_SOURCE_CONTEXT_INSUFFICIENT` の owner を確定する
4. confirm preview と generation 本体で別判定になっていないか確認する
5. 仕様として妥当か、強すぎるかを事実と推測に分けて記録する

## Findings

### 事実

- `source_fit` owner は `input_contract.py::_build_source_fit()`。
  - `improvement_case` は improvement signal があれば `pass`、なければ `block`。
  - `source_fit` は「semantic key と source signal の適合」を示し、`source_grounding_status` の十分性までは保証しない。
- `source_grounding_status` owner は `input_contract.py::_derive_source_grounding_status()`。
  - `source_grounding_required=true` かつ grounding item が 2 件未満なら `insufficient`。
- strict source context gate owner は `input_contract.py::_requires_strict_source_context_gate()`。
  - current code では `_is_company_introduction_like()` のみを返し、`improvement_case` は strict gate 対象外。
- `reason_code` / `needs_input_items` の final owner は `input_contract.py::build_contract_input_decision()`。
  - `source_fit.status=block` または company-intro strict gate のときだけ `INP_SOURCE_CONTEXT_INSUFFICIENT` を返す。
- confirm preview owner は `current_mainline_runner.py::build_current_mainline_confirm_preview()`。
  - `resolve_input_contract()` が返した `input_decision` をそのまま投影し、`allow_generate` は `action == "accept"` で決める。
- generation 本体の stop / continue 判定 owner は `newalgorithm_pipeline/pipeline.py::MinimalPipeline.generate()`。
  - 先頭で再度 `resolve_input_contract()` を実行し、同じ `input_decision` で fail-closed する。
- `note_writer_app.py` は confirm state を保持する UI owner であり、input decision owner ではない。
  - confirm 後に入力が変わると `_invalidate_journey_confirmation()` で再確定を要求する。
- 2026-03-14 回帰テストは current behavior と整合した。
  - `pytest note\\tests\\test_current_mainline_runner.py -q` -> `17 passed`
  - `pytest note\\tests\\test_current_mainline_regressions.py -q` -> `20 passed`
  - `test_current_mainline_improvement_case_accepts_sparse_grounding_when_source_fit_passes()` は `source_fit=pass` / `source_grounding_status=insufficient` / `input_decision=accept` を固定している。
- ローカル再現でも `improvement_case` は current code 上で preview / generate とも stop しない。
  - preview: `allow_generate=True`, `reason_code=OK`
  - generate: dummy LLM 付きで `runtime_reason_code=OK`, `pipeline_check.input_decision.action=accept`

### 推測

- `latest_ui_journey.json` / `ui_journey_log.jsonl` に残る 2026-03-13 の `improvement_case -> INP_SOURCE_CONTEXT_INSUFFICIENT` は historical artifact であり、2026-03-14 current code の単独根拠には使えない可能性が高い。
- preview stop の主因は current runtime owner の仕様ではなく、2026-03-13 時点の旧 runtime state、または stale UI/log artifact の残留である可能性が高い。

## Owner Decision

- `reason_code`: `input_contract.py::build_contract_input_decision()`
- `needs_input_items`: `input_contract.py::build_contract_input_decision()` と各 item builder
- `allow_generate`: `current_mainline_runner.py::build_current_mainline_confirm_preview()`
- `source_fit`: `input_contract.py::_build_source_fit()`
- `source_grounding_status`: `input_contract.py::_derive_source_grounding_status()`
- generation stop / continue 実行: `newalgorithm_pipeline/pipeline.py::MinimalPipeline.generate()`

## 判定順

1. `current_mainline_runner.py::resolve_current_mainline_ui_selection()`
2. `current_mainline_runner.py::build_current_mainline_input_contract()`
3. `generation_request_builder.py::build_raw_input_contract()`
4. `input_contract.py::resolve_input_contract()`
5. `input_contract.py::build_contract_input_decision()`
6. confirm preview では `current_mainline_runner.py::build_current_mainline_confirm_preview()` が `allow_generate` を投影
7. generation 本体では `newalgorithm_pipeline/pipeline.py::MinimalPipeline.generate()` が再度 `resolve_input_contract()` を実行し、同じ `input_decision` で停止可否を確定

## Conclusion

- `improvement_case` の current source gate は「source signal による `source_fit` gate」であり、「source grounding insufficiency による strict gate」ではない。
- したがって current code 基準では、`source_fit_status=pass` と `INP_SOURCE_CONTEXT_INSUFFICIENT` は `improvement_case` では両立しない。
- `source_fit_status=pass` と preview stop が両立する current code 上の説明は company-introduction-like に限定される。
- 今回の論点について runtime code の最小修正は不要。
- Phase03 へは「UI 表示と logging 投影に historical stop artifact がどう見えるか」を切り出して進む。

## Exit Criteria

- 判定責務の owner が明記されている
- confirm / generate の判定順が説明可能
- 過剰 gate か仕様かを owner 単位で説明可能

## Required Tests

- `py_compile` 対象 owner
- `pytest note\tests\test_current_mainline_runner.py -q`
- `pytest note\tests\test_current_mainline_regressions.py -q`

## Code Bug Check

- 判定ロジックの重複 owner がないか確認する
- `source_fit` と `input_decision` が別責務として整理されているか確認する

## Pipeline Bug Check

- confirm preview と generation 本体で別判定になっていないか確認する
- latest journey と audit に reason が整合しているか確認する

## LLM Safety Check

- prompt injection で `needs_input` や system-owned field が越権していないか確認する
- 過剰 gate が LLM safety ではなく仕様誤適用でないか確認する

## Retry Rule

- 同一事象の修正試行は最大 2 回

## Stop Condition

- 判定 owner が 2 か所以上に分裂していて切り戻し方針が定まらない場合
- runtime と品質の切り分けが崩れる場合

## Evidence to Record

- 該当コードの関数名
- 該当ログの reason / status
- 事実と推測の切り分け

## Evidence Recorded

- コード
  - `input_contract.py::_build_source_fit()`
  - `input_contract.py::_derive_source_grounding_status()`
  - `input_contract.py::_requires_strict_source_context_gate()`
  - `input_contract.py::build_contract_input_decision()`
  - `current_mainline_runner.py::build_current_mainline_confirm_preview()`
  - `newalgorithm_pipeline/pipeline.py::MinimalPipeline.generate()`
  - `note_writer_app.py::_invalidate_journey_confirmation()`
- ログ
  - `notecode/logs/latest_ui_journey.json`
  - `logs/ui_journey_log.jsonl`
  - 2026-03-13 の `improvement_case` preview stop は historical evidence として分離
- テスト
  - `note/tests/test_current_mainline_runner.py`
  - `note/tests/test_current_mainline_regressions.py`
- ローカル再現
  - sparse grounding の `improvement_case` で preview / generate とも `OK` を確認

## Handoff to Next Phase

- Phase03 では UI 表示と logging 投影の見え方だけに絞る
