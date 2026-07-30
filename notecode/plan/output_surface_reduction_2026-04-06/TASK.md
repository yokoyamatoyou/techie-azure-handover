# output_surface_reduction_2026-04-06 TASK

この package は `keep core, reduce output surface` を narrow phase へ固定する。  
`1 phase = 1 narrow hypothesis = 1 owner scope` を守り、completed reference / frozen reference を reopen しない。

## Global Rules

- current success path を壊さない
- completed reference package を reopen しない
- frozen architecture package を reopen しない
- prompt accretion 禁止
- module accretion 禁止
- rollback 可能な narrow diff だけを許可する
- helper 増殖を simplification と見なさない
- final output residual を article-type rule 増殖で救わない
- same failed hypothesis を unchanged で再投入しない
- 各 phase の自己修正は 3 回まで
- 3 回失敗したら rollback 後に停止し user report する

## Gates

### Entry Gate

- baseline / source-of-truth / rollback boundary が `README.md` / `PROGRESS.md` / `ROLLBACK.md` に固定されている
- owner scope が 1 file に閉じている
- phase hypothesis が completed / frozen package の blocked hypotheses を踏んでいない

### Pass Gate

- owner-local tests pass
- shared checks pass
- current success path regression なし
- rollback note 更新済み
- surface reduction が helper 増殖ではなく decision density の削減として説明できる

### Stop Gate

- 同一 phase で 3 回失敗
- current success path regression
- rollback 不可能な diff が必要
- planner / generator core を reopen しないと進めない

## Shared Checks

### Output Formatter Owner

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st08c or st07a_06 or st07a_07" -q
```

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

### Section-First Wrapper

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q
```

## Phase Map

### Phase 00 Package Freeze

- Objective:
  - keep / thin / remove の output-surface boundary を package docs に固定する
- Owner:
  - package docs only
- Exit:
  - next phase が `output_formatter.py` owner に閉じる

### Phase 01 Output Formatter Surface Reduction

- Objective:
  - final output shaping を `normalize body -> project title / lead -> add scaffold` に近づけ、article-type specific decision surface を `output_formatter.py` owner の中で薄くする
- Hypothesis:
  - `output_formatter.py` の title seed / lead seed / scaffold mode / body normalize branching を 1 本の formatter spine に寄せれば、completed owner scope を reopen せずに final surface を最も狭くできる
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- Tasks:
  - formatter main flow の article-type branch を inventory 化する
  - title / lead / scaffold decision point を narrow spine に寄せる
  - body normalize と final projection の境界を読みやすくする
- Exit:
  - formatter main flow が `normalize body -> project head -> scaffold` として読める

### Phase 02 Editor Guard Boundary Trim

- Objective:
  - Phase 01 後も duplication が final-stage boundary に残る場合だけ、sentence-integrity repair surface を `editor_guard.py` owner の中で薄くする
- Hypothesis:
  - `editor_guard.py` の repair kind / budget / warning surface を 1 本の acceptance spine に寄せれば、formatter 側へ residual fix を戻さずに final-stage boundary を閉じられる
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\editor_guard.py`
- Entry condition:
  - Phase 01 完了後も final-stage residual の主因が formatter / editor boundary duplication の場合だけ開始する
- Exit:
  - `editor_guard.py` が sentence-integrity repair owner として読め、formatter 側の hidden repair assumption が減っている

## Retry Discipline

- 同一 phase で 3 回失敗したら rollback して停止する
- failed hypothesis は `PROGRESS.md` と `ROLLBACK.md` に明記する
- prompt-only strengthening は retry option に入れない
