# TASK

## Owner Map

- Phase 0 baseline hygiene owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- Phase 1 UI owner:
  - `C:\tetie\notecode\note\note_writer_app.py`
  - `C:\tetie\notecode\note\note_writer_app_main_page_sections.py`
  - `C:\tetie\notecode\note\current_mainline_ui_result_adapter.py`
  - focused tests under `C:\tetie\notecode\note\tests\`
- Phase 2 source preflight owner:
  - pending; not implemented in this package.
- Phase 3 naturalness / repair trigger owner:
  - pending; not implemented in this package.
- Prompt surface owner:
  - rollback only; no new prompt expansion.

## Phase Order

1. Phase 0: rollback failed prompt surface additions.
2. Phase 1: separate `内容を確認` and explicit generation.
3. Phase 2: lightweight source preflight after Phase 1 green.
4. Phase 3: naturalness / repair trigger diagnosis after Phase 2.
5. Phase 4: final 8080 UI smoke.

## Phase 1 Acceptance

- `不足を確認` / `内容を確認` does not call `run_generation()`.
- Generation starts only from `この内容で生成を開始`.
- Journey stale / missing confirmation stops before `Generation started`.
- URL source list is not cleared by confirmation state refresh.
- UI / visible text does not expose internal implementation terms.
- 8080 smoke checks URL retention and generation start boundary.

## Checks

Required focused checks:

- `.\.venv\Scripts\python.exe -m py_compile note\note_writer_app.py note\note_writer_app_main_page_sections.py note\current_mainline_ui_result_adapter.py note\simple_note_pipeline\prompt_builder.py`
- `.\.venv\Scripts\python.exe -m pytest note\tests\test_note_writer_app_generation_execution_helpers.py note\tests\test_note_writer_app_generation_gate_helpers.py note\tests\test_note_writer_app_main_page_sections.py -q`

Additional rollback / adapter checks:

- `.\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_result_adapter.py note\tests\test_newalgorithm_phase06_logging_compat.py -q`
- `.\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "company_intro or company_introduction or generation_prompt" -q`
- `.\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py -k "company_intro or company_introduction" -q`
