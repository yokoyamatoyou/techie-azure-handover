# naturalness_recovery_2026-04-07 ROLLBACK

## Baseline

- restore target:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- current visible artifact baseline:
  - `C:\tetie\notecode\logs\latest_generation_output.txt`
  - `C:\tetie\notecode\logs\latest_generation_output.json`
  - `C:\tetie\notecode\logs\latest_generation_quality_report.json`
  - attempt id: `gen-f914d30e`
- current package boundary:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md`
- archive boundary:
  - `C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\`
- reference boundary:
  - active:
    - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\`
  - completed:
    - `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\`
    - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\`
  - frozen:
    - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\`
  - reopen しない

## Rollback Rule

- archive snapshot を current read order に戻さない
- 各 implementation phase は owner 1 file に閉じる
- rollback は phase owner の narrow diff 単位で行う
- route experiment は feature flag または owner-local branch diff 単位で戻す
- visible naturalness を telemetry wording だけで改善したことにしない

## Locked Keep / Floor / Conditional

- keep:
  - current runtime mainline
  - `grounded generic default`
  - planning / skeleton opt-in only
  - `single-pass + optional single repair 1回`
- floor:
  - prompt-only remains a floor
  - strongest baseline / best practice とは書かない
- conditional:
  - skeleton / planning remains conditional signal only
  - reopen candidate に戻さない
- current keep diff:
  - latest `simple_note_pipeline/pipeline.py` reopen keep diff は rollback しない
  - `V3 company intro guard` は `3/3` で `SYS_PIPELINE_FAILURE`
  - history-first opener を success artifact として返さない fail-closed keep を baseline にする
  - `V1 2/2 non-worse` / `V2 1/1 non-worse` / `G1 2/2 no visible regression`
  - `hidden_late_validation_v1` と fail-close payload diagnostics は rollback しない
  - `hidden_late_validation_v1` active scope は `branding + semantic_article_key=company_introduction` のみ
  - diagnostics は `hidden_late_validation` と `failure_candidate_summary` を keep
  - acceptance 緩和は未実施のまま keep
  - `branding_operational_source_contract_v1` は rollback しない
  - active scope は `article_type=branding` かつ `semantic_article_key=""` / `branding`
  - `semantic_article_key=company_introduction` は active scope から除外する
  - `comparative_review_source_contract_v1` は rollback しない
  - active scope は `article_type=comparative_review`
  - `company_introduction_operational_source_contract_v1` は rollback しない
  - active scope は `article_type=branding` かつ `semantic_article_key=company_introduction`
  - company_introduction source-presentation direct trial learning は runtime diff ではないため rollback target を作らない
  - company_introduction source-packet dry-run validation learning は runtime keep 前の evidence として残す
  - `company_intro_hidden_persona_contract_v1` の rollback / failed status は維持する
  - kept files は `simple_note_pipeline/pipeline.py` / `simple_note_pipeline/prompt_builder.py` / `test_simple_note_pipeline.py`
- failed / rolled back:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `heading_drift_reconstruction_simplification_first`
  - kept diff なし
  - unchanged retry 禁止
  - V3 run2 は title history-first
  - V3 run3 は first section history-first
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `pipeline_current_first_triage`
  - kept diff なし
  - unchanged retry 禁止
  - V3 company intro guard は 3/3 fail
- web boundary:
  - public web article compare は current-business-first pattern 支持の evidence
  - direct GPT web compare remains unavailable
  - WEB 勝利は主張しない

## Do-Not-Retry Hypotheses

- prompt-only strengthening を comparative gate なしで先にやること
- persona 拡張を comparative gate なしで先にやること
- formatter regex の追加だけで branding を救うこと
- `prompt_builder.py` simplification-first wording line を unchanged で再投入すること
- `pipeline.py` current-first source ordering / hint triage を unchanged で再投入すること
- `SECTION_SHADOW` reopen を初手に戻すこと
- `quality_guard.py` first にすること
- repair acceptance reopen を初手にすること
- sentence-final monotony line を main candidate に戻すこと
- `newalgorithm_pipeline/pipeline.py` に fixed routing table や broad branding branch を積み増すこと
- `newalgorithm_pipeline/pipeline.py` に source ordering / hint branch を accumulative に積み増すこと
- company_introduction へ `strengths` / `achievements` / `message` / `contact` / `company_posture` required-first の source presentation をそのまま runtime 化すること
- company_introduction runtime へ persona名を入れる前提で再実装すること
- `company_intro_hidden_persona_contract_v1` の rollback を source-presentation learning だけで解除すること
- company_introduction source-packet dry-run validation learning だけで runtime keep 扱いすること
- company_introduction の retry trigger を ending monotony only / general naturalness / polish / length only / preference-only rewrite にすること
- company_introduction の `source_limit` を visible article に出すこと
- planner / generator core を初手で全面置換すること
- pre-2026-04-02 rationale を current source-of-truth に戻すこと
- `C:\tetie\notecode\note\natural_blog_core.py`
  - first section history clamp 仮説
- `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
  - formatter-only surface polish 仮説
- `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
  - upstream distilled summary 単独仮説

## Current Stop Boundary

- same owner recovery hypothesis で 3 failures
- current keep diff を守ったまま success artifact を返せない
- current keep diff を捨てないと前進できない
- owner scope を超えないと前進できない
- multiple owner reopen が必要
- current success path regression

## Park Boundary

- legal な `1 owner / 1 hypothesis` が消えたら current package を parked / not fixed に戻す
- current fail-closed keep baseline を捨てずに parked judgment へ戻す
- parked judgment 自体は rollback 対象ではなく source-of-truth judgment として扱う

## Reopen Exception Boundary

- explicit user reopen / continue exception:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - current keep diff baseline を維持したまま current-business-first recovery を narrow に見る
- reopen scope は owner 1 file に閉じる
- `prompt_builder.py` / `newalgorithm_pipeline/pipeline.py` failed hypotheses は reopen しない

## Hidden Late Validation V1 Keep Boundary

- keep:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
    - `_build_hidden_late_validation_contract`
    - `_evaluate_hidden_late_validation`
    - `_hidden_late_validation_improved`
    - `_has_visible_forbidden_heading`
    - fail-close payload diagnostics for `hidden_late_validation`
    - fail-close candidate excerpt diagnostics as `failure_candidate_summary`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
    - hidden validation scope / forbidden heading / warning / repair rejection / fail payload tests
- keep evidence:
  - first live validation:
    - company intro `1/3 success`
    - forbidden heading leakage `0`
    - hidden token visible leakage `0`
    - guard OK
    - hidden trigger `0`
  - fail payload live validation:
    - company intro `2/3 success`
    - fail payload preserved `hidden_late_validation`
    - fail payload preserved `failure_candidate_summary`
    - fail run was `hidden_late_validation_failure_count = 0`
    - fail cause was `company_intro_naturalness_not_improved` with `heading_reanchor` + `ending_bucket_monotony`
    - forbidden heading leakage `0`
    - guard OK
- rollback target if future regression appears:
  - only the hidden late validation / fail payload diagnostics diff in:
    - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
    - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- do not rollback for:
  - company intro still not fully closed
  - hidden trigger count `0`
  - naturalness acceptance residual without leakage / guard regression
- future caution:
  - do not expand hidden checklist first
  - do not broaden active scope beyond `branding + company_introduction`
  - do not add article-type fixed routing table
  - do not relax `ending_monotony` so far that flat artifact returns as success

## Company Introduction Source Presentation Learning Boundary

- status:
  - direct trial learningとして保持し、後続の `company_introduction_operational_source_contract_v1` runtime keep の前段 evidence として扱う
  - rollback target はない
  - `company_intro_hidden_persona_contract_v1` の rollback / failed status は維持する
- trial result:
  - fixed condition は best persona / editor / regeneration 条件を固定
  - source presentation 4種 x 3 runs
  - `baseline`: middle-late similarity avg `0.343`, coverage `3/3 full`, unsupported `0`, leakage `0`, brochure `1`, generic `0`, abstract close `1`, naturalness `strong 3/3`
  - `operational packet`: middle-late similarity avg `0.325`, coverage `3/3 full`, unsupported `0`, leakage `0`, brochure `0`, generic `0`, abstract close `0`, naturalness `strong 3/3`
  - `company-profile packet`: middle-late similarity avg `0.332`, coverage `3/3 full`, unsupported `0`, leakage `0`, brochure `9`, generic `3`, abstract close `1`, naturalness `acceptable 3/3`
  - `sparse operational packet`: middle-late similarity avg `0.345`, coverage `3/3 full`, unsupported `0`, leakage `0`, brochure `0`, generic `0`, abstract close `0`, naturalness `acceptable-thin 3/3`
- learning:
  - GPT-5.4 mini は source presentation / slot 名 / source packet の形へ強く追従する
  - company_introduction の brochure tone は persona 不足より source の渡し方に誘発されていた可能性が高い
  - `company-profile packet` は unsupported を増やさない一方、brochure tone / generic company copy を強く誘発する
  - `sparse operational packet` は理念寄りを避けるが、`current_business` がないため会社紹介として薄くなる
  - `operational packet` は会社紹介のまま、顧客接点 / 支援範囲 / 進め方 / 相談前判断へ戻しやすい
- future runtime compression candidate, not implemented:
  - required candidate: `current_business` / `customer_situation_or_entry_point` / `support_scope_boundary` / `operating_process_steps` / `pre_contact_decision`
  - optional candidate: `proof_signal`
  - guard-only candidate: `source_limit`
  - not required candidate: `company_posture`
  - avoid source-contract slot names: `strengths` / `achievements` / `message` / `contact`
  - `source_limit` は visible article ではなく unsupported claim guard としてだけ使う候補
- source-packet dry-run validation:
  - validation 時点では runtime pipeline は実行していない
  - source packet preflight + direct/dry-run validation として実施した
  - full operational source は `3 sources x 3 runs = 9` で pass
  - thin process source は `2 sources x 3 runs = 6` で warn-boundary / warn-pass
  - company-profile negative は `3 cases` で fail / expected reject
  - unsupported claim guard は `5 induced cases` で `5/5` detected / rejected
  - non-target guard は announcement / branding / case_study / comparative_review の `4 article types` で inactive / pass
  - total `27 validations`
  - preflight result は full operational source `pass`、thin process source `warn-boundary`、company-profile negative `fail`、unsupported guard `pass + guard-risk`、non-target `inactive`
  - final validation は full operational source `pass`、thin process source `warn-pass`、company-profile negative `expected reject`、unsupported guard `guard pass`、non-target guard `pass`
  - full operational source は required 5 slots reflected / unsupported `0` / leakage `0` / brochure-generic-abstract `0`
  - thin process source は process thin だが `support_scope_boundary` / `pre_contact_decision` で厚みを補完し、source外の手順追加はなかった
  - company-profile negative は operational coverage fail と brochure / generic drift `3/3` を検出した
  - unsupported guard は source_limit visible leakage `0`
  - operational packet preflight は後続の live validation で runtime keep に昇格した
- runtime compression that was later kept:
  - required candidate: `current_business` / `customer_situation_or_entry_point` / `support_scope_boundary` / `operating_process_steps` / `pre_contact_decision`
  - optional candidate: `proof_signal`
  - guard-only candidate: `source_limit`
  - avoid: `strengths` / `achievements` / `message` / `contact` / `company_posture` required 化
  - guard candidate: unsupported claim / source_limit visible leakage / brochure-only / generic-company-copy / abstract-philosophy-only / wrong article type drift
  - forbidden retry trigger: ending monotony only / general naturalness / polish / length only / preference-only rewrite
- do not rollback / do not promote for:
  - this direct trial learning alone
  - operational packet dry-run validation success alone
  - company_intro naturalness preference without source-contract regression
- future caution:
  - next step requires explicit regression / scope expansion / acceptance residual decision
  - do not put persona / editor / trial names into runtime prompt or visible output
  - do not add article-type fixed routing table

## Company Introduction Operational Source Contract V1 Keep Boundary

- keep:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
    - company_introduction runtime source contract prepare / merge / validation
    - company_introduction source contract validation diagnostics
    - guard for missing required slot / unsupported claim / source_limit visible leakage / brochure-only / generic-company-copy / abstract-philosophy-only / wrong article type drift
    - retry skip for ending monotony only / general naturalness / polish / length only / preference-only rewrite
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
    - compressed company_introduction craft rules
    - no persona / editor / trial names in runtime prompt strategy
    - no visible `source_limit`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
    - active scope / inactive non-target scope / prompt leakage / source_limit leakage / negative company-profile / unsupported guard / retry boundary tests
- active scope:
  - `article_type=branding`
  - `semantic_article_key=company_introduction`
  - inactive for non-target article types
  - case_study / announcement / non-company-introduction branding / comparative_review keep behavior is not redefined
- source contract:
  - required:
    - `current_business`
    - `customer_situation_or_entry_point`
    - `support_scope_boundary`
    - `operating_process_steps`
    - `pre_contact_decision`
  - optional:
    - `proof_signal`
  - guard-only:
    - `source_limit`
- craft boundary:
  - source presentation / slot 名 / source packet を主要制御点として扱う
  - 会社紹介を顧客接点 / 支援範囲 / 進め方 / 相談前判断へ戻す
  - `strengths` / `achievements` / `message` / `contact` / `company_posture` required-first は do-not-retry 側に維持する
  - runtime prompt へ persona / editor / trial names は入れない
  - `source_limit` は visible article に出さない
  - article-type fixed routing table は追加しない
- retry allowed only for:
  - missing required slot
  - unsupported claim
  - wrong article type drift
  - brochure-only
  - generic-company-copy
  - abstract-philosophy-only
  - source_limit visible leakage
- retry forbidden for:
  - ending monotony only
  - general naturalness
  - polish
  - length only
  - preference-only rewrite
- keep evidence:
  - artifact:
    - `C:\tetie\notecode\logs\company_introduction_operational_source_contract_v1_live_validation_20260422-185418\combined_report.md`
    - `C:\tetie\notecode\logs\company_introduction_operational_source_contract_v1_live_validation_20260422-185418\combined_summary.json`
  - full operational source:
    - `9/9`
  - thin process source:
    - `6/6`
  - company-profile negative:
    - `3/3 expected reject`
  - unsupported induced guard:
    - `5/5 detected / rejected`
  - non-target live:
    - `4/4 inactive / pass`
  - persona / editor / trial leakage:
    - `0`
  - source_limit visible leakage:
    - `0`
  - active live retry_count:
    - `0`
  - retry boundary:
    - `6/6`
  - disallowed retry ids:
    - `[]`
  - errors:
    - `[]`
  - residual:
    - `None`
  - pass gate:
    - `overall=true`
- rollback target if future regression appears:
  - only the `company_introduction_operational_source_contract_v1` source contract / craft prompt / validation tests diff in:
    - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
    - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
    - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- do not rollback for:
  - `company_intro_hidden_persona_contract_v1` remains failed / rolled back
  - ending monotony only
  - general naturalness / polish / length preference without source-contract regression
  - non-target behavior that remains inactive / pass
- future caution:
  - do not broaden active scope beyond `article_type=branding` + `semantic_article_key=company_introduction`
  - do not add article-type fixed routing table
  - do not put persona / editor / trial names into runtime prompt or visible output
  - do not mark case_study / announcement / non-company-introduction branding / comparative_review as changed from this keep result

## Branding Operational Source Contract V1 Keep Boundary

- keep:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
    - branding runtime source contract prepare / merge / validation
    - `branding_source_contract_validation` diagnostics
    - repair acceptance gating for branding source contract improvement
    - retry skip for `ending_bucket_monotony` only
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
    - compressed branding craft rules
    - no persona / editor / trial names in runtime prompt strategy
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
    - active scope / inactive scope / prompt leakage / minimum slot / buried touchpoint / drift / unsupported claim / repair rejection / monotony-only skip tests
- active scope:
  - `article_type=branding`
  - `semantic_article_key=""` or `semantic_article_key=branding`
  - explicitly excludes `semantic_article_key=company_introduction`
- source contract:
  - required:
    - `customer_touchpoint`
    - `operating_behavior`
    - `decision_principle`
    - `support_process`
    - `brand_posture_in_action`
  - optional:
    - `proof_signal`
- retry allowed only for:
  - missing required slot
  - unsupported claim
  - wrong article type drift
  - `philosophy_only` / `advertising_copy` / `abstract_value_only`
  - `customer_touchpoint_buried`
- retry forbidden for:
  - `ending_bucket_monotony` only
  - general naturalness
  - polish
  - length only
- keep evidence:
  - artifact:
    - `C:\tetie\notecode\logs\branding_operational_source_contract_v1_live_validation_20260422-125158\combined_report.md`
    - `C:\tetie\notecode\logs\branding_operational_source_contract_v1_live_validation_20260422-125158\combined_summary.json`
  - branding operational full source:
    - `3/3 success`
  - branding operational sparse source:
    - `2/2 success`
  - unsupported claim guard:
    - success
  - non-target announcement guard:
    - success
  - visible persona / experiment leakage:
    - `0`
  - retry count:
    - `0`
  - retry only allowed causes:
    - `true`
  - pass gate:
    - `overall=true`
- shared-check residual:
  - focused simple note / quality:
    - `183 passed`
  - UI matrix:
    - `29 passed`
  - shared bundle:
    - `327 passed, 2 failed`
    - `test_st08b4_industry_analysis_title_and_lead_do_not_echo_prompt` is an already documented known unrelated industry-analysis residual
    - `test_st05ab10_ui_short_comparative_axis_lock_fixture_uses_specific_fit_carry_for_caution` returned `SYS_LLM_CLIENT_REQUIRED` and is outside branding owner scope
  - do not rollback branding keep diff for these non-target residuals alone
- rollback target if future regression appears:
  - only the `branding_operational_source_contract_v1` source contract / craft prompt / validation tests diff in:
    - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
    - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
    - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- do not rollback for:
  - company introduction still not fully closed
  - `ending_bucket_monotony` only
  - general naturalness / polish / length preference without source-contract regression
  - non-target shared-check residuals listed above
- future caution:
  - do not reopen company_introduction through this contract
  - do not add article-type fixed routing table
  - do not put persona / editor / trial names into runtime prompt or visible output
  - do not mark comparative_review / explanatory / daily as ready from this keep result

## Comparative Review Source Contract V1 Keep Boundary

- keep:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
    - comparative_review runtime source contract prepare / merge / validation
    - comparative_review source contract validation telemetry under body generation
    - guard for ranking / absolute winner / unsupported price-plan-result-vendor claim / exaggerated superiority / affiliate tone / generic recommendation / missing fit or caution / wrong article type drift
    - repair acceptance gating for comparative_review contract improvement / unsupported claim clear
    - retry skip for `ending_bucket_monotony` only
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
    - compressed comparative article craft rules
    - no persona / editor / trial names in runtime prompt strategy
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
    - active scope / inactive non-target scope / prompt leakage / required slot / drift / unsupported claim / missing fit / missing caution / repair rejection / monotony-only skip tests
- active scope:
  - `article_type=comparative_review`
  - inactive for non-target article types
  - comparative_review contract は company_introduction を定義しない
- source contract:
  - required:
    - `comparison_context`
    - `evaluation_axes`
    - `option_differences`
    - `fit_conditions`
    - `tradeoffs_or_cautions`
    - `decision_next_step`
  - optional:
    - `price_or_plan`
    - `source_limit`
- craft boundary:
  - 勝敗・ランキングではなく条件別判断へ戻す
  - 同じ評価軸で複数候補を比べる
  - 向く条件、避ける条件、確認順を後半まで維持する
  - 価格、プラン、成果、ベンダー優位は source-backed の場合だけ書く
  - article-type fixed routing table は追加しない
- retry allowed only for:
  - missing required slot
  - unsupported price / plan / result / vendor claim
  - wrong article type drift
  - `ranking_drift`
  - `absolute_winner_drift`
  - `exaggerated_superiority`
  - fit_conditions missing
  - tradeoff_or_caution missing
- retry forbidden for:
  - `ending_bucket_monotony` only
  - general naturalness
  - polish
  - length only
  - preference-only rewrite
- keep evidence:
  - artifact:
    - `C:\tetie\notecode\logs\comparative_review_source_contract_v1_live_validation_20260422-142920\combined_report.md`
    - `C:\tetie\notecode\logs\comparative_review_source_contract_v1_live_validation_20260422-142920\combined_summary.json`
  - comparative full source:
    - `3/3 success`
  - comparative sparse / source-limited:
    - `2/2 success`
  - unsupported price / plan / result / vendor guard:
    - success
  - non-target announcement guard:
    - success
  - visible persona / editor / trial leakage:
    - `0`
  - retry count:
    - `2 optional repair invocations`
  - disallowed retry ids:
    - `0`
  - retry only allowed causes:
    - `true`
  - pass gate:
    - `overall=true`
- shared-check residual:
  - focused simple note / quality:
    - `192 passed`
  - UI matrix:
    - `29 passed`
  - shared bundle:
    - `327 passed, 2 failed`
    - `st05ab10 comparative_axis_lock = SYS_LLM_CLIENT_REQUIRED`
    - `st08b4 industry_analysis title/lead residual`
  - do not mark these residuals fixed
  - do not rollback comparative_review_source_contract_v1 keep diff for these residuals alone
- rollback target if future regression appears:
  - only the `comparative_review_source_contract_v1` source contract / craft prompt / validation tests diff in:
    - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
    - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
    - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- do not rollback for:
  - company introduction still not fully closed
  - `ending_bucket_monotony` only
  - general naturalness / polish / length preference without source-contract regression
  - non-target shared-check residuals listed above
- future caution:
  - do not reopen company_introduction through this contract
  - do not add article-type fixed routing table
  - do not put persona / editor / trial names into runtime prompt or visible output
  - do not mark explanatory / industry_analysis / daily implementation as ready from this keep result
  - do not claim full shared green while shared bundle remains `327 passed, 2 failed`

## Expected Failure Modes

- telemetry 追加のつもりで output payload が肥大化する
- repair containment を先に広げすぎて upstream root cause が見えなくなる
- section-first route experiment が owner-local を超えて multiple file rewrite になる
- upstream source ordering diff 単独では downstream history-first reanchor を止めきれない
- fail-closed だけ成立して current-business-first success path が戻らない
- normalize 緩和を先に入れて symptom の責任 owner がぼける

## Per-Phase Rollback Intention

### Phase 00 Route / Style / Repair Telemetry Freeze

- frozen telemetry:
  - `writer_of_record`
  - `route_branch`
  - `section_path_used`
  - `style_profile_source`
  - `patch_path_refusal_reason`
  - `planned_vs_actual_heading_overlap`
- baseline note:
  - refreshed `latest_generation_output.json` keeps attempt `gen-c987d5e8` and now explains the current single-pass / patch-scope refusal path without changing visible body text
- rollback:
  - `pipeline.py` の telemetry keys 追加分だけを戻す

### Phase 01 Repair Trigger For Ending Monotony

- rollback:
  - `quality_guard.py` の ending monotony boost と telemetry diff だけを戻す

### Phase 02 Repair Patch Path And Acceptance For Branding

- rollback:
  - `simple_note_pipeline/pipeline.py` の branding patch path 条件と acceptance 条件だけを戻す

### Phase 03 Planning Opt-In Feature Gate

- rollback:
  - `newalgorithm_pipeline/pipeline.py` の `planning_opt_in_v1` composite gate diff だけを戻す
- close note:
  - `2026-04-12 21:54 JST` validation では `company / announcement / daily` は refusal のまま generic default を維持し、`ui-short-case-study-explain` は `dense_grounding_composite` で opt-in した
  - 以後、`technical explain` refusal を救うために同じ gate 緩和ラインを続けない
  - `technical explain / explanatory article` は current package から split out of package 済みとし、future reopen が必要な場合だけ separate line で扱う
  - future reopen の first owner candidate は `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` に留め、current package では reopen しない

### Phase 04 Company Intro Source-Aware Plan Prune

- rollback:
  - `natural_blog_core.py` の company intro defaults prune 分岐だけを戻す
- close note:
  - 2026-04-10 decision で `強み / 歩み / 提供価値` defaults は source bucket がない限り reopen しない
  - `ui-short-branding-company-grounded` は `会社の輪郭 -> 事業内容 -> 強み -> 結び` の 4 節 plan を keep する
  - first section history clamp 仮説は current docs lock judgment では do-not-retry とする

### Phase 05 Prompt Surface Constraint Preservation

- rollback:
  - `input_contract.py` の `prompt_surface_items` と associated telemetry だけを戻す
- close note:
  - prompt-only は floor として keep するが、`input_contract.py` の upstream distilled summary 単独 line は do-not-retry とする

### Phase 06 Branding Normalize Relaxation

- rollback:
  - `output_formatter.py` の branding-only normalize 分岐だけを戻す
- close note:
  - formatter-only surface polish 仮説は current docs lock judgment では do-not-retry とする
