# PHASE 07 MODULE SLIMMING

状態: pending  
目的: `pipeline.py` を orchestration に専念させ、module bloat を止める

## In Scope

- helper module への責務移動
- import graph の単方向化
- `pipeline.py` の短文化

## Out Of Scope

- runtime package の拡張
- UI redesign

## Planned Outputs

- slimmed `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- helper modules 一式

## Tasks

1. orchestration 以外の helper を外へ出す
2. result shape と progress API は維持する
3. circular import をなくす
4. file size / line count を budget に収める

## Budgets

- `pipeline.py <= 250 lines`
- runtime file count <= 6
- helper file 1 本あたりの責務を明確化

## Self-Test

- functional
  - mainline result shape が変わらない
- prompt injection / policy
  - security / validation が移動中に抜けていない
- anti-bloat
  - file 数や helper が増えすぎていない
- readability / owner boundary
  - file 名だけで責務が読める

## Exit Criteria

- `pipeline.py` が 250 lines 以下
- runtime package が 6 file 以内
- circular import なし

## Retry Rule

- import 崩れや contract 崩れは 2 回まで修正
- 2 回で解消しなければ blocked にして report
