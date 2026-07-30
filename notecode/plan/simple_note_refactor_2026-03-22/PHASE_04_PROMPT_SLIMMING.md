# PHASE 04 PROMPT SLIMMING

状態: pending  
目的: prompt を短くしつつ制御力を落とさない

## In Scope

- generation prompt の fixed 6 block 化
- repair prompt の fixed 4 block 化
- prose duplication の削減

## Out Of Scope

- prompt の機能追加
- phase 5 以降の validator 実装

## Planned Outputs

- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- prompt snapshot artifacts

## Tasks

1. current prompt を block 単位で分解する
2. article type 差分を profile table 側へ寄せる
3. repair prompt を issue-driven にする
4. prompt 長を baseline 比で 30%以上削減する

## Self-Test

- functional
  - quality を落とさず prompt が短い
- prompt injection / policy
  - rule を prose で足していない
- anti-bloat
  - new block を追加していない
- readability / owner boundary
  - prompt builder が独立して読める

## Exit Criteria

- generation prompt が baseline 比 30%以上短い
- repair prompt が issue-driven
- prompt accretion が発生していない

## Retry Rule

- snapshot 差分や品質低下は 2 回まで修正
- 2 回で戻らなければ blocked にして report
