# naturalness_recovery_2026-04-07 README

## Objective

- current success path を壊さず、branding / company introduction の visible surface を自然な日本語の読み物へ戻す narrow package を固定する
- 主因を `persona 不足` ではなく `route ownership / state loss / repair non-actuation` として扱い、owner-local な順序で修正する
- prompt accretion ではなく runtime owner と state flow を整え、改行・文末・主語省略・意味密度の改善を狙う

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
4. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
5. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
6. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
7. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md`
8. `C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md`
9. `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md`
10. `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md`
11. `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md`
12. `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md`
13. `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md`
14. `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md`
15. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md`
16. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md`
17. `C:\tetie\notecode\ALGORITHM.md`
18. `C:\tetie\WORKLOG.md`

## Source Of Truth

- current runtime baseline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- current visible artifact baseline:
  - `C:\tetie\notecode\logs\latest_generation_output.txt`
  - `C:\tetie\notecode\logs\latest_generation_output.json`
  - `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- current planning package:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- archive snapshot:
  - `C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\`
- active reference package:
  - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\`
- completed / frozen reference:
  - `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\`
  - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\`
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\`

## Current Decision

- overall category:
  - `COMPANY_INTRODUCTION_OPERATIONAL_SOURCE_CONTRACT_V1_RUNTIME_KEEP`
- repo decision:
  - `keep core, refactor boundaries`
- package theme:
  - `keep core, recover visible naturalness`
- current package objective:
  - blank `branding/company_introduction` の failed hypothesis lock と `hidden_late_validation_v1` guard を維持しつつ、`company_introduction_operational_source_contract_v1` を runtime keep として同期し、source contract / craft / guard / retry boundary に圧縮された範囲を rollback boundary へ固定する
- runtime / route keep-state:
  - default route は `grounded generic default`
  - planning / skeleton は `opt-in only`
  - structural baseline は `single-pass + optional single repair 1回`
- failed hypothesis locked:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `heading_drift_reconstruction_simplification_first`
  - wording simplification 単独 line は rollback 済み
  - kept diff はない
  - same hypothesis を unchanged で reopen しない
  - V1 は partial / non-worse
  - G1 は no visible regression
  - V2 は still awkward variance
  - V3 は mandatory gate fail
  - V3 run2 は title history-first
  - V3 run3 は first section history-first
  - よって `prompt_builder.py` wording simplification 単独は current winner ではない
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `pipeline_current_first_triage`
  - upstream minimal current-first hint / source ordering triage
  - rollback 済み
  - kept diff はない
  - unchanged retry 禁止
  - focused/shared は non-regression だったが V3 company intro guard は 3/3 fail
  - よって `pipeline.py` upstream source ordering / hint triage 単独も current winner ではない
- current keep diff:
  - latest `simple_note_pipeline/pipeline.py` owner reopen は rollback なしで keep された
  - touched files は `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` と `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
  - `V3` company intro guard は `3/3` で `SYS_PIPELINE_FAILURE`
  - `V1` は `2/2 non-worse`
  - `V2` は `1/1 non-worse`
  - `G1` は `2/2 no visible regression`
  - history-first opener を success artifact として返さない fail-closed keep は前進として扱う
  - 2026-04-18 時点では `success=true` の current-business-first artifact はまだ立証していなかった
- hidden_late_validation_v1 keep diff:
  - `hidden_late_validation_v1` は rollback なしで keep する
  - touched files は `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` と `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
  - helper は `_build_hidden_late_validation_contract` / `_evaluate_hidden_late_validation` / `_hidden_late_validation_improved` / `_has_visible_forbidden_heading`
  - diagnostics は `hidden_late_validation` / `failure_candidate_summary`
  - active scope は `branding + semantic_article_key=company_introduction` のみ
  - article-type fixed routing table は追加していない
  - acceptance 緩和は未実施
  - first live validation は company intro `1/3 success`、leakage `0`、guard OK、hidden trigger `0`
  - fail payload live validation は company intro `2/3 success`、fail payload diagnostics preserved、leakage `0`、guard OK
  - fail run は hidden checklist 不足ではなく `company_intro_naturalness_not_improved` with `heading_reanchor` + `ending_bucket_monotony`
  - target recovery repeatability は未 close
- company_introduction_operational_source_contract_v1 keep diff:
  - `company_introduction_operational_source_contract_v1` は rollback なしで runtime keep する
  - touched files は `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` / `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` / `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
  - active scope は `article_type=branding` かつ `semantic_article_key=company_introduction`
  - required source slots は `current_business` / `customer_situation_or_entry_point` / `support_scope_boundary` / `operating_process_steps` / `pre_contact_decision`
  - optional source slot は `proof_signal`
  - guard-only source slot は `source_limit`
  - persona / editor / trial names は runtime prompt に入れない
  - `source_limit` は visible article に出さず unsupported claim guard としてだけ扱う
  - retry forbidden は ending monotony only / general naturalness / polish / length only / preference-only rewrite
  - live validation artifact は `C:\tetie\notecode\logs\company_introduction_operational_source_contract_v1_live_validation_20260422-185418`
  - full operational source `9/9`、thin process source `6/6`、company-profile negative `3/3 expected reject`、unsupported induced guard `5/5 detected / rejected`、non-target live `4/4 inactive / pass`
  - persona/editor/trial leakage `0`、source_limit visible leakage `0`、active live retry_count `0`、retry boundary `6/6`、disallowed retry ids `[]`、errors `[]`、residual `None`、pass_gate.overall `true`
  - `company_intro_hidden_persona_contract_v1` の rollback / failed status は解除しない
  - case_study / announcement / non-company-introduction branding / comparative_review の既存 keep は再定義しない
  - article-type fixed routing table は追加していない
- next owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - current keep diff baseline を維持した same owner continue
- next narrow hypothesis:
  - next code hypothesis はまだ開始しない
  - `company_introduction_operational_source_contract_v1` は runtime keep のため、次に触るなら regression / scope expansion / acceptance residual が明示された場合だけ same owner の新 hypothesis として扱う
  - `ending_monotony` を緩めすぎて flat artifact を success に戻さない
- prompt-only:
  - `floor`
  - strongest baseline ではない
  - best practice とも書かない
- skeleton / planning:
  - `conditional signal only`
  - default reopen しない
  - winner 扱いしない
- public web article compare:
  - current-business-first pattern を支持する evidence として keep する
- direct GPT web compare:
  - `unavailable`
  - WEB 勝利はまだ主張しない
- technical explain / explanatory:
  - current package に戻さない
- article-type routing:
  - fixed routing table は追加しない
- do-not-retry narrow lines:
  - `C:\tetie\notecode\note\natural_blog_core.py`
    - first section history clamp 仮説
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
    - formatter-only surface polish 仮説
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
    - upstream distilled summary 単独仮説
- next code policy:
  - `pipeline.py` 1 owner triage の再判断は stop report で完了
  - latest fail-closed keep と `hidden_late_validation_v1` keep を baseline として維持し、次の code change は management 判断まで開始しない
- not adopted:
  - `prompt_builder.py` simplification-first line を current winner / completed として書き換えること
  - `SECTION_SHADOW` reopen を初手に戻すこと
  - `quality_guard.py` first
  - repair acceptance reopen first
  - sentence-final monotony first
  - `prompt-only winner` の断定
  - `planning / skeleton default across article types`
  - `technical explain / explanatory` の current package 戻し
  - `article-type fixed routing table`
  - prompt accretion で押し切ること
  - multiple owner simultaneous reopen
  - `genre-by-genre algorithm tuning accumulation`
  - `large-scale generator rewrite first`

## Package State

- package status:
  - active
  - not_closed
- package mode:
  - docs-lock-complete / company-introduction-operational-source-contract-runtime-keep
- current phase:
  - company introduction operational source contract v1 keep / docs sync / closeout
- phase 00 status:
  - completed
- phase 01 status:
  - deferred
- phase 02 status:
  - closed_without_advance
- phase 03 status:
  - completed
- phase 04 status:
  - completed
- phase 05 status:
  - historical_keep_diff
- phase 06 status:
  - conditional
- current honest status:
  - historical keep diff は current mainline に残る
  - ただし latest `prompt_builder.py` simplification-first retry は rollback 済み
  - latest `pipeline.py` current-first triage も rollback 済み
  - latest `simple_note_pipeline/pipeline.py` reopen keep diff は rollback していない
  - `hidden_late_validation_v1` と fail-close payload diagnostics は rollback していない
  - `company_introduction_operational_source_contract_v1` は runtime keep として rollback していない
  - unsafe history-first success path は `SYS_PIPELINE_FAILURE` で blocked できている
  - current-business-first / operational-source-backed success path は latest live validation で full source `9/9` と thin source `6/6` が PASS
  - naturalness 一般ではなく source contract / guard / retry boundary の runtime keep として closeout する
  - next code hypothesis はまだ開始しない
- next action:
  - source-of-truth と `company_introduction_operational_source_contract_v1` keep を同期する
  - next implementation window は不要
  - future change は regression / scope expansion / acceptance residual が明示された場合だけ management 判断で開始する

## Why

- latest same-owner reopen は `V3 company intro guard` を `3/3` で `SYS_PIPELINE_FAILURE` に倒し、history-first opener を success artifact として返さない fail-closed keep を作った
- `V1` は `2/2 non-worse`、`V2` は `1/1 non-worse`、`G1` は `2/2 no visible regression` であり、broad regression ではなく target opener recovery の未達として読むのが妥当
- この fixed read は、unsafe history-first success path を blocked した上で、source contract / craft / guard に圧縮した current-business-first success path を live validation で立証したということ
- rollback なしで keep diff が current mainline に残っており、owner scope も `simple_note_pipeline/pipeline.py` 1 file に閉じたままなので、next step は same failed reopen の retry ではなく current keep diff baseline 上の new recovery hypothesis として書ける
- したがって current package の management judgment は `company_introduction_operational_source_contract_v1` runtime keep とし、次の code change を自動継続しない
- prompt-only lane は fallback / floor としては keep できるが、strongest baseline や best practice とまでは言えなかった
- skeleton / planning lane は conditional signal を返したが、default reopen candidate に昇格するほどの勝ち筋は示さなかった
- public web article compare では、現在事業 / 現在の役割から入り、history は後段へ回し、社名反復を lead 後に落とし、短い段落で呼吸を作る pattern が観測された
- direct GPT web compare は unavailable のままで、WEB company intro baseline に勝ったという主張はできない
- deepresearch は evidence として読むが、current source-of-truth には昇格させない
- current objective は blank `branding/company_introduction` に閉じたままで、technical explain / explanatory は current package に戻さない
- `2026-04-12` の fixed3 route bypass compare では winner が `generic, generic, prompt_only` となり、`algorithm` は 3 case とも future default を正当化できなかった
- article-type observation では `company / announcement` が provisional に generic 寄りで、`daily / technical explain` は planning default を支える safe majority を作れなかった
- `2026-04-12 21:54 JST` の planning opt-in gate validation では、`company / announcement / daily` は refusal のまま generic default 側に残り、`ui-short-case-study-explain` は `activation_path = dense_grounding_composite` で opt-in した
- 同 validation では `bl-explanatory-misread-metric` が `article_type_prior = coverage_first_prior` かつ `reason_code = grounded_sections_insufficient` で refusal し、strict すぎる hard gate 問題ではなく source coverage / grounding readiness の別問題として切るべきことが見えた
- `daily` は `input_contract -> prompt_builder handoff -> prompt_builder simplify` と narrow loop を進めても `final_winner = none_safe_majority` のままで、局所 tuning を future default に昇格できない
- `technical explain` では naturalness より先に coverage unsafe が stop-loss になり、planning 利得より `coverage-first` の入口条件が必要だと分かった
- これにより current package の route 解釈は `planning / skeleton default` ではなく、`grounded generic default` を本線にし、planning は feature gate を通った場合だけ opt-in するほうが local evidence と整合する
- `input_contract.py` は raw prompt の micro-surface 指示を contract compression で落としうるが、その改善 diff も route default を generic から planning へ反転させる十分条件にはなっていない
- `company_introduction` は `strengths` / `achievements` / `message` / `contact` / `company_posture` required-first ではなく、operational source slots を主要制御点にするほうが brochure / generic drift を抑えやすい
- current UI 側でも role clarity は品質条件であり、曖昧な立場語を置くと追従性の高いモデルがその role 語を本文 surface に持ち込みやすい。現行 keep state は `C:\tetie\notecode\docs\ui_role_clarity_record_2026-04-08.md` を正本にする

## Complexity Snapshot

- primary concern:
  - route ownership と repair containment を同時に触ると原因の切り分けが崩れること
  - `article type = fixed route` を早く入れすぎると ad-hoc rule が増え、rollback しにくいこと
  - telemetry 不足のまま planning opt-in を入れると rollback しにくいこと
  - output normalize を先に緩めると root cause を見失うこと
- keep untouched first:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\note_writer_app.py`

## Simplification Direction

### Keep

- current success path の順序
- single-pass mainline と optional repair の現行構造
- `grounded generic default`
- planning は explicit feature gate を通ったときだけ opt-in する運用
- `planning_opt_in_v1` は `dense_grounding_composite` を含む composite gate として keep し、単一 hard gate へ戻さない
- docs-first / owner-local / rollback-first 運用
- `note_writer_app.py` の semantic ごとに狭めた role UI と `structure=auto` 固定

### Thin

- current package docs の split closeout wording
- `input_contract.py` の surface constraint loss
- `natural_blog_core.py` の source-unaware company intro defaults
- repair gate / patch / acceptance の detect-only surface
- branding 向け output normalize の過剰均し

### Remove As Default Assumption

- planning / skeleton を default にすれば広く勝てる前提
- Phase 03 完了後も gate 緩和を続ければ technical explain が救える前提
- algorithm tuning を各 genre に積めば勝てる前提
- persona を増やせば visible surface が先に改善する前提
- historical loop priority を future default とみなす前提
- quality telemetry が出ていれば本文も直っている前提
- unsupported section を generic filler で埋めても読みにくさに直結しない前提
- output normalize は branding の自然さを壊さない前提
- UI の曖昧な role label は harmless で、runtime 側だけ直せば十分という前提

## Non-Goals

- `simple_note_pipeline/pipeline.py` の本文生成骨格を初手で置換すること
- article-type fixed rule を current priors のまま hardcode すること
- `planning_opt_in_v1` の composite gate keep 後に、同じ gate 緩和ラインを惰性で続けること
- technical explain / explanatory article の coverage-first line を current package の next diff として reopen すること
- daily の owner-loop を future default の根拠なしに再開すること
- completed / frozen reference package を reopen すること
- pre-2026-04-02 work records を current planning surface に戻すこと
- hidden reviser や prompt accretion を増やすこと
