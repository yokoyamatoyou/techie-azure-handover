# ui_source_blog_contract_redesign_2026-04-18 ROLLBACK

## Baseline

- package category:
  - `DOCS_FIRST_UI_SOURCE_BLOG_CONTRACT_REDESIGN_REBUILD`
- restore target:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- inherited parked boundary:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- inherited redesign reference:
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\`
- new package boundary:
  - `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\README.md`
  - `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\TASK.md`
  - `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\PROGRESS.md`
  - `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\ROLLBACK.md`
  - `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\EXECUTION_PROMPT.md`
- companion docs:
  - `C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md`
  - `C:\tetie\notecode\docs\current_codex_state.md`
  - `C:\tetie\notecode\docs\current_codex_workflow.md`
  - `C:\tetie\notecode\docs\current_codex_control_tower_prompt.md`
  - `C:\tetie\notecode\docs\current_codex_work_instruction_prompt.md`
  - `C:\tetie\notecode\docs\ui_source_blog_contract_archive_candidate_inventory_2026-04-18.md`
  - `C:\tetie\notecode\docs\separate_window_execution_prompt_ui_source_blog_contract_redesign_docs_followup_2026-04-18.md`
- evidence only:
  - `C:\tetie\notecode\docs\opening_frame_redesign_research_synthesis_note_2026-04-18.md`
  - `C:\tetie\notecode\docs\opening_frame_minimal_control_comparison_note_2026-04-18.md`
  - `C:\tetie\notecode\docs\opening_frame_pipeline_control_surface_triage_note_2026-04-18.md`
  - `C:\tetie\notecode\research\新しいフォルダー (3)\00_external_ai_research_request_zero_base_ui_source_blog_algorithm_2026-04-18.md`
  - `C:\tetie\notecode\research\新しいフォルダー (3)\08_external_ai_research_response_zero_base_ui_source_blog_algorithm_2026-04-18.md`
  - `C:\tetie\notecode\research\新しいフォルダー (4)\01_deepresearch_first_plan_2026-04-19.md`
  - `C:\tetie\notecode\research\新しいフォルダー (4)\02_prior_new_research_comparison_note_2026-04-19.md`
  - `C:\tetie\notecode\research\新しいフォルダー (4)\03_single_question_deepresearch_surface_realization_card_2026-04-19.md`
  - `C:\tetie\notecode\research\新しいフォルダー (4)\04_surface_artifact_adoption_note_2026-04-19.md`
- code diff state:
  - production rollback は不要
  - rollback 対象は new package docs と companion docs だけ

## Rollback Rule

- `naturalness_recovery_2026-04-07` docs は触らない
- `opening_frame_redesign_2026-04-18` docs は触らない
- production code / tests / AGENTS / WORKLOG は触らない
- actual archive は行わない
- rollback は new package docs と companion docs の file-local diff 単位で行う
- new package が current package reopen と実質同じ line になった場合は new docs だけを止める
- exact code owner を early fix した文言が入った場合は new docs 側だけを戻す
- runtime code candidate を actual archive 対象として書き始めた場合は new docs 側だけを戻す
- post-docs separate management step が exact code owner fix / exact file mapping / implementation prompt に滑った場合は new docs 側だけを戻す
- `ready_for_stage_a_scan` が implementation start や owner shortlist 固定に滑った場合は new docs 側だけを戻す
- Phase 04 `Stage B artifact boundary minimum` が concrete file mapping / exact schema / numeric threshold / actual archive に滑った場合は new docs 側だけを戻す
- current Phase 05 が `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` / generation prompt handoff only を超えて `pipeline.py` / guard / repair / owner table へ広がった場合は current docs と current code diff だけを戻す
- current Phase 06 first slice が `run_current_mainline_genre_sweep.py` の `live=False` limited eval を超えて production runtime edit / multi-owner continuation に広がった場合は current docs diff と eval artifact diff だけを戻す

## Phase 01 Fixed Baseline

- contract axes:
  - `reader_task / evidence_mode / voice_distance / opener_mode / reuse_level`
- source role shorthand:
  - `fact / continuity / style_memory`
- current contract read:
  - `紹介` は `current_business_first / current_fact_required / organization_neutral`
  - `お知らせ / 事例・お客様の声 / 比較・選び方` は `strict_factual`
  - `解説・ノウハウ / 業界・市場の話題` は `grounded_preferred`
  - `日常のできごと` は `observation_first`
- source role model:
  - `fact` は required slot と first claim を支える
  - `continuity` は followup 文脈だけを支える
  - `style_memory` は style summary だけを支える
  - `theme` は intent seed / retrieval key であり fact ではない
- opening-frame relation:
  - `opening_frame` は `opener_mode` の subproblem
  - `title / lead / first heading / first section first claim` は同じ opener anchor に従う
  - company introduction では history を support only に留める
- Phase 01 shorthand carryover:
  - `reuse_level` default は `none`
  - shorthand は `reuse_level default = none until Phase 02`
  - exact numeric threshold は heuristic-only のままで、canonical baseline に昇格させない

## Phase 02 Concrete Plan Boundary

- current runtime mainline は keep する
- zero-base redesign は runtime replacement ではなく artifact-boundary redesign として読む
- `reuse_level` は contract axis のまま keep し、runtime では gated axis として読む
- continuity reuse は `continuity capsule` のみを返し、fact slot を埋めない
- style memory reuse は `style capsule` のみを返し、named fact / example / heading を返さない
- raw past blog text は canonical opener / writer input に戻さない
- opener owner は fact-primary / support-only だけを読み、`continuity` / `style_memory` を直接読まない
- ambiguity / insufficient corpus / duplication risk / fact insufficiency では `reuse_level = none` へ abstain する
- exact code owner は still `not fixed`

## Inherited Do-Not-Retry Hypotheses

- `prompt_builder.py` simplification-first wording line を unchanged で再投入すること
- `pipeline.py` current-first source ordering / hint triage を unchanged で再投入すること
- `pipeline.py` core_message current-first hint を unchanged で再投入すること
- `SECTION_SHADOW` reopen を初手に戻すこと
- `quality_guard.py` first にすること
- repair acceptance reopen を初手にすること
- sentence-final monotony line を main candidate に戻すこと
- `natural_blog_core.py` first section history clamp 仮説
- `output_formatter.py` formatter-only surface polish 仮説
- `input_contract.py` upstream distilled summary 単独仮説
- prompt accretion continuation
- fixed routing table
- planning / skeleton default reopen
- giant rewrite

## Package-Specific Archive Policy

- current package goal は `inventory only`
- `archive-safe-now` へ入れてよいのは
  - current prompt ではない historical docs / prompts
  - rollback 済み experiment notes
  - copy-only research support files
- `archive-later-after-confirmation` は
  - current package が still reference として見ている docs 群
  - `opening_frame_redesign_2026-04-18` まわりの docs / prompts
- `do-not-archive` は
  - current runtime code
  - current source-of-truth packages
  - current startup path docs
  - current prompt
  - current evidence boundary files
- Phase 03 closeout では current startup path docs / current package / current prompt / current runtime boundary を `do-not-archive` の current baseline として保守する
- production runtime code candidate はこの package では fixed しない
- post-docs separate management step は `hold_docs_only / ready_for_stage_a_scan / stop_and_user_report` の 3 出力に限定する
- `ready_for_stage_a_scan` は `Stage A telemetry only` の artifact-level readiness に限定し、owner fix へ進めない
- current post-docs management verdict は `stop_and_user_report` で、completed Phase 05 closeout 後の next forward move が `pipeline.py` / quality guard / repair / routing / broader eval lane / threshold canonicalization / package-wide owner table / implementation prompt / actual archive を要する boundary に留める
- `ready_for_stage_a_scan` / Stage A dispatch / separate management execution への言及は historical record または management contract reference であり、rollback baseline 上の current active route ではない
- grounding pass / semantic pass / source-opener-reuse boundary keep 後も fingerprint-side quality block が残り、current evidence だけでは next legal advance を決め切れないときだけ、future boundary note は single-question deepresearch trigger 1 問に限定する
- deepresearch-first lane の `comparison note -> single-question deepresearch -> adoption note` は close 済み research/evidence lane として keep し、current active route や package continuation に上げない
- `surface realization card` は completed Phase 05 artifact に留め、`surface profile` は alias only に留める
- current user-explicit Phase 05 では、`surface realization card` を writer-facing first construction artifact として `prompt_builder.py` handoff only に narrow に落とすことだけを許可する

## Stage A Readiness Baseline

- current Stage A checklist は `article_contract / fact sufficiency / opener support-only / reuse gate reason`
- `reuse_level = none` と fact insufficiency stop は legal Stage A output として維持する
- Stage A は telemetry only であり、`fact packet / opener card / capsules` を Stage A 自体には混ぜない
- current unresolved boundary は exact code owner / exact file mapping / implementation prompt / actual archive のまま維持する
- exact code owner / exact file mapping / implementation prompt / actual archive は Stage A では fixed しない

## Phase 04 Stage B Artifact Boundary Minimum

- current role boundary:
  - `fact packet` は fact-primary shadow artifact であり、required current fact slot / first-claim candidate / article-contract read を束ねる
  - `opener card` は `title / lead / first heading / first section first claim` の shared opener anchor を切り出す shadow artifact である
  - `continuity capsule` は followup context / repeated reader concern の support-only summary であり、missing fact slot を埋めない
  - `style capsule` は paragraph rhythm / ending mix / lead temperature / closing intensity の content-free summary であり、named fact / example / heading を返さない
- current stop boundary:
  - Phase 04 は role boundary の定義で止め、exact code owner / exact file mapping / implementation prompt / actual archive は fixed しない
  - concrete file mapping / exact schema / numeric threshold / activation rewrite に滑った場合は current docs diff だけを rollback する

## Phase 05 Surface Realization Card First Construction Slice

- current role boundary:
  - `surface realization card` は writer の直前に置く content-free surface artifact であり、new fact source ではない
  - current minimum fields は `paragraph_breath / sentence_length_band / ending_mix / nominalization_budget / subject_visibility / connective_tolerance`
  - opener owner は `continuity` / `style_memory` / `surface realization card` を直接読まない
- current exact owner / mapping:
  - exact code owner は `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` current slice only
  - exact file mapping は generation prompt の writer-facing `[SURFACE_REALIZATION_CARD]` handoff block only
- current closeout baseline:
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py` 1-file owner-local test-lane で `announcement / daily_story / branding` の writer prompt に `[SURFACE_REALIZATION_CARD]` と field 6 本が入ることを lock 済み
- current stop boundary:
  - `pipeline.py` / `quality_guard.py` / repair / routing / broader eval lane / owner table / implementation prompt / actual archive / threshold canonicalization へ滑った場合は current docs と current code diff だけを rollback する

## Phase 06 Surface Realization Card Offline Eval-First Slice

- current role boundary:
  - first slice は `C:\tetie\notecode\tools\run_current_mainline_genre_sweep.py` の `live=False` limited eval と generated artifact review に留める
  - target genres は `announcement / daily_story / branding`
  - current self-test artifact は `C:\tetie\notecode\logs\current_mainline_ui_runs\phase06_surface_realization_card_eval\` 配下の `summary.json / matrix.json / genre_issue_ledger.json / manual_review.md / research_notes.md`
  - current artifact read は `execution_mode = offline_deterministic` / `compatibility_rebuild_applied = true` / `contract_alignment.compatibility_source = native_minimal` に寄り、`互換経路の動作確認用に最小本文を返します。` と `〜を具体化します。` の active root は `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- current stop boundary:
  - first slice では production runtime file edit / `pipeline.py` / `quality_guard.py` / repair / routing / threshold canonicalization / actual archive を開かない
  - current eval read から `prompt_builder.py` を next owner に読み替えない
  - `pipeline.py` / runtime route change が必要になった時点で `stop_and_user_report`
  - eval result が single-owner narrow continuation に落ちない場合は `stop_and_user_report`
  - same slice error は 3 回まで自己修正し、未解決なら current docs diff と eval artifact diff だけを rollback する

## Package-Specific Stop Boundary

- current package reopen と実質同じ line になった
- `opening_frame_redesign_2026-04-18` の implementation continuation に滑った
- exact code owner を current Phase 05 slice 以外で `pipeline.py` や `prompt_builder.py` に早期固定した
- actual archive を今やりたくなった
- package objective が broad algorithm rewrite に膨らんだ
- self-blog reuse を fact source default として扱いたくなった
- `theme` を fact source に上げたくなった
- raw past blog text を opener input に戻したくなった
- opener owner に `continuity` / `style_memory` を直接読ませたくなった
- `reuse_level` を Phase 02 前に active default へ上げたくなった
- multiple worker implementation planning が必要になった
- post-docs separate management step で exact code owner shortlist を canonical にしたくなった
- `Stage A telemetry only` に `fact packet / opener card / capsules` や exact numeric threshold fix を混ぜたくなった
- Phase 04 の `fact packet / opener card / continuity capsule / style capsule` を concrete file owner / exact file mapping / implementation prompt に落としたくなった
- current Phase 05 の `surface realization card` を `prompt_builder.py` handoff only から broader route change に膨らませたくなった
- `Stage C / D / E` を first candidate に上げたくなった

## Reopen Boundary

- `naturalness_recovery_2026-04-07` は parked / not fixed のまま維持する
- `opening_frame_redesign_2026-04-18` は reference line のまま維持する
- docs phases pass 後も separate management step までは exact code owner = `not fixed` を維持する
- implementation owner を判断するとしても docs phases pass 後の separate management step に分ける
- separate management step は `hold_docs_only / ready_for_stage_a_scan / stop_and_user_report` だけを返す
- `ready_for_stage_a_scan` は `Stage A telemetry only` readiness scan であり、implementation start ではない
- current baseline では Stage A telemetry-only scan close 後に default で further docs-only slice を作らない
- ただし explicit user instruction があるときだけ、Phase 04 `Stage B artifact boundary minimum` の narrow docs-only slice を 1 本だけ追加できる
- completed Phase 05 closeout 後は、next forward move が必要になった時点で再び `stop_and_user_report` を返す
- explicit user instruction があるときだけ、completed Phase 05 closeout 後に Phase 06 `surface realization card offline eval-first slice` を 1 本だけ開ける
- fingerprint-side quality block 向けの future boundary note を broad redesign / early owner fix / multiple-question research reopen に膨らませない
- single-question deepresearch trigger は future boundary note only であり、active next step や reopen route ではない
- ただし user が deepresearch-first lane を explicit に選ぶときだけ、`comparison note -> single-question deepresearch -> adoption note` の research/evidence lane は許可する
- 上記 lane は closeout success を current baseline に反映するだけであり、completed Phase 05 closeout 後も `surface realization card` を `prompt_builder.py` handoff-only slice から broader owner / exact mapping / implementation prompt に膨らませない
- deepresearch-first lane は package reopen route ではなく、exact code owner / exact file mapping / implementation prompt / actual archive fix に滑ったら current docs diff だけを rollback する
- companion follow-up prompt は docs-only work slice 用であり implementation prompt ではない

## Expected Failure Modes

- `opening_frame` subproblem と top-level contract problem を混ぜてしまう
- article type contract がカテゴリ別長文ルール集に戻る
- self-blog reuse の設計が style と fact の混線に戻る
- continuity / style capsule が raw retrieval / raw exemplar に戻る
- opener owner が continuity / style を読んで history-first drift を再導入する
- archive inventory が actual delete plan へ膨らむ
- source role separation を fixed routing table の別名にしてしまう
