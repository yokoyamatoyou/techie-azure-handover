# naturalness recovery execution plan 2026-04-08

更新日: 2026-04-08
対象: `naturalness_recovery_2026-04-07` package の明日以降の実装順

## Objective

- current success path を壊さず、branding / company introduction の visible AI feel を narrow owner-local phases で改善する
- `repair non-actuation` を最初の known blockage として外しつつ、総合主因は `source-aware defaults / state loss` にあるかを切り分ける
- `route ownership` は一度 live で触って効果が頭打ちだったため、初手の再実装対象から外す

## Fixed Order

1. Phase A
   - `simple_note_pipeline/pipeline.py`
   - branding/company introduction の patch path / acceptance narrow fix
2. Phase B
   - `natural_blog_core.py`
   - company introduction defaults の source-aware prune
3. Phase C
   - `newalgorithm_pipeline/input_contract.py`
   - bounded surface memo preservation
4. Phase D
   - `newalgorithm_pipeline/pipeline.py`
   - route ownership experiment の reopen は A-C 後も broad flatness が残る場合だけ
5. Phase E
   - `newalgorithm_pipeline/output_formatter.py`
   - normalize relaxation は最後の conditional fallback

## Why This Order

- current telemetry では `repair_trigger_score=0.6` に到達しているため detect は起きている
- しかし `patch_path_refusal_reason = compact_plan_scope_ineligible`、`patch_path_used = false`、`repair_applied = false` で、known blockage がある
- ただし route promotion は 2026-04-08 の live gate で `writer_of_record` を変えても visible AI feel を改善できなかった
- したがって、順番は `repair blockage -> defaults -> state preservation` を先にやり、route は後回しにする

## Phase A

### Scope

- owner file:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- touch しない:
  - `natural_blog_core.py`
  - `input_contract.py`
  - `newalgorithm_pipeline/pipeline.py`
  - `quality_guard.py`

### Hypothesis

- branding/company introduction を `ending_bucket_monotony` 限定で patch path と acceptance に接続すれば、局所 surface defect が本文へ反映される

### Do

- branding/company introduction の patch scope eligibility を narrow に開く
- acceptance に `ending_bucket_monotony_score` または `ending_bucket_max_run` 改善を入れる
- `_repair_preserves_alignment()` と single repair 1回制約は keep する

### Pass

- branding sentinel で `patch_path_used = true` または `repair_applied = true`
- `ending_bucket_monotony_score` か `ending_bucket_max_run` が baseline より改善
- guard case regression なし

### Fail / rollback

- full rewrite 寄りの挙動になる
- unrelated genre regression が出る
- generic baseline と比べても visible AI feel が悪化する

## Phase B

### Scope

- owner file:
  - `C:\tetie\notecode\note\natural_blog_core.py`

### Hypothesis

- company introduction defaults を source-aware に prune すれば、generic filler と explanation-card 化が減る

### Do

- source bucket 不足時に absent slot を無理に立てない
- `強み / 歩み / 提供価値` を固定要求しない
- source-backed section だけで自然な流れを組む

### Pass

- branding/company introduction で後半の言い換え重複が減る
- abstract filler が減る
- target 2 cases で generic baseline より visible AI feel が良い

## Phase C

### Scope

- owner file:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`

### Hypothesis

- micro-surface 指示を bounded memo として保持すれば、prompt accretion なしで改行・話者・主語省略の自然さを戻せる

### Do

- raw prompt を再掲しない
- 最大 1-2 件の bounded surface memo だけを contract に保持する
- kept / dropped の理由を telemetry で説明できるようにする

### Pass

- target 2 cases で改行の呼吸と話者一貫性が generic baseline より改善
- prompt の長文化なし

## Phase D

### Entry condition

- Phase A-C 後も broad flatness が残り、telemetry 上も writer/style owner mismatch が主因候補として残る場合のみ

### Note

- 2026-04-08 の route promotion 実験は keep するが、初手で reopen しない

## Phase E

### Entry condition

- upstream と repair の改善後も paragraph breath だけが不自然に残る場合のみ

## Common Gate

- owner-local tests pass
- shared checks pass
- `C:\tetie\notecode\docs\stepwise_three_article_gate_2026-04-08.md` の fixed 3 cases を live compare
- target 2 cases で `step-optimized` が `generic` より AI 感が少ない
- guard 1 case で visible regression なし

## Stop Rule

- same phase 3 attempts
- rollback 不能
- multi-owner simultaneous edit が必要になった場合
- prompt accretion なしでは進めないと判明した場合
