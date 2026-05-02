# current codex control tower prompt

## Purpose

- 司令塔ウインドウ起動用の最初の prompt
- bootstrap / state / current package source-of-truth を前提に、低コンテキストで management lane を再開する
- deepresearch の要点は current docs に反映されたものを優先し、必要時だけ evidence として参照する

## Principles

- deepresearch を活かす
  - ただし deepresearch 本文を毎回貼り直さない
  - current state / current package docs に反映済みの判断を優先する
- コンテキストの少ないやり取りを保つ
  - file list の長い再掲をしない
  - current state の全文要約をしない
  - task delta だけを追加する
- モジュールの肥大化を防ぐ
  - giant rewrite を避ける
  - exact code owner / exact file mapping を早期固定しない
  - Stage A より後ろを初手にしない
- プロンプト肥大を防ぐ
  - full execution prompt を default に戻さない
  - narrow slice を 1 つだけ定義する
  - report は ultra-compact report にする

## Recommended Initial Prompt

```text
C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md を読み、この bootstrap に従って司令塔ウインドウとして自律的に進めてください。
current_codex_state.md と current package source-of-truth を正本として、deepresearch 反映済みの判断を優先しつつ、低コンテキストで次の narrow slice だけを管理してください。
モジュール肥大化・プロンプト肥大を防ぎ、exact code owner / exact file mapping / implementation prompt / actual archive は固定せず、final report は ultra-compact report にしてください。
```

## Recommended Now

- current state は `Phase 06 surface realization card offline eval-first slice active` なので、first work window は `C:\tetie\notecode\tools\run_current_mainline_genre_sweep.py --phase genre-rerun --genres announcement,daily_story,branding` の `live=False` limited eval と generated artifact review に閉じる
- completed Phase 05 baseline は `prompt_builder.py` 単独 owner の handoff-only closeout + `note/tests/test_simple_note_pipeline.py` 1-file owner-local test lock として keep し、quality improvement の成功前提には使わない
- `ready_for_stage_a_scan` / Stage A dispatch / separate management execution への helper 参照は historical record または management contract reference であり、current active route ではない
- grounding pass / semantic pass / source-opener-reuse boundary keep 後も fingerprint-side quality block が残り、existing evidence だけでは next legal advance を決め切れないときだけ、future boundary note は single-question deepresearch trigger 1 問に限定し、deepresearch 本体は reopen しない
- user が deepresearch-first lane を explicit に選ぶときだけ、current legal move は `comparison note -> single-question deepresearch -> adoption note` の research/evidence lane に限定する
- user explicit の deepresearch-first lane では read order を `current package docs -> C:\tetie\notecode\research\新しいフォルダー (4)\01_deepresearch_first_plan_2026-04-19.md -> C:\tetie\notecode\research\新しいフォルダー (4)\02_prior_new_research_comparison_note_2026-04-19.md -> C:\tetie\notecode\research\新しいフォルダー (4)\03_single_question_deepresearch_surface_realization_card_2026-04-19.md -> C:\tetie\notecode\research\新しいフォルダー (4)\04_surface_artifact_adoption_note_2026-04-19.md` に固定する
- deepresearch-first lane の closeout は completed research/evidence lane として keep し、`surface realization card` は completed Phase 05 artifact、`surface profile` は alias only に留める
- deepresearch-first lane は package reopen でも implementation planning でもなく、completed Phase 05 は `prompt_builder.py` handoff-only slice として close したまま保つ
- current Phase 06 は `announcement / daily_story / branding` の 3 genre limited eval を first slice とし、slice self-test pass 後にだけ次 slice を 1 本開く
- current eval result が `pipeline.py` / quality guard / repair / routing / threshold canonicalization / multi-owner planning / actual archive` を要するなら `stop_and_user_report` を返す

```text
C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md を読み、この bootstrap に従って司令塔ウインドウとして自律的に進めてください。
current_codex_state.md の locked decisions と completed Phase 04 / completed Phase 05 baseline を維持しつつ、Phase 06 は `run_current_mainline_genre_sweep.py --phase genre-rerun --genres announcement,daily_story,branding` の `live=False` limited eval から始めて next owner を narrow に判定してください。
モジュール肥大化・プロンプト肥大を防ぎ、slice ごとに self-test pass を確認してから次へ進め、package-wide owner table / implementation prompt / actual archive は固定せず、work window には必要最小限の指示だけを渡し、final report は ultra-compact report にしてください。
```

## Work Window Dispatch

- completed Phase 05 は `prompt_builder.py` 単独 owner の narrow construction slice closeout に留める
- current Phase 06 first dispatch は `run_current_mainline_genre_sweep.py --phase genre-rerun --genres announcement,daily_story,branding` の `live=False` limited eval と artifact review に限定し、production runtime edit を含めない
- explicit user exception で work window を開くとしても、本文は 2-3 行に留め、line 2 では completed Phase 04 の role boundary と completed Phase 05 の handoff-only closeout boundary だけを明示する
- current Phase 06 dispatch では line 3 に `each slice self-test pass -> next slice / retry up to 3 -> stop_and_user_report` だけを追加する
- `editable-scope-only` lock が必要な current slice では line 3 だけを追加し、scope 外 fix を混ぜない
- fingerprint-side quality block が remaining issue でも、single-question deepresearch trigger 1 問を超えて broad redesign / owner fix / implementation planning へ膨らませない
- deepresearch-first lane を開くとしても、comparison note / single-question deepresearch / adoption note の closeout を research/evidence lane として先に置き、`surface realization card` を current construction artifact としても `prompt_builder.py` handoff-only を超えて package docs continuation と混ぜない
- `separate_window_execution_prompt_ui_source_blog_contract_redesign_docs_followup_2026-04-18.md` は expanded fallback only とし、bootstrap / state / current package docs で足りる限り貼らない

## Control Tower Role

- current state を読んで current package の next slice を narrow に定義する
- completed Phase 04 `Stage B artifact boundary minimum` の role boundary を drift させない
- work window へ渡す指示を短く保つ
- docs-only boundary / current mainline keep / inventory-only archive policy を守る
- deepresearch や evidence docs は必要時だけ読む

## Not This Window

- production code edit
- test edit
- implementation prompt 作成
- exact code owner fix
- exact file mapping fix
- actual archive 実行
- Stage C / D / E first
- full prompt の再肥大化

## Ultra-Compact Report

- default は 2-3 行
- `updated: control-tower docs-only, <scope>, <verdict or next narrow slice>`
- `kept: <only the still-important locked/unresolved states>`
- `untouched: code/tests/web unchanged`
- `read:` は startup path change か package switch のときだけ使う
