# announcement — Luna B genre-profile human review

> This is a no-API contract/replay bundle. It does not claim that a Luna B article was generated for this type.

## Saved-artifact fixture

- saved baseline article: `notecode/logs/0628/route_v_guarded_user_evaluation_artifact_no_api_20260628_134325/human_review_articles/04_announcement.md`
- saved source-packet reference: `notecode/logs/0628/rv_ui_img_20260628_180205/announcement/r2/b1/source_packets.json`
- compact saved-signal labels: 日付, 対象, 変更点
- baseline body floor: `900`

## Rendered profile

```text
genre profile: announcement
導入で優先するsource材料: 日付、対象、変更点
読者の到達目的: 必要な変更・対象・時期を迷わず把握する
大まかな段落の流れ: 要点 → 対象と時期 → 変更の具体 → sourceにある案内先のみ
話者・主語省略: 告知主体、対象、日付と依頼は省略しない
このタイプ固有の重大リスク: 必要情報よりブログ風の長文化が前に出ること
body floor: 900 / CTA: source_optional
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
4. Does the profile directly prevent this type's major risk: 必要情報よりブログ風の長文化が前に出ること?
5. Does the profile add only type framing, not a new persona, stage, repair path, or fallback?

## Prompt accounting

- common Stage 1 core chars: `402`
- common Stage 2 core chars: `404`
- profile chars: `235`
- rendered Stage 1 chars (stub ledger): `716`
- rendered Stage 2 chars (stub ledger + draft marker): `748`
