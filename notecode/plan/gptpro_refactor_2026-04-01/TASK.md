# gptpro_refactor_2026-04-01 TASK

このファイルは phase ごとの実行単位、gate、retry-stop、final visual loop を固定する。  
`1 phase = 1 narrow hypothesis = 1 owner scope` を崩さない。

## Global Rules

- current success path を壊さない
- prompt accretion 禁止
- module accretion 禁止
- `human_resonance*` は初手で触らない
- rollback 可能な narrow diff だけを許可する
- 各 phase の自己修正は 3 回まで
- 3 回失敗したら停止して user report する
- failed hypothesis は rollback 後に `ROLLBACK.md` と `PROGRESS.md` へ残し、そのまま再投入しない

## Gates

### Entry Gate

- baseline と rollback boundary が `README.md` / `ROLLBACK.md` / `PROGRESS.md` に明文化されている
- owner scope が 1 つに閉じている
- current success path を壊していない

### Pass Gate

- phase-specific owner-local tests pass
- shared regression checks pass
- blocked hypothesis を踏んでいない
- rollback note を更新済み

### Auto-Advance Gate

- `PROGRESS.md` に evidence と next phase を書いた
- next phase の hypothesis / owner scope / attempts_used が初期化されている

### Stop Gate

- 同一 phase で 3 回失敗
- current success path regression
- rollback 不可能な diff が必要
- failed hypothesis のそのまま再投入が必要になった

### Completion Gate

- 全 phase 完走
- 3 文書生成
- Codex 目視確認
- 問題があれば最大 4 ループまで修正 + 再生成
- 同一ループで 3 本とも問題なし

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

## Phase Map

### Phase 00 Baseline Freeze

- Objective:
  - baseline / rollback boundary / blocked hypotheses / kept state を固定する
- Owner:
  - package docs only
- Tasks:
  - source-of-truth priority を固定
  - current success path を固定
  - compare kept state と failed hypothesis boundary を固定
- Exit:
  - baseline と rollback boundary が明文化されている

### Phase 01 Responsibility Inventory

- Objective:
  - meaning-layer / surface-layer / repair / observability の責務表を作る
- Owner:
  - package docs only
- Tasks:
  - `input_contract.py`
  - `prompt_builder.py`
  - `simple_note_pipeline/pipeline.py`
  - `quality_guard.py`
  - `rendering.py`
  - `quality_observability_mixin.py`
  - `output_formatter.py`
    を responsibility table へ落とす
- Exit:
  - 次 phase の owner scope が 1 file に絞れている

### Phase 02 Contract Narrow Hardening

- Objective:
  - shadow spec に必要な contract を既存 field だけでより明示的にする
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
  - owner-local tests
- Tasks:
  - existing focus / must_cover / comparison / register / pronoun data を bounded internal bundle に整理する
  - new public field を増やさない
- Required Checks:
  - owner-local contract tests
  - Focused Pipeline
  - Quality Guard
  - Current Mainline Boundary
- Exit:
  - later phase が複数 field を寄せ集めずに 1 つの internal summary を参照できる
- Rollback:
  - `input_contract.py` の narrow diff を戻す

### Phase 03 Section Shadow Spec

- Objective:
  - section 単位の shadow representation を導入する
- Owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - owner-local tests
- Tasks:
  - existing semantic ledger と contract summary から section shadow 入力を導出する
  - new module は増やさない
- Required Checks:
  - owner-local prompt builder tests
  - Focused Pipeline
  - Quality Guard
  - Current Mainline Boundary
- Exit:
  - shadow representation が prompt builder owner 内で完結する
- Rollback:
  - shadow representation の導出と prompt 注入を戻す

### Phase 04 Controlled Realization

- Objective:
  - shadow -> prose の順序と drift 防止を固定する
- Owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - owner-local tests
- Tasks:
  - shadow がある場合だけ controlled realization を有効化する
  - fail-open fallback を維持する
- Required Checks:
  - owner-local pipeline tests
  - Focused Pipeline
  - Quality Guard
  - Current Mainline Boundary
- Exit:
  - shadow 不成立でも current success path に戻れる
- Rollback:
  - controlled realization gate を閉じる

### Phase 05 Local Patch Alignment

- Objective:
  - flagged span patch を GPTPRO 方針に合わせる
- Owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - owner-local tests
- Tasks:
  - claim / anchor を壊さない局所 patch 指示へ寄せる
  - full rewrite fallback を増やさない
- Required Checks:
  - owner-local prompt builder tests
  - Focused Pipeline
  - Quality Guard
  - Current Mainline Boundary
- Exit:
  - patch が local repair のまま動く
- Rollback:
  - local patch alignment 文面を戻す

### Phase 06 Comparative Stabilization

- Objective:
  - residual compare case を新構造で再挑戦する
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - owner-local tests
- Tasks:
  - target は `st-comparative-cross-department` のみ
  - failed `section_generator.py` slimming は再投入しない
  - failed `discourse_planner.py` hypothesis は unchanged で再投入しない
- Required Checks:
  - owner-local compare tests
  - Focused Pipeline
  - Quality Guard
  - Current Mainline Boundary
  - targeted rerun 3 回
- Exit:
  - targeted rerun 3/3 安定
- Rollback:
  - compare-specific narrow diff を戻す

### Phase 07 Sentinel Sweep

- Objective:
  - branding / announcement / case_study / comparative の regression 確認
- Owner:
  - code edit なし想定
- Tasks:
  - `tools/run_current_mainline_genre_sweep.py --phase genre-rerun --live --genres branding,announcement,case_study,comparative_review`
- Required Checks:
  - Current Mainline Boundary
- Exit:
  - kept state regression なし

### Phase 07a Branding Title Prompt Echo Fix

- Objective:
  - `bl-branding-values-stance` の title prompt echo を `output_formatter.py` owner だけで解消する
- Hypothesis:
  - `_prefer_generated_title` に topic-overlap + mid-title sentence boundary ガードを追加すれば、LLM が prompt_raw をそのまま title に生成した場合を reject し、`_compact_title` fallback で適切な title を出せる
- Owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
  - owner-local tests
- Tasks:
  - `_is_title_prompt_echo(title, topic)` helper を追加
  - `_prefer_generated_title` に `topic` kwarg とガードを追加
  - `format_output` から `topic` を渡す
- Required Checks:
  - owner-local tests
  - Focused Pipeline
  - Quality Guard
  - Current Mainline Boundary
  - 4 genre sentinel rerun
- Exit:
  - `bl-branding-values-stance` の title が prompt echo ではない
  - 他 genre の regression なし
- Rollback:
  - `_is_title_prompt_echo` helper と `_prefer_generated_title` の topic ガードを戻す

### Phase 08 Final Live And Visual Loop

- Objective:
  - 3 文書生成 + Codex 目視確認 + 最大 4 ループ
- Fixed Cases:
  - `st-comparative-cross-department`
  - `ui-short-announcement-dense-must-cover`
  - `ui-short-case-study-explain`
- Tasks:
  - 3 本生成する
  - `.json` と `.txt` を目視確認する
  - 問題があれば `1 loop = 1 owner scope` で修正する
  - 再生成する
- Required Checks:
  - shared checks
  - fixed 3 cases rerun
- Exit:
  - 1 ループで 3 本とも問題なし

## Final Visual Loop

### Run Command

```text
C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\tools\run_current_mainline_genre_sweep.py --phase genre-rerun --live --case-ids st-comparative-cross-department,ui-short-announcement-dense-must-cover,ui-short-case-study-explain
```

### Loop Rule

1. 3 本生成する
2. Codex が目視確認する
3. 問題があれば 1 owner scope だけ修正する
4. shared checks を再実行する
5. 3 本を再生成する
6. 最大 4 ループまで
7. 1 ループで 3 本とも問題なしなら完了
8. 4 ループで安定しなければ residual を記録して停止
