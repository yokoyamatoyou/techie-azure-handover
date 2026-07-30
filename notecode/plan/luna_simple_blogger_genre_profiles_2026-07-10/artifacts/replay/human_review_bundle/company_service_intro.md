# company_service_intro — Luna B genre-profile human review

> This is a no-API contract/replay bundle. It does not claim that a Luna B article was generated for this type.

## Saved-artifact fixture

- saved baseline article: `notecode/logs/0628/route_v_guarded_user_evaluation_artifact_no_api_20260628_134325/human_review_articles/02_company_service_intro.md`
- saved source-packet reference: `notecode/logs/0628/rv_ui_img_20260628_180205/company_service_intro/r3/c1/source_packets.json`
- compact saved-signal labels: 仕事, 商品, 現場
- baseline body floor: `1400`

## Rendered profile

```text
genre profile: company_service_intro
導入で優先するsource材料: 仕事、商品、現場
読者の到達目的: 何を、どの現場へ届ける会社かを具体からつかむ
大まかな段落の流れ: 現場の具体 → 仕事と商品 → 支える範囲 → source内の継続する動き
話者・主語省略: 会社の行為・責任は段落境界で明示する
このタイプ固有の重大リスク: 外部紹介または理念要約だけになること
body floor: 1400 / CTA: source_optional
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
4. Does the profile directly prevent this type's major risk: 外部紹介または理念要約だけになること?
5. Does the profile add only type framing, not a new persona, stage, repair path, or fallback?

## Prompt accounting

- common Stage 1 core chars: `402`
- common Stage 2 core chars: `404`
- profile chars: `246`
- rendered Stage 1 chars (stub ledger): `735`
- rendered Stage 2 chars (stub ledger + draft marker): `767`
