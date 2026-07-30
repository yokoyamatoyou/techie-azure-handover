# visible_output_integrity_2026-04-06 TASK

この package は `keep core, enforce visible output integrity` を narrow phase へ固定する。  
`1 phase = 1 narrow hypothesis = 1 owner scope` を守り、completed / frozen reference と pre-2026-04-02 archive-only records を reopen しない。

## Global Rules

- current success path を壊さない
- pre-2026-04-02 records は archive-only に留める
- completed reference package を reopen しない
- frozen architecture package を reopen しない
- prompt accretion 禁止
- module accretion 禁止
- deletion-first で surface を減らす
- visible red symptom を warning-only success のまま残さない
- same failed hypothesis を unchanged で再投入しない
- 各 phase の自己修正は 3 回まで
- 3 回失敗したら rollback 後に停止し user report する

## Gates

### Entry Gate

- archive snapshot / current baseline / rollback boundary が `README.md` / `PROGRESS.md` / `ROLLBACK.md` に固定されている
- owner scope が 1 file に閉じている
- phase hypothesis が pre-2026-04-02 records や completed package の旧 trial を unchanged で再投入していない

### Pass Gate

- owner-local tests pass
- shared checks pass
- current success path regression なし
- rollback note 更新済み
- visible red symptom が warning-only success ではなく、trim / block / fail-closed のいずれかで説明できる

### Stop Gate

- 同一 phase で 3 回失敗
- current success path regression
- rollback 不可能な diff が必要
- planner / generator core を reopen しないと進めない

## Shared Checks

### Output Formatter Owner

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q
```

### Output Guard / Runner Boundary

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_runner.py -q
```

### UI Warning Surface

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_note_writer_app_generation_execution_helpers.py -q
```

### Focused Pipeline

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q
```

### Current Mainline Boundary

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py note\tests\test_simple_note_quality_guard.py -q
```

## Phase Map

### Phase 00 Archive Boundary And Current Snapshot Freeze

- Objective:
  - pre-2026-04-02 work records を archive-only に固定し、current visible baseline を docs に固定する
- Owner:
  - package docs + archive snapshot only
- Exit:
  - separate window の read order が current package + archive snapshot + completed/frozen refs に閉じる

### Phase 01 Output Formatter Title Integrity Trim

- Objective:
  - malformed title を作る stitched fallback を `output_formatter.py` owner で narrow に減らす
- Hypothesis:
  - `_resolve_output_title()` -> `_compact_title()` の fallback を trim し、empty / weak title path を body-derived compact seed か fail-closed label に寄せれば、visible red title を prompt accretion なしで止められる
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- Tasks:
  - latest visible red title の generation path を focused test で固定する
  - explanatory title fallback の stitched join を削る / thin にする
  - weak title / empty topic path を user-visible red にならない narrow contract に寄せる
- Exit:
  - latest red title shape が focused test で再現しなくなる

### Phase 02 Output Guard Visible Boundary Hardening

- Objective:
  - user-visible red symptom を `output_guard.py` owner で warning-only success の外へ出す
- Hypothesis:
  - title integrity と selected visible monotony symptom を final artifact check の blocking reason に寄せれば、UI success path を増やさずに red output を減らせる
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
- Tasks:
  - title integrity 用の narrow guard を追加する
  - visible red symptom だけを soft warning から block / hard-fail 側へ寄せる
  - observe-only 指標と blocking 指標を混ぜない
- Exit:
  - malformed title / severe visible monotony が warning-only success では残らない

### Phase 03 UI Warning Surface Trim

- Objective:
  - Phase 02 後も user-visible red symptom が warning-only success で render される場合だけ、UI surface を narrow に trim する
- Hypothesis:
  - `note_writer_app.py` の success projection を guard decision に合わせて narrow に切れば、visible red symptom の render path を閉じられる
- Owner:
  - `C:\tetie\notecode\note\note_writer_app.py`
- Entry condition:
  - Phase 02 後も selected symptom が block されず、UI warning-only success で render される場合だけ開始する
- Exit:
  - selected symptom が UI success path に残らない

## Retry Discipline

- 同一 phase で 3 回失敗したら rollback して停止する
- failed hypothesis は `PROGRESS.md` と `ROLLBACK.md` に明記する
- prompt-only strengthening は retry option に入れない
