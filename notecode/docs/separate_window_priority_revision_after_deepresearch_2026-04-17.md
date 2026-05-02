# separate window priority revision after deepresearch 2026-04-17

## Purpose

- Claude Opus 4.7 deepresearch を受けて、
  separate lines の優先順位を source-of-truth 本体を書き換えずに整理する

## Revised Priority

### Priority 1

- `sentence-final pattern monotony cap + single repair`

#### Why

- 日本語特有の visible AI-feel に直結しやすい
- current baseline の既知 symptom と整合する
- detection signal が比較的明確
- `single-pass + optional single repair 1回` に自然に入る
- route default / planner default を変えずに試せる

### Priority 2

- `reference realization policy` の compare-only continuation

#### Why

- 重要な問題設定ではある
- ただし current framing の 3-policy bundle は強くない
- 特に `subject_reintroduction_policy` は再設計前提

### Priority 3

- discourse / paragraph seam line
  - centering-like boundary checks
  - connective diversity
  - paragraph seam control

#### Why

- promising だが telemetry / dataset / narrower framing が必要

## Compare Impact

- 既存の `reference realization policy` compare plan は破棄しない
- ただし意味づけを変更する
  - `next likely production line`
    ではなく
  - `separate evidence check`
    として扱う

## Production Gate Revision

- compare 後に `GO` が出ても、
  即 `reference realization policy` を first production owner にしない
- compare 結果は
  - `この line を完全に捨てるか`
  - `後順位の separate candidate として keep するか`
  の判断に使う

## New Proposed Working Order

1. deepresearch reflection memo を keep
2. `reference realization policy` compare を実施するか、management で skip するか判断
3. 並行してではなく、次の planning line を
   `sentence-final monotony cap + single repair`
   に切り替える
4. その line で prompt / telemetry / repair scope の narrow proposal を作る
5. そこで初めて production owner 候補を検討する

## No-Go Triggers

- deepresearch を理由に giant rewrite を始める
- 文末 line を理由に formatter-only polish へ流れる
- 文末 line を理由に hidden reviser を増やす
- `reference realization policy` compare の勝敗を mock path や metrics だけで決める

## Management Summary

- `reference realization policy` は evidence line として keep
- next main line は `sentence-final monotony cap + single repair`
- current source-of-truth はまだ変更しない

