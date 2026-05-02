# separate window execution prompt note_writer_app split phase01 closeout 2026-04-23

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
- C:\tetie\notecode\note\tests\test_note_writer_app_head_assets.py
- C:\tetie\notecode\note\tests\test_note_writer_app_ui_simulation.py
- C:\tetie\notecode\note\tests\test_note_writer_app_generation_execution_helpers.py
- C:\tetie\WORKLOG.md

今回の依頼種別:
- separate-window closeout prompt
- `NOTE_WRITER_APP_SPLIT_PHASE01_CLOSEOUT`
- runtime 実装 window ではなく、green 化済み `Phase 01` を package 正本へ反映する narrow docs window

この window の primary objective:
- `Phase 01: head assets` が green になった current state を、`note_writer_app_split_2026-04-23` package 正本へ反映する
- `PROGRESS.md` / `EXECUTION_PROMPT.md` / `WORKLOG.md` を current status に合わせて最小更新する
- runtime code / tests / AGENTS は触らない

この window に入る前提事実:
- `note_writer_app.py` head assets 抽出差分はすでに workspace に入っている
- `主な読者` default contract は blank-start ではなく `一般読者` default で確定している
- audience default alignment は test 側のみで解消済み
- parent window で次を確認済み:
  - `py_compile`
    - C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile C:\tetie\notecode\note\note_writer_app.py C:\tetie\notecode\note\note_writer_app_head_assets.py C:\tetie\notecode\note\tests\test_note_writer_app_head_assets.py
    - pass
  - required `Phase 01` suite
    - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest C:\tetie\notecode\note\tests\test_note_writer_app_head_assets.py C:\tetie\notecode\note\tests\test_note_writer_app_phase01_minimal_ui.py C:\tetie\notecode\note\tests\test_note_writer_app_ui_simulation.py -q
    - `17 passed`
  - shared current-mainline safety suite
    - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest C:\tetie\notecode\note\tests\test_current_mainline_runner.py C:\tetie\notecode\note\tests\test_current_mainline_regressions.py C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py -q
    - `130 passed`
  - `C:\tetie\notecode\logs\app.log`
    - `ImportError` / `ModuleNotFoundError` / head-assets 起因の startup failure は新規なし
    - recurring `base_events` `ConnectionResetError` は継続しているが、current evidence では `Phase 01` regression としては扱わない
- この確認結果により、current workspace state では ALGORITHM contract 変更や current success path regression の兆候は見えていない

不変条件:
- global current source of truth は引き続き
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
  のまま
- `note_writer_app_split_2026-04-23` は separate initiative のまま維持する
- current success path
  - C:\tetie\notecode\note\current_mainline_runner.py
  - -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  を維持する
- `note_writer_app.py` は UI shell / confirm-before-generate flow / widget mutation / logging trigger timing owner のまま
- final contract resolve / `input_decision` source of truth は UI 側へ戻さない
- logging schema / file persistence owner は動かさない
- GPT Image 2 は post-success work のまま
- `single-pass + optional single repair 1回` を崩さない

この window で触ってよいファイル:
- C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md
- C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\EXECUTION_PROMPT.md
- C:\tetie\WORKLOG.md

この window で触ってはいけないファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\notecode\note\note_writer_app.py
- C:\tetie\notecode\note\note_writer_app_head_assets.py
- C:\tetie\notecode\note\tests\test_note_writer_app_head_assets.py
- C:\tetie\notecode\note\tests\test_note_writer_app_ui_simulation.py
- C:\tetie\notecode\note\tests\test_note_writer_app_generation_execution_helpers.py
- C:\tetie\notecode\note\current_mainline_runner.py
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\current_mainline_owner_split\NOTE_WRITER_APP_WINDOW_HANDOFF_2026-04-23.md

この window でやること:
1. package docs を読み、`Phase 01` がまだ pending のまま残っている箇所を確認する
2. `PROGRESS.md` を最小更新して、`Phase 01: Head Assets` を completed にする
3. `PROGRESS.md` に今回の verified facts を反映する
   - head assets module 抽出済み
   - audience default alignment により required suite が green
   - ALGORITHM / current success path に current drift evidence なし
4. `Next phase` を `Phase 02: Source / Upload / Bootstrap Helpers` に進める
5. `EXECUTION_PROMPT.md` を最小更新して、次 window が `Phase 02` だけ読めば着手できる状態にする
6. `WORKLOG.md` に `Phase 01` closeout 完了と verification summary を追記する
7. ここで停止する。`Phase 02` 実装は始めない

`PROGRESS.md` に必ず反映すること:
- current phase は `Phase 02` に進める
- `Phase 01` status は `completed`
- `Phase 01` の outcome:
  - `note_writer_app_head_assets.py` へ theme / CSS / sticky-step JS を退避
  - `note_writer_app.py` には import と registration order だけを維持
  - required suite green
  - shared current-mainline suite green
- runtime status:
  - algorithm contract unchanged in current workspace evidence
  - production success path regression not observed

`EXECUTION_PROMPT.md` の更新ルール:
- `Phase 01 only` の記述を current state に合わせて外す
- 次 window の対象を `Phase 02: Source / Upload / Bootstrap Helpers` のみに固定する
- ただし `Phase 03` 以降へ自動連鎖させない
- runtime owner boundary / ALGORITHM invariants / current success path invariants は維持する

この window では原則再実行しないもの:
- broad runtime edits
- new tests
- AGENTS update
- `Phase 02` implementation

再確認してよいこと:
- docs 更新前に、workspace に新しい runtime 差分が乗っていないかを目視で確認すること
- もし `note_writer_app.py` / `note_writer_app_head_assets.py` / relevant tests に別ウインドウの追加差分が見つかったら、docs 更新せず停止して report すること

stop conditions:
- `Phase 01` verified facts と current workspace が一致しない
- `Phase 02` の実装論点を混ぜないと docs が書けない
- runtime / test / AGENTS を触らないと前進できない

最後の報告形式:
- 参照ルールファイル
- 今回の実施範囲
- 更新したファイル
- `Phase 01` closeout の反映内容
- 実施した確認
- rollback 要否
- 次 action
```
