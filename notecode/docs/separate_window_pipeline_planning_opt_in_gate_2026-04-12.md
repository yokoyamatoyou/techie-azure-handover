# separate window pipeline planning opt-in gate 2026-04-12

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
- C:\tetie\notecode\docs\separate_window_reframe_route_policy_2026-04-12.md
- C:\tetie\notecode\docs\separate_window_docs_revise_route_interpretation_2026-04-12.md
- C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md

開始時に必ず確認する artifact:
- C:\tetie\notecode\logs\latest_generation_output.txt
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\latest_generation_quality_report.json
- company-intro / route evidence:
  - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-155752-fixed3-loop1-company-intro-brief-self-reference\combined_summary.json
  - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-225911-fixed3-cycle3-root-fix-section-acceptance\combined_summary.json
  - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260411-233627-fixed3-cycle4-root-fix-company-intro-route-exclusion\combined_summary.json
  - C:\tetie\notecode\logs\codex_minimum_hybrid_compare_matrix\20260412-011207-fixed3-codex-route-bypass-20260412\combined_summary.json
- article-type observation:
  - C:\tetie\notecode\logs\codex_article_type_route_observation\20260412-094857-fourtype-fivebatch\combined_report.md
  - C:\tetie\notecode\logs\codex_article_type_route_observation\20260412-094857-fourtype-fivebatch\combined_report.json
- daily sequence:
  - C:\tetie\notecode\logs\codex_daily_compare_gate\20260412-110830-daily-input-contract-fivebatch\combined_report.md
  - C:\tetie\notecode\logs\codex_daily_compare_gate\20260412-113511-daily-prompt-builder-fivebatch\combined_report.md
  - C:\tetie\notecode\logs\codex_daily_compare_gate\20260412-183815-daily-prompt-builder-simplify-fivebatch\combined_report.md

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

今回の役割:
- あなたは first code diff worker です
- docs-first reframe 後の最初の code change を、`C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` のみに閉じて実装します
- 目的は `grounded generic default` を保ったまま、planning / skeleton route を `explicit opt-in` に閉じることです

今回の current interpretation:
- default route:
  - `grounded generic`
- planning route:
  - `opt-in only`
- article-type priors:
  - `company / announcement -> generic prior`
  - `daily -> generic or prompt-like prior until grounding safe majority`
  - `technical explain -> coverage-first prior; planning only if ordering benefit is source-backed`
- article type は fixed routing table ではなく prior としてだけ使う

今回の narrow question:
- `pipeline.py` で planning opt-in feature gate を入れれば、non-opt-in case では generic default を保ちつつ、planning default 前提の route ambiguity を止められるか
- gate refusal reason / opt-in reason を telemetry で narrow に説明できるか

owner:
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py

hard rule:
- 1 diff = 1 narrow hypothesis = 1 owner scope = 1 rollback unit
- 初回実験は `pipeline.py` のみ
- `input_contract.py`、`prompt_builder.py`、`natural_blog_core.py`、`output_formatter.py`、`simple_note_pipeline/pipeline.py` は同時に触らない
- prompt accretion 禁止
- branch accretion 禁止
- article-type fixed routing table 禁止
- same hypothesis unchanged retry は 3 回まで

今回の hypothesis:
- planning / skeleton を default にしないと明示した current docs に合わせ、`pipeline.py` で opt-in gate を入れれば route ambiguity が減る
- `company / announcement / daily` のような non-opt-in case で generic default を保てる
- opt-in case が少なくてもよく、初回 diff では「planning を必要 case に限定すること」が目的であり、planning 勝利を大量に証明する必要はない

planning opt-in gate の方針:
- 次をすべて見るが、初回は narrow な heuristic でよい
  - source-backed distinct fact cluster
  - must-cover を section role 分離で扱う意味
  - narrative compression の低さ
  - ordering benefit > visible template cost
  - `no source, no standalone section`
- article type は prior としてだけ参照する
- gate を満たさない場合は `grounded generic default` に残す

今回の do:
- `pipeline.py` で現在の route decision / compact-plan entry / section-path entry を読む
- opt-in gate を 1 箇所に閉じて追加する
- non-opt-in case の refusal reason code を残す
- opt-in case の activation reason code を残す
- telemetry で
  - why generic default was kept
  - why planning was allowed
  を説明できるようにする
- owner-local tests
- shared checks
- gate を見るための compare / live rerun を実行する

今回の do not:
- company / announcement / daily / technical explain を hard-code しない
- article-type table を mainline に埋め込まない
- planning path を勝たせるために prompt を足さない
- downstream handoff を同時にいじらない
- repair acceptance や formatter を同時に触らない

今回の case selection:
- company-intro / branding:
  - `ui-short-branding-company-grounded`
- announcement:
  - `ui-short-announcement-dense-must-cover`
- daily:
  - `bl-daily-learning-log-grounded`
- technical explain:
  - `bl-explanatory-misread-metric`
- guard:
  - `ui-short-case-study-explain`

今回の compare modes:
- `generic`
- `algorithm step-optimized`
- `prompt-only persona`

今回の first-goal:
- planning opt-in gate の挙動確認が主
- `algorithm` が全 case で勝つ必要はない
- むしろ non-opt-in case で generic default が保たれることのほうが重要

pass condition:
- non-opt-in case で `grounded generic default` が維持される
- refusal reason が telemetry で narrow に説明できる
- opt-in した case があるなら、その case で ordering benefit を artifact と telemetry で説明できる
- guard regression がない
- coverage unsafe を増やさない
- rollback が owner-local diff で説明できる

rollback condition:
- gate が article-type hardcode 相当に崩れる
- non-opt-in case で generic default が崩れる
- refusal / activation reason が曖昧で telemetry で説明できない
- coverage unsafe を増やす
- owner scope が `pipeline.py` を超えないと成立しない

stop condition:
- gate は入ったが、ordering benefit と template cost を machine-observable に説明できず、次 owner が複数ファイル同時編集になる
- この場合は keep ではなく stop として持ち帰る

evaluation axes:
1. route clarity
- generic default を保った case
- planning opt-in を許可した case
- refusal / activation reason code の説明可能性

2. output safety
- must_cover_reflection_rate
- source_trace_coverage
- coverage unsafe の増減

3. visible quality
- opt-in case で template cost が増えていないか
- generic default case で不必要な planning surface が混入していないか

4. complexity
- route policy が simpler になったか
- future default を docs と矛盾なく説明できるか

tests:
- owner-local:
  - `pipeline.py` の route decision / telemetry / planning entry 関連 test を探し、必要なら narrow に追加する
- shared checks:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q
- known unrelated failure は切り分けて報告する

最終報告で必ず示すこと:
1. 読んだ正本ファイル
2. touched owner file
3. gate 仮説
4. 変更内容
5. 実行した tests
6. gate に使った artifact / telemetry
7. generic default を保った case
8. opt-in を許可した case
9. refusal / activation reason の説明
10. keep / rollback / stop の判定
11. AGENTS / WORKLOG / plan docs 更新の有無

最終的に欲しい答え:
- `pipeline.py` の narrow feature gate で current docs と runtime を揃えられるか
- それとも gate の前提自体がまだ機械化できず、別の docs / telemetry step が必要か
```
