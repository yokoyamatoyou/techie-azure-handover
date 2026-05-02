# pipeline current first triage stop report 2026-04-18

## Position

- この文書は `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` owner の `PIPELINE_CURRENT_FIRST_TRIAGE` 実行結果を固定する stop report である
- current source-of-truth update の補助 result doc であり、production diff の keep を意味しない
- production code / tests の kept diff はない

## Summary

- blocked task:
  - `pipeline.py` owner だけで company intro opener の current-first anchor を upstream source ordering / hint ownership で安定化すること
- completed work:
  - 指定 read order の正本と result docs を読了
  - `pipeline.py` と discourse-planner 側の opener 関与点を確認
  - same owner hypothesis を 3 回まで試行
  - owner-local tests / shared checks / live validation を実施
  - fail 判定後に `pipeline.py` と追加 test diff は rollback 済み
- final kept diff:
  - なし

## Fixed Read

- focused / shared checks では current success path の明確な regression は出ていない
- ただし mandatory gate は `V3 company intro guard`
- `V3` は variance を含めて最後まで通らなかった
- title / first heading / first section のいずれかが history-first に戻る variance を owner-local では止めきれなかった

## Attempts

### Attempt 1

- discourse-plan 用 contract で current-first slot order を優先させる narrow diff を実装
- focused tests は通過
- live では `V3` が history-first のまま fail

### Attempt 2

- history/current mixed source に対する planning bucket ownership を追加補正
- focused/shared は通過
- live matrix では `V3` が 3 runs 中 2 runs history-first

### Attempt 3

- section 1 への history 再流入を抑えるため source bucket / ordering をさらに絞った
- focused/shared は通過
- final live matrix では `V3` が 3 runs 中 3 runs で title か first heading が history-first
- rollback して停止

## Validation Read

- `V1`:
  - `2/2 non-worse`
- `V2`:
  - `1/1 non-worse`
- `G1`:
  - `2/2 no visible regression`
- `V3`:
  - `3/3 fail`
  - title または first heading が history-first に戻った

## Management Implication

- `pipeline.py` 単独 reopen は same owner hypothesis 3 failures に到達した
- `pipeline.py` current-first triage の unchanged retry は current prompt として使わない
- current source-of-truth 上の next owner は未確定に戻し、management judgment を先に更新する必要がある
- 次の separate execution を直ちに implementation に進めるのではなく、management prompt で next owner / next narrow hypothesis / block を再判定する

## Non-Updates

- AGENTS は更新していない
- WORKLOG はこの result note 単体では更新していない
- current package docs はこの result note 単体では更新していない
