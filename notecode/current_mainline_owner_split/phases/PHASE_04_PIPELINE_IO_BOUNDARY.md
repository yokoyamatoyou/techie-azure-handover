# PHASE_04_PIPELINE_IO_BOUNDARY

- Last Updated: 2026-03-14

## Objective

- request build、runner execute、snapshot / audit の I/O 契約境界を整理する。

## In Scope

- generation request の組み立て
- runner の execute 入出力
- snapshot / audit に流す key
- field source の追跡可能性

## Out of Scope

- UI wording
- 本文品質
- モデル設定

## Target Owners

- `generation_request_builder.py`
- `current_mainline_runner.py`
- `current_mainline_runtime_logging.py`

## Target Files

- `C:\tetie\notecode\note\generation_request_builder.py`
- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\telemetry_writer.py`
- `C:\tetie\notecode\note\current_mainline_runtime_logging.py`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\generation_audit_log.jsonl`

## Preconditions

- Phase03 completed
- UI / logging の責務境界が確定している

## Tasks

1. build / execute / snapshot / audit の I/O 契約を列挙する
2. 重複保持している field を洗い出す
3. source of truth を concern ごとに 1 つへ寄せる
4. rollback 条件を整理する

## Findings

### 事実

- `current_mainline_runner.py::resolve_current_mainline_ui_selection()` が UI journey から `article_type` / `semantic_article_key` / `comparison_axes` を route 解決する owner。
  - `generation_request_builder.py` は route 判定を持たず、runner が解決した値を受け取って raw contract に載せる。
- `generation_request_builder.py::build_raw_input_contract()` は raw transport owner。
  - `source` と `source_inputs` に同じ正規化済み source list を入れる。
  - `prompt_raw` と `topic` に同じ user prompt を入れる。
  - `length_mode` と `length_mode_requested` を同値で保持する。
  - `field_sources` / `ui_journey` / `semantic_article_key` / `comparison_axes` を transport metadata として残す。
  - この段階では `source_fit` / `source_grounding_status` / `input_decision` を確定しない。
- `current_mainline_runner.py::build_current_mainline_input_contract()` は `resolve_current_mainline_ui_selection()` -> `build_raw_input_contract()` -> `normalize_input_contract_v1()` の順で current mainline の normalized input を作る。
  - runner は normalized contract を返すが、final resolve owner ではない。
- `generation_request_builder.py::build_pipeline_payload()` は execute 向け adapter owner。
  - `input_contract` を shallow copy した payload に対して `source_inputs` から `source` を再構築する。
  - generation 実行時の `user_prompt_text` で `prompt_raw` と `topic` を再上書きする。
  - 元の `input_contract` は mutate しない。
- `newalgorithm_pipeline/pipeline.py::MinimalPipeline.generate()` は generation 本体の resolved contract owner。
  - 先頭で `resolve_input_contract(payload)` を再実行し、stop / clarify / accept を final に判定する。
  - accept path では resolved contract を `build_pipeline_check(contract=contract, ...)` に渡す。
- `newalgorithm_pipeline/telemetry_writer.py::build_pipeline_check()` は `pipeline_check.input_contract` に resolved contract をそのまま格納する。
  - snapshot / audit 側が見る contract の正本は raw builder 出力ではなく pipeline 側で再 resolve された contract。
- `current_mainline_runner.py::execute_current_mainline_generation()` は execute wrapper owner。
  - pipeline 例外時は fail-closed result を作り、`pipeline_check.input_contract` に caller 側 `input_contract` を補完する。
  - pipeline が failure result を返した場合も `pipeline_check.input_contract` が欠けないように normalize する。
- `current_mainline_runtime_logging.py::persist_latest_generation_snapshot()` は generation snapshot / audit projection owner。
  - `result["pipeline_check"]["input_contract"]` を唯一の source of truth として読む。
  - `latest_generation_output.json` には full `input_contract` と full `source_fit` を保存する。
  - `generation_audit_log.jsonl` には reduced `input_contract` を保存し、`source_fit` は `source_fit_status` に圧縮する。
- 現物ログも current code と一致している。
  - `latest_generation_output.json` は `input_contract.semantic_article_key` / `ui_journey` / full `source_fit` を保持する。
  - `generation_audit_log.jsonl` は `input_contract.semantic_article_key` / `ui_journey` / `source_fit_status` を保持する。
- テストが current shape を固定している。
  - `test_generation_request_builder.py` は raw build の duplicate fields と `build_pipeline_payload()` の non-mutation を固定する。
  - `test_current_mainline_runner.py` は execute path の `pipeline_check.input_contract` fallback と prompt refresh を固定する。
  - `test_newalgorithm_phase06_logging_compat.py` は snapshot が full contract、audit が reduced projection であることを固定する。

### 推測

- current code の duplicate fields は accidental な owner 混線ではなく、compatibility transport と projection 粒度の違いを吸収するための保持とみるのが妥当。
- `source` / `topic` / `length_mode_requested` を安易に削ると、runner・pipeline・logging のいずれかで compat break を起こす可能性が高い。

## IO Contract by Stage

| Stage | Owner | Input | Output | Source of Truth |
|---|---|---|---|---|
| UI route resolve | `current_mainline_runner.py::resolve_current_mainline_ui_selection()` | `article_type`, `ui_journey`, `comparison_axes` | route-resolved `article_type`, `semantic_article_key`, `ui_journey`, `comparison_axes` | runner |
| raw request build | `generation_request_builder.py::build_raw_input_contract()` | resolved selection, UI fields, interview answers, sources | raw input contract | builder transport |
| normalized current input | `current_mainline_runner.py::build_current_mainline_input_contract()` | raw input contract | normalized input contract | runner wrapper |
| confirm resolve | `input_contract.py::resolve_input_contract()` via runner | normalized input contract | resolved contract, `input_decision`, `source_fit` | input contract owner |
| generate payload adapt | `generation_request_builder.py::build_pipeline_payload()` | caller `input_contract`, generation-time prompt | payload with refreshed `source` / `prompt_raw` / `topic` | builder adapter |
| generation resolve / execute | `pipeline.py::MinimalPipeline.generate()` | payload | success or fail-closed result with `pipeline_check` | pipeline |
| pipeline telemetry build | `telemetry_writer.py::build_pipeline_check()` | resolved contract + runtime artifacts | `pipeline_check.input_contract` and related telemetry | pipeline helper |
| latest snapshot / audit | `current_mainline_runtime_logging.py::persist_latest_generation_snapshot()` | generation `result`, attempt metadata | latest JSON/TXT, quality report, audit line | logging projection |

## Intentional Redundancy

- `source` / `source_inputs`
  - transport owner: `generation_request_builder.py`
  - runtime meaning: execute payload は毎回 `source_inputs` から `source` を再構築する
  - したがって stable transport field は `source_inputs`、`source` は execute alias として扱う
- `prompt_raw` / `topic`
  - transport owner: `generation_request_builder.py`
  - execute owner: generation 実行時は `build_pipeline_payload()` が両方を最新 prompt で再同期する
  - stale confirm preview prompt を generation に持ち込まないための duplicate
- `length_mode` / `length_mode_requested`
  - current code では同値保持
  - audit / compatibility では requested value を明示的に残すため削除しない
- snapshot `input_contract.source_fit` / audit `input_contract.source_fit_status`
  - source of truth はどちらも `pipeline_check.input_contract.source_fit`
  - snapshot は full projection、audit は compact projection
- `article_type` / `semantic_article_key`
  - 同義ではない
  - `article_type` は runtime category、`semantic_article_key` は UI journey semantic trace

## Owner Decision

- UI route mapping と legacy fallback route: `current_mainline_runner.py`
- raw field gather / duplicate transport / execute payload adaptation: `generation_request_builder.py`
- final resolved contract meaning (`source_fit`, `source_grounding_status`, `input_decision`): `input_contract.py`
- generation result の `pipeline_check.input_contract` 化: `pipeline.py` + `telemetry_writer.py`
- generation fail-closed 時の `pipeline_check.input_contract` fallback: `current_mainline_runner.py`
- latest snapshot / audit の保存粒度: `current_mainline_runtime_logging.py`

## Rollback Conditions

- `source_inputs` を削除しない。
  - execute payload が `source` をここから再構築しているため。
- `prompt_raw` と `topic` の二重保持を削除しない。
  - execute path と downstream helper の互換が崩れるため。
- `length_mode_requested` を audit から外さない。
  - requested/effective の切り分け導線が失われるため。
- `execute_current_mainline_generation()` の `pipeline_check.input_contract` fallback を外さない。
  - pipeline failure 時に snapshot / audit の traceability が切れるため。
- snapshot を reduced shape、audit を full shape に寄せない。
  - current compat tests は「snapshot full / audit compact」を前提にしているため。

## Conclusion

- current code 基準では、build / execute / snapshot / audit の主境界は矛盾していない。
- 重複 field の多くは owner split の失敗ではなく、transport alias と compact projection のための intentional redundancy で説明できる。
- runtime code の最小修正は不要。
- 以後 shape を触る場合は 1 owner ずつ切る。
  - request build shape: `generation_request_builder.py`
  - fail-closed generation trace: `current_mainline_runner.py`
  - snapshot / audit schema: `current_mainline_runtime_logging.py`

## Exit Criteria

- build / execute / snapshot / audit の境界が文書で説明可能
- field の重複保持が把握されている
- rollback 条件が文書で説明可能

## Required Tests

- `py_compile` 対象 owner
- `pytest note\tests\test_current_mainline_runner.py -q`
- 必要時のみ `pytest note\tests\test_generation_request_builder.py -q`
- 必要時のみ `pytest note\tests\test_newalgorithm_phase06_logging_compat.py -q`

## Code Bug Check

- 同じ field を複数 owner が正本扱いしていないか確認する

## Pipeline Bug Check

- request build から audit まで field が途切れていないか確認する
- snapshot と latest output の key が矛盾していないか確認する

## LLM Safety Check

- source field や system-owned field が build 段階で越権混入していないか確認する

## Retry Rule

- 同一事象の修正試行は最大 2 回

## Stop Condition

- builder / runner / logging の 3 owner 以上へ同時修正が必要と判明した場合は停止して slice を切り直す

## Evidence to Record

- I/O 契約表
- 該当ログ key
- rollback 条件

## Evidence Recorded

- コード
  - `generation_request_builder.py::build_raw_input_contract()`
  - `generation_request_builder.py::build_pipeline_payload()`
  - `current_mainline_runner.py::resolve_current_mainline_ui_selection()`
  - `current_mainline_runner.py::build_current_mainline_input_contract()`
  - `current_mainline_runner.py::execute_current_mainline_generation()`
  - `newalgorithm_pipeline/pipeline.py::MinimalPipeline.generate()`
  - `newalgorithm_pipeline/telemetry_writer.py::build_pipeline_check()`
  - `current_mainline_runtime_logging.py::persist_latest_generation_snapshot()`
- ログ
  - `notecode/logs/latest_generation_output.json`
  - `notecode/logs/generation_audit_log.jsonl`
- テスト
  - `note/tests/test_generation_request_builder.py`
  - `note/tests/test_current_mainline_runner.py`
  - `note/tests/test_newalgorithm_phase06_logging_compat.py`

## Handoff to Next Phase

- Phase05 では acceptance、rollback、handoff 導線を固定する
