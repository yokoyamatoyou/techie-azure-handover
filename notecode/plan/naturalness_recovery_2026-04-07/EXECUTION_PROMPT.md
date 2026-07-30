# naturalness_recovery_2026-04-07 EXECUTION PROMPT

## next startup use

- 次回起動時の canonical prompt は次の文書を使う
  - `C:\tetie\notecode\docs\simple_note_pipeline_company_intro_current_business_first_recovery_prompt_2026-04-18.md`
- current planning source-of-truth は `naturalness_recovery_2026-04-07` package に固定する
- `visible_output_integrity_2026-04-06` は active reference として扱う
- pre-2026-04-02 records は archive snapshot 経由でのみ参照する
- completed / frozen reference package は reopen しない
- historical separate-window prompts は evidence としては読めるが、current prompt として継承しない
- current judgment category は `COMPANY_INTRODUCTION_OPERATIONAL_SOURCE_CONTRACT_V1_RUNTIME_KEEP`
- current default route は `grounded generic default`
- planning / skeleton route は explicit feature gate を通った場合だけ opt-in する
- structural baseline は `single-pass + optional single repair 1回`
- latest `prompt_builder.py` simplification-first wording line は failed hypothesis / rollback 済みと扱う
- latest `pipeline.py` current-first source ordering / hint triage も failed hypothesis / rollback 済みと扱う
- same hypothesis を unchanged で reopen しない
- latest `simple_note_pipeline/pipeline.py` reopen keep diff は baseline として維持する
- `company_introduction_operational_source_contract_v1` は runtime keep として維持する
- active scope は `article_type=branding` かつ `semantic_article_key=company_introduction`
- source contract required は `current_business` / `customer_situation_or_entry_point` / `support_scope_boundary` / `operating_process_steps` / `pre_contact_decision`
- optional は `proof_signal`、guard-only は `source_limit`
- runtime prompt へ persona / editor / trial names は入れず、`source_limit` は visible article に出さない
- next owner / next narrow hypothesis は未開始
- prompt-only は floor、skeleton / planning は conditional signal only として扱う
- `natural_blog_core.py` first section history clamp / `output_formatter.py` formatter-only surface polish / `input_contract.py` upstream distilled summary only は do-not-retry とする
- public web article compare は current-business-first pattern 支持の evidence として読む
- direct GPT web compare は unavailable のまま keep し、WEB 勝利は主張しない
- package は docs closeout 状態で、next implementation window は不要

## prompt

```text
この package doc の current startup prompt は次を参照する:
- C:\tetie\notecode\docs\simple_note_pipeline_company_intro_current_business_first_recovery_prompt_2026-04-18.md

use the document above verbatim.

do not reuse:
- C:\tetie\notecode\docs\simple_note_pipeline_company_intro_acceptance_reopen_prompt_2026-04-18.md
- C:\tetie\notecode\docs\parked_package_prompt_naturalness_recovery_2026-04-18.md
- C:\tetie\notecode\docs\management_prompt_explicit_reopen_simple_note_pipeline_company_intro_acceptance_2026-04-18.md
- C:\tetie\notecode\docs\management_prompt_after_simple_note_pipeline_company_intro_acceptance_reopen_2026-04-18.md
- C:\tetie\notecode\docs\management_prompt_after_failed_pipeline_current_first_triage_2026-04-18.md
- C:\tetie\notecode\docs\pipeline_current_first_triage_prompt_2026-04-18.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_reconstruction_simplification_first_2026-04-18.md
- any older `prompt_builder.py` first implementation prompt as the current owner prompt

current keep note:
- `company_introduction_operational_source_contract_v1` live validation PASS を runtime keep として扱う
- C:\tetie\notecode\logs\company_introduction_operational_source_contract_v1_live_validation_20260422-185418
- next implementation is only needed if a new regression / scope expansion / acceptance residual is explicitly opened
```
