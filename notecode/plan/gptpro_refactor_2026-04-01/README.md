# gptpro_refactor_2026-04-01

`C:\tetie\notecode\GPTPRO.txt` を判断材料にしつつ、current kept state を壊さず rollback 可能な narrow phase で進める current execution package。

## Objective

- current success path を維持したまま、meaning-layer / surface-layer 分離を `rollback 可能な新 refactor package` として再始動する
- model 未定のままでも進められるよう、各 phase を mini で扱える narrow 粒度に固定する
- phase pass 後だけ自律的に次 phase へ進み、3 回失敗したら停止して user report する

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\README.md`
4. `C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\TASK.md`
5. `C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\PROGRESS.md`
6. `C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\ROLLBACK.md`
7. `C:\tetie\notecode\ALGORITHM.md`
8. `C:\tetie\WORKLOG.md`
9. `C:\tetie\notecode\GPTPRO.txt`
10. `C:\tetie\notecode_current_mainline_handoff_2026-03-31.md`

## Source-Of-Truth Priority

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\README.md`
4. `C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\TASK.md`
5. `C:\tetie\notecode\plan\gptpro_refactor_2026-04-01\PROGRESS.md`
6. `C:\tetie\notecode\ALGORITHM.md`
7. `C:\tetie\WORKLOG.md`
8. `C:\tetie\notecode\GPTPRO.txt`

## Global Policy

- root `AGENTS.md` は入口のまま維持し、詳細仕様はこの package と service docs 側へ寄せる
- current success path を壊さない
- prompt accretion をしない
- rollback 不可能な大改修をしない
- 1 phase で複数 mechanism を触らない
- 失敗した仮説をそのまま再投入しない
- `human_resonance*` を初手で触らない
- phase pass 条件には `PROGRESS.md` 更新を含める

## Current Success Path

- `C:\tetie\notecode\note\current_mainline_runner.py`
- `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## Current Kept State

- `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
  - compare axis normalization fix
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - compare opener / ranking soften
- `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
  - tool-compare abswinner narrow fix
- `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
  - compare repeated ending diversification の安全版

## Baseline

- `C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\` は completed baseline として扱う
- `C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\` は freeze 済み package として reopen しない
- current compare path の kept state / residual / failed hypothesis boundary は
  - `C:\tetie\notecode_current_mainline_handoff_2026-03-31.md`
  - `C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-01.md`
  を参照する

## Non-Goals

- `simple_note_refactor_2026-03-22` の reopen
- compare 専用 module / class の追加
- semantic gate の早期 reopen
- `gpt-5.4` promotion の先行決定
- unrelated genre への横展開
- root `AGENTS.md` への詳細仕様追記
