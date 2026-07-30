# persona_iterative_trial_2026-04-23

## 目次
- objective
- scope
- read order
- owner route
- non-goals

## objective
- current mainline だけで hidden contract を使った persona iterative trial を実装し、7 article type sweep を separate initiative として回せる状態にする。
- global source-of-truth は `naturalness_recovery_2026-04-07` のまま維持する。
- visible output に persona 名 / trial 名 / source contract 名を出さず、craft guard / repair guard / trial telemetry に圧縮する。

## scope
- 実装 owner route は `C:\tetie\notecode\note\note_writer_app.py -> C:\tetie\notecode\note\current_mainline_runner.py -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- planning package owner は `C:\tetie\notecode\plan\persona_iterative_trial_2026-04-23\`
- run artifact root は `C:\tetie\notecode\新しいフォルダー\新しいフォルダー (5)\persona_iterative_trial_window_run\`
- hidden runtime fields
  - `_persona_contract`
  - `_source_packet`
  - `_persona_trial`
- trial acceptance では `一般読者` default fallback を valid pass とみなさない。

## read order
1. `C:\tetie\notecode\plan\persona_iterative_trial_2026-04-23\README.md`
2. `C:\tetie\notecode\plan\persona_iterative_trial_2026-04-23\TASK.md`
3. `C:\tetie\notecode\plan\persona_iterative_trial_2026-04-23\PROGRESS.md`
4. `C:\tetie\notecode\plan\persona_iterative_trial_2026-04-23\ROLLBACK.md`
5. `C:\tetie\notecode\plan\persona_iterative_trial_2026-04-23\EXECUTION_PROMPT.md`
6. `C:\tetie\notecode\docs\persona_source_generation_contract_master_plan_2026-04-23.md`
7. `C:\tetie\notecode\ALGORITHM.md`

## owner route
- contract build / re-resolve / telemetry
  - `C:\tetie\notecode\note\current_mainline_runner.py`
- hidden contract family and source packet helpers
  - `C:\tetie\notecode\note\current_mainline_persona_trial.py`
- generation / repair guard consumption
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- runtime source contract to hidden source packet mapping
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- trial driver / manifests / log bootstrap
  - `C:\tetie\notecode\note\persona_iterative_trial_tooling.py`
  - `C:\tetie\notecode\tools\run_persona_iterative_trial.py`

## non-goals
- `C:\tetie\notecode\note\article_generator.py` の修正
- `C:\tetie\notecode\note\article_style_persona_mixin.py` の修正
- legacy persona shim の再利用や reopen
- UI default audience の変更
- `single-pass + optional single repair 1回` の変更
- prompt / visible output への persona / trial / source_contract 露出
