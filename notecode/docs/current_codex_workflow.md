# current codex workflow

## Goal

- separate window 開始時の prompt を最小化する
- current state と source-of-truth の責務を分ける
- historical prompt の増殖を止める

## Doc Tiers

### Tier 0 Stable Bootstrap

- file:
  - `C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md`
- role:
  - user が新しい window を起動するときの最短入口
- update when:
  - current package が切り替わる
  - startup read order が変わる
  - expanded fallback path が変わる

### Tier 1 Stable State Capsule

- file:
  - `C:\tetie\notecode\docs\current_codex_state.md`
- role:
  - current phase / editable scope / next action / stop boundary の短い要約
- update when:
  - phase が変わる
  - editable scope が変わる
  - next autonomous slice が変わる

### Tier 2 Package Source-Of-Truth

- files:
  - current package の `README.md / TASK.md / PROGRESS.md / ROLLBACK.md / EXECUTION_PROMPT.md`
- role:
  - current work の正本
- update when:
  - hypothesis / gate / rollback boundary / execution contract が変わる

### Tier 3 Evidence And History

- files:
  - research notes
  - deepresearch-first planning note
  - deepresearch verification notes
  - old separate-window prompts
  - old management prompts
- role:
  - reasoning support と historical record
- rule:
  - default startup path に使わない

## Precedence

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\docs\current_codex_state.md`
4. current package source-of-truth
5. evidence / history docs

- startup entry は bootstrap -> state -> package docs の順に取る
- current state と package docs が衝突したら package source-of-truth を優先する

## Update Rules

- same package / same phase の通常進行:
  - `PROGRESS.md` と `current_codex_state.md` を更新する
- same package / phase contract change:
  - package docs 5 本と `current_codex_state.md` を更新する
- package switch:
  - `current_codex_autonomous_bootstrap.md` と `current_codex_state.md` を先に更新する
- new prompt doc の追加:
  - default では禁止
  - 新しい window type が本当に別物になったときだけ許可する
- old prompt doc:
  - current startup path から外れたら history 扱いに落とす

## Startup Best Practice

- user は 1 行だけ送る
  - `C:\tetie\notecode\docs\current_codex_autonomous_bootstrap.md を読み、この bootstrap に従って自律的に進めてください。`
- 司令塔ウインドウの最初の prompt は次を使う
  - `C:\tetie\notecode\docs\current_codex_control_tower_prompt.md`
- task delta の書き方は次を使う
  - `C:\tetie\notecode\docs\current_codex_work_instruction_prompt.md`
- work window へ渡す default 指示は、current verdict が dispatch を許可するときだけ `current_codex_work_instruction_prompt.md` の 2-3 行 template を使う
- completed Phase 05 `surface realization card first construction slice` は `prompt_builder.py` handoff-only baseline と `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py` 1-file owner-local test lock completed の current baseline として keep する
- current Phase 06 は explicit user-opened eval-first lane なので、first work window dispatch は `C:\tetie\notecode\tools\run_current_mainline_genre_sweep.py` の `live=False` limited eval と generated artifact review に限定する
- current Phase 06 first slice では production runtime file edit を開かず、slice self-test pass 後にだけ次 slice を 1 本進める
- user が deepresearch-first lane を explicit に選んだときだけ、current package docs の後で `C:\tetie\notecode\research\新しいフォルダー (4)\01_deepresearch_first_plan_2026-04-19.md` と closeout note `C:\tetie\notecode\research\新しいフォルダー (4)\02_prior_new_research_comparison_note_2026-04-19.md` / `C:\tetie\notecode\research\新しいフォルダー (4)\03_single_question_deepresearch_surface_realization_card_2026-04-19.md` / `C:\tetie\notecode\research\新しいフォルダー (4)\04_surface_artifact_adoption_note_2026-04-19.md` を読む
- deepresearch-first lane は research/evidence lane であり、package reopen や code continuation に読み替えない
- deepresearch-first lane の closeout は completed research/evidence lane として keep し、`surface realization card` は completed Phase 05 artifact、`surface profile` は alias only に留める
- explicit user exception で dispatch する場合も、line 2 では completed Phase 04 の role boundary と completed Phase 05 の closeout / stop boundary だけを短く pin する
- current Phase 06 dispatch では line 2 に `offline eval-first / 3 genre / live=False / self-test then next slice` を短く pin する
- `ready_for_stage_a_scan` / Stage A dispatch / separate management execution への helper 参照は historical record または management contract reference であり、current active route ではない
- expanded fallback prompt は bootstrap / state / current package docs だけでは起動できないときだけ使う
- phase を pin したいときだけ 1 行追加する
  - `current_codex_state.md の current phase を維持し、docs-only で続けてください。`
- editable scope を pin したいときだけ 1 行追加する
  - `current_codex_state.md の editable scope だけを更新し、editable-scope-only lock を維持して、production code / AGENTS / WORKLOG は触らないでください。`
- window 側は bootstrap -> state -> package docs の順に読む
- evidence/history の深掘りは必要になってから行う

## Window Close Best Practice

- current phase が変わらなければ `PROGRESS.md` と `current_codex_state.md` を揃える
- current phase が変わったら package docs 5 本と `current_codex_state.md` を揃える
- startup path が変わったら `current_codex_autonomous_bootstrap.md` を更新する
- final report は 2-3 行の ultra-compact report を default にする

## Ultra-Compact Report

- default format:
  - `updated: <scope>, <phase/status or verdict>, next <next step>`
  - `kept: <only the still-important locked/unresolved states>`
  - `untouched: code/tests/web unchanged`
- `read:` は startup path change や package switch があったときだけ付ける
- file list / AGENTS / WORKLOG / current package path を毎回列挙しない
- 同じ window で scope が狭いときは `untouched:` を省略して 2 行で閉じてよい
- tests 未実行や web 未使用は `untouched:` 行にまとめる

## Anti-Patterns

- 毎回新しい dated startup prompt を増やすこと
- historical prompt 群を source-of-truth の代わりに読むこと
- current state を更新せず package docs だけ変えること
- package switch 後に bootstrap を古いまま放置すること
- long pasted prompt がないと動けない前提に戻ること
- expanded fallback prompt を default dispatch として毎回貼ること
- final report で read file list や unchanged baseline を長く再掲すること
