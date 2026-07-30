# PHASE 01 ARCHIVE BOUNDARY AND BASELINE FREEZE

状態: pending  
目的: pre-refactor 情報を current refactor と分離し、baseline を固定する

## In Scope

- archive boundary の固定
- baseline article sample の保存
- prompt length / module size / current metrics の baseline 化

## Out Of Scope

- learner 導入
- UI 変更
- prompt 再設計

## Planned Outputs

- `C:\tetie\notecode\archive\simple_note_refactor_prestart_2026-03-22\README.md`
- `C:\tetie\notecode\archive\simple_note_refactor_prestart_2026-03-22\manifest.json`
- `C:\tetie\notecode\logs\simple_note_refactor_baseline_2026-03-22\`
- `C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\PROGRESS.md`

## Tasks

1. current docs / logs / runtime entry の snapshot 対象を列挙する
2. pre-refactor archive manifest を作る
3. article type ごとの baseline sample を保存する
4. current metrics を固定する
   - `paragraph_first_person_starts`
   - `repeated_opening_count`
   - `duplicate_paragraph_count`
   - `same_ending_runs`
   - `topic_opening_ratio`
   - `must_cover_reflection_rate`
5. current prompt length と module line count を記録する

## Self-Test

- functional
  - baseline artifact が再読可能
- prompt injection / policy
  - snapshot に秘匿情報や不要な prompt 実体を混ぜていない
- anti-bloat
  - archive と current plan を混在させていない
- readability / owner boundary
  - phase 1 outputs の path が一意に追える

## Exit Criteria

- pre-refactor archive boundary が fixed
- baseline sample が article type ごとに保存済み
- current baseline metrics が記録済み

## Retry Rule

- path 不整合や欠落があれば 2 回まで修正
- 2 回で揃わなければ blocked にして report
