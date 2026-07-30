# compat_layer_removal_2026-04-20 PROGRESS

## Current Goal

- `newalgorithm_pipeline` を current success path から外す準備として、implementation-ready な narrow package を固定する

## Current Status

- Package status:
  - active
  - docs_ready
  - implementation_not_started
- Current phase:
  - phase 01 runtime responsibility map
- Status:
  - `READY_FOR_SEPARATE_WINDOW_DIRECT_PATH_TRIAGE`

## Fixed Read

- 現行実体は `simple_note_pipeline`
- ただし success path はまだ `newalgorithm_pipeline` を通る
- よって `newalgorithm_pipeline` を dead code とみなして即削除するのは誤り
- separate window の first move は「削除」ではなく「直結化 feasibility 確認」

## Compressed Summary Of Older Context

- `naturalness_recovery_2026-04-07` docs は company intro / naturalness / fail-closed keep の package であり、互換レイヤ撤去の source-of-truth ではない
- そこから引き継ぐ実務上の制約は以下だけ:
  - current success path を壊さない
  - owner scope を narrow に保つ
  - current runtime mainline は `simple_note_pipeline`
  - compatibility import path は `newalgorithm_pipeline`
- 非直近の separate-window docs は archive 的背景であり、この package では参照列挙しない

## Owner Scope

- docs owner:
  - `C:\tetie\notecode\plan\compat_layer_removal_2026-04-20\README.md`
  - `C:\tetie\notecode\plan\compat_layer_removal_2026-04-20\TASK.md`
  - `C:\tetie\notecode\plan\compat_layer_removal_2026-04-20\PROGRESS.md`
- next implementation owner:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`

## Next Action

- separate window で Phase 01 を開始する
- まず `newalgorithm_pipeline` の runtime responsibilities を short map 化する
- `current_mainline_runner -> simple_note_pipeline` 直結の最小 diff 候補を出す
- その結果に応じて Phase 02 へ進む

## Suggested Separate-Window Prompt

```text
参照ルール:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\compat_layer_removal_2026-04-20\README.md
- C:\tetie\notecode\plan\compat_layer_removal_2026-04-20\TASK.md
- C:\tetie\notecode\plan\compat_layer_removal_2026-04-20\PROGRESS.md

今回の依頼:
- Phase 01 runtime responsibility map と Phase 02 direct path adoption を連続で扱ってよい
- 目的は current success path から newalgorithm compatibility layer を外すこと
- first move は削除ではなく直結化
- owner scope は current_mainline_runner.py と必要最小限の adapter に閉じる
- simple_note_pipeline の意味変更はしない
- findings first
- narrow diff
- shared checks を通す
```

## Open Risks

- `newalgorithm_pipeline` が wrapper 以上の runtime semantics を持っている可能性
- tests / tools が wrapper import に依存している可能性
- direct path 化で telemetry / output guard の取り回しが変わる可能性

## Docs Note

- この package は意図的に短く保っている
- 非直近の肥大 docs は source-of-truth に昇格させず、必要な判断だけここへ圧縮している
