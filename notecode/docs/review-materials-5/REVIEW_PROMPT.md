以下のフォルダー一式を読んで、`comparative_review` について「今は新しい意味層拡張を実装しない」という判断が正しいかをレビューしてください。

対象フォルダー:
`C:\tetie\notecode\docs\新しいフォルダー (5)`

まず読む順番:

1. `FILES.md`
2. `CURRENT_REASONING.md`
3. `01_GPTPRO.txt`
4. `02_notecode_current_mainline_handoff_2026-03-31.md`
5. `03_semantic_surface_PROGRESS.md`
6. `04_input_contract.py`
7. `05_pipeline.py`
8. `06_prompt_builder.py`
9. `07_quality_guard.py`
10. `08_bl-comparative-selection-criteria.txt`
11. `09_st-comparative-cross-department.txt`
12. 必要なら `10_comparative_live_summary.json`

前提:

- 元コードは変更しないでください。今回はレビューだけです。
- ideal rewrite 前提ではなく、current mainline に対する現実的な判断をしてください。
- narrow diff / rollbackable / no prompt accretion / no module accretion の制約があります。
- `human_resonance*` は今回の対象外です。
- 2026-03-31 時点の current mainline を前提にしてください。

確認したい核心:

1. `CURRENT_REASONING.md` に書かれた「今は意味層を増やさない」理由は正しいですか。
2. 現在の `comparative_review` の残差は、主に semantic-layer の問題ですか、それとも surface-layer / contract normalization の問題ですか。
3. もし今 meaning-layer を増やすべきなら、最小の 1 slice は何ですか。
4. その slice は、どの owner file を触れば足りますか。`primary <= 2 files`, `support <= 1 file` を守って答えてください。
5. 逆に、今は増やすべきでないなら、どの evidence が揃ったら意味層拡張に進むべきですか。

出力形式は固定してください。

## 1. Verdict

- `correct`
- `partially_correct`
- `incorrect`

のどれか 1 つ。

## 2. Why

- `CURRENT_REASONING.md` のうち正しい点
- 弱い点
- 見落とし

## 3. Layer Diagnosis

- 今の residual を `semantic` / `surface` / `mixed` のどれと見るか
- その根拠を、本文 artifact と code の両方から説明

## 4. If We Should Expand Meaning-Layer Now

- 最小 slice 名
- 目的
- 触る file
- 新しく増やす semantic field または contract
- なぜ narrow rollback が可能か
- 絶対に触らないもの

## 5. If We Should Not Expand Meaning-Layer Now

- 維持すべき理由
- 次に集めるべき evidence
- 次の narrow slice 候補

## 6. Concrete Recommendation

- `do now`
- `do later`
- `do not do`

の 3 区分で明確に書いてください。

理想論ではなく、current mainline に対して実際に安全に進められる判断をください。日本語で答えてください。
