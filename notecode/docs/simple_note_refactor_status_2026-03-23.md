# simple note refactor status 2026-03-23

最終更新: 2026-03-23  
対象: `C:\tetie\notecode\plan\simple_note_refactor_2026-03-22` の close-state 確認  
スコープ: completed package の凍結状態、runtime mainline との関係、次の narrow fix 境界の整理

## 目次

- 1. Snapshot
- 2. Current Source of Truth
- 3. Completed / Pending Initiative の切り分け
- 4. Regression / Live Evidence
- 5. Article Type ごとの品質要約
- 6. 改善済み / 未解決
- 7. Dead Code / Quarantine / Retirement
- 8. 次に触るならどの owner か
- 9. やってはいけないこと

## 1. Snapshot

- `simple_note_refactor_2026-03-22` は 2026-03-22 時点で `completed`。
- current runtime mainline は `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`。
- current runtime architecture は次で固定済み。
  - source digest
  - single-pass body generation
  - deterministic note postprocess / rule check
  - light / score-based quality guard
  - optional single repair 1回
  - output / telemetry
- fixed rule:
  - free text は残す
  - question flow は unresolved slot 補完に限定する
  - `## 目次` は markdown に留める
  - note rule check は validator で必須
- compatibility import path は `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`。
- close-state の意味は「plan package を reopen せず、症状起点の narrow fix だけを別 initiative で扱う」こと。

## 2. Current Source of Truth

- refactor package 正本:
  - `C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\README.md`
  - `C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\PROGRESS.md`
- close-state read order:
  - `C:\tetie\AGENTS.md`
  - `C:\tetie\notecode\AGENTS.md`
  - `C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\README.md`
  - `C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\PROGRESS.md`
  - `C:\tetie\notecode\ALGORITHM.md`
  - `C:\tetie\WORKLOG.md`
- compat redirect は正本ではない。
  - `C:\tetie\notecode\plan\simple_note_pipeline_phase_plan_2026-03-22.md`
  - `C:\tetie\notecode\plan\simple_note_pipeline_refactor_progress_2026-03-22.md`
- archive / legacy plan は判断根拠に混ぜない。

## 3. Completed / Pending Initiative の切り分け

### Completed

- Phase00 Plan Lock And Rules
- Phase01 Archive Boundary And Baseline Freeze
- Phase02 Human Corpus And Learner Foundation
- Phase03 Writing Profile And Visible UI Cleanup
- Phase04 Prompt Slimming
- Phase05 Postprocess Formatter And Note Rule Validator
- Phase06 Quality Guard V2
- Phase07 Module Slimming
- Phase08 Handoff Freeze

### Pending だが refactor package の対象外

- current mainline quality threshold 改善
- `branding/company_introduction` の human gate
- vNext/current integration Phase05
- Phase 6 retirement
- quarantine-only `Slice 10`

結論:

- completed 済みの simple note refactor と、未完了の quality / integration initiative を混在させない。
- 次の runtime narrow fix が必要でも、まず reopen 先は refactor package ではなく current quality 側の owner で判断する。

## 4. Regression / Live Evidence

### 2026-03-23 local regression

- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py note\tests\test_simple_note_postprocess.py -q`
  - `8 passed`
- compatibility / current mainline 側の fresh check:
  - `test_current_mainline_runner.py` + `test_current_mainline_regressions.py` + `test_current_mainline_ui_matrix.py`
    - `67 passed`
  - `test_current_mainline_model_compare_tool.py` + `test_newalgorithm_phase06_logging_compat.py`
    - `32 passed`

### 2026-03-22 recent live output

- rejected evidence:
  - `C:\tetie\notecode\logs\current_mainline_ui_short_matrix_phase05_live_recollect_run01_20260322.json`
  - `branding/company_introduction` が `POL_PROMPT_ECHO`
- accepted evidence:
  - `C:\tetie\notecode\logs\current_mainline_ui_short_matrix_phase05_live_recollect_run02_20260322.json`
  - `C:\tetie\notecode\logs\current_mainline_ui_short_matrix_phase05_live_recollect_run03_20260322.json`
  - いずれも `10/10 success`、retry `0`、fallback `0`
  - `rubric_mean_total=7.9`
- compare evidence:
  - `C:\tetie\notecode\logs\current_mainline_model_compare\20260322-225926\summary.json`
  - `gpt-5.4-mini short_mean=6.6`
  - `gpt-4.1-mini-2025-04-14 short_mean=4.8`

読み替え:

- refactor package は runtime stability を達成している。
- 未解決は architecture 破綻ではなく、quality threshold と article-type fit の残差である。

## 5. Article Type ごとの品質要約

| article type | current quality | refactor 観点の判断 |
|---|---|---|
| `explanatory_article` | `8/10`、gate pass | pipeline / formatter / validator は安定。残差は本文の flatness |
| `daily_story` | `8-9/10`、gate pass | source 薄めケースでも mainline が崩れない。補足の入れ過ぎは禁物 |
| `branding` | `8/10`、gate pass だが echo 感度高い | refactor は route を壊していない。残る論点は wording / carry 配分 |
| `announcement` | `8/10`、gate pass | note rule check は効いている。dense must-cover は本文反映がまだ弱い |
| `case_study` | `8/10`、gate pass | structure は改善済み。再現条件と must_cover の密度がまだ足りない |
| `industry_analysis` | `8/10`、gate pass |論点整理は通る。nominalization / ending repetition が残る |
| `comparative_review` | standard `8/10`、axis-lock `7/10` | refactor 本体ではなく article-type fit の配分課題。最優先の narrow residual |

共通 residual:

- スタイロメトリ
- 統計言語学
- paragraph / rhythm / ending distribution / repetition control
- must_cover の本文反映
- article type ごとの fit

## 6. 改善済み / 未解決

### 改善済み

- 本文 mainline を `single-pass + optional single repair 1回` に固定できた。
- `## 目次` と note rule check を validator で必須化できた。
- prompt slimming と module slimming の完了状態を維持している。
- score-based quality guard と repair trigger の枠組みは stable。
- accepted live runs では retry / fallback drift が 0。

### 未解決

- `rubric_mean_total >= 8.0` の cross-type 達成は未完。
- almost all types で `partial_contract_reflection` と `flat_or_repetitive` が残る。
- announcement / case_study の `must_cover_reflection_rate` が `0.6667` に留まる。
- comparative axis lock は `comparative_axis_soft_shift` が残る。
- `latest_generation_output.*` の freshness が 2026-03-13 で止まっている。

## 7. Dead Code / Quarantine / Retirement

- refactor completed 後も legacy は quarantine 扱い。
- `note/legacy_current/` は helper / compat 用 entry として残すが、本文 mainline の source of truth ではない。
- `ArticleGenerator`、`human_resonance*`、`vnext` は本文 mainline owner に戻さない。
- Phase 6 retirement は未着手で、simple note refactor completed 状態と混ぜない。
- `Slice 10` quarantine-only reopen は default next action にしない。

## 8. 次に触るならどの owner か

- completed package を reopen するのではなく、quality residual の owner を触るべき。
- 本命 owner は `C:\tetie\notecode\note\natural_blog_core.py`。
  - refactor package が解いたのは orchestration / prompt / validator / guard の構造問題。
  - いま残っているのは article-type fit、anchor / carry、rhythm、ending distribution の本文品質問題。
- refactor-owned module を触る必要があるなら最小候補は `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`。
  - 用途は計測の補助だけ。
  - repair path 増設、guard の肥大化、module の再分裂は不可。

## 9. やってはいけないこと

- prompt accretion
- module accretion
- 文字数を増やすこと自体を目的にすること
- source にない断定的な補足を足すこと
- completed の simple note refactor package を勝手に reopen すること
- prompt で must_cover 取りこぼしを埋めようとして rule / module を増やすこと
- old `ArticleGenerator` / `human_resonance*` / `vnext` を本文 mainline に戻すこと
- source が薄い場合に reader-helpful の範囲を超えて事実を補うこと
