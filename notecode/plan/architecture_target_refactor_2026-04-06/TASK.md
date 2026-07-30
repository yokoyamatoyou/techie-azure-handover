# architecture_target_refactor_2026-04-06 TASK

この package は target architecture への移行順序を固定する。  
`1 phase = 1 narrow hypothesis = 1 owner scope` を守り、current success path を壊さない。

## Global Rules

- current success path を壊さない
- prompt accretion 禁止
- module accretion 禁止
- rollback 可能な narrow diff だけを許可する
- hidden reviser を増やさない
- same failed hypothesis を unchanged で再投入しない
- 各 phase の自己修正は 3 回まで
- 3 回失敗したら rollback 後に停止し user report する

## Gates

### Entry Gate

- baseline と rollback boundary が `README.md` / `PROGRESS.md` / `ROLLBACK.md` に固定されている
- owner scope が 1 file に閉じている
- phase hypothesis が current package の blocked hypotheses を踏んでいない

### Pass Gate

- owner-local tests pass
- shared checks pass
- current success path regression なし
- rollback note 更新済み

### Stop Gate

- 同一 phase で 3 回失敗
- current success path regression
- rollback 不可能な diff が必要
- failed hypothesis の unchanged 再投入が必要

## Shared Checks

### Focused Pipeline

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q
```

### Quality Guard

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q
```

### Current Mainline Boundary

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q
```

## Phase Map

### Phase 00 Package Freeze

- Objective:
  - target architecture verdict / keep-refactor-replace / blocked hypotheses を package に固定する
- Owner:
  - package docs only
- Exit:
  - docs-only package が次 phase の基準として使える

### Phase 01 Canonical Plan State

- Objective:
  - planner-owned canonical plan state を 1 本に固定する
- Hypothesis:
  - `DiscourseSection` の contract を runtime spine に昇格させるだけで、plan の支配点が明確になる
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py`
- Tasks:
  - section contract の必須 field を固定する
  - route-local extension を bounded に整理する
  - planner output の正規化 helper を owner-local に閉じる
- Exit:
  - downstream が「どの plan を使うか」で迷わない

### Phase 02 Attributed Fact Slots

- Objective:
  - `source_grounding_items` を evidence slot として正規化する
- Hypothesis:
  - section intent と fact slot を 1:1 ではなく bounded set にすることで、source starvation と source drift の両方を減らせる
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py`
- Tasks:
  - source slot の label / role / optionality を内部仕様として固定する
  - case_study の `change` / `condition` に必要な slot 種別を明文化する
- Exit:
  - planner が section ごとの usable evidence set を返せる

### Phase 03 Section State Promotion

- Objective:
  - generator 内部の軽量 state を canonical section state へ昇格させる
- Hypothesis:
  - `previous_summary` だけでなく `remaining_must_cover` / `used_fact_slots` / `section_ledger` を外化すると、後半失速を抑えやすい
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\section_generator.py`
- Tasks:
  - local state schema を owner-local に固定する
  - summary bridge を keep しつつ、ledger を主 state にする
- Exit:
  - section writer が plan state を consume/update する形になる

### Phase 04 Route-Gated Section-First Mainline

- Objective:
  - default mainline の一部 route を section-first writer に寄せる
- Hypothesis:
  - 1 route だけ section-first を本流化しても fail-open を維持できる
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- Tasks:
  - experiment route ではなく narrow route 本流で canonical plan state を使う
  - fallback は残すが、quality spine の主役を section-first に寄せる
- Exit:
  - 1 route で `single-pass rescue chain` 依存が下がる

### Phase 05 Constrained Micro-Revision

- Objective:
  - revision を hidden writer から constrained micro-revision へ縮退させる
- Hypothesis:
  - source と plan に anchored な micro-revision は、現行 repair より安全に働く
- Owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Tasks:
  - rewrite ではなく section-local repair に限定する
  - external source / plan / fact slots を参照しない revision を増やさない
- Exit:
  - repair が本文の意味を再構成しない

### Phase 06 Wrapper Demotion

- Objective:
  - compatibility wrapper を恒久本体から降格させる
- Hypothesis:
  - planner/state/writer/revision の spine が立てば、wrapper は validator / adapter に縮退できる
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- Tasks:
  - hidden coupling を減らす
  - path ごとの品質支配点を明文化する
- Exit:
  - quality spine が 1 本に見える

## Retry Discipline

- 同一 phase で 3 回失敗したら rollback して停止する
- failed hypothesis は `PROGRESS.md` と `ROLLBACK.md` に明記する
- prompt-only strengthening は retry option に入れない
