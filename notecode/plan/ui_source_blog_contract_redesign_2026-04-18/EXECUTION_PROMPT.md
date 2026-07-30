# ui_source_blog_contract_redesign_2026-04-18 EXECUTION PROMPT

## next startup use

- package category:
  - `DOCS_FIRST_UI_SOURCE_BLOG_CONTRACT_REDESIGN_REBUILD`
- 次回起動時の shortest startup path は次を使う
  - `C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md`
- current state が `stop_and_user_report` の間は work window への default dispatch を止め、Template D を current default に戻さない
- expanded fallback prompt path は次だが、default dispatch には戻さない
  - `C:\tetie\notecode\docs\separate_window_execution_prompt_ui_source_blog_contract_redesign_docs_followup_2026-04-18.md`
- current planning source-of-truth は `ui_source_blog_contract_redesign_2026-04-18` package に固定する
- current state capsule は次を使う
  - `C:\tetie\notecode\docs\current_codex_state.md`
- doc system rule は次を使う
  - `C:\tetie\notecode\docs\current_codex_workflow.md`
- control-tower initial prompt は次を使う
  - `C:\tetie\notecode\docs\current_codex_control_tower_prompt.md`
- compact work instruction template は次を使う
  - `C:\tetie\notecode\docs\current_codex_work_instruction_prompt.md`
- `naturalness_recovery_2026-04-07` は parked / not fixed のまま維持する
- `opening_frame_redesign_2026-04-18` は reference line として扱う
- current runtime mainline は keep し、zero-base redesign は docs-only artifact boundary として進める
- actual archive は `not yet`
- archive work は inventory only に留める
- current narrow code owner は `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- current narrow code step は completed closeout: `prompt_builder.py` generation prompt の writer-facing `[SURFACE_REALIZATION_CARD]` handoff-only baseline + `note/tests/test_simple_note_pipeline.py` 1-file owner-local test lock
- current eval-first owner scope は `C:\tetie\notecode\tools\run_current_mainline_genre_sweep.py` invocation only
- Phase 01 fixed baseline は次の通り
  - contract axes は `reader_task / evidence_mode / voice_distance / opener_mode / reuse_level`
  - source role は `fact / continuity / style_memory`
  - `opening_frame` は `opener_mode` の subproblem
  - `reuse_level` default は `none`
  - shorthand は `reuse_level default = none until Phase 02`
- Phase 02 fixed line は次の通り
  - `reuse_level` は keep axis / gated runtime axis
  - `theme` は fact source ではない
  - continuity / style は capsule only
  - opener owner は fact-only read
- Phase 03 status は `completed`
- Phase 04 status は `completed`
- Phase 05 status は `completed`
- Phase 06 status は `first_slice_completed_stop_and_user_report`
- Phase 04 fixed boundary は次の通り
  - `fact packet` は fact-primary shadow artifact
  - `opener card` は opener-anchor shadow artifact
  - `continuity capsule` は support-only continuity summary
  - `style capsule` は content-free style summary
- Phase 05 fixed boundary は次の通り
  - `surface realization card` は writer-facing content-free surface artifact
  - current minimum fields は `paragraph_breath / sentence_length_band / ending_mix / nominalization_budget / subject_visibility / connective_tolerance`
  - current exact file mapping は generation prompt の writer-facing `[SURFACE_REALIZATION_CARD]` handoff block only
- current Phase 06 first slice artifact は `C:\tetie\notecode\logs\current_mainline_ui_runs\phase06_surface_realization_card_eval\` に生成済みで、`summary.json / matrix.json / genre_issue_ledger.json / manual_review.md / research_notes.md` を含む
- current Phase 06 self-test artifact は `summary.json / matrix.json / genre_issue_ledger.json / manual_review.md / research_notes.md`
- post-docs management verdict は `stop_and_user_report` を維持し、current Phase 06 first slice は close 済み artifact read として扱う
- next step は completed Phase 04 を baseline として維持しつつ、completed Phase 05 を `prompt_builder.py` handoff-only baseline + 1-file owner-local test closeout として keep し、current Phase 06 artifact read を `offline_deterministic` / `native_minimal` stop evidence として同期する
- grounding pass / semantic pass / source-opener-reuse boundary keep 後も fingerprint-side quality block が残り、current evidence だけでは next legal advance を決め切れないときだけ、future boundary note は single-question deepresearch trigger 1 問に限定する
- user が deepresearch-first lane を explicit に選ぶときだけ、current legal move は package docs continuation ではなく `comparison note -> single-question deepresearch -> adoption note` の research/evidence lane に限定する
- deepresearch-first lane の closeout は completed research/evidence lane として keep し、`surface realization card` は completed Phase 05 artifact、`surface profile` は alias only に留める
- current Stage A telemetry checklist は `article_contract / fact sufficiency / opener support-only / reuse gate reason`
- `ready_for_stage_a_scan` への言及は management contract / historical reference only であり、current default dispatch ではない
- `reuse_level = none` と fact insufficiency stop は legal Stage A output
- completed Phase 05 は `prompt_builder.py` handoff-only narrow construction slice として keep し、current Phase 06 first slice は offline eval-first だけを扱う
- current Phase 06 first slice では production runtime file edit を扱わない
- post-docs management outputs は `hold_docs_only / ready_for_stage_a_scan / stop_and_user_report`
- first candidate は `Stage A telemetry only` の artifact-level readiness として読む
- exact code owner / exact file mapping / implementation prompt / actual archive は fixed しない
- companion inventory note は次を参照する
  - `C:\tetie\notecode\docs\ui_source_blog_contract_archive_candidate_inventory_2026-04-18.md`
- `prompt_builder.py` simplification-first wording line / `pipeline.py` current-first triage / `pipeline.py` core_message current-first hint は unchanged retry しない
- production code / tests / AGENTS / WORKLOG / inherited parked package docs はこの prompt では編集しない
- `theme` は fact source にしない
- opener owner は `continuity` / `style_memory` を直接読まない
- `C:\tetie\notecode\docs\separate_window_execution_prompt_ui_source_blog_contract_redesign_docs_start_2026-04-18.md` は package creation 用の historical prompt として扱い、current prompt にはしない

## expanded fallback prompt

- 下記 block は bootstrap / state / current package docs だけでは足りないときの expanded fallback 用である
- current state が `stop_and_user_report` の間は default work-window dispatch に使わず、この block を毎回貼らない

```text
C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md を読み、この bootstrap に従って自律的に進めてください。
completed Phase 04 / completed Phase 05 baseline と Phase 06 first slice artifact read を維持したまま、current_codex_state.md の stop boundary に従って docs sync だけを確認してください。
各 slice は 3 回まで自己修正し、`pipeline.py` / quality guard / repair / routing / multi-owner planning / actual archive が必要になったら user report して停止し、final report は `updated:` / `kept:` / `untouched:` で返してください。

参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\README.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\TASK.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\PROGRESS.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\ROLLBACK.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\EXECUTION_PROMPT.md
- C:\tetie\notecode\docs\ui_source_blog_contract_archive_candidate_inventory_2026-04-18.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\README.md
- C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\PROGRESS.md
- C:\tetie\notecode\docs\deepresearch_algorithm_validation_note_2026-04-18.md
- C:\tetie\notecode\research\新しいフォルダー (3)\00_external_ai_research_request_zero_base_ui_source_blog_algorithm_2026-04-18.md
- C:\tetie\notecode\research\新しいフォルダー (3)\08_external_ai_research_response_zero_base_ui_source_blog_algorithm_2026-04-18.md
- C:\tetie\notecode\research\新しいフォルダー (4)\01_deepresearch_first_plan_2026-04-19.md
- C:\tetie\notecode\research\新しいフォルダー (4)\02_prior_new_research_comparison_note_2026-04-19.md
- C:\tetie\notecode\research\新しいフォルダー (4)\03_single_question_deepresearch_surface_realization_card_2026-04-19.md
- C:\tetie\notecode\research\新しいフォルダー (4)\04_surface_artifact_adoption_note_2026-04-19.md
- C:\tetie\WORKLOG.md

今回の依頼種別:
- docs-first redesign follow-up
- `UI_SOURCE_BLOG_CONTRACT_REDESIGN_EVAL_FIRST_CONTINUE`
- implementation prompt ではない
- actual archive prompt ではない

今回の実施範囲:
- `ui_source_blog_contract_redesign_2026-04-18` package の Phase 06 eval-first follow-up を行う
- focus は completed Phase 04 / completed Phase 05 baseline を keep しつつ、`run_current_mainline_genre_sweep.py --phase genre-rerun --genres announcement,daily_story,branding` の `live=False` limited eval で artifact を取り、next owner narrowing を判定すること
- production runtime code / AGENTS / WORKLOG / inherited parked package docs は編集しない
- actual archive は行わない

current fixed judgment:
- current package:
  - C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18
- current package state:
  - active / not closed
- inherited parked boundary:
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07
- reference redesign line:
  - C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18
- current runtime mainline:
  - keep
- zero-base redesign read:
  - runtime replacement ではなく `contract / source / opener / reuse` artifact boundary redesign
- current narrow code owner:
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py current Phase 05 slice only
- current narrow code step:
  - completed closeout: `prompt_builder.py` generation prompt の writer-facing `[SURFACE_REALIZATION_CARD]` handoff-only baseline + `note/tests/test_simple_note_pipeline.py` 1-file owner-local test lock
- package-wide owner table:
  - not fixed
- Phase 01 fixed baseline:
  - contract axes は `reader_task / evidence_mode / voice_distance / opener_mode / reuse_level`
  - source role は `fact / continuity / style_memory`
  - `opening_frame` は `opener_mode` の subproblem
  - `reuse_level` default は `none`
  - shorthand は `reuse_level default = none until Phase 02`
- concrete Phase 02 line:
  - `reuse_level` は keep axis / gated runtime axis
  - `theme` は fact source ではない
  - continuity / style は capsule only
  - opener owner は fact-only read
- Phase 03 status:
  - completed
- Phase 04 status:
  - completed
- Phase 04 fixed boundary:
  - `fact packet` は fact-primary shadow artifact
  - `opener card` は opener-anchor shadow artifact
  - `continuity capsule` は support-only continuity summary
  - `style capsule` は content-free style summary
- Phase 05 status:
  - completed
- Phase 05 fixed boundary:
  - `surface realization card` は completed Phase 05 artifact
  - current exact file mapping は generation prompt の writer-facing `[SURFACE_REALIZATION_CARD]` handoff block only
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py` 1-file owner-local test-lane で `announcement / daily_story / branding` の writer prompt lock まで closeout 済み
- Phase 06 status:
  - first_slice_completed_stop_and_user_report
- Phase 06 first slice:
  - artifact root は `C:\tetie\notecode\logs\current_mainline_ui_runs\phase06_surface_realization_card_eval\`
  - self-test artifact `summary.json / matrix.json / genre_issue_ledger.json / manual_review.md / research_notes.md` は生成確認済み
  - current summary read は `15 cases / short_gate 11/15 / announcement 2/5 / daily_story 5/5 / branding 4/5`
- post-docs management verdict:
  - `stop_and_user_report`
- next step:
  - completed Phase 04 `Stage B artifact boundary minimum` と completed Phase 05 `prompt_builder.py` handoff-only baseline + 1-file owner-local test closeout を baseline として keep し、Phase 06 first slice artifact read を source-of-truth に同期する
  - representative case json read は `execution_mode = offline_deterministic` / `compatibility_rebuild_applied = true` / `contract_alignment.compatibility_source = native_minimal`
  - `pipeline.py` / quality guard / repair / routing / broader eval lane / threshold canonicalization / package-wide owner table / implementation prompt / actual archive を直ちに要求する read なので `stop_and_user_report`
- grounding pass / semantic pass / source-opener-reuse boundary keep 後も fingerprint-side quality block が残り、current evidence だけでは next legal advance を決め切れないときだけ、future boundary note は single-question deepresearch trigger 1 問に限定する
- user が deepresearch-first lane を explicit に選ぶときだけ、`C:\tetie\notecode\research\新しいフォルダー (4)\01_deepresearch_first_plan_2026-04-19.md` と closeout note `C:\tetie\notecode\research\新しいフォルダー (4)\02_prior_new_research_comparison_note_2026-04-19.md` / `C:\tetie\notecode\research\新しいフォルダー (4)\03_single_question_deepresearch_surface_realization_card_2026-04-19.md` / `C:\tetie\notecode\research\新しいフォルダー (4)\04_surface_artifact_adoption_note_2026-04-19.md` に従って `comparison note -> single-question deepresearch -> adoption note` の research/evidence lane に進む
- deepresearch-first lane の closeout success は source-of-truth gate pass の current baseline として keep し、`surface realization card` は completed Phase 05 artifact、`surface profile` は alias only に留める
- current Stage A telemetry checklist:
  - `article_contract / fact sufficiency / opener support-only / reuse gate reason`
- Stage A legal outputs:
  - `reuse_level = none`
  - fact insufficiency stop
- post-docs management outputs:
  - `hold_docs_only`
  - `ready_for_stage_a_scan`
  - `stop_and_user_report`
- first candidate read:
  - `Stage A telemetry only` の artifact-level readiness
  - exact code owner / exact file mapping / implementation prompt / actual archive は fixed しない
- actual archive:
  - not yet
  - inventory only

this window will do:
1. completed Phase 04 / completed Phase 05 baseline を崩さずに保守する
2. `C:\tetie\notecode\logs\current_mainline_ui_runs\phase06_surface_realization_card_eval\` の artifact read を source-of-truth に同期する
3. current eval read が `pipeline.py` / runtime route change boundary に落ちたことを keep し、next slice は開かない
4. exact code owner / exact file mapping / implementation prompt / actual archive は unresolved のまま維持する

this window will not do:
- production code edit
- production runtime test expansion を初手で行うこと
- current package reopen
- opening_frame implementation continuation
- exact code owner fix
- exact file mapping fix
- implementation prompt 作成
- actual archive 実行
- `Stage C / D / E` を first candidate にすること
- prompt accretion continuation
- fixed routing table
- giant rewrite
- `theme` を fact source に戻すこと
- raw past blog text を opener input に戻すこと

stop conditions:
- package theme が broad rewrite に膨らむ
- exact code owner を early fix したくなる
- exact file mapping を fixed したくなる
- actual archive を今やりたくなる
- `fact packet / opener card / capsules` を concrete file mapping / implementation prompt / exact numeric threshold fix に落としたくなる
- self-blog reuse を fact source default にしたくなる
- `theme` を fact source にしたくなる
- opener owner に `continuity` / `style_memory` を読ませたくなる
- `Stage C / D / E` を first candidate にしたくなる
- multiple worker implementation planning が必要になる
- same slice で 3 回自己修正しても eval artifact 生成または narrowing judgment が解けない

final report should use ultra-compact report:
1. default は `updated:` / `kept:` / `untouched:` の 2-3 行だけで閉じる
2. `read:` は startup path change または package switch があったときだけ書く
3. file list / AGENTS / WORKLOG / inherited parked package docs の再掲はしない
4. `kept:` は locked decisions 全文ではなく current verdict に必要な unresolved state だけを書く
```
