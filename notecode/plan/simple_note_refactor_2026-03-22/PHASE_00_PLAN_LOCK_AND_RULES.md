# PHASE 00 PLAN LOCK AND RULES

状態: completed  
目的: refactor 全体の進め方と完了定義を固定する

## In Scope

- phase 構成の固定
- 完了定義の固定
- stop / retry ルールの固定

## Out Of Scope

- runtime behavior 変更
- UI 変更
- prompt 変更

## Outputs

- `README.md`
- `PROGRESS.md`
- phase 文書一式

## Self-Test

- functional
  - read order が明示されている
- prompt injection / policy
  - rule が user prompt 依存になっていない
- anti-bloat
  - plan package が冗長な補助文書だらけになっていない
- readability / owner boundary
  - AI が phase 単位で読める

## Exit Criteria

- refactor package の入口が fixed
- global rules が fixed
- progress update rule が fixed

## Retry Rule

- doc 不整合があれば 2 回まで修正
- 2 回で解消しなければ stop して user report
