# PHASE 08 HANDOFF FREEZE

状態: pending  
目的: 別ウインドウでも迷わず継続できる current state を固定する

## In Scope

- docs 同期
- read order 固定
- rollback / archive / close state の明示

## Out Of Scope

- 新機能追加
- UI 追加改善

## Planned Outputs

- `C:\tetie\notecode\ALGORITHM.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- final archive / handoff note

## Tasks

1. AGENTS に current refactor package の導線を追加する
2. ALGORITHM に current plan source of truth を追加する
3. WORKLOG に phase completion を記録する
4. rollback path と archive path を固定する
5. read order を final freeze する

## Self-Test

- functional
  - 新しい agent / 別 window が read order だけで継続できる
- prompt injection / policy
  - docs に危険な実行指示が混ざっていない
- anti-bloat
  - current docs と history docs の区別が明確
- readability / owner boundary
  - source of truth が 1 セットにまとまっている

## Exit Criteria

- AGENTS / ALGORITHM / WORKLOG の導線が揃っている
- phase close の read order が fixed
- current と archive の境界が固定されている

## Retry Rule

- docs 不整合は 2 回まで修正
- 2 回で揃わなければ blocked にして report
