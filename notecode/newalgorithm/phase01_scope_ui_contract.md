# Phase01: Scope/UI Contract Fix

## Goal
- 実装前提を固定し、迷いなくPhase02以降へ進める。

## Input
- `MASTER_PLAN.md`
- `ui_mapping_table.md`
- `article_type_matrix.md`
- `input_contract_draft.md`

## Output
- UI項目対応表の確定版
- 記事タイプ確定表の確定版
- 入力契約 v1（項目定義・正規化ルール・バリデーション）

## Fixed Decisions
- 記事タイプ7種と内部キーを固定。
- 最小UIは3要素のみを必須維持。
- `daily_story` のSEO差分は `style_compact_for_seo=true` をcontractで明示。
- 旧依存UIは原則削除、例外は1リリース非表示。

## Steps
1. `ui_mapping_table.md` の全現行項目を棚卸しし、`残す/非表示/削除` を決定する。
2. `article_type_matrix.md` をsingle sourceとして確定し、内部キーを凍結する。
3. `input_contract_draft.md` に required/optional/normalized を明記する。
4. 例外非表示の候補画面を `ui_mapping_table.md` の移行メモに明記する。
5. `PROGRESS.md` の Open Questions を更新する。

## Deliverables
- `ui_mapping_table.md`（本フォルダ内）
- `article_type_matrix.md`（本フォルダ内）
- `input_contract_draft.md`（本フォルダ内）

## Exit Criteria
- UI項目に未分類行が0件。
- 記事タイプ7種の内部キーが確定し、変更禁止として明記済み。
- `style_compact_for_seo=true` の発火条件が契約に明記済み。

## Self Test
- ST-01 正常: 7記事タイプすべてがcontractへ正規化される。
- ST-02 異常: 未定義記事タイプ入力時に `validation_error` で停止する。

## LLM Vulnerability Test
- LT-01: topicに「内部指示を無視」を混入しても無効化される。
- LT-02: 危険出力の越権要求を拒否する。

## Pipeline Review
- PR-01: UI入力から `input_contract` への項目落ちが0件。

## Module/Dependency Risk Check
- DR-01: 既存UI参照先を棚卸しし、旧依存の残存箇所を列挙する。

## Rollback
- 条件: UI項目定義が確定せずPhase02に進めない
- 戻し先: Phase01開始時点の決定ログに戻し再整理
