# separate window pipeline gate calibration 2026-04-12

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
- C:\tetie\notecode\docs\management_window_route_policy_coordinator_2026-04-12.md
- C:\tetie\notecode\docs\separate_window_pipeline_planning_opt_in_gate_2026-04-12.md
- C:\tetie\notecode\docs\separate_window_validate_planning_opt_in_gate_2026-04-12.md

開始時に必ず確認する artifact:
- C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-205904-fivecase-live\combined_report.md
- C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-205904-fivecase-live\combined_report.json
- C:\tetie\notecode\logs\codex_article_type_route_observation\20260412-094857-fourtype-fivebatch\combined_report.json
- C:\tetie\notecode\logs\latest_generation_output.json

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

今回の役割:
- あなたは `planning_opt_in_v1` calibration worker です
- 変更は `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` のみに閉じます
- 目的は `KEEP_GATE_BUT_TOO_STRICT` を解消することです

current evidence:
- company / announcement / daily / technical explain / guard の 5 case 全てが refusal
- refusal reason は全件 `source_fact_clusters_insufficient`
- company / announcement / daily refusal 自体は妥当
- technical explain / case-study まで refusal なのは strict すぎる
- gate が実質 `distinct_fact_clusters >= 3` の hard gate になっている

今回の narrow question:
- `distinct_fact_clusters` 単独依存をやめ、複合条件で planning opt-in を判断すれば、company / announcement / daily を generic 側に残したまま、technical explain か case-study を opt-in 対象として拾えるか

owner:
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py

hard rule:
- 1 diff = 1 narrow hypothesis = 1 owner scope = 1 rollback unit
- `pipeline.py` 以外を触らない
- article-type fixed routing table を入れない
- prompt accretion 禁止
- branch accretion 禁止
- multi-owner edit 禁止

今回の hypothesis:
- `distinct_fact_clusters` を必須単独条件にせず、
  - grounded_sections
  - grounded_section_ratio
  - must_cover_count
  - no_source_standalone_ok
  - article-type prior
  の複合条件へ変えると、gate の strictness を落としつつ default generic を保てる

今回の calibration 方針:
- keep:
  - company / announcement / daily は refusal 寄り
- allow:
  - technical explain / case-study 相当では、ordering benefit 候補を拾える余地を作る
- do not:
  - article-type だけで opt-in を決めない
  - cluster 閾値を単純に 1 段下げるだけで終わらせない

今回の do:
- `pipeline.py` の `planning_opt_in_v1` 判定を読む
- `distinct_fact_clusters` hard gate を複合判定へ置き換える
- refusal / activation reason code を維持または改善する
- telemetry でどの条件の組み合わせが効いたか説明できるようにする
- owner-local tests を追加または更新する
- shared checks を回す
- 同じ 5 case で compare/live rerun を再実行する

今回の do not:
- input_contract.py を触らない
- prompt_builder.py を触らない
- formatter を触らない
- daily を再救済しない
- docs を再び大きく変えない

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

pass condition:
- company / announcement / daily は refusal または generic default 維持
- technical explain か guard case-study の少なくとも一方で opt-in が起きる、または refusal reason が複合条件として narrow に説明される
- opt-in case があるなら、activation reason が artifact / telemetry で説明可能
- coverage unsafe を増やさない
- guard regression なし

rollback condition:
- company / announcement / daily で opt-in が起きる
- refusal / activation reason が曖昧になる
- compare で coverage unsafe が増える
- owner scope が `pipeline.py` を超えないと成立しない

stop condition:
- 複合 gate にしても全部 refusal のまま
- または opt-in は起きるが ordering benefit を説明できない
- この場合は gate calibration 以上の問題として stop して報告する

tests:
- owner-local:
  - `test_newalgorithm_phase03_pipeline.py` の gate telemetry / route decision テスト
- shared checks:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q

最終報告で必ず示すこと:
1. touched owner file
2. hypothesis
3. gate calibration の内容
4. 実行した tests
5. rerun artifact
6. 各 case の refusal / activation reason
7. keep / rollback / stop の判定
8. AGENTS / WORKLOG / plan docs 更新の有無

最終的に欲しい答え:
- `planning_opt_in_v1` を複合 gate にすることで、strict すぎる問題は解消するか
- それでも解消しないなら、gate calibration ではなく別問題として切り直すべきか
```
