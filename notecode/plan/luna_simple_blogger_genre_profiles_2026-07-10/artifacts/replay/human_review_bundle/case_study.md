# case_study — Luna B genre-profile human review

> This is a no-API contract/replay bundle. It does not claim that a Luna B article was generated for this type.

## Saved-artifact fixture

- saved baseline article: `notecode/logs/0628/route_v_guarded_user_evaluation_artifact_no_api_20260628_134325/human_review_articles/06_case_study.md`
- saved source-packet reference: `notecode/logs/0628/rv_ui_img_20260628_180205/case_study/r/a1/source_packets.json`
- compact saved-signal labels: 課題, 対応, 変化
- baseline body floor: `1200`

## Rendered profile

```text
genre profile: case_study
導入で優先するsource材料: 課題、対応、sourceにある変化
読者の到達目的: 何が起き、何を行い、どこまで分かるかを追える
大まかな段落の流れ: 課題の場面 → 対応の具体 → sourceにある変化 → 未確認を足さない結び
話者・主語省略: 顧客・当社・協力者が交わるたび主語を明示する
このタイプ固有の重大リスク: 根拠のない成果や顧客感情を補うこと
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
4. Does the profile directly prevent this type's major risk: 根拠のない成果や顧客感情を補うこと?
5. Does the profile add only type framing, not a new persona, stage, repair path, or fallback?

## Prompt accounting

- common Stage 1 core chars: `402`
- common Stage 2 core chars: `404`
- profile chars: `238`
- rendered Stage 1 chars (stub ledger): `716`
- rendered Stage 2 chars (stub ledger + draft marker): `748`
