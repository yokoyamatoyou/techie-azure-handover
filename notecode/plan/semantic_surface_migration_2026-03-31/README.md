# semantic_surface_migration_2026-03-31

`C:\tetie\notecode\GPTPRO.txt` の方向性に基づき、current mainline を壊さずに `meaning-layer` と `surface-layer` を段階的に分離するための autonomous execution package。

## Goal

- current success path を維持したまま、`GPTPRO.txt` ベースのアルゴリズム移行を段階的に進める
- 既に導入した `semantic ledger` を起点に、次の 3 つを current mainline へ寄せる
  - omission / zero-anaphora の判定
  - ending control
  - flagged span local patch
- 各 phase 完了後に `prompt injection / code readability / UI integration / pipeline` を確認し、green のときだけ次へ進む

## Success Definition

- current success path を維持する
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> super().generate(...)`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `simple_note_pipeline` において、meaning-layer と surface-layer の責務が今より明確になる
- omission / ending / patch の 3 系統が `single-pass owner` を壊さず narrow に導入される
- final live sweep で kept state regression がない
- rollback path が phase ごとに残る

## Non-Goals

- `simple_note_refactor_2026-03-22` の reopen
- `human_resonance*` 本体の初手改修
- prompt accretion で押し切ること
- owner 不明の global tuning
- UI の visible redesign

## Fixed Constraints

- mainline owner は `simple_note_pipeline` を維持する
- phase ごとに `entry -> implementation -> checks -> progress update -> next phase` の順に進む
- 各 phase は mini モデルでも理解・検証できる粒度にする
- 同一 phase の自己修正は最大 3 回まで
- 3 回で gate を越えられなければ停止して user report へ切り替える
- rollback は phase ごとに即時可能な narrow diff を前提にする
- prompt / module の肥大化は禁止

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\GPTPRO.txt`
4. `C:\tetie\notecode\ALGORITHM.md`
5. `C:\tetie\WORKLOG.md`
6. `C:\tetie\notecode_current_mainline_handoff_2026-03-31.md`
7. `C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\TASK.md`
8. `C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\PROGRESS.md`
9. `C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\EXECUTION_PROMPT.md`

## Current Baseline

- `semantic ledger` は current mainline に最小導入済み
- generation prompt と repair prompt は meaning-layer を参照できる
- `semantic_anchor_coverage` / `semantic_claim_coverage` は観測可能
- 次の論点は `GPTPRO.txt` が言う full migration ではなく、`narrow introduction of the next mechanism` に固定する

## Phase Map

### Phase 00 Baseline Freeze

- baseline / kept state / rollback boundary を固定する

### Phase 01 Semantic vs Surface Inventory

- 現在どこまで meaning-layer / surface-layer が分離済みかを棚卸しする

### Phase 02 Omission Observability

- zero-anaphora / omission の曖昧化を検知する観測値を追加する

### Phase 03 Omission Repair Rules

- omission を「全文再生成」でなく「repair guidance / local rule」で扱う

### Phase 04 Omission Activation

- explanatory / industry など safe boundary に限定して omission-aware behavior を有効化する

### Phase 05 Ending Observability

- 文末の単調さを bucket 単位で観測し、どこまで rule 化すべきかを固定する

### Phase 06 Ending Control

- ending monotony を prompt wording ではなく narrow controller で抑える

### Phase 07 Flagged Span Patch Scaffold

- 全文 rewrite ではなく flagged span patch を差し込む最小 scaffold を作る

### Phase 08 Flagged Span Patch Activation

- repair が必要なケースだけ局所 patch を有効化する

### Phase 09 Sentinel Sweep

- announcement / comparative / branding / case_study 側の kept state regression を確認する

### Phase 10 Final Live And Closeout

- live sweep, docs update, kept state 固定, next residual 記録

## Mandatory Checks After Every Phase

1. prompt injection / policy:
   - relevant regressions green
2. code readability:
   - owner が膨れていない
   - 条件分岐が同種の足し算になっていない
3. UI integration:
   - `current_mainline_runner` / `ui_matrix` regressions green
4. pipeline:
   - `simple_note_pipeline` focused tests green

## Stop Rule

- 同一 phase で 3 回自己修正しても gate を越えられない
- announcement kept fix regression
- comparative rollback 済み仮説の再投入
- owner file 増加が narrow slice を超える
- rollback 不能な diff が必要になった

## Required Progress Discipline

- phase 開始前に `PROGRESS.md` を `in_progress` へ更新する
- phase pass 後に evidence / tests / rollback note を記録する
- 停止時は必ず `試した修正 / 失敗理由 / 残課題 / 次の narrow slice` を残す
