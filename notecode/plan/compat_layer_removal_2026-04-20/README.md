# compat_layer_removal_2026-04-20 README

## Objective

- SaaS 化に向けて current runtime path から `note/newalgorithm_pipeline/pipeline.py` の互換レイヤを外し、`note/current_mainline_runner.py -> note/simple_note_pipeline/pipeline.py` の直結経路へ寄せる
- 直結化のあとで、互換レイヤと legacy compatibility surface の dead code 候補を安全に棚卸しする
- 旧経路を感覚で削らず、runtime path / test path / tool path の実参照を先に確定する

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\compat_layer_removal_2026-04-20\README.md`
4. `C:\tetie\notecode\plan\compat_layer_removal_2026-04-20\TASK.md`
5. `C:\tetie\notecode\plan\compat_layer_removal_2026-04-20\PROGRESS.md`
6. `C:\tetie\notecode\plan\compat_layer_removal_2026-04-20\EXECUTION_PROMPT.md`
7. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
8. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
9. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
10. `C:\tetie\WORKLOG.md`

## Source Of Truth

- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- current runtime mainline:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- compatibility import path still on success path:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- current UI shell entry:
  - `C:\tetie\notecode\note\note_writer_app.py`
- current logs / visible artifact:
  - `C:\tetie\notecode\logs\latest_generation_output.json`
  - `C:\tetie\notecode\logs\latest_generation_quality_report.json`
  - `C:\tetie\notecode\logs\app.log`

## Current Decision

- `simple_note_pipeline` が現行の実体である
- `newalgorithm_pipeline` は削除済みではなく、current success path 上の compatibility wrapper として残っている
- SaaS 化の観点では、互換レイヤを通したまま dead code 削除を始めるのは危険
- 先に runtime path を直結化し、その後に compatibility surface を縮める

## Compressed Context

- `naturalness_recovery_2026-04-07` package は company intro / fail-closed keep の current judgment を固定する package であり、今回の目的ではない
- 上記 package から今回必要なのは以下だけ:
  - current success path はまだ `newalgorithm_pipeline -> simple_note_pipeline` を通る
  - current mainline を壊さない
  - `1 phase = 1 narrow hypothesis = 1 owner scope`
  - prompt / module accretion を避ける
- `docs/simple_note_pipeline_company_intro_current_business_first_recovery_prompt_2026-04-18.md` は company intro guard recovery 用であり、compat layer removal の source-of-truth にはしない
- 非直近の separate-window prompt 群は archive 的 evidence として扱い、この package では再要約しない

## Non-Goals

- company intro fail-closed guard の再調整
- UI wizard / required input 修正
- `simple_note_pipeline` 内部の品質ロジック整理
- 大規模リファクタ
- docs 一括整理

## Package Shape

- Phase 01:
  - runtime path の責務棚卸し
  - `current_mainline_runner` 直結化の可否判定
- Phase 02:
  - `newalgorithm_pipeline` を success path から外す最小 diff
- Phase 03:
  - compatibility surface / dead code 候補一覧化
- Phase 04:
  - 削除してよい dead code を narrow diff で落とす別 implementation lane へ渡す

## Why This Package

- 今の repo では `newalgorithm_pipeline` は dead code ではなく compatibility path である
- そのため、SaaS 向けの整理は「削除」から入るより「直結化」から入るほうが安全
- current package の company intro / naturalness 系判断を汚さず、runtime boundary だけを narrow に扱える
