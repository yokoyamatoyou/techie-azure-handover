# gptpro_refactor_2026-04-01 ROLLBACK

## Baseline

- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- current kept state:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- completed baseline package:
  - `C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\`

## Restore Targets

- restore priority 1:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- restore priority 2:
  - `C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\PROGRESS.md`
  - `C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\ROLLBACK.md`
  - `C:\tetie\WORKLOG.md`

## Per-Phase Rollback Boundary

- Phase 00:
  - docs only。package files の baseline 記述を戻せばよい
- Phase 01:
  - docs only。responsibility inventory を戻せばよい
- Phase 02:
  - `input_contract.py` の narrow diff のみ戻す
- Phase 03:
  - `prompt_builder.py` の shadow spec 導出と prompt injection points のみ戻す
- Phase 04:
  - `simple_note_pipeline/pipeline.py` の controlled realization helper / `shadow_section_drift` span / `pipeline_check.body_generation.controlled_realization` 注入のみ戻す
- Phase 05:
  - `prompt_builder.py` の repair-side `SECTION_SHADOW` block と `shadow_patch` scope lines のみ戻す
- Phase 06:
  - `newalgorithm_pipeline/pipeline.py` の cross-department closing stabilizer / comparative final-body editor-guard reapply / stage-diagnostic report split のみ戻す
- Phase 07:
  - `newalgorithm_pipeline/pipeline.py` の announcement target-section prompt-echo stabilizer と announcement final-body editor-guard reapply のみ戻す
- Phase 07a:
  - `output_formatter.py` の `_is_title_prompt_echo` helper と `_prefer_generated_title` の `topic` ガードのみ戻す
- Phase 08:
  - 1 loop で触った owner scope だけ戻す

## Do-Not-Retry Hypotheses

- compare source-grounding rollback 仮説の再投入
- `section_generator.py` の cross-department fit / caution / closing input slimming
- 2026-04-01 `discourse_planner.py` の cross-department axis-only seed narrowing を unchanged で再投入
- prompt echo detector 側の threshold 調整
- `output_formatter.py` の surface-only stopgap で compare residual を止血する案
- `prompt_builder.py` の wording tightening を積み増して押し切る案
- company introduction で `HARD_CONTRACT` に company voice / 見出し冒頭の話者再アンカーを直入れして押し切る案
- `prompt_builder.py` の compact plan schema に `span=lean|standard|thick` を足し、`SECTION_RHYTHM` block で section 配分を直指定して押し切る案
- `prompt_builder.py` の `HARD_CONTRACT` で「つながる説明は同じ段落でまとめる」を強く入れ、anti-fragment を paragraph bundling で押し切る案
- `discourse_planner.py` で `case_study change/condition` の source grounding を pair packing だけで押し切る案
- `discourse_planner.py` で `case_study` source grounding を sentence 粒度へ split して押し切る案
- `human_resonance*` 初手介入
- Phase 07 で `pipeline.py` の次に `output_formatter.py` へ owner scope を広げて続行する案

## Keep State To Preserve

- compare axis normalization fix
- compare opener / ranking soften
- tool-compare abswinner narrow fix
- compare repeated ending diversification の安全版
- semantic/surface migration で導入済みの omission / ending / patch path baseline

## Stop Conditions Requiring Rollback

- current success path regression
- owner scope が 1 file を超えて膨らむ
- shared checks failure
- targeted rerun 3 回で安定しない
- rollback note に反する failed hypothesis の再投入が必要になる
