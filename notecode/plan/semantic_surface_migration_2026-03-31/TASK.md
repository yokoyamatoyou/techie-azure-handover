# semantic_surface_migration_2026-03-31 TASK

このファイルは phase ごとの実行単位と gate を管理する。  
1 phase = 1 narrow hypothesis を原則にし、mini でも理解できる粒度に固定する。

## Global Rules

- current success path を壊さない
- `prompt accretion` 禁止
- `module accretion` 禁止
- `human_resonance*` は初手で触らない
- phase ごとに rollback 可能な narrow diff にする
- 自己修正は phase ごとに 3 回まで
- 3 回失敗したら停止して user report

## Shared Check Commands

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

---

## Phase 00 Baseline Freeze

- Objective:
  - current kept state / baseline / rollback boundary を固定する
- Owner:
  - read-only
- Tasks:
  - `GPTPRO.txt`, handoff, ALGORITHM, WORKLOG を読み、baseline を `PROGRESS.md` へ転記
  - current success path と blocked hypotheses を固定
- Exit:
  - baseline / blocked hypotheses / rollback boundary が明文化されている

## Phase 01 Semantic vs Surface Inventory

- Objective:
  - current code で meaning-layer と surface-layer がどこまで分かれているかを棚卸しする
- Owner:
  - read-only
- Tasks:
  - `prompt_builder.py`
  - `pipeline.py`
  - `quality_guard.py`
  - `rendering.py`
    の responsibility table を作る
- Exit:
  - 次に追加する mechanism が 1 つに絞れる

## Phase 02 Omission Observability

- Objective:
  - omission / zero-anaphora ambiguity を測る観測値を追加する
- Owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
  - tests
- Tasks:
  - omission ambiguity の heuristic を narrow に追加
  - diagnostics / pipeline_check へ expose
- Required Checks:
  - Focused Pipeline
  - Quality Guard
  - Current Mainline Boundary
- Exit:
  - omission-related metric が観測できる
  - false positive で hard fail しない
- Rollback:
  - metric 追加だけを戻せば baseline へ戻れる

## Phase 03 Omission Repair Rules

- Objective:
  - omission を全文 rewrite ではなく local repair guidance で扱う
- Owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - tests
- Tasks:
  - repair prompt に omission-specific rule を追加
  - claim / anchor を保った surface-only repair を維持
- Required Checks:
  - Focused Pipeline
  - Quality Guard
  - Current Mainline Boundary
- Exit:
  - omission repair guidance が明示される
  - repair が全文書き換えに戻らない
- Rollback:
  - repair prompt の追加 rule を外す

## Phase 04 Omission Activation

- Objective:
  - omission-aware behavior を safe boundary で有効化する
- Owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - tests
- Tasks:
  - activation boundary を explanatory / industry など既存 safe scope に限定
  - fail-open fallback を維持
- Required Checks:
  - Focused Pipeline
  - Quality Guard
  - Current Mainline Boundary
- Exit:
  - activation scope が明確
  - announcement / comparative regression なし
- Rollback:
  - activation boundary を戻す

## Phase 05 Ending Observability

- Objective:
  - ending monotony を bucket 単位で観測する
- Owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
  - tests
- Tasks:
  - ending bucket or ending sequence metrics を追加
  - pipeline_check へ expose
- Required Checks:
  - Focused Pipeline
  - Quality Guard
  - Current Mainline Boundary
- Exit:
  - 文末単調性を定量で追える
- Rollback:
  - metric 追加のみ戻す

## Phase 06 Ending Control

- Objective:
  - 文末の揺れを prompt wording ではなく narrow controller で扱う
- Owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\postprocess.py` または `quality_guard.py`
  - tests
- Tasks:
  - same ending run を局所的に崩す controller を narrow に導入
  - grammar / readability を壊さない
- Required Checks:
  - Focused Pipeline
  - Quality Guard
  - Current Mainline Boundary
- Exit:
  - same ending run が改善
  - flatness 改善に対して grammar regression なし
- Rollback:
  - controller のみ戻す

## Phase 07 Flagged Span Patch Scaffold

- Objective:
  - flagged span patch の scaffold を作る
- Owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - tests
- Tasks:
  - full rewrite ではなく issue span 単位の patch path を定義
  - 初期は scaffold / hidden gate でよい
- Required Checks:
  - Focused Pipeline
  - Quality Guard
  - Current Mainline Boundary
- Exit:
  - patch scaffold が fail-open で存在する
- Rollback:
  - hidden path ごと戻す

## Phase 08 Flagged Span Patch Activation

- Objective:
  - patch path を限定ケースで有効化する
- Owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - tests
- Tasks:
  - low-risk phase / low-risk article type に限定して patch activation
  - full rewrite fallback を増やさない
- Required Checks:
  - Focused Pipeline
  - Quality Guard
  - Current Mainline Boundary
- Exit:
  - patch が local repair として動く
  - baseline regression なし
- Rollback:
  - activation off

## Phase 09 Sentinel Sweep

- Objective:
  - kept state regression を出していないか cross-route で確認する
- Owner:
  - code edit なし想定
- Tasks:
  - announcement
  - comparative
  - branding
  - case_study
    の sentinel check
- Required Checks:
  - Current Mainline Boundary
- Exit:
  - sentinel green

## Phase 10 Final Live And Closeout

- Objective:
  - final live / docs / handoff をまとめて close する
- Owner:
  - code + docs
- Tasks:
  - live sweep
  - kept state fix
  - `ALGORITHM.md` / `WORKLOG.md` / `PROGRESS.md` 更新
  - next residual 記録
- Required Checks:
  - Focused Pipeline
  - Quality Guard
  - Current Mainline Boundary
- Exit:
  - kept state と next residual が明文化されている
