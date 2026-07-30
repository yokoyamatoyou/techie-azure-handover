# note_writer_app_split_2026-04-23 TASK

この package は `C:\tetie\notecode\note\note_writer_app.py` の安全な段階分割を separate initiative として固定する。  
`naturalness_recovery_2026-04-07` の current source of truth は置き換えず、`current_mainline_owner_split` completed judgment と `ALGORITHM.md` 不変条件を保ったまま、`1 phase = 1 narrow hypothesis = 1 owner scope` で進める。

## Global Rules

- current success path を壊さない
- `note_writer_app.py` は最後まで UI shell / confirm-before-generate flow / widget mutation / logging trigger timing owner のまま扱う
- final contract resolve / `input_decision` source of truth を UI 側へ戻さない
- logging schema / file persistence owner を `current_mainline_runtime_logging.py` から動かさない
- GPT Image 2 は本文 mainline ではなく post-success work のまま維持する
- persona / editor / trial names を runtime prompt や visible output に戻さない
- structural baseline は `single-pass + optional single repair 1回` を維持する
- `naturalness_recovery_2026-04-07` とこの split package を混ぜない
- completed reference / frozen reference / archive-only records を reopen しない
- 各 phase は runtime 実装の細分化ではなく rollback unit を狭くすることを目的にする
- `run_generation()` body 本体、completion / exception / finally cleanup timing、image prompt step、auto legal postcheck、confirm state mutation は late-phase candidate として park する
- 同一事象の retry-stop は `current_mainline_owner_split` に合わせて `2` 回までとする
- 2 回失敗したら phase rollback 後に停止し user report する

## Entry Gate

- `README.md` / `PROGRESS.md` / `ROLLBACK.md` に split initiative と global current source of truth の差が固定されている
- `note_writer_app.py` current facts が package docs に固定されている
- `OWNER_MAP.md` の owner boundary と `ALGORITHM.md` 不変条件を参照済みである
- phase hypothesis が `1 owner scope` に閉じている
- late-phase risk を初手に含めていない

## Pass Gate

- touched files が phase owner に閉じている
- `C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile <touched files>` が通る
- package に定義した phase local pytest が通る
- `C:\tetie\notecode\logs\app.log` に import / startup traceback の新規増加がない
- 必要な場合のみ `latest_ui_journey.json` / `latest_generation_output.json` / `latest_generation_quality_report.json` shape を確認し、runtime drift がない
- `PROGRESS.md` と `C:\tetie\WORKLOG.md` に結果が反映されている

## Stop Gate

- phase を完了するために `run_generation()` body 本体へ踏み込む必要が出た
- completion / exception / finally cleanup timing owner を動かさないと前進できない
- `input_decision` / logging schema / file persistence / runner decision owner をまたぐ必要が出た
- rollback 不能な wide edit になった
- current success path regression が出た
- 同一事象で `2/2` 失敗した

## Required Checks

### Common Checks

- `C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile <touched files>`
- `C:\tetie\notecode\logs\app.log` に import / startup traceback 増加がないこと

### Phase-Local Pytest Plan

- Phase 01:
  - `test_note_writer_app_head_assets.py`
  - `test_note_writer_app_phase01_minimal_ui.py`
  - `test_note_writer_app_ui_simulation.py`
- Phase 02:
  - `test_note_writer_app_source_helpers.py`
  - `test_note_writer_app_phase01_minimal_ui.py`
  - `test_note_writer_app_ui_simulation.py`
- Phase 03:
  - `test_note_writer_app_subviews.py`
  - `test_note_writer_app_phase01_minimal_ui.py`
  - `test_note_writer_app_ui_simulation.py`
  - `test_note_writer_app_post_success_helpers.py`
- Phase 04:
  - `test_note_writer_app_manual_legal_helpers.py`
  - `test_note_writer_app_post_success_helpers.py`
  - `test_note_writer_app_snapshot_helpers.py`
- Phase 05:
  - `test_note_writer_app_main_page_sections.py`
  - `test_note_writer_app_phase01_minimal_ui.py`
  - `test_note_writer_app_generation_gate_helpers.py`
  - `test_note_writer_app_ui_simulation.py`
  - `test_current_mainline_ui_matrix.py`
- Phase 06:
  - `test_note_writer_app_generation_execution_helpers.py`
  - `test_note_writer_app_post_success_helpers.py`
  - `test_note_writer_app_snapshot_helpers.py`
  - `test_current_mainline_ui_result_adapter.py`
  - `test_newalgorithm_phase04_ui_wiring.py`
  - `test_current_mainline_ui_matrix.py`

### Log Shape Checks For Phase 04+

- `C:\tetie\notecode\logs\latest_ui_journey.json`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\latest_generation_quality_report.json`

## Phase Map

### Phase 01 Head Assets

- Objective:
  - `app.colors` と 2 本の `ui.add_head_html` を safe asset module へ退避する
- Hypothesis:
  - head assets は import-time side effects を増やさず、call order を `note_writer_app.py` に残したまま外出しできる
- Owner:
  - `note_writer_app.py`
- Touched files:
  - `C:\tetie\notecode\note\note_writer_app.py`
  - `C:\tetie\notecode\note\note_writer_app_head_assets.py`
  - `C:\tetie\notecode\note\tests\test_note_writer_app_head_assets.py`
- Required checks:
  - `py_compile` on touched files
  - `test_note_writer_app_head_assets.py`
  - `test_note_writer_app_phase01_minimal_ui.py`
  - `test_note_writer_app_ui_simulation.py`
- Rollback if:
  - import 時例外
  - sticky step JS 破損
  - CSS class / id drift

### Phase 02 Source / Upload / Bootstrap Helpers

- Objective:
  - source add/remove、upload save、recent restore、cleanup target selection を helper module へ出す
- Hypothesis:
  - state mutation / `ui.notify` / refresh timing を `note_writer_app.py` に残せば、source helper 部分だけ narrow に外出しできる
- Owner:
  - `note_writer_app.py`
- Touched files:
  - `C:\tetie\notecode\note\note_writer_app.py`
  - `C:\tetie\notecode\note\note_writer_app_source_helpers.py`
  - `C:\tetie\notecode\note\tests\test_note_writer_app_source_helpers.py`
- Required checks:
  - `py_compile` on touched files
  - `test_note_writer_app_source_helpers.py`
  - `test_note_writer_app_phase01_minimal_ui.py`
  - `test_note_writer_app_ui_simulation.py`
- Rollback if:
  - source add/remove timing drift
  - upload path or whitelist drift
  - import-time cleanup side effect drift

### Phase 03 Standalone Subviews

- Objective:
  - source list / genre dialogs / privacy blur / generated images / scroll / copy を subview module へ出す
- Hypothesis:
  - callback と shared context を明示引数化すれば subview cluster は UI shell から外出しできる
- Owner:
  - `note_writer_app.py`
- Touched files:
  - `C:\tetie\notecode\note\note_writer_app.py`
  - `C:\tetie\notecode\note\note_writer_app_subviews.py`
  - `C:\tetie\notecode\note\tests\test_note_writer_app_subviews.py`
- Required checks:
  - `py_compile` on touched files
  - `test_note_writer_app_subviews.py`
  - `test_note_writer_app_phase01_minimal_ui.py`
  - `test_note_writer_app_ui_simulation.py`
  - `test_note_writer_app_post_success_helpers.py`
- Rollback if:
  - source list UI drift
  - blur preview / save drift
  - generated image card CTA drift

### Phase 04 Manual Legal Local Helpers

- Objective:
  - `run_legal_check` 周辺の helper / payload だけを module へ外出しする
- Hypothesis:
  - widget mutation と event timing を local に残せば、manual legal helper 部分だけ safe に切れる
- Owner:
  - `note_writer_app.py`
- Touched files:
  - `C:\tetie\notecode\note\note_writer_app.py`
  - `C:\tetie\notecode\note\note_writer_app_manual_legal_helpers.py`
  - `C:\tetie\notecode\note\tests\test_note_writer_app_manual_legal_helpers.py`
- Required checks:
  - `py_compile` on touched files
  - `test_note_writer_app_manual_legal_helpers.py`
  - `test_note_writer_app_post_success_helpers.py`
  - `test_note_writer_app_snapshot_helpers.py`
  - log shape checks
- Rollback if:
  - generated-body recheck drift
  - apply suggestion drift
  - failure-preserve-body drift
- Explicit non-scope:
  - `_resolve_current_mainline_auto_legal_postcheck`

### Phase 05 Main Page Pre-Generation Builders

- Objective:
  - header / journey / source-mode / required-input wizard の layout builder を section module へ出す
- Hypothesis:
  - callback と state mutation を local のまま保てば、pre-generation section builder は narrow に外出しできる
- Owner:
  - `note_writer_app.py`
- Touched files:
  - `C:\tetie\notecode\note\note_writer_app.py`
  - `C:\tetie\notecode\note\note_writer_app_main_page_sections.py`
  - `C:\tetie\notecode\note\tests\test_note_writer_app_main_page_sections.py`
- Required checks:
  - `py_compile` on touched files
  - `test_note_writer_app_main_page_sections.py`
  - `test_note_writer_app_phase01_minimal_ui.py`
  - `test_note_writer_app_generation_gate_helpers.py`
  - `test_note_writer_app_ui_simulation.py`
  - `test_current_mainline_ui_matrix.py`
- Rollback if:
  - source-mode gate drift
  - audience / writer wizard drift
  - journey confirmation drift

### Phase 06 Main Page Post-Generation Builders

- Objective:
  - result / review / image / manual legal panel の layout builder を section module へ出す
- Hypothesis:
  - render builder だけを抜けば、high-risk timing owner を動かさず post-generation UI surface を薄くできる
- Owner:
  - `note_writer_app.py`
- Touched files:
  - `C:\tetie\notecode\note\note_writer_app.py`
  - `C:\tetie\notecode\note\note_writer_app_main_page_sections.py`
  - related tests
- Required checks:
  - `py_compile` on touched files
  - `test_note_writer_app_generation_execution_helpers.py`
  - `test_note_writer_app_post_success_helpers.py`
  - `test_note_writer_app_snapshot_helpers.py`
  - `test_current_mainline_ui_result_adapter.py`
  - `test_newalgorithm_phase04_ui_wiring.py`
  - `test_current_mainline_ui_matrix.py`
  - log shape checks
- Rollback if:
  - preview / result / review / image / legal panel visibility drift
  - terminal timing coupling appears

## Parked Late Candidates

- `run_generation()` body 本体
- completion / exception / finally cleanup timing
- `_run_current_mainline_image_prompt_step`
- `_resolve_current_mainline_auto_legal_postcheck`
- journey confirm state mutation

## Refined Execution Order

- docs-only phase:
  - create package docs
  - update `AGENTS.md` and `WORKLOG.md`
  - do not edit runtime code
- first implementation window:
  - `Phase 01` only
  - if green, update `PROGRESS.md` and `WORKLOG.md`, then stop
- next windows:
  - never chain automatically
  - reopen one phase at a time with one rollback unit
