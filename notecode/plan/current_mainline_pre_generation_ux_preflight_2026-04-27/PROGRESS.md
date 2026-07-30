# PROGRESS

## 2026-04-27

Status: Phase 0 + Phase 1 implemented. Phase 2 / Phase 3 not implemented.

### Phase 0

- Confirmed `prompt_builder.py` was at failed naturalness prompt surface after hash `4F29076F...`.
- No Git repo / exact `82DC095B...` backup was available.
- Manually rolled back the failed prompt surface additions described in WORKLOG.
- Kept accepted launch-blocker source contract files:
  - `company_intro_source_contract.py`: `A27EFB795402D2F1186BB98084BEE8BE441C58867062F21305B54728D46E6508`
  - `company_intro_source_contract_guard.py`: `2327FF6CE4D82F1EE5E33D24D4E6D6D3956CF086192CC9FA3721590BD41BFEEA`
- Current `prompt_builder.py` hash after manual rollback:
  - `2BB17FAF9034B2315FE8AA85A20B6074F277C51CC3EEDBF5BF9B699E353F8E58`

### Phase 1

- `journey_confirm_button` now runs confirmation only.
- Journey generation button is visible as an explicit action.
- The generation button label is `この内容で生成を開始`.
- Missing / stale journey confirmation is rejected before generation begins.
- Confirmation required message now tells the user to confirm first, then press the explicit generation button.
- Initial Step 4 badge is `未確認`.

### Changed Files

- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\note_writer_app_main_page_sections.py`
- `C:\tetie\notecode\note\current_mainline_ui_result_adapter.py`
- `C:\tetie\notecode\note\tests\test_note_writer_app_generation_gate_helpers.py`
- `C:\tetie\notecode\note\tests\test_current_mainline_ui_result_adapter.py`
- `C:\tetie\notecode\note\tests\test_newalgorithm_phase06_logging_compat.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

### Checks

- `py_compile`: passed.
- focused UI helper tests: `96 passed`.
- result adapter / logging compat tests: `64 passed`.
- prompt rollback regression tests: `113 passed, 132 deselected`.
- current mainline runner company intro tests: `11 passed, 65 deselected`.

### UI Smoke

- 8080 restarted to load current code: PID `26280` -> `3036`.
- Repro URL 4件 added and retained in the UI:
  - `https://www.sanin-sanso.co.jp/`
  - `https://www.sanin-sanso.co.jp/company/info/`
  - `https://www.sanin-sanso.co.jp/company/history/`
  - `https://www.sanin-sanso.co.jp/home/price/`
- Journey selection changed to `会社・サービスの紹介記事を書く` / `自社・会社紹介`.
- `不足を確認` / `内容を確認` did not increase `Generation started`.
  - before confirmation click: `Generation started` count `299`
  - after confirmation click: `Generation started` count `299`
- Confirmation made the explicit generation button visible/enabled as `この内容で生成を開始`.
- Explicit generation click increased `Generation started` to `300`.
- Smoke attempt: `gen-75fac897`
  - `source_count=4`
  - URL source logs retained all 4 URLs.
  - fetch summary `success=4 failure=0`
  - generation core completed.
- 8080 listener retained on PID `3036`.
  - No new `deleted client`, `deleted slot`, `ERR_CONNECTION_REFUSED`, `Accept failed` observed in the checked tail.
