# orchestration_surface_reduction_2026-04-06 TASK

この package は `keep core, reduce orchestration surface` を narrow phase へ固定する。  
`1 phase = 1 narrow hypothesis = 1 owner scope` を守り、frozen architecture reference を reopen しない。

## Global Rules

- current success path を壊さない
- frozen architecture package を reopen しない
- prompt accretion 禁止
- module accretion 禁止
- rollback 可能な narrow diff だけを許可する
- helper 増殖を simplification と見なさない
- quality 改善を名目に wrapper / repair branch を増やさない
- same failed hypothesis を unchanged で再投入しない
- 各 phase の自己修正は 3 回まで
- 3 回失敗したら rollback 後に停止し user report する

## Gates

### Entry Gate

- baseline / source-of-truth / rollback boundary が `README.md` / `PROGRESS.md` / `ROLLBACK.md` に固定されている
- owner scope が 1 file に閉じている
- phase hypothesis が frozen architecture package の blocked hypotheses を踏んでいない

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
  - keep / thin / remove の simplification boundary を package docs に固定する
- Owner:
  - package docs only
- Exit:
  - frozen architecture reference を reopen せず、次 phase が owner-local に切れる

### Phase 01 Wrapper Surface Reduction

- Objective:
  - wrapper を `primary generation -> adapter / validator` に近づけ、article-type specific orchestration surface を main flow から減らす
- Hypothesis:
  - `newalgorithm_pipeline/pipeline.py` の compatibility rebuild / stabilizer branching を 1 本の postprocess decision spine に寄せれば、core を残したまま最も重い surface を先に薄くできる
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- Tasks:
  - wrapper main flow の article-type branch を inventory 化する
  - compatibility rebuild / preserve / stabilizer の decision point を narrow spine に寄せる
  - wrapper-local telemetry は keep しつつ、branch owner ambiguity を減らす
- Exit:
  - wrapper の main flow が `section generation -> postprocess spine -> format` として読める

### Phase 02 Repair Surface Reduction

- Objective:
  - repair を multi-branch orchestration から single acceptance spine へ縮退させる
- Hypothesis:
  - `simple_note_pipeline/pipeline.py` の repair activation / patch-path / acceptance を 1 本の accept rule に畳めば、single-pass + optional single repair contract を守ったまま surface を薄くできる
- Owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Tasks:
  - repair entrypoint を 1 本に固定する
  - `flagged scope + alignment + trigger improvement` を accept spine にまとめる
  - repair-specific fallback の分岐増殖を止める
- Exit:
  - repair の通過条件が 1 か所に集約され、本文 owner と repair owner の境界が読める

### Phase 03 Boundary Projection Trim

- Objective:
  - runner の boundary projection を必要最小限に薄くし、package 全体の orchestration surface を閉じる
- Hypothesis:
  - Phase 01-02 後も complexity が残る場合だけ `current_mainline_runner.py` を projection-only に寄せれば、mainline surface をさらに縮められる
- Owner:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
- Entry condition:
  - Phase 01-02 完了後も boundary duplication が main blocker の場合だけ開始する
- Exit:
  - runner が contract build / execution call / fail-closed normalize / boundary projection に留まる

## Retry Discipline

- 同一 phase で 3 回失敗したら rollback して停止する
- failed hypothesis は `PROGRESS.md` と `ROLLBACK.md` に明記する
- prompt-only strengthening は retry option に入れない
