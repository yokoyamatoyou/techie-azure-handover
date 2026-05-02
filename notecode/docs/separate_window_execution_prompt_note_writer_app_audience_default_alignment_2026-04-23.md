# separate window execution prompt note_writer_app audience default alignment 2026-04-23

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
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
- C:\tetie\WORKLOG.md

今回の依頼種別:
- separate-window implementation prompt
- `NOTE_WRITER_APP_AUDIENCE_DEFAULT_ALIGNMENT`
- head-assets 継続 window ではなく、別論点の new window
- docs-only prompt ではない

今回の user request:
- `Phase 01: head assets` の差分は保持したまま、required suite を落としている別論点を narrow に詰めたい
- 失敗している `test_note_writer_app_ui_simulation.py` は `主な読者` が空欄前提だが、現行アプリは `"一般読者"` を既定値として入れている
- 次はこの論点だけに閉じた指示 prompt が必要

この window を新規に分ける理由:
- `head assets` extraction 自体は focused checks と `app.log` で non-regression だった
- 失敗している 3 件は asset extraction ではなく `audience` 初期値 contract / UI simulation expectation のズレ
- `Phase 01` の rollback 要因ではないため、head assets diff を保持したまま別 owner-local 問題として切るほうが安全

この window の primary objective:
- `note_writer_app.py` における `主な読者` 初期値 contract を確認する
- current intended behavior が
  - blank-start なのか
  - `"一般読者"` default なのか
  を repo evidence で確定する
- その contract に合わせて `test_note_writer_app_ui_simulation.py` と必要最小限の code / tests を整合させる
- `head assets` diff や split package docs は触らない

今回の前提:
- current success path は
  - C:\tetie\notecode\note\current_mainline_runner.py
  - -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  を維持する
- `note_writer_app.py` は UI shell / confirm-before-generate flow / widget mutation / logging trigger timing owner のまま扱う
- final contract resolve / `input_decision` source of truth を UI 側へ戻さない
- logging schema / file persistence owner は `current_mainline_runtime_logging.py` のまま
- `single-pass + optional single repair 1回` を崩さない
- `naturalness_recovery_2026-04-07` current source of truth は置き換えない
- `note_writer_app_split_2026-04-23` package は separate initiative のまま
- `Phase 01: head assets` diff は保持し、無関係なら rollback しない

current evidence you must start from:
- `C:\tetie\notecode\note\note_writer_app.py`
  - `_default_audience_profile_text()` は現状 `"一般読者"` を返す
  - `_prepare_current_mainline_required_inputs()` は blank audience を `"一般読者"` に normalize する
  - `ui.input("主な読者", value=_default_audience_profile_text(), ...)` が少なくとも 2 箇所ある
- `C:\tetie\notecode\note\tests\test_note_writer_app_generation_execution_helpers.py`
  - `test_prepare_current_mainline_required_inputs_collects_missing_fields()` は blank audience -> `"一般読者"` を期待している
  - `test_default_audience_profile_text_is_short_gate_default()` も `"一般読者"` を期待している
- `C:\tetie\WORKLOG.md`
  - `2026-04-23 追記（notecode generation UI UX gate fix）` に
    - `STEP3 読者: UI default を 一般読者 にし、空欄必須扱いで gate が止まらないようにした`
    と記録がある
- failing tests:
  - `C:\tetie\notecode\note\tests\test_note_writer_app_ui_simulation.py`
  - 3 件とも blank-start 前提で入力している

working hypothesis:
- current repo evidence 上は `"一般読者"` default が intended behavior であり、今回の 3 failures は test drift の可能性が高い
- ただし UI / helper / WORKLOG / runner contract の間に矛盾があれば、test だけ直す前に code side の intent を再確認する

この window の narrow scope:
1. audience default contract audit
   - `一般読者` default が intentional か accidental かを repo evidence で確定する
2. UI simulation alignment
   - current intended behavior に合わせて `test_note_writer_app_ui_simulation.py` を整合させる
3. only if clearly necessary:
   - `note_writer_app.py` の `主な読者` 初期値実装を narrow に修正する
4. regression confirmation
   - focused suite を green にする

this window is not for:
- `Phase 02` source/upload/bootstrap helpers
- subview extraction
- manual legal helper extraction
- `main_page()` builder 化
- `run_generation()` 本体の分割
- audience UX の broad redesign
- AGENTS 更新
- split package docs の進捗更新
- head assets rollback

files you should inspect first:
- C:\tetie\notecode\note\note_writer_app.py
  - `_default_audience_profile_text`
  - `_prepare_current_mainline_required_inputs`
  - `ui.input("主な読者", value=...)`
- C:\tetie\notecode\note\tests\test_note_writer_app_ui_simulation.py
- C:\tetie\notecode\note\tests\test_note_writer_app_generation_execution_helpers.py
- C:\tetie\WORKLOG.md
  - `2026-04-23 追記（notecode generation UI UX gate fix）`
- 必要時のみ:
  - C:\tetie\notecode\note\tests\test_note_writer_app_generation_gate_helpers.py
  - C:\tetie\notecode\note\tests\test_note_writer_app_phase01_minimal_ui.py

files you may edit:
- C:\tetie\notecode\note\note_writer_app.py
- C:\tetie\notecode\note\tests\test_note_writer_app_ui_simulation.py
- 必要時のみ:
  - C:\tetie\notecode\note\tests\test_note_writer_app_generation_execution_helpers.py
  - C:\tetie\WORKLOG.md

files you must not edit:
- C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md
- C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\TASK.md
- C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\ROLLBACK.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\AGENTS.md
- C:\tetie\notecode\note\note_writer_app_head_assets.py
- C:\tetie\notecode\note\current_mainline_runner.py
- C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
- C:\tetie\notecode\note\current_mainline_runtime_logging.py

recommended execution order:
1. confirm the current repo evidence for audience default behavior
2. decide whether current intended contract is:
   - `一般読者` default, or
   - blank-start
3. prefer the narrower fix:
   - if default is intentional, update UI simulation tests
   - only if evidence shows the default is wrong, update code and the affected tests together
4. run focused checks
5. if green, add a short `WORKLOG.md` entry for this audience-default alignment slice
6. stop

required checks:
- py_compile:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile C:\tetie\notecode\note\note_writer_app.py C:\tetie\notecode\note\tests\test_note_writer_app_ui_simulation.py C:\tetie\notecode\note\tests\test_note_writer_app_generation_execution_helpers.py
- pytest:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest C:\tetie\notecode\note\tests\test_note_writer_app_ui_simulation.py C:\tetie\notecode\note\tests\test_note_writer_app_generation_execution_helpers.py C:\tetie\notecode\note\tests\test_note_writer_app_phase01_minimal_ui.py -q
- if touched:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest C:\tetie\notecode\note\tests\test_note_writer_app_generation_gate_helpers.py -q

success criteria:
- audience default contract is explicitly resolved
- failing `ui_simulation` 3 cases are green
- no new regressions in the focused audience / required-input helper suite
- `head assets` diff remains intact

stop conditions:
- issue cannot be resolved without changing runner / input_contract / logging owner
- issue expands into a broad required-input redesign
- same issue fails `2/2`
- evidence for intended audience default remains contradictory after local audit

最後の報告形式:
- 参照ルールファイル
- 今回の実施範囲
- 変更したファイル
- audience default contract の判断
- 実施した checks と結果
- `ui_simulation` failure 解消可否
- rollback 要否
- 次 action
```
