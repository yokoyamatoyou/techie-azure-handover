# Owner Map

- Last Updated: 2026-03-16

## Boundary Rule

- owner は「判断責務がどこにあるか」で切る。
- 同じ判断を複数 owner に重複させない。
- UI shell、input decision、request build、runtime logging を分離して扱う。
- `Called By / Calls To` は production の direct edge だけを書く。
- `Related Logs` は direct write と projected field を分けて書く。

## Owner Table

| Owner File | Primary Responsibility | Non-Responsibility | Primary Inputs | Primary Outputs | Called By | Calls To | Related Logs | Related Tests |
|---|---|---|---|---|---|---|---|---|
| `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py` | `normalize_input_contract_v1()` 後の final contract resolve。`semantic_article_key` fallback、`source_grounding_items` / `source_grounding_status`、`source_fit`、`need_question`、`input_decision` を確定する | UI route mapping、raw field gathering、confirm UI 文言、snapshot / audit 永続化 | raw input contract、pipeline payload、`source_documents`、prompt intent signal | resolved contract、`input_decision`、`question_items`、`source_fit`、`source_grounding_status` | `current_mainline_runner.py`、`newalgorithm_pipeline/pipeline.py` | `input_contract_v1.py`、`intent_profile.py`、`interview_contract_mapper.py` | direct: なし<br>projected: `latest_generation_output.json.input_contract`、`generation_audit_log.jsonl.input_contract`、`latest_ui_journey.json.events[].extra.source_fit_status` | direct: `test_current_mainline_runner.py`、`test_current_mainline_regressions.py`<br>cross-owner: `test_newalgorithm_phase06_logging_compat.py` |
| `C:\tetie\notecode\note\current_mainline_runner.py` | UI selection を route に解決し、question policy / confirm preview / generate 実行を orchestration する。pipeline error を fail-closed に正規化し、success 結果へ output guard を適用する。approved route の Phase04 rehearsal では `pipeline_check.cutover_rehearsal` を投影する | `input_decision` ルール確定、UI status text、confirm state 保持、log schema / file write | UI journey 選択、raw form args、pipeline instance、`prompt_raw` | resolved selection、question policy、confirm preview、generation result、approved route rehearsal projection | `note_writer_app.py` | `generation_request_builder.py`、`input_contract.py`、`newalgorithm_pipeline/pipeline.py::MinimalPipeline.generate`、`output_guard.py` | direct: なし<br>projected: `note_writer_app.py` 経由で UI journey / snapshot に載る `reason_code`、`allow_generate`、`semantic_article_key`、`pipeline_check.cutover_rehearsal` | direct: `test_current_mainline_runner.py`<br>cross-owner: `test_current_mainline_ui_matrix.py`、`test_newalgorithm_phase04_ui_wiring.py` |
| `C:\tetie\notecode\note\generation_request_builder.py` | UI / interview / source 入力から raw input contract と pipeline payload を組み立て、`field_sources`、`ui_journey`、`comparison_axes` を保全する | final `semantic_article_key` fallback、`input_decision`、confirm gate、UI logging | UI form state、resolved selection、source inputs / documents、interview answers | raw input contract、pipeline payload、`field_sources` metadata | `current_mainline_runner.py` | `current_mainline_input_policy.py`、`interview_contract_mapper.py`、`source_document_utils.py` | direct: なし<br>projected: `latest_generation_output.json.input_contract.field_sources`、`generation_audit_log.jsonl.input_contract` | direct: `test_generation_request_builder.py`<br>cross-owner: `test_current_mainline_runner.py` |
| `C:\tetie\notecode\note\note_writer_app.py` | NiceGUI の UI state と confirm-before-generate flow を持ち、widget binding、confirm state mutation、logging call timing を確定する | final contract resolve、`input_decision` の source of truth、log JSON schema / file path、quality metric の算出 | user interaction、app state、source contexts、runner outputs | selection summary、confirm state、表示更新、runtime logging への wrapper 引数 | user interaction / NiceGUI events | `current_mainline_runner.py`、`current_mainline_runtime_logging.py`、`current_mainline_ui_confirm_adapter.py`、`current_mainline_ui_generation_state_adapter.py`、`current_mainline_ui_result_adapter.py`、`current_mainline_ui_generation_telemetry_adapter.py` | direct trigger: `latest_ui_journey.json`、`ui_journey_log.jsonl`、`latest_generation_output.json`、`latest_generation_quality_report.json`、`generation_audit_log.jsonl` を wrapper 経由で起動<br>direct write: なし | direct: `test_newalgorithm_phase04_ui_wiring.py`、`test_current_mainline_ui_matrix.py`<br>cross-owner: `test_current_mainline_regressions.py` |
| `C:\tetie\notecode\note\current_mainline_ui_generation_state_adapter.py` | `run_generation()` の pre-run UI reset/start transition plan、top-level exception transition plan、finally cleanup transition plan、complete terminal state transition plan を plain-data 化して組み立てる | actual widget mutation、start timestamp、phase progress、logging / snapshot trigger timing、outcome 決定、finish logging、result projection | pre-delay notice、preview placeholder、exception phase | pre-run state plan dict、exception state plan dict、cleanup state plan dict、complete state plan dict | `note_writer_app.py` | module 内 helper のみ | direct: なし | direct: `test_current_mainline_ui_generation_state_adapter.py` |
| `C:\tetie\notecode\note\current_mainline_ui_generation_telemetry_adapter.py` | `run_generation()` の UI journey event payload、pre-generate reject / pause gate extra、latest snapshot kwargs を plain-data 化して組み立てる | logging schema / file persistence、trigger timing、UI widget mutation、quality gate 判定 | attempt metadata、source items、selection summary、prompt metadata、result / blocked flag | event request dict、generation gate extra dict、snapshot request dict | `note_writer_app.py` | module 内 helper のみ | direct: なし<br>projected: `note_writer_app.py` 経由で UI journey / snapshot に渡る `status_text`、`reason_code`、`question_generation_owner`、`generation_gate_kind`、snapshot kwargs | direct: `test_current_mainline_ui_generation_telemetry_adapter.py`<br>cross-owner: `test_newalgorithm_phase06_logging_compat.py` |
| `C:\tetie\notecode\note\current_mainline_runtime_logging.py` | UI journey / latest snapshot / quality report / audit の schema shaping と file persistence を担う。`runtime_reason_code` の分類は projection 用に限定する | `input_decision` の一次判定、UI 文言、confirm / generate orchestration、quality gate 判定 | result、`pipeline_check.input_contract`、attempt metadata、status text、telemetry | `latest_ui_journey.json`、`ui_journey_log.jsonl`、`latest_generation_output.txt/json`、`latest_generation_quality_report.json`、`generation_audit_log.jsonl` | `note_writer_app.py` | module 内 helper のみ | direct write: `latest_ui_journey.json`、`ui_journey_log.jsonl`、`latest_generation_output.txt/json`、`latest_generation_quality_report.json`、`generation_audit_log.jsonl`<br>projected: `latest_ui_journey.json.latest_decision`、`latest_ui_journey.json.latest_generation_gate` | direct: `test_newalgorithm_phase06_logging_compat.py`<br>cross-owner: `test_current_mainline_regressions.py` |

## Cross-Owner Call Map

- `note_writer_app.py` -> `current_mainline_runner.py`
- `note_writer_app.py` -> `current_mainline_runtime_logging.py`
- `note_writer_app.py` -> `current_mainline_ui_confirm_adapter.py`
- `note_writer_app.py` -> `current_mainline_ui_generation_state_adapter.py`
- `note_writer_app.py` -> `current_mainline_ui_generation_telemetry_adapter.py`
- `note_writer_app.py` -> `current_mainline_ui_result_adapter.py`
- `current_mainline_runner.py` -> `generation_request_builder.py`
- `current_mainline_runner.py` -> `input_contract.py`
- `current_mainline_runner.py` -> `newalgorithm_pipeline/pipeline.py::MinimalPipeline.generate`
- `newalgorithm_pipeline/pipeline.py::MinimalPipeline.generate` -> `input_contract.py`
- production direct edge なし: `current_mainline_runner.py` -> `current_mainline_runtime_logging.py`

## Source of Truth by Concern

- UI route mapping (`purpose_key` / `target_key` -> `article_type` / `semantic_article_key`): `current_mainline_runner.py::resolve_current_mainline_ui_selection()`
- raw input contract / `field_sources` / `ui_journey` 組み立て: `generation_request_builder.py::build_raw_input_contract()`
- final normalized contract / `source_fit` / `input_decision`: `input_contract.py::resolve_input_contract()`
- confirm preview response shape (`allow_generate`, `needs_input_items`): `current_mainline_runner.py::build_current_mainline_confirm_preview()`
- journey confirm signature / preview projection / confirm wording: `current_mainline_ui_confirm_adapter.py`
- generation pre-run UI reset/start transition plan: `current_mainline_ui_generation_state_adapter.py::build_current_mainline_generation_prerun_plan()`
- generation top-level exception UI transition plan: `current_mainline_ui_generation_state_adapter.py::build_current_mainline_generation_exception_plan()`
- generation finally cleanup UI transition plan: `current_mainline_ui_generation_state_adapter.py::build_current_mainline_generation_cleanup_plan()`
- generation complete terminal state transition plan: `current_mainline_ui_generation_state_adapter.py::build_current_mainline_generation_complete_plan()`
- generation UI journey event request / pre-generate gate extra / latest snapshot request assembly: `current_mainline_ui_generation_telemetry_adapter.py`
- generation success render projection (`hashtags_plain` / `note_body_text` / `review_sections` / success wording): `current_mainline_ui_result_adapter.py::build_current_mainline_success_view()`
- output guard blocked UI projection (`source_error_content` / blocked wording / `runtime_reason_code` patch): `current_mainline_ui_result_adapter.py::build_current_mainline_output_guard_blocked_view()`
- generate invoke / fail-closed normalization / success path output guard: `current_mainline_runner.py::execute_current_mainline_generation()`
- approved route の Phase04 rehearsal summary: `current_mainline_runner.py::execute_current_mainline_generation() -> pipeline_check.cutover_rehearsal`
- UI confirmation state / status text / 再確定要求: `note_writer_app.py`
- UI journey event schema / persistence: `current_mainline_runtime_logging.py::append_ui_journey_event()`
- `latest_ui_journey.json.latest_generation_gate` projection: `current_mainline_runtime_logging.py::append_ui_journey_event()`
- latest snapshot / quality report / audit schema / persistence: `current_mainline_runtime_logging.py::persist_latest_generation_snapshot()`

## Evidence Note

- current behavior の正本は現コードと 2026-03-14 の回帰テスト (`test_current_mainline_runner.py`, `test_current_mainline_regressions.py`) を優先する。
- 2026-03-13 の `latest_ui_journey.json` / `ui_journey_log.jsonl` に残る `improvement_case` preview stop は履歴として有効だが、current behavior の単独根拠には使わない。

## Open Boundary Risks

- confirm preview は `current_mainline_runner.py` で resolve し、generate 本体は `MinimalPipeline.generate()` で再度 resolve するため、Phase02 で判定順の再確認が必要
- `latest_ui_journey.json.latest_decision` は confirm preview の resolved contract と UI confirm guard (`invalidated` / `no_sources` / `fetch_failed`) を同じ箱へ投影するため、`decision_origin` / `confirm_gate_kind` を併読しないと source of truth を誤読しやすい
- `latest_ui_journey.json.latest_generation_gate` は UI shell の pre-generate reject / pause projection であり、runner / pipeline の gate owner と誤読しないよう `decision_origin=ui_generation_guard` を前提に読む必要がある
- `note_writer_app.py` が logging trigger owner、`current_mainline_runtime_logging.py` が schema / persistence owner なので、event timing と payload schema の責務混線に注意
- `latest_generation_quality_report.json` は projection であり、runtime gate owner と誤読すると runtime / quality の境界が崩れる
