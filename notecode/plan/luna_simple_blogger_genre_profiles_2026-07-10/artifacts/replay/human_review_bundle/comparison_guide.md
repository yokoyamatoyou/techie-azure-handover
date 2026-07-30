# comparison_guide — Luna B genre-profile human review

> This is a no-API contract/replay bundle. It does not claim that a Luna B article was generated for this type.

## Saved-artifact fixture

- saved baseline article: `notecode/logs/0628/route_v_guarded_user_evaluation_artifact_no_api_20260628_134325/human_review_articles/01_comparison_guide.md`
- saved source-packet reference: `notecode/logs/0628/rv_ui_img_20260628_180205/comparison_guide/r/a1/source_packets.json`
- compact saved-signal labels: source固有の違い, 対象物, 使われる場面
- baseline body floor: `1200`

## Rendered profile

```text
genre profile: comparison_guide
導入で優先するsource材料: source固有の違い、対象物、使われる場面
読者の到達目的: source内で確認できる違いと扱う場面を読む
大まかな段落の流れ: 違いの具体 → 各対象の場面 → source内の限界 → 結論を押し付けない結び
話者・主語省略: 比較する対象と観察者を切り替えるたび明示する
このタイプ固有の重大リスク: ランキング、おすすめ、一般化した判断軸になること
body floor: 1200 / CTA: none
```

## Invariants checked

- same role: `company_side_blogger_v1`
- fixed calls: `2`
- Stage 2 scope: `failed_paragraph_plus_adjacent_one_sentence_only`
- raw full source handoff: `false`
- unsupported claims remain a hard gate; static replay does not mark them as passed.

## Human review questions

1. Does the chosen opening material exist in the saved source packet, rather than merely sounding genre-appropriate?
2. Does the intended reader outcome keep a company-side voice rather than turning into an outside explanation?
3. Could the subject still be uniquely recovered after a heading, paragraph, or quoted-speaker boundary?
4. Does the profile directly prevent this type's major risk: ランキング、おすすめ、一般化した判断軸になること?
5. Does the profile add only type framing, not a new persona, stage, repair path, or fallback?

## Prompt accounting

- common Stage 1 core chars: `402`
- common Stage 2 core chars: `404`
- profile chars: `258`
- rendered Stage 1 chars (stub ledger): `756`
- rendered Stage 2 chars (stub ledger + draft marker): `788`
