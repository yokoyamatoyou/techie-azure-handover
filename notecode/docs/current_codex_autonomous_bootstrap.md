# current codex autonomous bootstrap

## Purpose

- separate window を毎回の長文 prompt なしで開始するための最短入口
- current state は `C:\tetie\notecode\docs\current_codex_state.md` に集約する
- 詳細ルールは current package source-of-truth を読む
- historical prompt 群は default startup path に使わない
- deepresearch-first lane は user explicit のときだけ使い、default startup path には混ぜない

## Shortest Start Message

- user は原則として次の 1 行だけ送ればよい
  - `C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md を読み、この bootstrap に従って自律的に進めてください。`

## Optional Short Addendum

- phase や scope を明示したいときだけ 1-2 行追加する
- default では参照ファイル一覧を貼り直さない
- task wording template は次を使う
  - `C:\tetie\notecode\docs\current_codex_work_instruction_prompt.md`
- 司令塔ウインドウ起動 prompt は次を使う
  - `C:\tetie\notecode\docs\current_codex_control_tower_prompt.md`

### Template A Minimal

- `C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md を読み、この bootstrap に従って自律的に進めてください。`

### Template B Phase-Pinned

- `C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md を読み、この bootstrap に従って自律的に進めてください。`
- `current_codex_state.md の current phase を維持し、docs-only で続けてください。`

### Template C Strict Scope

- `C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md を読み、この bootstrap に従って自律的に進めてください。`
- `current_codex_state.md の editable scope だけを更新し、editable-scope-only lock を維持して、production code / AGENTS / WORKLOG は触らないでください。`

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\docs\current_codex_state.md`
4. current state が指す package source-of-truth
5. 必要になった evidence only docs

- user が deepresearch-first lane を explicit に選んだときだけ、step 4 の後で `C:\tetie\notecode\research\新しいフォルダー (4)\01_deepresearch_first_plan_2026-04-19.md` / `C:\tetie\notecode\research\新しいフォルダー (4)\02_prior_new_research_comparison_note_2026-04-19.md` / `C:\tetie\notecode\research\新しいフォルダー (4)\03_single_question_deepresearch_surface_realization_card_2026-04-19.md` / `C:\tetie\notecode\research\新しいフォルダー (4)\04_surface_artifact_adoption_note_2026-04-19.md` を読む

## Current Route

- current package:
  - `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\`
- current mode:
  - docs-first zero-base redesign + eval-first narrow execution slice
- current phase:
  - Phase 06 `surface realization card offline eval-first slice` first-slice artifact read completed
- post-phase management step:
  - `slice_self_test_then_next_slice_or_stop_and_user_report`
- current fixed boundary:
  - `fact packet` = fact-primary shadow artifact
  - `opener card` = opener-anchor shadow artifact
  - `continuity capsule` = support-only continuity summary
  - `style capsule` = content-free style summary
- completed Phase 05 owner baseline:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- completed Phase 05 file mapping baseline:
  - generation prompt の writer-facing `[SURFACE_REALIZATION_CARD]` handoff block only
- current Phase 06 first slice:
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\phase06_surface_realization_card_eval\` に `summary.json / matrix.json / genre_issue_ledger.json / manual_review.md / research_notes.md` が生成済みで、summary read は `15 cases / short_gate 11/15 / announcement 2/5 / daily_story 5/5 / branding 4/5`
- runtime policy:
  - current mainline keep
- owner policy:
  - package-wide owner table / implementation prompt / actual archive は `not fixed`
- optional research-first notes:
  - `C:\tetie\notecode\research\新しいフォルダー (4)\01_deepresearch_first_plan_2026-04-19.md`
  - `C:\tetie\notecode\research\新しいフォルダー (4)\02_prior_new_research_comparison_note_2026-04-19.md`
  - `C:\tetie\notecode\research\新しいフォルダー (4)\03_single_question_deepresearch_surface_realization_card_2026-04-19.md`
  - `C:\tetie\notecode\research\新しいフォルダー (4)\04_surface_artifact_adoption_note_2026-04-19.md`

## Default Working Contract

- first action は `current_codex_state.md` の確認
- docs-only scope では current state / current package / helper docs の drift だけを current editable scope 内で同期する
- `fact packet` は required current fact slot / first-claim candidate を fact-primary source だけで束ねる
- `opener card` は `fact packet` から shared opener anchor を切り出し、`continuity capsule` / `style capsule` を direct input にしない
- `continuity capsule` は support-only summary に留め、missing fact slot や opener anchor を埋めない
- `style capsule` は content-free summary に留め、fact / example / heading を足さない
- completed Phase 04 boundary と Stage A close は current baseline として keep する
- deepresearch-first lane の closeout は completed research/evidence lane として keep し、`surface realization card` は completed Phase 05 artifact、`surface profile` は alias only に留める
- current user-explicit Phase 05 は close 済み narrow construction slice として keep する
- current user-explicit Phase 06 first slice は executed eval-first slice として close し、same-window next slice は default で開かない
- current first slice read は production runtime file edit ではなく、`announcement / daily_story / branding` の 3 genre を `live=False` limited eval で読んだ結果に留める
- current first slice self-test は `summary.json / matrix.json / genre_issue_ledger.json / manual_review.md / research_notes.md` の生成確認までで pass とする
- `surface realization card` は new fact source にしない
- opener owner は `continuity` / `style_memory` / `surface realization card` を直接読まない
- current slice minimum fields は `paragraph_breath / sentence_length_band / ending_mix / nominalization_budget / subject_visibility / connective_tolerance`
- owner-local verification pass は `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py` 1-file test-lane で `announcement / daily_story / branding` の 3 case を lock し、`[SURFACE_REALIZATION_CARD]` block と field 6 本が分かれるところまで completed baseline に反映した
- current Phase 06 first move は completed Phase 05 handoff-only baseline の成否を前提に進めず、offline eval artifact で next owner narrowing を取りに行く
- each slice は self-test pass 後にだけ次 slice へ進み、same slice で 3 回まで自己修正し、解けなければ `stop_and_user_report` を返す
- current next legal move は eval artifact read が still single-owner narrow continuation に落ちるときだけ同一 work window で 1 slice 進める。ただし current read は `execution_mode = offline_deterministic` / `compatibility_rebuild_applied = true` / `contract_alignment.compatibility_source = native_minimal` に寄り、active placeholder root も `note/newalgorithm_pipeline/pipeline.py` にあるため、current verdict は `stop_and_user_report`
- helper docs に残る `ready_for_stage_a_scan` / Stage A dispatch / `Template D` / separate management execution 参照は historical record または management contract reference であり、current active route ではない
- fingerprint-side quality block が残る場合でも、optional future boundary note は single-question deepresearch trigger 1 問だけであり、active next step ではない
- user が deepresearch-first lane を explicit に選ぶときだけ、`comparison note -> single-question deepresearch -> adoption note` を current legal move として扱う
- deepresearch-first lane は research/evidence lane であり、current package reopen や broad code continuation にしない
- code work は current state で明示される narrow slice の範囲だけで進め、Phase 06 first slice は eval-first に固定する
- `theme` は fact source にしない
- opener owner は `continuity` / `style_memory` / `surface realization card` を直接読まない
- actual archive は行わない
- old separate-window prompt を掘るのは current state または current package docs が必要と書いたときだけにする

## Escalation

- current state と package docs が衝突したら package source-of-truth を優先する
- package switch / phase switch / editable scope change が起きたら `current_codex_state.md` を先に更新する
- deepresearch-first lane を current active priority に上げるときは `current_codex_state.md` を先に更新する
- startup に長文 prompt が必要だと感じたら、まず `C:\tetie\notecode\docs\current_codex_workflow.md` の doc tier と update rule を見直す

## Expanded Fallback

- full prompt が必要なときだけ次を使う
  - `C:\tetie\notecode\docs\separate_window_execution_prompt_ui_source_blog_contract_redesign_docs_followup_2026-04-18.md`

## Report Style

- final report は ultra-compact report を default にする
- 2-3 行で十分
- file list の全文再掲はしない
