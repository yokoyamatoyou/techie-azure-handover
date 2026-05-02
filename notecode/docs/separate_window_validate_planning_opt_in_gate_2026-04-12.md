# separate window validate planning opt-in gate 2026-04-12

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
- C:\tetie\notecode\docs\autonomous_naturalness_repair_plan_2026-04-11.md
- C:\tetie\notecode\docs\separate_window_pipeline_planning_opt_in_gate_2026-04-12.md
- C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md

開始時に必ず確認する artifact:
- C:\tetie\notecode\logs\latest_generation_output.txt
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\latest_generation_quality_report.json
- C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-155752-fixed3-loop1-company-intro-brief-self-reference\combined_summary.json
- C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-225911-fixed3-cycle3-root-fix-section-acceptance\combined_summary.json
- C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-233627-fixed3-cycle4-root-fix-company-intro-route-exclusion\combined_summary.json
- C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260412-011207-fixed3-codex-route-bypass-20260412\combined_summary.json
- C:\tetie\notecode\logs\codex_article_type_route_observation\20260412-094857-fourtype-fivebatch\combined_report.json

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

今回の役割:
- あなたは `planning_opt_in_v1` の validation runner です
- 新しい実装はしない
- 目的は gate の calibration を実ケースで確認することです
- 肥大化を避けるため、code edit は禁止します

今回の narrow question:
- `planning_opt_in_v1` は non-opt-in case で `grounded generic default` を保てているか
- opt-in される case は artifact と telemetry で説明可能か
- gate は厳しすぎるか、広すぎるか

hard rule:
- code edit しない
- tests を直さない
- article-type fixed routing table を足さない
- prompt accretion 禁止
- compare / live rerun / artifact review のみ

対象ケース:
- company:
  - `ui-short-branding-company-grounded`
- announcement:
  - `ui-short-announcement-dense-must-cover`
- daily:
  - `bl-daily-learning-log-grounded`
- technical explain:
  - `bl-explanatory-misread-metric`
- guard:
  - `ui-short-case-study-explain`

compare modes:
- `generic`
- `algorithm step-optimized`
- `prompt-only persona`

今回の主目的:
- quality 勝敗より先に route 判定の妥当性を見る
- 各ケースで
  - `route_branch`
  - `planning_opt_in_gate`
  - `planning_opt_in_gate_refused`
  - `planning_opt_in_section_path`
  - distinct fact cluster
  - grounded section count / ratio
  - must-cover count
  - article-type prior
  を記録する

期待する挙動:
- company:
  - 基本 refusal 側
- announcement:
  - 基本 refusal 側
- daily:
  - 基本 refusal 側
- technical explain:
  - refusal でもよいが、opt-in されるなら ordering benefit が説明可能であること
- guard:
  - regression なし

判定カテゴリ:
- `KEEP_GATE_AS_IS`
- `KEEP_GATE_BUT_TOO_STRICT`
- `KEEP_GATE_BUT_TOO_WIDE`
- `STOP_AND_REPORT_NEEDS_NEW_TELEMETRY`

pass 条件:
- non-opt-in case で generic default が保たれる
- refusal reason が narrow に説明できる
- opt-in case があるなら activation reason が narrow に説明できる
- coverage unsafe を増やさない
- guard regression なし

too strict の兆候:
- technical explain / case-study 相当でも opt-in が全く起きない
- refusal reason が常に同型で、ordering benefit を拾えていない

too wide の兆候:
- company / announcement / daily で opt-in が起きる
- opt-in したのに visible template cost が高い

stop 条件:
- telemetry だけでは ordering benefit と template cost を説明できない
- 次に進むには複数 owner の同時編集が必要

実行:
- 既存 compare harness を使う
- 結果 artifact root を明示する
- combined report を md/json で残す

最終報告で必ず示すこと:
1. 読んだ正本ファイル
2. 実行したケース
3. 各ケースの route 判定
4. refusal / activation reason
5. `generic / algorithm / prompt-only` の比較結果
6. gate の総合判定
7. 次に code diff が必要か、不要か
8. AGENTS / WORKLOG / plan docs / code を触っていないこと

最終的に欲しい答え:
- `planning_opt_in_v1` は現状維持でよいか
- 調整が必要なら gate が厳しすぎるのか広すぎるのか
- 次の 1 owner を動かす前に十分な calibration が取れたか
```
