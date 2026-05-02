# separate window docs revise route interpretation 2026-04-12

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
- C:\tetie\notecode\docs\skeleton_role_revision_proposal_2026-04-11.md
- C:\tetie\notecode\docs\separate_window_evaluate_external_research_2026-04-12.md
- C:\tetie\notecode\docs\separate_window_observe_article_type_routes_2026-04-12.md
- C:\tetie\notecode\docs\separate_window_daily_grounding_stability_2026-04-12.md
- C:\tetie\notecode\docs\separate_window_daily_compare_gate_2026-04-12.md
- C:\tetie\notecode\docs\separate_window_daily_prompt_handoff_2026-04-12.md
- C:\tetie\notecode\docs\separate_window_daily_prompt_simplify_final_loop_2026-04-12.md
- C:\tetie\notecode\docs\separate_window_reframe_route_policy_2026-04-12.md
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
  - C:\tetie\notecode\logs\codex_daily_compare_gate\20260412-110830-daily-input-contract-fivebatch\combined_report.json
  - C:\tetie\notecode\logs\codex_daily_compare_gate\20260412-113511-daily-prompt-builder-fivebatch\combined_report.md
  - C:\tetie\notecode\logs\codex_daily_compare_gate\20260412-183815-daily-prompt-builder-simplify-fivebatch\combined_report.md

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

今回の役割:
- あなたは docs-first reframe worker です
- コード編集はしません
- 目的は current package docs を `grounded generic default + planning opt-in` に揃えることです
- route policy の再解釈を source-of-truth に反映し、今後の separate-window 実装が古い loop priority を future default と誤解しない状態にします

今回の判定前提:
- route policy review の結論は `REVISE_ROUTE_INTERPRETATION_DOCS_FIRST`
- company / announcement / daily / technical explain の local evidence は、`planning/skeleton default` を維持するより `grounded generic default` を本線にし、planning は opt-in にすべきことを示している
- 次の code diff より先に docs を揃える必要がある

今回の更新対象:
1. C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
2. C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
3. C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
4. C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
5. C:\tetie\notecode\docs\autonomous_naturalness_repair_plan_2026-04-11.md

今回の非更新対象:
- C:\tetie\AGENTS.md
- C:\tetie\WORKLOG.md
- runtime code 全体
- completed / frozen / archive-only docs

今回の reframe 内容:
1. default route
- `grounded generic default`
- source に沿って簡潔に書く経路を current default として明示する

2. planning route
- `planning opt-in`
- default ではなく feature gate を通ったときだけ許可する

3. article type の扱い
- fixed rule ではなく prior
- company / announcement:
  - generic 側へ強い prior
- daily:
  - generic or prompt-like 側へ prior
  - grounding safe majority が出るまで planning は opt-in しない
- technical explain:
  - neutral ではなく coverage-first prior
  - source-backed ordering benefit が見えた場合だけ planning opt-in

4. planning opt-in rule
- source-backed に 3 つ以上の distinct fact cluster がある
- must-cover を section role 分離で扱う意味がある
- narrative compression が低い
- visible template cost より ordering benefit が大きい
- `no source, no standalone section` を満たせる

今回の docs 反映方針:
- README:
  - Current Decision / Why / Simplification Direction / Non-Goals を route reframe に合わせて更新する
  - `planning/skeleton default` を示唆する古い語りを削る
- TASK:
  - phase map を route reopen 前提から reframe する
  - `planning opt-in only if feature gate passes` を明記する
  - current known dead loops を future default として残さない
- PROGRESS:
  - current phase を `route interpretation reframe / docs-first` へ更新する
  - daily の final simplify rollback まで含めて current evidence を整理する
  - `company / announcement provisional generic`, `daily unresolved`, `technical explain coverage-first unresolved` を反映する
- EXECUTION_PROMPT:
  - current loop priority を future default と誤解させる文言を削る
  - 次回起動時の prompt で `grounded generic default + planning opt-in` を source-of-truth として扱わせる
- autonomous_naturalness_repair_plan:
  - loop priority を historical evidence と current default を分けて書く
  - `planning/skeleton を勝たせる` ではなく `default route の再設定` を中心に読み替える

今回の do:
- docs を読み直して route default に関する旧前提を特定する
- 上の 5 ファイルだけを更新する
- wording を最小変更で揃える
- historical record は消さず、current interpretation だけを明確に上書きする
- rollback boundary を壊さない

今回の do not:
- runtime code を編集しない
- tests を回さなくてよい
- article-type 別の大量 parameter table を書かない
- new package を起こさない
- completed / frozen docs を reopen しない
- daily loop を再提案しない

文面上の重要ポイント:
- `algorithm tuning を各 genre に積めば勝てる` という含意を消す
- `generic default を明示しないまま owner-loop を重ねる` 状態をやめる
- `planning route = explicit opt-in` を明文化する
- `historical experiments` と `current decision` を分離する

期待する最終報告:
1. 読んだ正本ファイル
2. 更新した docs
3. 反映した route interpretation の要点
4. まだ unresolved な点
5. AGENTS / WORKLOG / code を触っていないこと
6. 次の first code owner を 1 つだけ提案するなら何か

最終的に欲しい状態:
- current source-of-truth を読めば、今の default が `grounded generic`
- planning は feature gate を通った時だけ opt-in
- company / announcement / daily / technical explain の暫定解釈が docs 上で矛盾しない
- 次の code diff を `pipeline.py` の narrow feature gate に自然に繋げられる
```
