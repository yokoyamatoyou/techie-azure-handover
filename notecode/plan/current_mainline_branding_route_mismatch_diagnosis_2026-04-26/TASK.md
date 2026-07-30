# current_mainline_branding_route_mismatch_diagnosis_2026-04-26 TASK

## Global Rules

- Docs-only package.
- Product code / prompt / threshold / repair / guard / UI implementation must remain unchanged.
- Announcement fix remains closed and reference-only.
- Do not add article-type-specific branching to `pipeline.py`.
- Do not classify body 0 as source shortage when route mismatch evidence explains it.
- Next implementation owner, if any, must be validation harness only.

## Phase Map

| Phase | Scope | Exit |
|---|---|---|
| 0 | package shell | README / TASK / PROGRESS / ROLLBACK / EXECUTION_PROMPT exist |
| 1 | artifact inspection | values-stance attempt artifacts inspected and exact route values recorded |
| 2 | route flow proof | UI controls -> ui_journey -> resolver -> input_contract chain documented |
| 3 | classification | primary and secondary classifications fixed |
| 4 | owner decision | next owner limited to validation harness |
| 5 | implementation prompt | separate-window prompt created for harness-only follow-up |
| 6 | closeout | WORKLOG updated and docs-only verification completed |

## Evidence Contract

Record these exact facts:

- `source_inventory.json`
  - `case_id=bl-branding-values-stance`
  - `article_type_target=non-company branding / values stance`
  - `article_type_for_ui=non-company branding`
  - `semantic_article_key_expected=branding`
  - controls select `purpose=会社・サービスの紹介記事を書く`
  - controls select `target=自社・会社紹介`
- `per_attempt_summary.jsonl`
  - attempts 1 and 2 both `input_required_block`
  - attempts 1 and 2 both `runtime_reason_code=SYS_PIPELINE_FAILURE`
  - attempts 1 and 2 both `article_type=branding`
  - attempts 1 and 2 both `semantic_article_key=company_introduction`
  - attempts 1 and 2 both body 0
- `latest_generation_output.json`
  - `ui_journey={purpose_key:introduce,target_key:company}`
  - `input_contract.semantic_article_key=company_introduction`
  - `input_contract.field_sources.semantic_article_key=ui_journey`
  - `input_contract.source_fit.status=pass`
  - `input_contract.source_grounding_status=resolved`
  - `input_contract.source_fit.candidate_targets=[company_introduction, implementation_case, improvement_case]`
- `run_log_source_ui_regression.py`
  - controls are copied from historical/casebook path.
  - replay selects `controls["target"]`.

## Owner Decision

Next owner if implementation is needed:

- validation harness issue only.

Do not assign:

- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## Required Checks

Docs-only verification:

- Confirm all five package docs exist.
- Confirm `C:\tetie\WORKLOG.md` has exactly one entry for this diagnosis.
- Confirm no product files were changed by this package.

No pytest is required for this package because no runtime code changes are made.

## Stop Conditions

- If evidence contradicts `ui_journey -> company_introduction`, stop and report instead of writing implementation guidance.
- If a proposed fix requires product code, prompt, threshold, repair, or pipeline branching, stop and keep this package docs-only.
