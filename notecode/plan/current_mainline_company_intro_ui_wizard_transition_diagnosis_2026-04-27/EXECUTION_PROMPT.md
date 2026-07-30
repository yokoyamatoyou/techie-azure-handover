# Next Prompt: company_introduction validation harness only

Use this only if implementation is requested after this diagnosis.

```text
作業場所: C:\tetie\notecode
現在日時: 2026-04-27 JST

目的:
- `current_mainline_company_intro_ui_wizard_transition_diagnosis_2026-04-27` の診断結果を受け、company_introduction の UI wizard transition failure を validation harness owner だけで切り分ける。
- product code / prompt / persona / source contract / threshold / repair / guard / pipeline / image auto は変更しない。

必読:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\current_mainline_company_intro_ui_wizard_transition_diagnosis_2026-04-27\README.md
- C:\tetie\notecode\plan\current_mainline_company_intro_ui_wizard_transition_diagnosis_2026-04-27\PROGRESS.md
- C:\tetie\notecode\logs\article_type_self_perspective_quality_validation_record_continue_20260427-004338\summary.json
- C:\tetie\notecode\logs\article_type_self_perspective_quality_validation_record_continue_20260427-004338\ui_live\company_introduction_kyoto_latest_log\attempt_3\attempt_error.json
- C:\tetie\notecode\logs\article_type_self_perspective_quality_validation_record_continue_20260427-004338\ui_live\company_introduction_kyoto_latest_log\attempt_4\attempt_error.json
- C:\tetie\notecode\logs\article_type_self_perspective_quality_validation_record_continue_20260427-004338\ui_live\company_introduction_kyoto_latest_log\attempt_5\attempt_error.json
- C:\tetie\notecode\logs\article_type_self_perspective_quality_validation_record_continue_20260427-004338\ui_live\company_introduction_kyoto_latest_log\attempt_6\attempt_error.json
- C:\tetie\notecode\logs\article_type_self_perspective_quality_validation_record_continue_20260427-004338\run_record_continue_validation.py
- C:\tetie\notecode\logs\article_type_self_perspective_quality_validation_record_continue_20260427-004338\run_company_intro_replacement_attempt.py
- C:\tetie\WORKLOG.md

Owner:
- validation harness / artifact collection only

Hypothesis:
company_introduction の managed default target / writer state に対して、harness が fixed sequence (`STEP2 内容`, `誰の立場で書くか`, `内容を確認`) を待つため transition を誤判定している。

Task:
- company_introduction 1件だけの minimal transition check を作る。
- active wizard state を artifact に保存する。
- 次へボタンは active step container 内の visible/enabled button に限定する。
- `STEP2` が managed default で skip されても failure にしない。
- `STEP4 書き手` が managed default 表示済みなら speaker 選択を必須にしない。
- generation が始まった attempt と次 attempt の source upload が重ならないよう、attempt boundary を artifact 上で明示する。
- 成功条件は confirm state 到達の証跡保存まで。本文品質評価へ進まない。

Forbidden:
- product code changes
- C:\tetie\notecode\note\note_writer_app.py
- helper module additions/splits
- timeout extension
- sleep addition
- exception swallowing
- full validation rerun
- self-perspective / repair rejection changes
- prompt / persona / source contract / algorithm / threshold / quality_guard / output_guard / pipeline / blog_image_auto changes

Acceptance:
- Harness records actual visible step/text at each transition.
- Product code hash remains unchanged.
- No generation overlap from a previous attempt is present in the collected evidence.
- If the minimal transition still fails with correct active-state handling, stop and reclassify as possible product wizard state bug in a new package.
```

