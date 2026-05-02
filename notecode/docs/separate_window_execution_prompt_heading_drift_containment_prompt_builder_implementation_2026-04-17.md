# separate window execution prompt heading drift containment prompt builder implementation 2026-04-17

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_instruction_handoff_heading_drift_containment_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_management_planning_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_triage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_visible_smoke_after_rollback_note_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\summary.json
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

今回の依頼種別:
- implementation prompt
- `HEADING_DRIFT_CONTAINMENT_FIRST` line の first owner implementation
- source-of-truth update ではない
- deepresearch prompt ではない

今回の実施範囲:
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` の generation prompt emission だけを触り、`TITLE_LEAD_HEADING_CONTRACT_FIRST` を 1 diff に閉じて実装する
- initial draft 側で
  - title drift
  - lead drift
  - heading wording / heading sequence drift
  - company intro first heading の history-first reanchor
  を抑えるため、title / lead / first heading / first-section role を同一 frame に縛る短い contract cluster を generation prompt に追加または強化する
- `pipeline.py` / `quality_guard.py` / current package docs / AGENTS / WORKLOG には触れない
- owner-local tests、必要最小限の shared checks、可能なら narrow visible self-eval まで自律的に進める

current inherited judgment:
- current redirect line:
  - `HEADING_DRIFT_CONTAINMENT_FIRST`
- first owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- first lever:
  - `TITLE_LEAD_HEADING_CONTRACT_FIRST`
- narrow hypothesis:
  - generation prompt の `HARD_CONTRACT` / `STRUCTURE` に、title / lead / first heading / first-section role を同一 frame に縛る短い contract cluster を追加すれば、repair acceptance reopen なしで initial draft の drift を先に containment できる
- backlog only:
  - `COMPANY_INTRO_FRAME_REUSE_FIRST`
- do not first:
  - `SECTION_SHADOW` の company intro 再導入
  - repair acceptance reopen
  - `quality_guard.py` first
  - `sentence-final monotony` continuation

implementation target:
- first read:
  - `prompt_builder.py` の
    - `build_generation_blocks()`
    - `build_generation_prompt()`
    - company intro preflight generation blocks
    - title / lead / structure guidance
  を確認する
- first implementation scope:
  - generation-side contract line のみ
  - 既存 `HARD_CONTRACT` / `STRUCTURE` へ短い line を追加するか、既存 line を短く補強する
  - 新 block の大量追加や section-level scaffold の reopen はしない
- acceptable local shape:
  - explanatory と company intro の両方に効く wording
  - first heading と first section が lead の延長線上にあることを促す
  - company intro では current business / current support から入り、history を背景に回す read を壊さない
  - title / lead / heading が同じ論点を言い換え反復するだけにならないよう、役割差も残す

implementation constraints:
- `1 phase = 1 narrow hypothesis = 1 owner scope` を守る
- prompt accretion 禁止
- module accretion 禁止
- helper 追加は最小限にとどめる
- `SECTION_SHADOW` block の company intro 再導入をしない
- `pipeline.py` の compact-plan scaffold / dispatch / acceptance を reopen しない
- `quality_guard.py` の trigger / issue classification を reopen しない
- route default / planning default / formatter policy discussion に広げない

do not:
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` を編集しない
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py` を編集しない
- AGENTS / WORKLOG / current package docs を更新しない
- prompt を長文化して雑に囲わない
- title / lead / heading / company intro frame 以外の論点を同時に触らない
- `SECTION_SHADOW` omission keep test をひっくり返さない
- live compare が重くても scope を広げて実装を続けない

touched files:
- code:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- tests:
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- optional generated artifacts for self-eval only:
  - `C:\tetie\notecode\logs\` 配下の新規 owner-local artifact

self-execution policy:
1. まず local code read で最小 diff を決める
2. 実装する
3. owner-local tests を実行する
4. test failure や実装エラーが出たら、まず local context だけで自己修正する
5. local context だけで解けない blocking error に限り、WEB検索を1回だけ行ってよい
6. WEB検索は official docs / primary sources を優先し、実装判断の主根拠を web へ置き換えない
7. WEB検索後の自己修正でも失敗したら、その時点で user report を作って停止する
8. エラーが解消したら、可能な範囲で shared checks と visible self-eval まで自律的に進める

owner-local test expectations:
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "distilled_brief or longform_explanatory or tone_specific_lines or distinguishes_title_and_lead_tone or blank_company_intro_generation_prompt_locks_first_section_to_current_business or generation_prompt_slims_company_intro_section_shadow_block" -q`
- 必要なら上記に加えて、この diff を固定する focused test を `test_simple_note_pipeline.py` に追加してよい
- focused test は
  - title / lead / first heading / first-section role の frame contract が prompt に入ること
  - company intro current-business-first keep を壊さないこと
  - company intro `SECTION_SHADOW` omission keep を壊さないこと
  のいずれかに閉じる

shared checks:
- first preference:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
- if owner-local and full simple-note tests pass without blocker:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
- current success path regression suspicion が出た場合だけ:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q`

visible self-eval:
- tests が通り、scope を広げずに実施できる場合だけ narrow に行う
- preferred read:
  - prompt text を直接確認し、
    - title / lead / first heading / first-section role の contract cluster が短く入っているか
    - explanatory と company intro の両方に同じ frame read がかかるか
    - company intro で history-first を許しすぎていないか
    - 同じ論点の重複言い換えを強める wording になっていないか
  を自分でレビューする
- optional:
  - current path の narrow rerun を 1〜2 case だけ実施してもよい
  - ただし rerun 準備で owner scope を広げない
  - rerun が重い / 不安定なら prompt text review までで止める

success condition:
- diff が `prompt_builder.py` owner に閉じている
- owner-local tests pass
- full simple-note test まで通るか、少なくとも failure が owner 外ではないと説明できる
- new or updated tests が implementation hypothesis を固定している
- self-review で prompt accretion が許容範囲に収まり、company intro keep line を壊していないと説明できる

stop conditions:
- `prompt_builder.py` だけでは解けず、`pipeline.py` まで触りたくなった
- `SECTION_SHADOW` company intro 再導入をしないと進めないと感じた
- `quality_guard.py` / acceptance threshold へ論点が逸れた
- focused test でなく broad failure の追跡に入りそうになった
- local self-fix + 1回のWEB検索後も error が解消しない

最終報告項目:
1. 読んだ参照ルールファイル
2. 今回の実施範囲
3. 実装した narrow hypothesis
4. touched files
5. 追加または更新した test
6. 実行したコマンド
7. test / check 結果
8. visible self-eval の要点
9. WEB検索を使ったかどうか
10. stop condition に触れず完了したか、またはどこで停止したか
11. production code / tests 以外の AGENTS / WORKLOG / current package docs を更新していないこと
```
