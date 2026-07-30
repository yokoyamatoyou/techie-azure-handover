# PHASE 06 QUALITY GUARD V2

状態: pending  
目的: AIっぽさと legal risk を scorer で扱う

## In Scope

- heuristic metrics
- learner score
- AIIndex
- legal guard v2

## Out Of Scope

- heavy post-rewrite
- model fallback policy 変更

## Planned Outputs

- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\note\simple_note_pipeline\style_learner.py`
- quality artifacts

## Tasks

1. heuristics を整理する
2. learner score を統合する
3. `AIIndex` を定義する
4. legal guard を一般的な企業発信リスク 기준へ広げる
5. repair trigger を score-based にする

## Mandatory Checks

- AI-likeness
  - sentence / paragraph variation
  - opener repetition
  - explicit subject behavior
  - ending monotony
  - topic echo
- legal
  - `No.1`
  - superiority
  - guarantee
  - unverified legal citation
  - stealth-like copy

## Self-Test

- functional
  - `AIIndex` と legal summary が出る
- prompt injection / policy
  - user prompt をそのまま legal rule にしない
- anti-bloat
  - special-case rule が増えすぎていない
- readability / owner boundary
  - scoring と generation が分離されている

## Exit Criteria

- repair trigger が score-based
- `AIIndex` が heuristic + learner の構成で説明できる
- legal guard が一般ルールとして読める

## Retry Rule

- score instability は 2 回まで修正
- 2 回で安定しなければ blocked にして report
