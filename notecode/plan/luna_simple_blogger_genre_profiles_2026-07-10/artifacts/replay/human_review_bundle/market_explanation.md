# market_explanation — Luna B genre-profile human review

> This is a no-API contract/replay bundle. It does not claim that a Luna B article was generated for this type.

## Saved-artifact fixture

- saved baseline article: `notecode/logs/0628/route_v_guarded_user_evaluation_artifact_no_api_20260628_134325/human_review_articles/03_market_explanation.md`
- saved source-packet reference: `notecode/logs/0628/rv_ui_img_20260628_180205/market_explanation/r3/c2/source_packets.json`
- compact saved-signal labels: source上の変化, 現場の論点, 具体物
- baseline body floor: `1200`

## Rendered profile

```text
genre profile: market_explanation
導入で優先するsource材料: source上の変化、現場の論点、具体物
読者の到達目的: 自社が見ている変化と関係する仕事をつかむ
大まかな段落の流れ: 変化の場面 → 自社の接点 → sourceにある論点 → 第三者要約にしない結び
話者・主語省略: 市場・第三者・当社の観察をまたぐ前に主語を置く
このタイプ固有の重大リスク: 第三者による資料要約の口調になること
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
4. Does the profile directly prevent this type's major risk: 第三者による資料要約の口調になること?
5. Does the profile add only type framing, not a new persona, stage, repair path, or fallback?

## Prompt accounting

- common Stage 1 core chars: `402`
- common Stage 2 core chars: `404`
- profile chars: `250`
- rendered Stage 1 chars (stub ledger): `748`
- rendered Stage 2 chars (stub ledger + draft marker): `780`
