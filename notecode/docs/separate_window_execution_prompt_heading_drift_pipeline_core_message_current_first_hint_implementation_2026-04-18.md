# separate window execution prompt heading drift pipeline core message current first hint implementation 2026-04-18

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
- C:\tetie\notecode\docs\separate_window_heading_drift_pipeline_contract_hint_consumer_triage_note_2026-04-18.md
- C:\tetie\notecode\docs\separate_window_heading_drift_upstream_current_first_hint_pipeline_triage_note_2026-04-18.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_pipeline_contract_hint_consumer_triage_2026-04-18.md
- C:\tetie\notecode\logs\heading_drift_upstream_current_first_hint_live_validation_20260418-142418\summary.json
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py
- C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py
- C:\tetie\notecode\note\tests\test_current_mainline_runner.py
- C:\tetie\notecode\note\tests\test_current_mainline_regressions.py
- C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py

今回の依頼種別:
- owner-local implementation prompt
- `CORE_MESSAGE_CURRENT_FIRST_HINT_ONLY`
- source-of-truth update ではない

今回の実施範囲:
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` の post-hydration / pre-plan slot だけを触る
- blank or weak `core_message` の narrow fill だけを 1 diff で入れる
- touched tests は current owner に必要なものだけ
- AGENTS / WORKLOG / current package docs は更新しない

inherited decision:
- previous failed hypothesis:
  - `SOURCE_GROUNDING_ORDER_ONLY`
  - rollback 済み
  - unchanged retry 禁止
- current triage conclusion:
  - `CORE_MESSAGE_CURRENT_FIRST_HINT_ONLY`
- reason summary:
  - V3 では first heading は少し動いたが title が history-first に残った
  - `topic_statement` は raw topic の後ろに隠れる
  - `must_cover` は V3 ですでに current-first だった
  - `core_message` は blank で、既存 consumer の
    - `prompt_builder.py` `core=...`
    - company-intro writer brief
    - compatibility `writing_intent`
    に同時に届く

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
- `prompt_builder.py` simplification-first wording retry 禁止
- `pipeline.py` source ordering retry 禁止
- `discourse_planner.py` / `input_contract.py` / `quality_guard.py` / `simple_note_pipeline/pipeline.py` を触らない

exact owner slot:
- owner file:
  - C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- exact hook:
  - `MinimalPipeline.generate()`
  - `resolve_input_contract(normalized_payload)` 後
  - `contract = _hydrate_compatibility_source_documents(dict(resolved.contract or {}))` の直後
  - `sections = list(build_discourse_plan(contract))` の直前
- current line block:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:2522-2563`

exact implementation target:
- add one narrow helper in `pipeline.py`
- helper responsibility:
  - blank or weak `contract["core_message"]` を
    current-business-first / history-background の 1 line intent にだけ補う
- preferred insertion:
  - hydration の直後に helper を呼ぶ
- preferred shape:
  - pure helper returning updated contract
  - no new field
  - no source reorder
  - no prompt-builder wording追加

allowed trigger scope:
- keep narrow to current package objective
- preferred trigger:
  - `article_type == "branding"`
  - `semantic_article_key == "company_introduction"`
- fill condition:
  - `core_message` が blank
  - or generic self-intro wording で current-business-first intent が弱い場合だけ
- if weakness 判定を入れるなら
  - narrow string heuristic に留める
  - blank / `会社紹介を進めたい` 系の generic fill 程度まで
  - broad classifier にしない

hint wording guidance:
- first choice:
  - `C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py:269-277` の current company-intro default と整合する短い 1 line
- semantic target:
  - 今の事業 / 導入初期を支える姿勢を先に示す
  - 歩み / history は背景として後ろに回す
- keep short
  - 1 sentence
  - prompt surface accretion に見えない長さ

read-only evidence to confirm before edit:
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:2522-2563`
  - post-hydration / pre-plan slot
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:2411-2412`
  - `topic_hint` / `writing_intent`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py:955-956`
  - `core=...`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py:1985`
  - raw topic fallback order
- `C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py:269-277`
  - company-intro core default

what not to do:
- `contract["topic"]` を変えない
- `contract["prompt_raw"]` を変えない
- `contract["topic_statement"]` を変えない
- `contract["must_cover"]` を reorder しない
- `source_documents` / `source_grounding_items` を reorder しない
- `prompt_builder.py` を触らない
- `discourse_planner.py` を触らない
- bridge enable を広げない
- new route / new feature gate を作らない
- `SECTION_SHADOW` reopen
- dead code の温存
- failed hypothesis の混載

expected touched files:
- production:
  - C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- tests:
  - C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py
- if current-mainline payload or regression surface まで reach を確認する必要がある場合だけ:
  - C:\tetie\notecode\note\tests\test_current_mainline_runner.py
  - C:\tetie\notecode\note\tests\test_current_mainline_regressions.py

preferred test additions:
1. owner-local core_message fill test
  - narrow company-intro contract
  - blank `core_message`
  - assert helper or generate-slot output fills current-first hint
2. generic-or-weak company-intro fill guard test
  - generic `core_message` だけ補う
  - explicit strong `core_message` は上書きしない
3. non-target guard test
  - non-company-intro or non-branding は unchanged
4. if generate-level test is easier than helper unit:
  - capture contract passed into `build_discourse_plan(contract)` or downstream consumer and assert `core_message` only changes in narrow target case

existing tests worth reading first:
- `test_st05d_branding_company_intro_keeps_dx_context_from_prompt`
- `test_st07aaac_branding_company_intro_stays_on_single_pass_without_experiment_flag`
- `test_st08h_branding_source_grounded_company_intro_prefers_local_section_focus`
- `test_st08b1b_case_study_lead_uses_core_message_to_separate_from_first_section`
- `test_execute_current_mainline_generation_reresolves_stale_company_intro_fields`
- `test_assess_current_mainline_question_policy_company_intro_source_backed_skips_core_message_requirement`

execution order:
1. read refs / triage note / exact hook slot
2. inspect existing `core_message` consumers and company-intro tests
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
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "company_intro or core_message or st08h or st07aaac" -q
- shared owner boundary:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
- ui boundary:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q
- full simple-note tests は不要
  - cross-boundary failure が出た場合だけ理由付きで追加

known unrelated failure boundary:
- if shared checks hit the already-known owner-outside fail
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
  - V3 title が history-first に戻らない
  - V3 lead / first heading / first section が history-first に戻らない
  - `core_message` fill が explicit strong input を壊していない
- keep:
  - V1 non-worse
  - V2 not worse than previous awkward baseline
  - G1 no visible regression
- telemetry は secondary
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
- `pipeline.py` の `core_message` fill helper と call site だけ戻す
- tests は owner-local diff だけ戻す
- `prompt_builder.py` / `discourse_planner.py` / `input_contract.py` / source ordering へ波及させない

final report must include:
1. 読んだ参照ルールファイル
2. 今回の実施範囲
3. touched files
4. exact hook location
5. 実装した narrow hypothesis
6. helper の責務
7. fill condition と non-overwrite guard
8. 追加 / 更新した tests
9. 実行したコマンド
10. test / check 結果
11. live validation matrix と variance coverage
12. visible self-eval
13. WEB検索を使ったかどうか
14. stop condition に触れず完了したか
15. AGENTS / WORKLOG / current package docs を更新していないこと
```
