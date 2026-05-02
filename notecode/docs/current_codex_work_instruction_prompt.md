# current codex work instruction prompt

## Purpose

- separate window に送る作業指示を短く保つための stable prompt helper
- context は `current_codex_autonomous_bootstrap.md` と `current_codex_state.md` に寄せる
- user は task delta だけを追加で指示する

## Context Rule

- 参照ファイル一覧を毎回貼り直さない
- current package / locked decisions / editable scope を長く再説明しない
- 変えたいものだけを書く
- override したい制約がない限り、current state をそのまま使う

## Default Dispatch Rule

- work window へ渡す default 指示は 2-3 行に留める
- current default は `current_codex_state.md` の current verdict に従う
- completed Phase 05 `surface realization card first construction slice` は `prompt_builder.py` handoff-only baseline と `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py` 1-file owner-local test lock completed の baseline として keep する
- current Phase 06 first dispatch は close 済みで、default では再実行しない。current artifact read は `C:\tetie\notecode\logs\current_mainline_ui_runs\phase06_surface_realization_card_eval\` の `summary.json / matrix.json / genre_issue_ledger.json / manual_review.md / research_notes.md` を keep する
- completed Phase 04 `Stage B artifact boundary minimum` の `fact packet / opener card / continuity capsule / style capsule` role boundary は keep しつつ、current slice の file mapping は `prompt_builder.py` generation prompt handoff only に限定する
- `C:\tetie\notecode\docs\separate_window_execution_prompt_ui_source_blog_contract_redesign_docs_followup_2026-04-18.md` は expanded fallback only とし、bootstrap / state / current package docs だけでは足りないときだけ使う
- grounding pass / semantic pass / source-opener-reuse boundary keep 後も fingerprint-side quality block が残り、existing evidence だけでは next legal advance を決め切れないときだけ、future boundary note は single-question deepresearch trigger 1 問に限定する
- user が deepresearch-first lane を explicit に選ぶときだけ、`C:\tetie\notecode\research\新しいフォルダー (4)\01_deepresearch_first_plan_2026-04-19.md` と closeout note `C:\tetie\notecode\research\新しいフォルダー (4)\02_prior_new_research_comparison_note_2026-04-19.md` / `C:\tetie\notecode\research\新しいフォルダー (4)\03_single_question_deepresearch_surface_realization_card_2026-04-19.md` / `C:\tetie\notecode\research\新しいフォルダー (4)\04_surface_artifact_adoption_note_2026-04-19.md` を参照し、`comparison note -> single-question deepresearch -> adoption note` の順で narrow に進める
- deepresearch-first lane は package reopen / code continuation / owner fix に読み替えない
- deepresearch-first lane の closeout は completed research/evidence lane として keep し、`surface realization card` は completed Phase 05 artifact、`surface profile` は alias only に留める
- final report も default では 2-3 行に留め、`read:` や file list を常用しない
- current Phase 06 では `each slice = self-test pass -> docs sync -> next slice` を default rule にし、same slice error は 3 回まで自己修正して未解決なら `stop_and_user_report` を返す

## Prompt Shape

- line 1:
  - `C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md を読み、この bootstrap に従って自律的に進めてください。`
- line 2:
  - current task delta
- optional line 3:
  - scope lock / stop boundary / report style

## Template Status

- Template A-C は generic helper として残す
- Template D は historical Stage A shorthand reference であり、current default ではない
- current state が `stop_and_user_report` の間は new work window を default dispatch しない

## Template A Minimal Continue

```text
C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md を読み、この bootstrap に従って自律的に進めてください。
current_codex_state.md の next autonomous slice に従って続けてください。
```

## Template B Docs-Only Continue

```text
C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md を読み、この bootstrap に従って自律的に進めてください。
current_codex_state.md の current phase を維持し、docs-only で続けてください。
current_codex_state.md の editable scope だけを更新し、`editable-scope-only` lock を維持して、final report は ultra-compact report にしてください。
```

## Template C Separate Management Step

```text
C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md を読み、この bootstrap に従って自律的に進めてください。
current_codex_state.md の next autonomous slice に従い、separate management step を docs-only で進めてください。
exact code owner / exact file mapping / implementation prompt / actual archive は固定せず、final report は ultra-compact report にしてください。
```

## Template D Stage A Readiness Scan Reference

- shorthand:
  - `Stage A telemetry only` = `article_contract / fact sufficiency / opener support-only / reuse gate reason`

```text
C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md を読み、この bootstrap に従って自律的に進めてください。
historical reference only: current_codex_state.md が `ready_for_stage_a_scan` を active verdict としていた時点の shorthand に従い、Stage A telemetry only の readiness scan を docs-only で進めてください。
current_codex_state.md の editable scope だけを更新し、`editable-scope-only` lock を維持して、exact code owner / exact file mapping / implementation prompt / actual archive は固定せず、final report は `updated:` / `kept:` / `untouched:` で返してください。
```

## Recommended Now

- current state は `Phase 06 first slice completed / stop_and_user_report` で、current artifact read は `15 cases / short_gate 11/15 / announcement 2/5 / daily_story 5/5 / branding 4/5`
- completed Phase 04 では `fact packet / opener card / continuity capsule / style capsule` の role boundary を keep し、completed Phase 05 では `surface realization card` を `prompt_builder.py` generation prompt block に narrow に落とした baseline と `test_simple_note_pipeline.py` 1-file owner-local test lock complete を keep する
- `ready_for_stage_a_scan` / Template D / Stage A dispatch への参照は historical record または management contract reference であり、current active route ではない
- grounding pass / semantic pass / source-opener-reuse boundary keep 後も fingerprint-side quality block が残り、existing evidence だけでは next legal advance を決め切れないときだけ、future boundary note は single-question deepresearch trigger 1 問に限定し、deepresearch 本体は reopen しない
- user explicit の deepresearch-first lane では、comparison note / single-question deepresearch / adoption note を close 済み research/evidence lane として package docs と混ぜずに扱い、`surface realization card` は current construction artifact、`surface profile` は alias only に留める
- representative case json read が `execution_mode = offline_deterministic` / `compatibility_rebuild_applied = true` / `contract_alignment.compatibility_source = native_minimal` に寄り、active placeholder root も `note/newalgorithm_pipeline/pipeline.py` にあるため、current next slice は開かず `stop_and_user_report` を返す
- `editable-scope-only` の current slice では current verdict と unresolved boundary だけを短く report し、fixed baseline の長い再掲はしない
- final report は `updated:` / `kept:` / `untouched:` のみを default にし、`read:` は省略する

## Template E Phase 06 Eval-First

```text
C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md を読み、この bootstrap に従って自律的に進めてください。
completed Phase 04 / completed Phase 05 baseline を維持したまま、Phase 06 は `run_current_mainline_genre_sweep.py --phase genre-rerun --genres announcement,daily_story,branding` の `live=False` limited eval で進め、self-test pass 後にだけ次 slice を 1 本進めてください。
各 slice は 3 回まで自己修正し、`pipeline.py` / quality guard / repair / routing / multi-owner planning / actual archive が必要になったら user report して停止し、final report は `updated:` / `kept:` / `untouched:` で返してください。
```

## When To Add More

- phase を固定したい
- editable scope をさらに狭めたい
- output format を固定したい
- それ以外では行を増やさない

## Anti-Patterns

- file path の長い列挙を本文に戻すこと
- current state の全文要約を再度書くこと
- inherited package の説明を毎回貼ること
- `theme` / `reuse_level` / opener boundary の fixed line を user prompt に毎回再掲すること
- full execution prompt を default に戻すこと
- final report に read file list や unchanged baseline を毎回書くこと
