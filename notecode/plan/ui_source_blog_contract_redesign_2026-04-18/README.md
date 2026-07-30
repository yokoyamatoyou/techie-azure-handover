# ui_source_blog_contract_redesign_2026-04-18 README

## Objective

- current runtime mainline は維持し、改修対象は docs-first zero-base redesign line に閉じる
- 開発判断を `局所 symptom 修正` から `UI article contract / source role separation / self-blog reuse policy` の docs-first 再設計へ切り替える
- `opening_frame_redesign_2026-04-18` を下位の設計論点として保持しつつ、さらに上位の `UI -> source -> Japanese blog contract` 問題を separate top-level line として固定する
- deadcode archive は actual archive ではなく `inventory only` に留め、current runtime / current package / AGENTS / WORKLOG を触らずに次の docs-only work slice へ渡す

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\README.md`
4. `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\TASK.md`
5. `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\PROGRESS.md`
6. `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\ROLLBACK.md`
7. `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\EXECUTION_PROMPT.md`
8. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
9. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
10. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
11. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
12. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md`
13. `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\README.md`
14. `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\TASK.md`
15. `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\PROGRESS.md`
16. `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\ROLLBACK.md`
17. `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\EXECUTION_PROMPT.md`
18. `C:\tetie\notecode\docs\opening_frame_redesign_research_synthesis_note_2026-04-18.md`
19. `C:\tetie\notecode\docs\opening_frame_minimal_control_comparison_note_2026-04-18.md`
20. `C:\tetie\notecode\docs\opening_frame_pipeline_control_surface_triage_note_2026-04-18.md`
21. `C:\tetie\notecode\research\新しいフォルダー (3)\00_external_ai_research_request_zero_base_ui_source_blog_algorithm_2026-04-18.md`
22. `C:\tetie\notecode\research\新しいフォルダー (3)\08_external_ai_research_response_zero_base_ui_source_blog_algorithm_2026-04-18.md`
23. `C:\tetie\WORKLOG.md`

- user が deepresearch-first lane を explicit に選ぶときだけ、この package docs の後で `C:\tetie\notecode\research\新しいフォルダー (4)\01_deepresearch_first_plan_2026-04-19.md` / `C:\tetie\notecode\research\新しいフォルダー (4)\02_prior_new_research_comparison_note_2026-04-19.md` / `C:\tetie\notecode\research\新しいフォルダー (4)\03_single_question_deepresearch_surface_realization_card_2026-04-19.md` / `C:\tetie\notecode\research\新しいフォルダー (4)\04_surface_artifact_adoption_note_2026-04-19.md` を closeout evidence として読む

## Source Of Truth

- this package:
  - `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\README.md`
  - `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\TASK.md`
  - `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\PROGRESS.md`
  - `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\ROLLBACK.md`
  - `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\EXECUTION_PROMPT.md`
- inherited parked boundary:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- inherited redesign reference:
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\`
- companion docs:
  - `C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md`
  - `C:\tetie\notecode\docs\current_codex_state.md`
  - `C:\tetie\notecode\docs\current_codex_workflow.md`
  - `C:\tetie\notecode\docs\current_codex_control_tower_prompt.md`
  - `C:\tetie\notecode\docs\current_codex_work_instruction_prompt.md`
  - `C:\tetie\notecode\docs\ui_source_blog_contract_archive_candidate_inventory_2026-04-18.md`
  - `C:\tetie\notecode\docs\separate_window_execution_prompt_ui_source_blog_contract_redesign_docs_followup_2026-04-18.md`
- evidence only:
  - `C:\tetie\notecode\docs\deepresearch_algorithm_validation_note_2026-04-18.md`
  - `C:\tetie\notecode\docs\opening_frame_redesign_research_synthesis_note_2026-04-18.md`
  - `C:\tetie\notecode\docs\opening_frame_minimal_control_comparison_note_2026-04-18.md`
  - `C:\tetie\notecode\docs\opening_frame_pipeline_control_surface_triage_note_2026-04-18.md`
  - `C:\tetie\notecode\research\新しいフォルダー (3)\00_external_ai_research_request_zero_base_ui_source_blog_algorithm_2026-04-18.md`
  - `C:\tetie\notecode\research\新しいフォルダー (3)\08_external_ai_research_response_zero_base_ui_source_blog_algorithm_2026-04-18.md`
  - `C:\tetie\notecode\research\新しいフォルダー (4)\01_deepresearch_first_plan_2026-04-19.md`
  - `C:\tetie\notecode\research\新しいフォルダー (4)\02_prior_new_research_comparison_note_2026-04-19.md`
  - `C:\tetie\notecode\research\新しいフォルダー (4)\03_single_question_deepresearch_surface_realization_card_2026-04-19.md`
  - `C:\tetie\notecode\research\新しいフォルダー (4)\04_surface_artifact_adoption_note_2026-04-19.md`
- current runtime baseline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## Current Decision

- package category:
  - `DOCS_FIRST_UI_SOURCE_BLOG_CONTRACT_REDESIGN_REBUILD`
- current decision:
  - `keep current mainline, continue zero-base redesign line`
- package theme:
  - `ui article contract / source role separation / opener boundary / self-blog reuse policy / minimal control axes`
- package position:
  - current package reopen ではない
  - `opening_frame_redesign_2026-04-18` の implementation continuation ではない
  - docs-only top-level line
  - current runtime mainline keep を前提にした zero-base redesign line
- actual archive:
  - `not yet`
  - inventory only
- first code owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` (current Phase 05 slice only)
- first code step:
  - generation prompt の writer-facing `[SURFACE_REALIZATION_CARD]` handoff
- post-docs management verdict:
  - prior resting verdict は `stop_and_user_report`
- explicit user exception:
  - one post-stop docs-only management slice for Phase 04 `Stage B artifact boundary minimum` is allowed
  - one user-explicit narrow construction slice for Phase 05 `surface realization card first construction slice` is allowed
  - one user-explicit eval-first slice for Phase 06 `surface realization card offline eval-first slice` is allowed
- next step:
- Stage A telemetry-only scan は `pass / pass / pass (inferred) / pass (inferred)` まで閉じたものとして keep する
- Phase 04 で `Stage B` の artifact boundary だけを最小定義し、`fact packet / opener card / continuity capsule / style capsule` の role と stop boundary を current baseline に固定した
- deepresearch-first lane の closeout は completed research/evidence lane として keep し、`surface realization card` は completed Phase 05 artifact、`surface profile` は alias only に留める
- completed Phase 05 は `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` の generation prompt handoff-only baseline と `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py` 1-file owner-local verification pass まで current baseline に固定した
- current Phase 06 first move は completed 済みで、`C:\tetie\notecode\logs\current_mainline_ui_runs\phase06_surface_realization_card_eval\` に `summary.json / matrix.json / genre_issue_ledger.json / manual_review.md / research_notes.md` を固定した
- current Phase 06 first slice summary read は `15 cases / short_gate 11/15 / announcement 2/5 / daily_story 5/5 / branding 4/5`
- representative case json read は `execution_mode = offline_deterministic` / `compatibility_rebuild_applied = true` / `contract_alignment.compatibility_source = native_minimal` に寄り、`互換経路の動作確認用に最小本文を返します。` と `〜を具体化します。` の active root も `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` にある
- current next legal move は same-window next slice ではなく `stop_and_user_report` で、`prompt_builder.py` 継続や broader eval continuation へ読み替えない
  - `ready_for_stage_a_scan` / Stage A dispatch / separate management execution への本文後半の言及は historical record または management contract reference であり、current active route ではない
  - user が deepresearch-first lane を explicit に選ぶときだけ、current legal move は package reopen ではなく `comparison note -> single-question deepresearch -> adoption note` の research/evidence lane に限定する
  - exact code owner table / implementation prompt / actual archive は still `not fixed`
- inherited boundaries:
  - `naturalness_recovery_2026-04-07` は parked / not fixed のまま維持する
  - `opening_frame_redesign_2026-04-18` は reference line として keep し、current owner prompt にはしない
- companion docs created:
  - `C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md`
  - `C:\tetie\notecode\docs\current_codex_state.md`
  - `C:\tetie\notecode\docs\current_codex_workflow.md`
  - `C:\tetie\notecode\docs\current_codex_control_tower_prompt.md`
  - `C:\tetie\notecode\docs\current_codex_work_instruction_prompt.md`
  - `C:\tetie\notecode\docs\ui_source_blog_contract_archive_candidate_inventory_2026-04-18.md`
  - `C:\tetie\notecode\docs\separate_window_execution_prompt_ui_source_blog_contract_redesign_docs_followup_2026-04-18.md`

## Fixed Phase 01 Baseline

### Minimal Contract Axes

- `reader_task`
  - 読者に何を理解・判断・共有させる記事か
- `evidence_mode`
  - どの強さの根拠が必要か
- `voice_distance`
  - 読者との距離感をどう置くか
- `opener_mode`
  - 最初に何を理解させるか
- `reuse_level`
  - default は `none`
  - shorthand は `reuse_level default = none until Phase 02`
  - `continuity` / `style_memory` は Phase 02 で activation policy を固定するまで昇格させない

### UI Article Contract Read

| UI article type | reader_task | evidence_mode | voice_distance | opener_mode |
|---|---|---|---|---|
| `解説・ノウハウ` | `turn_knowledge_into_action` | `grounded_preferred` | `neutral_explainer` | `judgment_first` |
| `日常のできごと` | `share_scene_and_learning` | `observation_first` | `first_person_light` | `scene_then_learning` |
| `紹介` | `understand_current_business` | `current_fact_required` | `organization_neutral` | `current_business_first` |
| `お知らせ` | `confirm_change_and_action` | `strict_factual` | `official_concise` | `change_first` |
| `事例・お客様の声` | `understand_reproducible_change` | `strict_factual` | `guide_operator` | `outcome_then_conditions` |
| `業界・市場の話題` | `evaluate_market_shift` | `grounded_preferred` | `analyst_neutral` | `shift_then_axes` |
| `比較・選び方` | `compare_options_by_axes` | `strict_factual` | `evaluator_neutral` | `comparison_axis_first` |

### Source Role Model

- `fact`
  - 今回の記事で required slot と first claim を成立させる current source
  - URL / PDF / 手入力メモ / 会社情報 / web supplement をここに入れる
  - self-blog は default でここへ入れない
- `continuity`
  - followup 文脈、既存読者前提、シリーズ接続だけを担う補助 source
  - missing fact slot の穴埋め owner にはしない
- `style_memory`
  - 段落長、文末 mix、導入温度、閉じ方の傾向だけを要約して持つ
  - raw fact や section claim を持たせない

### Source Fallback Boundary

- `strict_factual`
  - required slot が欠けたら stop する
- `current_fact_required`
  - `current_overview` または `current_offering` が欠けたら stop する
  - history は support only に留める
- `grounded_preferred`
  - web supplement か claim narrowing は許可する
  - source のない standalone section は作らない
- `observation_first`
  - firsthand memo を primary fact にできる
  - ただし `style_memory` とは混ぜない

### opening_frame Position

- `opening_frame` は独立 package theme ではなく `opener_mode` の subproblem として読む
- `title / lead / first heading / first section first claim` は同じ opener anchor に従う
- `紹介` / company introduction では `current_business_first` を opener invariant とし、history は後段 support に留める

## Package State

- package status:
  - active
  - not_closed
- package mode:
  - docs-first top-level redesign
- current phase:
  - Phase 06 `surface realization card offline eval-first slice`
- phase 01 status:
  - completed
- phase 02 status:
  - completed
- phase 03 status:
  - completed
- phase 04 status:
  - completed
- phase 05 status:
  - completed
- phase 06 status:
  - first_slice_completed_stop_and_user_report
- current honest status:
  - UI article type は `reader_task / evidence_mode / voice_distance / opener_mode / reuse_level` で読む baseline に圧縮した
  - source role は `fact / continuity / style_memory` の 3 role に固定した
  - `opening_frame` は `opener_mode` の subproblem として package judgement に吸収した
  - current runtime mainline は untouched のまま維持し、zero-base redesign は docs-only line に閉じている
  - `reuse_level` は 5th axis のまま keep し、runtime では gated axis として読む concrete line に寄せている
  - `continuity` / `style_memory` は capsule / summary only 候補として扱い、fact や opener source へ昇格させない
  - opener owner は fact-primary / support-only だけを読み、`continuity` / `style_memory` を直接読まない
  - actual archive は pending のままで、candidate inventory だけを作成した
  - archive candidate inventory は `archive-safe-now / archive-later-after-confirmation / do-not-archive` で confirmed した
  - current startup path docs は current package companion boundary として `do-not-archive` に固定する
  - post-docs separate management step は `stop_and_user_report` を default resting verdict として維持し、allowed outputs は `hold_docs_only / ready_for_stage_a_scan / stop_and_user_report` の 3 出力に限定したまま維持する
  - first candidate は exact file owner ではなく `Stage A telemetry only` の artifact-level readiness として扱い、その scan は `pass / pass / pass (inferred) / pass (inferred)` まで閉じた
  - current `Stage A telemetry only` read は `article_contract / fact sufficiency / opener support-only / reuse gate reason` の 4 telemetry を説明可能にした
  - `reuse_level = none` と fact insufficiency stop は legal な Stage A output として維持する
  - explicit user instruction により prior stop 後の narrow docs-only Phase 04 を 1 本だけ開き、`Stage B` の artifact boundary を最小定義した
  - `fact packet` は fact-primary shadow artifact、`opener card` は opener-anchor shadow artifact、`continuity capsule / style capsule` は support-only capsule として整理した
- current Phase 05 では `surface realization card` を writer-facing surface artifact として採用し、current slice exact code owner を `prompt_builder.py` 1 file に narrow に固定した
- current Phase 05 exact file mapping は generation prompt の `[SURFACE_REALIZATION_CARD]` handoff block only に留める
- current Phase 05 では owner-local verification が `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py` 1-file test-lane で `announcement / daily_story / branding` の 3 case を lock し、field 6 本が category hardcode 追加なしで分かれるところまで確認した
- current Phase 05 close 後も package-wide owner table / implementation prompt / actual archive は unresolved のまま維持する
- current Phase 06 first slice は production runtime file edit を開かず、`run_current_mainline_genre_sweep.py` の `live=False` limited eval と generated artifact review に閉じる
- current Phase 06 target genres は `announcement / daily_story / branding`
- current Phase 06 の self-test rule は `artifact generation pass -> docs sync -> next slice`
- current Phase 06 の error rule は `same slice で 3 回まで自己修正し、未解決なら stop_and_user_report`
- current Phase 06 first slice self-test artifact は `C:\tetie\notecode\logs\current_mainline_ui_runs\phase06_surface_realization_card_eval\` に揃い、summary read は `15 cases / short_gate 11/15 / announcement 2/5 / daily_story 5/5 / branding 4/5`
- representative case json read は `execution_mode = offline_deterministic` / `compatibility_rebuild_applied = true` / `contract_alignment.compatibility_source = native_minimal` に寄っており、current eval result は `prompt_builder.py` の next narrow continuation ではなく `pipeline.py` / runtime route read を要する stop evidence として扱う
- next action:
  - stable bootstrap / state / package-doc flow を current startup path として維持する
  - archive inventory note の current startup path / current package / current prompt / current runtime boundary を `do-not-archive` の current baseline として保守する
  - docs phases と Stage A telemetry-only scan close は pass 済み baseline として維持する
  - Phase 04 `Stage B artifact boundary minimum` の role 定義を current baseline として保守する
- Phase 06 first slice artifact read と stop boundary を current baseline として保守する
- next forward move は current eval read では single-owner narrow continuation に落ちないため `stop_and_user_report` を返す
  - grounding pass / semantic pass / source-opener-reuse boundary keep 後も fingerprint-side quality block が残り、current evidence だけでは next legal advance を決め切れないときだけ、future boundary note は single-question deepresearch trigger 1 問に限定する
  - user が deepresearch-first lane を explicit に選ぶときだけ、current legal move は `comparison note -> single-question deepresearch -> adoption note` に限定し、current package docs continuation や code continuation へ読み替えない
  - `comparison note -> single-question deepresearch -> adoption note` は close 済み research/evidence lane として keep し、`surface realization card` は completed Phase 05 artifact、`surface profile` は alias only に留める
  - separate window は `current_codex_autonomous_bootstrap.md` を最短入口にし、long pasted prompt を default にしない

## Separate Management Step Design

- role:
  - docs phases pass 後の management judgment を implementation prompt / code diff / actual archive から切り離す
- management inputs:
  - Phase 01 の `reader_task / evidence_mode / voice_distance / opener_mode / reuse_level`
  - Phase 02 の `fact / continuity / style_memory` と `Stage A -> E` artifact order
  - Phase 03 の `do-not-archive` baseline
- allowed outputs:
  - `hold_docs_only`
    - baseline は keep するが、management judgment を進める材料がまだ薄い
  - `ready_for_stage_a_scan`
    - first candidate を `Stage A telemetry only` の readiness scan に限定して次 slice へ渡す
  - `stop_and_user_report`
    - owner fix / implementation prompt / actual archive / editable scope 外が必要になったので停止する
- fixed read:
  - first candidate は artifact-level の `Stage A telemetry only` に固定し、exact file owner へ落とさない
  - `ready_for_stage_a_scan` は owner fix でも implementation start でもない
  - `Stage C / D / E` を first candidate にしない
  - actual archive / implementation prompt / exact code owner fixed は still forbidden
- explicit exception rule:
  - explicit user instruction があるときだけ、prior `stop_and_user_report` 後に narrow docs-only slice を 1 本だけ追加できる
  - その slice は artifact boundary 定義に閉じ、exact code owner / exact file mapping / implementation prompt / actual archive を fixed しない
- current verdict:
  - `stop_and_user_report`
  - docs phases pass baseline と `do-not-archive` baseline は keep できており、Stage A telemetry-only scan も `pass / pass / pass (inferred) / pass (inferred)` まで閉じた
  - current explicit exception slices では Phase 04 `Stage B artifact boundary minimum` と Phase 05 `prompt_builder.py` handoff-only closeout だけを narrow advance として fixed した
- completed Phase 05 closeout 後の next forward move は `pipeline.py` / quality guard / repair / routing / broader eval lane / threshold canonicalization / package-wide owner table / implementation prompt / actual archive のいずれかを要する
  - `ready_for_stage_a_scan` は current verdict ではなく、historical record または management contract reference に留まる
  - grounding pass / semantic pass / source-opener-reuse boundary keep 後も fingerprint-side quality block が残り、current evidence だけでは next legal advance を決め切れないときだけ、future boundary note は single-question deepresearch trigger 1 問に限定する
  - exact code owner / exact file mapping / implementation prompt / actual archive は unresolved のまま維持する

## Stage A Readiness Read

- role:
  - `ready_for_stage_a_scan` を keep したまま、first candidate を telemetry artifact の説明可能性だけに閉じる
- fixed artifact checklist:
  - `article_contract`
    - `reader_task / evidence_mode / voice_distance / opener_mode / reuse_level` の current read を短く出せる
  - `fact sufficiency`
    - required current fact の充足 / 欠落と stop or narrow reason を出せる
  - `opener support-only`
    - opener anchor は fact-primary のまま維持し、history / continuity / style を support-only 扱いと説明できる
  - `reuse gate reason`
    - requested reuse と effective result、`reuse_level = none` を含む abstain reason を出せる
- fixed boundary:
  - Stage A は telemetry only であり、`fact packet / opener card / capsules` の shadow artifact はまだ要求しない
  - exact code owner / exact file mapping / implementation prompt / actual archive は fixed しない
  - `Stage C / D / E` を first candidate にしない

## Stage B Artifact Boundary Minimum

- role:
  - Stage B は shadow artifact の role boundary を最小定義する docs-only slice であり、implementation owner や file mapping を決める段ではない
- `fact packet`:
  - `reader_task / evidence_mode / opener_mode` と required current fact slot / first-claim candidate を fact-primary source だけで束ねる
  - `continuity` / `style_memory` / `theme` / raw past blog text を fact packet に混ぜない
- `opener card`:
  - `title / lead / first heading / first section first claim` の shared opener anchor を `fact packet` から切り出す opening-surface artifact として扱う
  - history は support-only に留め、`continuity capsule` / `style capsule` を direct input にしない
- `continuity capsule`:
  - series relation / already-known context / repeated reader concern の summary only に留める
  - missing fact slot を埋めず、opener anchor も決めない
- `style capsule`:
  - paragraph rhythm / ending mix / lead temperature / closing intensity の content-free summary only に留める
  - named fact / example / heading を追加せず、opener anchor も決めない
- fixed stop boundary:
  - current slice は role boundary の定義で止め、exact code owner / exact file mapping / implementation prompt / actual archive は fixed しない
  - concrete file mapping / exact schema / numeric threshold / actual archive へ進みたくなったら `stop_and_user_report` を返す

## Why

- `opening_frame_redesign_2026-04-18` は opener ownership を切り出す判断として妥当だったが、external research が支持しているのはさらに上位の `article contract / source role separation / self-blog reuse policy` である
- `naturalness_recovery_2026-04-07` は parked / not fixed で維持されており、same retry line を rename して current package に戻す余地はない
- `opening frame` だけを current line にすると、`prompt_builder` retry / `pipeline` retry / guard accumulation のどれかに再吸収されやすい
- new top-level docs-only package に切り出したうえで、Phase 01 で `opening_frame` を `opener_mode` 配下へ再配置し、UI 起点の最小 contract と source role を先に固定できた
- current mainline keep と zero-base redesign は矛盾せず、current runtime を保持したまま `contract / source / opener / reuse` artifact を切り分けるほうが rollback しやすい
- category 差は `reader_task / evidence_mode / voice_distance / opener_mode` の組み合わせで説明でき、self-blog reuse はまだ default fact source に上げなくてよいと確定した
- archive work を inventory only に留めることで、mainline を壊さずに deadcode boundary だけを明示できる

## Simplification Direction

### Keep

- current runtime mainline
- current runtime mainline keep と zero-base redesign docs line の分離
- `naturalness_recovery_2026-04-07` の parked / not fixed boundary
- `opening_frame_redesign_2026-04-18` の reference-only position
- docs-first / rollback-first / `1 phase = 1 narrow hypothesis = 1 owner scope`
- `reader_task / evidence_mode / voice_distance / opener_mode / reuse_level` の 5 軸 contract
- source role の `fact / continuity / style_memory` 分離
- actual archive を later decision に残すこと
- exact code owner を `not fixed` に保つこと

### Thin

- UI article type の責務を少数の control axes に圧縮する
- source model を `fact / continuity / style_memory` の 3 role へ圧縮する
- self-blog reuse を `continuity reuse` と `style memory reuse` へ分離する
- self-blog raw retrieval を capsule / summary policy へ薄くする
- archive work を `inventory only` に制限する

### Remove As Default Assumption

- `prompt_builder.py` を primary control surface に戻す前提
- `pipeline.py` retry line を rename して legal line に見せる前提
- fixed routing table を増やす前提
- self-blog を default で fact source として使う前提
- `theme` を fact source に上げる前提
- opener owner が `continuity` / `style_memory` を直接読めばよい前提
- `opening_frame` だけ切れば全体契約まで片付く前提
- actual archive を今やる前提
- prompt accretion continuation
- hidden reviser accumulation

## Non-Goals

- production code implementation
- tests implementation
- `naturalness_recovery_2026-04-07` の current package reopen
- `opening_frame_redesign_2026-04-18` の implementation prompt 作成
- fixed routing table
- category hardcode の増殖
- prompt accretion continuation
- hidden reviser accumulation
- giant rewrite
- actual archive execution
- AGENTS / WORKLOG の更新
