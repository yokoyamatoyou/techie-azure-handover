# separate window execution prompt note_writer_app split phase01 head assets 2026-04-23

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
- C:\tetie\WORKLOG.md

今回の依頼種別:
- separate-window implementation prompt
- `NOTE_WRITER_APP_SPLIT_PHASE01_HEAD_ASSETS`
- docs-only prompt ではない
- planning 継続ではなく implementation window 開始 prompt

今回の user request:
- `note_writer_app_split_2026-04-23` package の next action を、別ウインドウでそのまま着手できる prompt として渡したい
- 今回の execution window は `Phase 01: head assets` だけに閉じる
- `Phase 02` 以降へ自動連鎖しない

この window の primary objective:
- `C:\tetie\notecode\note\note_writer_app.py` から
  - `app.colors(...)`
  - 1 本目の `ui.add_head_html(...)` CSS / font / favicon block
  - 2 本目の `ui.add_head_html(...)` sticky step JS block
  を `C:\tetie\notecode\note\note_writer_app_head_assets.py` へ退避する
- ただし registration の call order は `note_writer_app.py` 側に残す
- current success path と UI shell owner を変えない

今回の前提:
- global current source of truth は引き続き
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
  に固定する
- `note_writer_app_split_2026-04-23` は `note_writer_app.py` safe split 用の separate initiative であり、global current source-of-truth の置換ではない
- current success path は
  - C:\tetie\notecode\note\current_mainline_runner.py
  - -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  を維持する
- `note_writer_app.py` は最後まで
  - UI shell
  - confirm-before-generate flow
  - actual widget mutation
  - logging trigger timing
  owner のまま維持する
- final contract resolve / `input_decision` source of truth は UI 側へ戻さない
- logging schema / file persistence owner は `current_mainline_runtime_logging.py` のまま
- GPT Image 2 は post-success work のまま
- `single-pass + optional single repair 1回` を崩さない
- completed / frozen reference package を reopen しない
- `current_mainline_owner_split` completed judgment を reopen しない

current code facts you must start from:
- target file:
  - C:\tetie\notecode\note\note_writer_app.py
- fixed baseline facts:
  - total lines: `9201`
  - `main_page()`: `4798`
  - `run_generation()`: `7775`
  - manual legal local handler `run_legal_check()`: `9103`
  - upload / source helpers: `3599-3702`
  - head assets block: `3752-4730`
- `Phase 01` の touched files planned by package:
  - C:\tetie\notecode\note\note_writer_app.py
  - C:\tetie\notecode\note\note_writer_app_head_assets.py
  - C:\tetie\notecode\note\tests\test_note_writer_app_head_assets.py

this window's narrow scope:
1. create `note_writer_app_head_assets.py`
2. move head asset data / registration helper only
3. leave registration order in `note_writer_app.py`
4. add focused tests for head asset extraction
5. run only the required focused checks
6. if green:
   - update C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md
   - update C:\tetie\WORKLOG.md
   - stop

implementation boundary:
- you may edit:
  - C:\tetie\notecode\note\note_writer_app.py
  - C:\tetie\notecode\note\note_writer_app_head_assets.py
  - C:\tetie\notecode\note\tests\test_note_writer_app_head_assets.py
  - green の場合のみ:
    - C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md
    - C:\tetie\WORKLOG.md
- you must not edit:
  - C:\tetie\notecode\current_mainline_owner_split\NOTE_WRITER_APP_WINDOW_HANDOFF_2026-04-23.md
  - C:\tetie\notecode\note\current_mainline_runner.py
  - C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
  - C:\tetie\notecode\note\current_mainline_runtime_logging.py
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - C:\tetie\notecode\note\note_writer_app_source_helpers.py
  - C:\tetie\notecode\note\note_writer_app_subviews.py
  - C:\tetie\notecode\note\note_writer_app_manual_legal_helpers.py
  - C:\tetie\notecode\note\note_writer_app_main_page_sections.py
  - C:\tetie\notecode\AGENTS.md
  - C:\tetie\AGENTS.md

required implementation shape:
- asset module には head asset data / registration helper だけを置く
- asset module は `state`、`ui.context.client`、generation timing、logging timing を持たない
- `note_writer_app.py` では import 後に既存順序で registration を呼ぶ
- CSS class 名、JS selector、favicon path、font link、theme color を変えない
- `main_page()`、`run_generation()`、manual legal local handler の ownership は変えない

explicit non-goals in this window:
- source/upload helper extraction
- subview extraction
- manual legal helper extraction
- `main_page()` builder 化
- `run_generation()` body の分割
- completion / exception / finally cleanup timing の整理
- image prompt / auto legal postcheck の整理
- confirm state mutation の整理

recommended working order:
1. read package docs and owner split references
2. inspect the existing `app.colors(...)` and both `ui.add_head_html(...)` blocks in `note_writer_app.py`
3. create `note_writer_app_head_assets.py` with the minimum registration surface
4. update `note_writer_app.py` to import and call the new helper without changing registration order
5. add focused tests that pin:
   - theme colors
   - CSS block registration
   - sticky step JS registration
6. run required checks
7. inspect `C:\tetie\notecode\logs\app.log` for new import/startup traceback
8. if all green, update package `PROGRESS.md` and `WORKLOG.md`
9. stop without starting `Phase 02`

required checks:
- py_compile:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile C:\tetie\notecode\note\note_writer_app.py C:\tetie\notecode\note\note_writer_app_head_assets.py C:\tetie\notecode\note\tests\test_note_writer_app_head_assets.py
- pytest:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest C:\tetie\notecode\note\tests\test_note_writer_app_head_assets.py C:\tetie\notecode\note\tests\test_note_writer_app_phase01_minimal_ui.py C:\tetie\notecode\note\tests\test_note_writer_app_ui_simulation.py -q
- log check:
  - C:\tetie\notecode\logs\app.log に import / startup traceback の新規増加がないこと

rollback conditions:
- import 時例外が出る
- sticky step JS が壊れる
- CSS class / id drift が出る
- head asset extraction だけで閉じなくなる
- `main_page()` callback や `run_generation()` timing owner に踏み込まないと直せない

stop conditions:
- same issue で `2/2` 失敗した
- `current_mainline_runner.py` / `current_mainline_runtime_logging.py` / `input_contract.py` owner をまたぐ必要が出た
- `Phase 02` 以降の論点を混ぜないと前進できない
- current success path regression が出た

最後の報告形式:
- 参照ルールファイル
- 今回の実施範囲
- 変更したファイル
- 実施した checks と結果
- `Phase 01` 完了可否
- rollback 要否
- 次 action
```
