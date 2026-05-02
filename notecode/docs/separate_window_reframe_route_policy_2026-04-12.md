# separate window reframe route policy 2026-04-12

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
- あなたは route policy reviewer / reframe gatekeeper です
- 新しい実装はしない
- 目的は、現在の evidence から `default route` と `planning opt-in rule` を再定義する価値があるかを判定することです
- current package を動かすなら、どの doc をどう更新すべきかを最小変更で提案してください

今回の background:
- `company_introduction` では generic 側優勢が繰り返し出た
- article-type observation では company / announcement が provisional に generic 寄り
- daily は contract retention と prompt handoff を経ても safe majority 未達、final simplify loop は rollback
- technical explain では algorithm 利得より coverage unsafe が先に出た
- したがって「現行 algorithm を各 genre へ tuning して勝たせる」方向は弱い

今回の narrow question:
- planning / skeleton を default とする current interpretation を、`grounded generic default + planning opt-in` へ reframe すべきか
- もし reframe するなら、article type fixed rule ではなく feature-based rule としてどう置くべきか
- 次の 1 diff は code 実装か、まず docs revision か

重要:
- 外部 research を鵜呑みにしない
- local experiments と compare artifacts を優先する
- package objective `keep core, recover visible naturalness` は壊さない
- broad rewrite を提案しない
- `1 next diff = 1 owner scope` に落とせること

今回の評価観点:
1. novelty
- 今さら route policy を変えるだけの新しい evidence が十分あるか

2. actionability
- `default = grounded generic`
- `planning = opt-in`
  を code owner / docs owner / next diff に落とせるか

3. fit to local evidence
- company / announcement / daily / technical explain の各 evidence と整合するか

4. complexity
- prompt accretion / module accretion / branch accretion を増やさないか

5. decision power
- reframe すると next step が clearer / safer になるか

期待する出力:
1. 読んだファイル一覧
2. local evidence の要点 5-10 行
3. 現在の route interpretation と衝突している点
4. 判定
   - `KEEP_CURRENT_ROUTE_INTERPRETATION`
   - `REVISE_ROUTE_INTERPRETATION_DOCS_FIRST`
   - `REVISE_ROUTE_INTERPRETATION_AND_NEXT_DIFF`
5. 判定理由
6. reframe するなら:
   - default route の考え方
   - planning opt-in の feature rule
   - article type は prior としてどう使うか
   - 更新すべき docs
   - 次の 1 diff の owner
7. reframe しないなら:
   - なぜ現行解釈を維持するのか
   - 何の evidence が足りないのか
8. AGENTS / WORKLOG / plan docs 更新の要否

強い reframe 条件:
- company / announcement / daily の 3 方向で「algorithm tuning より simpler default」が一貫している
- daily の複数 owner-loop が safe majority を作れず、局所 tuning が限界だと説明できる
- technical explain でも planning 利得より coverage unsafe が先に出ている
- feature-based rule へ落とせる

reframe 不可条件:
- 単に generic がたまたま勝っただけ
- next owner が複数同時でないと動かない
- article type ごとの ad-hoc rule を大量に増やすしかない
- current package objective と矛盾する

今回の do:
- docs と artifact を読む
- company / announcement / daily / technical explain の evidence を整理する
- route policy の provisional map を作る
- docs-first で十分か、次の code diff まで指定すべきかを判断する

do not:
- code edit しない
- tests を回さなくてよい
- prompt を増やす提案をしない
- daily の再実装ループを提案しない
- article-type 別の大量 parameter table を提案しない

最終的に欲しい答え:
- いま algorithm 方向性を変えるべきか
- 変えるなら `grounded generic default + planning opt-in` へ寄せるべきか
- 次は docs revision から入るべきか、owner-local code diff を打つべきか
```
