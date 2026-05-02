# Current Reasoning

## Question

`comparative_review` の residual が残っている中で、今すぐ新しい meaning-layer を増やすべきか。

現時点の判断は `まだ増やさない` です。

## Why We Are Not Expanding Meaning-Layer Right Now

1. 今回観測された残差の主因は、意味崩壊より `raw axis token leakage` と `thin comparative sections` に見えた。
   - `approval_flow` や `support_density` のような token 漏れ
   - 比較見出しが 1 文で終わり、差の理由が薄い出力

2. これらはまず上流正規化と existing repair path で触れるべき種類の問題だった。
   - `input_contract.py` で比較軸ラベルを正規化
   - `quality_guard.py` で thin comparative section を検知
   - `prompt_builder.py` では compare line の humanize を補助

3. meaning-layer の誤りは、surface-layer の誤りより被害範囲が広い。
   - claim や anchor を誤って固定すると、全 section に同じ誤りが伝播しやすい
   - rollback も surface-only fix より重くなる

4. current mainline はまだ GPTPRO の full architecture ではない。
   - `single-pass + optional single repair 1回`
   - shadow draft / sentence-level claim binding / omission judge / patch-only local rewrite の完全版ではない
   - この状態で部分的な semantic field を増やすと hybrid complexity が増えやすい

5. package と current rules が narrow diff 前提だった。
   - prompt accretion を避ける
   - module accretion を避ける
   - rollback 可能な diff に限る
   - owner boundary を狭く保つ

6. 最新の targeted live では、比較ジャンルは gate を維持したまま改善した。
   - `short_gate_passed=5/5`
   - `rubric_mean_total=7.4`
   - `.txt` artifact から raw axis token は消えた
   - まだ `8.0` には届かないが、少なくとも今回の残差は semantic collapse より surface/contract normalization 側の寄与が大きいと見ている

## What We Want Reviewed

以下を確認したいです。

1. 上の判断は技術的に妥当か。
2. 実は今の時点で meaning-layer を 1 段だけ増やすべきなら、その最小 slice は何か。
3. もし増やすべきでないなら、どの evidence が揃った時点で意味層拡張に進むべきか。

## Constraints That Still Apply

- 元コードはそのままにしたい
- prompt accretion は避けたい
- module accretion は避けたい
- rollback 不能な設計変更は避けたい
- `human_resonance*` はまだ触らない
- comparative_review の narrow slice 以上には広げない
