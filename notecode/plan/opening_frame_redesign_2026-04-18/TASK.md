# opening_frame_redesign_2026-04-18 TASK

この package は `naturalness_recovery_2026-04-07` を parked のまま維持しつつ、`opening frame ownership` を separate redesign line として docs-only で固定する。  
`1 phase = 1 narrow hypothesis = 1 owner scope` を守り、current parked boundary と inherited do-not-retry を崩さない。

## Global Rules

- current package `naturalness_recovery_2026-04-07` は parked / not fixed のまま維持する
- production code / tests / AGENTS / WORKLOG / current package docs は編集しない
- first line は docs-only とし、code diff を始めない
- research は evidence として読むが source-of-truth には昇格させない
- package theme は `opening frame ownership / role separation / current-business-first invariant` に固定する
- `minimal_control_layer` は package theme ではなく first design question として扱う
- `pipeline.py` を first code owner に確定しない
- `prompt_builder.py` を first code owner に確定しない
- first code owner は `not fixed` と書く
- tentative future candidate が必要な場合だけ `newalgorithm_pipeline/pipeline.py` 周辺の最小 opening-frame control surface に触れてよい
- `prompt_builder.py` simplification-first wording line の unchanged retry はしない
- `pipeline.py` current-first source ordering / hint triage の unchanged retry はしない
- `pipeline.py` core_message current-first hint の unchanged retry はしない
- `SECTION_SHADOW` reopen first に戻さない
- `quality_guard.py` first にしない
- repair acceptance reopen first にしない
- `natural_blog_core.py` first section history clamp 仮説は do-not-retry として継承する
- `output_formatter.py` formatter-only surface polish 仮説は do-not-retry として継承する
- `input_contract.py` upstream distilled summary 単独仮説は do-not-retry として継承する
- prompt accretion continuation 禁止
- fixed routing table 禁止
- planning / skeleton default reopen 禁止
- giant rewrite 禁止
- hidden reviser accumulation 禁止
- current package reopen と実質同じ文書しか書けない場合は停止して user report する

## Current Locked Outcome

- package category:
  - `DOCS_FIRST_NEW_PACKAGE_AFTER_PARKED_NATURALNESS_RECOVERY`
- current decision:
  - `opening frame redesign is a separate redesign line`
- current package state:
  - `naturalness_recovery_2026-04-07` は parked / not fixed
- current success path:
  - keep
- first code owner:
  - `not fixed`
- first code step:
  - `not started`
- next step:
  - `docs-first design triage`
- tentative future code candidate:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` 周辺の最小 opening-frame control surface
  - current package retry の unchanged reopen ではない
- inherited do-not-retry:
  - `prompt_builder.py` simplification-first wording line
  - `pipeline.py` current-first source ordering / hint triage
  - `pipeline.py` core_message current-first hint
  - `SECTION_SHADOW` reopen first
  - `quality_guard.py` first
  - repair acceptance reopen first
  - `natural_blog_core.py` first section history clamp
  - `output_formatter.py` formatter-only surface polish
  - `input_contract.py` upstream distilled summary only
  - prompt accretion continuation
  - fixed routing table
  - planning / skeleton default reopen
  - giant rewrite
- evidence boundary:
  - research synthesis と research 3 本は evidence only
- package close state:
  - not closed
  - next action は Phase 01 docs-only design comparison

## Gates

### Entry Gate

- new package が current parked package と role conflict していない
- inherited do-not-retry boundary が README / TASK / PROGRESS / ROLLBACK / EXECUTION_PROMPT に固定されている
- first code owner が `not fixed` のまま維持されている
- research を evidence として扱い、source-of-truth と混ぜていない

### Pass Gate

- docs 5 本が互いに整合している
- current package parked judgment と衝突していない
- `opening frame redesign is a separate redesign line` が 5 本で一貫している
- next step が implementation に滑っていない
- first code owner がまだ `not fixed` である
- production code / tests / AGENTS / WORKLOG / current package docs を更新していない

### Stop Gate

- current package reopen と実質同じ内容しか書けない
- first code owner を early fix したくなった
- package objective が broad redesign に膨らんだ
- `minimal_control_layer` implementation を先に固定したくなった
- multiple owner implementation planning が必要になった

## Shared Checks

- `README.md` / `TASK.md` / `PROGRESS.md` / `ROLLBACK.md` / `EXECUTION_PROMPT.md` が package category と current decision で一致している
- `README.md` / `TASK.md` / `PROGRESS.md` / `EXECUTION_PROMPT.md` が `first code owner = not fixed` を維持している
- `README.md` / `ROLLBACK.md` / `EXECUTION_PROMPT.md` が current package parked boundary を明記している
- forbidden update がない

## Phase Map

### Phase 00 Objective / Boundary Freeze

- Objective:
  - opener ownership problem と evaluation boundary を narrow に固定する
- Hypothesis:
  - `opening frame ownership / role separation / current-business-first invariant` を separate redesign line として切り出せば、current parked package を reopen せずに legal な next design question を保持できる
- Owner:
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\`
- Tasks:
  - objective / non-goals / do-not-retry inheritance を固定する
  - `minimal_control_layer` を first design question に留める
  - first code owner を `not fixed` に固定する
- Exit:
  - package objective / non-goals / parked boundary / evaluation set が固定される

### Phase 01 Minimal Control Placement Comparison

- Objective:
  - code を書かずに minimal control placement candidate を比較する
- Hypothesis:
  - `prompt_builder` frame card / `pipeline.py` opening-frame control surface / tiny deterministic guard の 3 候補を docs-only で比較すれば、legal な `1 owner / 1 hypothesis` 候補が 1 本に絞れる、または未確定のまま stop できる
- Owner:
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\`
- Candidates:
  - `prompt_builder` frame card
  - `pipeline.py` opening-frame control surface
  - tiny deterministic guard
- Exit:
  - legal な `1 owner / 1 hypothesis` candidate が 1 本に絞られる
  - または `not fixed` のまま stop boundary を書ける

## Refined Execution Order

- before any code diff:
  - current parked boundary と inherited do-not-retry を確認する
- Phase 00:
  - objective / non-goals / source-of-truth / rollback boundary を docs-only で固定する
- Phase 01:
  - control placement candidates を code なしで比較する
  - `pipeline.py` と `prompt_builder.py` の unchanged reopen と混同しない
- only after Phase 01 pass:
  - separate implementation prompt を別 step で作るか判断する
  - 同じ step で code diff は始めない
- last resort:
  - stop and user report

## Retry Discipline

- 各 docs phase の自己修正は 3 回まで
- 3 回失敗したら new package docs だけを rollback 対象として停止する
- failed framing は `PROGRESS.md` と `ROLLBACK.md` に明記する
