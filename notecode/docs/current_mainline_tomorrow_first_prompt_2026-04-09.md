# current mainline tomorrow first prompt

更新日: 2026-04-08
用途: 2026-04-09 の separate window で `naturalness_recovery_2026-04-07` package を慎重に再開するための prompt

## copy-paste prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\notecode\docs\naturalness_recovery_execution_plan_2026-04-08.md
- C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-09.md
- C:\tetie\notecode\docs\ui_role_clarity_record_2026-04-08.md
- C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md

今回の実施範囲:
- current package objective は `keep core, recover visible naturalness`
- current success path を壊さない
- 明日の初手は Phase 02 の known blockage removal のみ
- `simple_note_pipeline/pipeline.py` owner だけを触る
- route ownership reopen を同時に始めない
- prompt accretion / module accretion をしない

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
4. C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
5. C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
6. C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
7. C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
8. C:\tetie\notecode\docs\naturalness_recovery_execution_plan_2026-04-08.md
9. C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-09.md
10. C:\tetie\notecode\docs\ui_role_clarity_record_2026-04-08.md
11. C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md
12. C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md
13. C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md
14. C:\tetie\notecode\ALGORITHM.md
15. C:\tetie\WORKLOG.md

開始時に必ず確認する artifact:
1. C:\tetie\notecode\logs\latest_generation_output.txt
2. C:\tetie\notecode\logs\latest_generation_output.json
3. C:\tetie\notecode\logs\latest_generation_quality_report.json
4. latest gate artifact:
   - C:\tetie\notecode\logs\stepwise_three_article_gate\20260408-205226-phase03_branding_route_promotion\

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

current known facts:
- `ending_bucket_max_run = 29`
- `ending_bucket_monotony_score = 1.0`
- `repair_trigger_score = 0.6`
- `repair_applied = false`
- `patch_path_used = false`
- `writer_of_record = simple_note_pipeline`
- `route_branch = single_pass_default`
- `style_profile_source = newalgorithm_pipeline.default_style_profile`
- `patch_path_refusal_reason = compact_plan_scope_ineligible`

重要な判断:
- repair non-actuation は first known blockage だが、総合主因の単独候補ではない
- route promotion は 2026-04-08 live gate で `writer_of_record` を変えても visible AI feel を改善できなかった
- よって明日は Phase 02 を先に終え、残差があれば次は Phase 04 `natural_blog_core.py` に進む

明日の実行順:
1. `simple_note_pipeline/pipeline.py` の patch path eligibility / repair acceptance 条件を読む
2. branding/company introduction を `ending_bucket_monotony` 限定で narrow patch path に接続する
3. acceptance に monotony 改善条件を追加する
4. focused tests を追加または更新する
5. owner-local tests を実行する
6. shared checks を実行する
7. `stepwise_three_article_gate_2026-04-08.md` の fixed 3 cases で live compare を行う
8. target 2 cases で generic baseline 比較と目視レビューを行う
9. docs / worklog を更新して停止する

do-not:
- `natural_blog_core.py` を同時に触らない
- `input_contract.py` を同時に触らない
- `newalgorithm_pipeline/pipeline.py` を同時に触らない
- prompt-only strengthening に流れない
- route ownership reopen を同時に始めない

stop:
- same phase で 3 attempt 失敗
- owner-local diff に閉じなくなる
- current success path regression
- repair blockage を外しても broad flatness の改善が全く見えず、しかも targeted patch telemetry も立たない

最終報告で必ず示すこと:
- 読んだ正本ファイル
- 読んだ artifact
- touched owner file
- 実施した変更
- 実行した tests
- live gate の結果
- rollback の有無
- 次 phase を 04 / 05 / 03 のどれにするか、その理由
- AGENTS / WORKLOG 更新の有無
```
