# separate window execution prompt heading drift upstream current first hint pipeline implementation 2026-04-18

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_heading_drift_upstream_current_first_hint_management_planning_note_2026-04-18.md
- C:\tetie\notecode\docs\separate_window_heading_drift_upstream_current_first_hint_pipeline_triage_note_2026-04-18.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_upstream_current_first_hint_pipeline_triage_2026-04-18.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_live_validation_note_2026-04-17.md
- C:\tetie\notecode\logs\heading_drift_reconstruction_simplification_first_20260418-121729\summary.json
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py
- C:\tetie\notecode\note\tests\test_current_mainline_runner.py
- C:\tetie\notecode\note\tests\test_current_mainline_regressions.py
- C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py

今回の依頼種別:
- owner-local implementation prompt
- `SOURCE_GROUNDING_ORDER_ONLY`
- source-of-truth update ではない

今回の実施範囲:
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` の post-hydration / pre-plan slot に
  company intro current-first priority の source ordering を 1 diff で入れる
- touched tests は current owner に必要なものだけ
- `prompt_builder.py` retry には戻らない
- AGENTS / WORKLOG / current package docs は更新しない

inherited decision:
- management note conclusion:
  - `PIPELINE_UPSTREAM_CURRENT_FIRST_HINT_OWNER`
- triage note conclusion:
  - `SOURCE_GROUNDING_ORDER_ONLY`
- exact hook location:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:2401-2441`
  - `MinimalPipeline.generate()`
  - `contract = _hydrate_compatibility_source_documents(...)` の直後
  - `sections = list(build_discourse_plan(contract))` の直前

current package constraints:
- current default route:
  - `grounded generic default`
- planning / skeleton:
  - opt-in only
  - default reopen しない
- structural baseline:
  - `single-pass + optional single repair 1回`
- prompt accretion 禁止
- hidden reviser accretion 禁止
- fixed routing table 追加禁止
- `prompt_builder.py` same hypothesis retry 禁止
- `discourse_planner.py` / `input_contract.py` / `quality_guard.py` / `simple_note_pipeline/pipeline.py` を初手で触らない

problem framing:
- `prompt_builder.py` simplification pass は rollback 済み
- summary:
  - V1 partial / non-worse
  - V2 still awkward variance
  - G1 no visible regression
  - V3 mandatory gate fail
- exact visible failure:
  - V3 run2:
    - title が history-first
  - V3 run3:
    - first section が history-first
- current read:
  - wording 不足というより source salience / ordering variance

exact implementation target:
- add one narrow helper in `pipeline.py`
- helper responsibility:
  - reorder only `contract["source_documents"]`
  - and/or `contract["source_grounding_items"]`
  - for narrow company-intro current-first priority
- preferred insertion point:
  - immediately after hydration in `MinimalPipeline.generate()`
  - before `build_discourse_plan(contract)`
- preferred shape:
  - pure helper returning updated contract
  - stable reorder
  - no new prompt wording
  - no new contract field unless absolutely unavoidable

allowed trigger scope:
- keep narrow to current package objective
- preferred trigger:
  - `article_type == "branding"`
  - `semantic_article_key == "company_introduction"`
- if you need one more guard, prefer evidence-based guard
  - current-business-like evidence exists
  - history-like evidence exists
- do not widen to all branding or all article types

ordering rule guidance:
- source_grounding_items:
  - current-business / overview / strength / service-like facts first
  - history-like facts later
  - preserve relative order within the same priority band
- source_documents:
  - if document content/title/locator clearly indicates current business / company overview / strength, prefer earlier
  - if clearly history / 沿革 / 創業 / 歩み, prefer later
  - preserve relative order within the same priority band
- keep heuristic minimal
- do not build a broad classifier table
- do not add category tuning beyond this narrow company intro case

read-only evidence inside `pipeline.py`:
- hydration boundary only:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:838-873`
  - `_hydrate_compatibility_source_documents(...)`
- downstream order sensitivity evidence:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:1091-1116`
  - `_build_compatibility_body(...)`
  - `_section_fact_text(...)` uses `source_grounding_items[index]`
- compact-plan bridge is not first diff:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:2258-2269`

what not to do:
- `prompt_builder.py` wording retry
- `CONTRACT_HINT_BEFORE_DISCOURSE_PLAN`
- `COMPACT_PLAN_BRIDGE_ENTRY_ONLY`
- bridge enable 条件の拡張
- new planning default
- new routing table
- acceptance threshold reopen
- quality trigger tuning
- large refactor
- commented dead code

expected touched files:
- production:
  - C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- tests:
  - C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py
  - if needed only:
    - C:\tetie\notecode\note\tests\test_current_mainline_runner.py
    - C:\tetie\notecode\note\tests\test_current_mainline_regressions.py

preferred test additions:
1. owner-local source-order test
   - company intro contract with mixed overview/strength/history items
   - assert reordered `source_grounding_items` passed into planning or helper output keeps history after current-business items
2. generate()-level hook test
   - capture contract after hydration / before discourse plan
   - assert source order is changed only for narrow company-intro case
3. non-target guard test
   - generic branding or product_intro order is unchanged
4. if source_documents are reordered:
   - assert relative stable order inside same band is preserved

existing tests worth reading first:
- `test_st05ab7a_product_intro_discourse_assigns_history_after_service_facts`
- `test_st05d_branding_company_intro_keeps_dx_context_from_prompt`
- `test_st07aaac_branding_company_intro_stays_on_single_pass_without_experiment_flag`
- `test_execute_current_mainline_generation_reresolves_stale_company_intro_fields`
- company intro regressions that read source fact order in `test_current_mainline_regressions.py`

execution order:
1. read refs / triage note / exact hook slot
2. inspect existing company-intro and source-order tests
3. implement one helper + one call site in `generate()`
4. add/update owner-local tests
5. run owner-local and shared checks
6. run live validation matrix
7. visible self-eval
8. if pass, report and stop
9. if fail, local self-fix up to 3 tries
10. if still fail, rollback and stop report

test / check order:
- focused owner-local:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "company_intro or product_intro_discourse_assigns_history_after_service_facts or current_first or source_grounding_order" -q
- shared owner boundary:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
- ui boundary:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q
- if you touch only `pipeline.py`, `test_simple_note_pipeline.py` is not mandatory unless failure indicates cross-boundary impact

known unrelated failure boundary:
- if full `test_newalgorithm_phase03_pipeline.py` hits the already-known owner-outside fail
  - `test_st08b4_industry_analysis_title_and_lead_do_not_echo_prompt`
  - report it as inherited
  - do not chase it in this phase

live validation matrix:
- mandatory cases:
  - V1 latest adaptive explanatory baseline rerun
  - V2 saved adaptive explanatory replay
  - V3 company intro guard
  - G1 non-target branding guard
- preferred variance coverage:
  - V3 x3
  - V1 x2
  - V2 x1
  - G1 x2
- if runtime/cost blocks preferred count:
  - run at least original 4-case matrix
  - explicitly report variance coverage insufficient

success gate:
- mandatory:
  - V3 no history-first opener across preferred runs
  - title / first heading / first section do not revert to history-first
- keep:
  - V1 non-worse
  - V2 not worse than previous awkward baseline
  - G1 no visible regression
- telemetry is secondary
  - visible text judgment first

autonomous policy:
- error がなければ自律的に実装 -> test -> live validation -> visible self-eval まで進む
- error / blocker 時:
  - local self-fix を優先
  - WEB search は 1 回だけ許可
  - official docs / primary sources 優先
  - query と採用理由を最終報告で短く示す
- same hypothesis で 3 回 visible failure なら rollback して停止

rollback boundary:
- `pipeline.py` の source ordering helper と call site だけ戻す
- tests は owner-local diff だけ戻す
- `prompt_builder.py` / `discourse_planner.py` / `input_contract.py` へ波及させない

final report must include:
1. 読んだ参照ルールファイル
2. 今回の実施範囲
3. touched files
4. exact hook location
5. 実装した narrow hypothesis
6. helper の責務
7. 追加 / 更新した tests
8. 実行したコマンド
9. test / check 結果
10. live validation matrix と variance coverage
11. visible self-eval
12. WEB検索を使ったかどうか
13. stop condition に触れず完了したか
14. AGENTS / WORKLOG / current package docs を更新していないこと
```
