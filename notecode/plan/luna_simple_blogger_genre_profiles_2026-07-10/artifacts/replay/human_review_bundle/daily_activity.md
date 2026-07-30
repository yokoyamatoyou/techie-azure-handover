# daily_activity — Luna B genre-profile human review

> This is a no-API contract/replay bundle. It does not claim that a Luna B article was generated for this type.

## Saved-artifact fixture

- saved baseline article: `notecode/logs/0628/route_v_guarded_user_evaluation_artifact_no_api_20260628_134325/human_review_articles/05_daily_activity.md`
- saved source-packet reference: `notecode/logs/0628/rv_ui_img_20260628_180205/daily_activity/r2/b1/source_packets.json`
- compact saved-signal labels: 場所, 道具, 動作
- baseline body floor: `1200`

## Rendered profile

```text
genre profile: daily_activity
導入で優先するsource材料: 場所、道具、動作
読者の到達目的: その日の仕事がどの順番で進むかを具体で追う
大まかな段落の流れ: 場面の開始 → 道具と動作 → 順番と関係者 → sourceにある次の動き
話者・主語省略: 作業者・来訪者・対象物が変わるたび主語を明示する
このタイプ固有の重大リスク: sourceにない感情や手応えを付け足すこと
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
4. Does the profile directly prevent this type's major risk: sourceにない感情や手応えを付け足すこと?
5. Does the profile add only type framing, not a new persona, stage, repair path, or fallback?

## Prompt accounting

- common Stage 1 core chars: `402`
- common Stage 2 core chars: `404`
- profile chars: `237`
- rendered Stage 1 chars (stub ledger): `719`
- rendered Stage 2 chars (stub ledger + draft marker): `751`
