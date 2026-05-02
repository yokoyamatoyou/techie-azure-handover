# separate window execution prompt note_writer_app split phase03 subviews 2026-04-23

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\README.md
- C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\TASK.md
- C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md
- C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\ROLLBACK.md
- C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\EXECUTION_PROMPT.md
- C:\tetie\notecode\current_mainline_owner_split\EXECUTION_RULES.md
- C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md
- C:\tetie\notecode\current_mainline_owner_split\TEST_AND_SAFETY_MATRIX.md
- C:\tetie\notecode\current_mainline_owner_split\NOTE_WRITER_APP_WINDOW_HANDOFF_2026-04-23.md
- C:\tetie\notecode\ALGORITHM.md
  - ## 4. Single-Pass Generation
  - ## 5. Repair Algorithm
  - ## 12. Persona / Source Packet / Editing Persona Contract
  - ## 13. GPT Image 2 Image Generation Algorithm
- C:\tetie\notecode\note\note_writer_app.py
- C:\tetie\notecode\note\note_writer_app_head_assets.py
- C:\tetie\notecode\note\note_writer_app_source_helpers.py
- C:\tetie\WORKLOG.md

今回の依頼種別:
- separate-window implementation prompt
- `NOTE_WRITER_APP_SPLIT_PHASE03_STANDALONE_SUBVIEWS`
- docs-only prompt ではない

今回の判断:
- `Phase 01` と `Phase 02` が green で閉じているため、分割はまだ続けてよい
- ただし high-risk owner は依然 parked のままなので、次は `Phase 03: Standalone Subviews` だけに閉じる

この window の primary objective:
- source list / custom genre list-edit-delete dialogs / privacy blur dialog / generated images container / scroll-copy helper を `C:\tetie\notecode\note\note_writer_app_subviews.py` へ narrow に外出しする
- callback と shared context を明示引数化し、`note_writer_app.py` の hidden ownership を増やさない
- `run_generation()`、confirm state mutation、logging trigger timing、manual legal timing は local に残す

current code anchors:
- `sources_container()` around `note_writer_app.py:1596`
- `custom_genres_container()` around `note_writer_app.py:1627`
- `_open_edit_dialog()` around `note_writer_app.py:1649`
- `_confirm_delete_genre()` around `note_writer_app.py:1715`
- `_open_privacy_blur_dialog()` around `note_writer_app.py:1739`
- `generated_images_container()` around `note_writer_app.py:1912`
- `_scroll_to_generation_result()` around `note_writer_app.py:1960`
- `_copy_text()` around `note_writer_app.py:1966`

今回触ってよいファイル:
- C:\tetie\notecode\note\note_writer_app.py
- C:\tetie\notecode\note\note_writer_app_subviews.py
- C:\tetie\notecode\note\tests\test_note_writer_app_subviews.py
- green の場合のみ:
  - C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md
  - C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\EXECUTION_PROMPT.md
  - C:\tetie\WORKLOG.md

今回触ってはいけないファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\notecode\note\current_mainline_runner.py
- C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
- C:\tetie\notecode\note\current_mainline_runtime_logging.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\note_writer_app_head_assets.py
- C:\tetie\notecode\note\note_writer_app_source_helpers.py
- C:\tetie\notecode\note\note_writer_app_manual_legal_helpers.py
- C:\tetie\notecode\note\note_writer_app_main_page_sections.py

実装ルール:
- `note_writer_app_subviews.py` には standalone subview builder と pure UI helper だけを置く
- `note_writer_app.py` 側には次を残す:
  - `state` mutation
  - `ui.notify`
  - `_log_ui_usage`
  - refresh timing
  - privacy blur preview/save 実処理
  - generated image run / refresh timing
  - `run_generation()` body
  - confirm state mutation
  - import-time cleanup
- custom genre は list / edit / delete dialog まで。AI optimize/add flow は非対象
- callback と shared context は hidden capture ではなく明示引数にする
- `Phase 01` / `Phase 02` baseline を再編集しない

required checks:
- py_compile:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile C:\tetie\notecode\note\note_writer_app.py C:\tetie\notecode\note\note_writer_app_subviews.py C:\tetie\notecode\note\tests\test_note_writer_app_subviews.py
- pytest:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest C:\tetie\notecode\note\tests\test_note_writer_app_subviews.py C:\tetie\notecode\note\tests\test_note_writer_app_phase01_minimal_ui.py C:\tetie\notecode\note\tests\test_note_writer_app_ui_simulation.py C:\tetie\notecode\note\tests\test_note_writer_app_post_success_helpers.py -q
- log check:
  - `C:\tetie\notecode\logs\app.log` に `ImportError` / `ModuleNotFoundError` / `note_writer_app_subviews` 起因の startup failure の新規増加がないこと
  - recurring `base_events` `ConnectionResetError` は既存事象として据え置く

rollback conditions:
- source list UI drift
- blur preview / save drift
- generated image card CTA drift
- standalone subview extraction だけで閉じなくなる

stop conditions:
- `Phase 04` 以降の論点を混ぜないと前進できない
- `run_generation()`、confirm state mutation、logging owner、image prompt、auto legal postcheck へ波及しそうになった
- same issue で `2/2` 失敗した

最後の報告形式:
- 参照ルールファイル
- 今回の実施範囲
- 変更したファイル
- 実施した checks と結果
- `Phase 03` 完了可否
- rollback 要否
- 次 action
```
