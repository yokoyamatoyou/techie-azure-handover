# compat_layer_removal_2026-04-20 TASK

この package は `newalgorithm_pipeline` を current success path から外し、compatibility surface を dead code 候補へ落とすための narrow package です。  
削除は runtime path の直結化後に行い、`simple_note_pipeline` 本体の品質ロジックには踏み込みません。

## Global Rules

- current success path を壊さない
- `1 phase = 1 narrow hypothesis = 1 owner scope`
- compatibility layer removal と quality algorithm change を混ぜない
- `simple_note_pipeline/pipeline.py` の意味変更はしない
- prompt accretion をしない
- docs accretion をしない
- dead code 判定前に runtime path を外す
- deleted candidates は reference search と test search の両方で確認する
- `note_writer_app.py` の UI 改修と混ぜない
- `naturalness_recovery_2026-04-07` package docs は reopen しない
- current package の fail-closed keep judgment を変更しない

## Current Locked Read

- `simple_note_pipeline` が実体
- `newalgorithm_pipeline` は互換 wrapper
- `current_mainline_runner` はまだ wrapper を通る
- よって、いまの `newalgorithm_pipeline` は dead code ではない
- dead code 削除の前に、runtime path からの切断が必要

## Entry Gate

- `current_mainline_runner.py`
- `newalgorithm_pipeline/pipeline.py`
- `simple_note_pipeline/pipeline.py`
- current mainline test 群
- current UI matrix test 群
を読んで、互換レイヤが何を担っているか short map を作れていること

## Pass Gate

- `current_mainline_runner -> simple_note_pipeline` 直結化の差分が narrow に閉じている
- shared checks が green
- `newalgorithm_pipeline` が runtime path 上で不要になったことを code search で示せる
- dead code 候補一覧に「まだ使っているもの」が混ざっていない

## Stop Gate

- `newalgorithm_pipeline` が単なる wrapper ではなく、runtime semantics を持っていて 1 phase で切れない
- `simple_note_pipeline` 側の contract change が必要
- UI / tests / tools / batch scripts の複数 owner 同時変更が不可避
- shared checks で current success path regression が出る

## Shared Checks

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
```

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_simple_note_pipeline.py -q
```

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q
```

## Phase Map

### Phase 01 Runtime Responsibility Map

- Objective:
  - `newalgorithm_pipeline` が current success path で担っている責務を 1 画面で説明できる状態にする
- Hypothesis:
  - 互換レイヤの責務を分解すると、runtime path を壊さずに `current_mainline_runner` へ寄せられる
- Owner:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- Tasks:
  - import / call chain / payload normalization / output guard / telemetry merge の責務を short map にする
  - `simple_note_pipeline` へ直結する時に必要な最小 adapter を特定する
- Exit:
  - `wrapper responsibilities` と `direct path candidate` が箇条書きで確定

### Phase 02 Direct Path Adoption

- Objective:
  - `current_mainline_runner` から `simple_note_pipeline` へ直結する
- Hypothesis:
  - compatibility wrapper が担っている責務のうち必須部分を runner 側へ寄せれば、`newalgorithm_pipeline` を success path から外せる
- Owner:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - 必要なら owner-local な最小 adapter file 1 本まで
- Tasks:
  - direct path を実装する
  - runner / regression / ui matrix tests を通す
  - `newalgorithm_pipeline` を current success path から外したことを code path で示す
- Exit:
  - current success path が `current_mainline_runner -> simple_note_pipeline` になる

### Phase 03 Compatibility Surface Inventory

- Objective:
  - `newalgorithm_pipeline` 配下のうち、runtime path から外れたものを dead code 候補として整理する
- Hypothesis:
  - direct path 化の後なら、compatibility surface は `used / transitional / dead candidate` に 3 分類できる
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\`
- Tasks:
  - code search
  - test search
  - tool / script search
  - import graph の簡易棚卸し
  - 削除候補一覧を作る
- Exit:
  - file / symbol 単位で dead candidate が列挙される

### Phase 04 Dead Code Removal Lane

- Objective:
  - dead candidate を narrow diff で削除する implementation lane に渡す
- Hypothesis:
  - runtime path を外した後なら、互換 surface の一部は安全に削除できる
- Owner:
  - Phase 03 で dead と確定した file / symbol 単位
- Tasks:
  - 削除順序を決める
  - rollback 単位を小さく切る
  - test updates を最小化する
- Exit:
  - separate execution 用 prompt が書ける

## First Implementation Prompt Boundary

- first diff で触ってよい:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - owner-local adapter file 1 本まで
  - relevant tests
- first diff で触らない:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\note_writer_app.py`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\*`
  - `C:\tetie\notecode\docs\*`

## Implementation-Ready Notes

- separate window ではまず `newalgorithm_pipeline/pipeline.py` を削除しない
- 先に `current_mainline_runner` 直結化の差分を作る
- 直結後に `newalgorithm_pipeline` を no-longer-runtime-path として inventory 化する
- dead code 判定は `not used in success path` と `not imported anywhere meaningful` の両方を満たすものだけに限定する
