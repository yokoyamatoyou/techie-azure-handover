# simple_note_refactor_2026-03-22

対象: `C:\tetie\notecode`  
状態: current_refactor_plan  
目的: `note` 向け本文 mainline を、single-pass を維持したまま人間らしさ重視で再設計する

## Read Order

1. `C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\README.md`
2. `C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\PROGRESS.md`
3. `C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\EXECUTION_PROMPT_DEFAULT_MODE.md`
4. `C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\PHASE_00_PLAN_LOCK_AND_RULES.md`
5. current phase の phase 文書
6. `C:\tetie\notecode\ALGORITHM.md`
7. `C:\tetie\WORKLOG.md`

## Current Decisions

- 本文 mainline は `single-pass + optional single repair 1回` を維持する
- `## 目次` は markdown に留める
- note rule check は validator で必須化する
- human corpus / learner は first track で入れる
- learner の初期モデルは `RandomForest`
- visible UI は first track で最小整理する
- branding は `subtype=company/product/service` と `focus=4種` で扱う
- prompt accretion と module accretion を禁止する

## Package Map

- `README.md`
  - この計画パッケージの入口
- `PROGRESS.md`
  - current status / next slice / blocker / update rule
- `EXECUTION_PROMPT_DEFAULT_MODE.md`
  - 別ウインドウでそのまま使える実行開始 prompt
- `PHASE_00_PLAN_LOCK_AND_RULES.md`
  - refactor の共通ルールと完了定義
- `PHASE_01_ARCHIVE_BOUNDARY_AND_BASELINE_FREEZE.md`
  - pre-refactor archive 分離と baseline 固定
- `PHASE_02_HUMAN_CORPUS_AND_LEARNER_FOUNDATION.md`
  - human corpus と learner 基礎
- `PHASE_03_WRITING_PROFILE_AND_VISIBLE_UI_CLEANUP.md`
  - profile resolver と UI 最小整理
- `PHASE_04_PROMPT_SLIMMING.md`
  - prompt 置換と短縮
- `PHASE_05_POSTPROCESS_FORMATTER_AND_NOTE_RULE_VALIDATOR.md`
  - formatter / validator / deterministic local edit
- `PHASE_06_QUALITY_GUARD_V2.md`
  - AIIndex と legal guard v2
- `PHASE_07_MODULE_SLIMMING.md`
  - orchestration 以外の責務分離
- `PHASE_08_HANDOFF_FREEZE.md`
  - close / handoff / archive の固定

## Global Rules

- 1 slice で同時に 2 phase 進めない
- 1 slice の changed files は原則 5 file 以内
- 新規 runtime file 追加は `replacement` とセットで行う
- `note/simple_note_pipeline/` の runtime file は `__init__.py` を除いて最大 6 本
- free text は残す
- pattern select は追加してよい
- current interview / question flow は generic brainstorming ではなく unresolved slot 補完に使う

## Completion Definition

各 phase は次の 4 系統の自己テストが通るまで completed にしない。

1. functional
   - phase で意図した機能差分が出ている
2. prompt injection / policy
   - 自由入力や source で prompt injection を誘発していない
3. anti-bloat
   - prompt と module が肥大化していない
4. readability / owner boundary
   - file 責務が読みやすく、owner boundary を壊していない

## Error Handling Rule

- 実装中にエラーや失敗が出た場合は、その場で最大 2 回まで修正を試みる
- 2 回で解消しない場合は、その phase を `blocked` にする
- `blocked` のまま scope を広げず、ユーザーへ停止理由を報告する

## Pre-Refactor Boundary Rule

- pre-refactor 情報は archive 側へ退避し、current refactor の plan / progress / logs と混在させない
- current refactor の正本はこの package 配下だけに置く
- compat 用の旧 path は redirect 文書に留める

## Compatibility Paths

- `C:\tetie\notecode\plan\simple_note_pipeline_phase_plan_2026-03-22.md`
  - この package への redirect
- `C:\tetie\notecode\plan\simple_note_pipeline_refactor_progress_2026-03-22.md`
  - `PROGRESS.md` への redirect
