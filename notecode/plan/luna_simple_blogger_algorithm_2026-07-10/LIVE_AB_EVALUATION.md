# Live A/B Evaluation

## Outcome

Decision: `Arm A provisional winner; two-stage B not adopted`.

This is one saved-source observation, not a general Luna acceptance. Both arms generated complete articles and passed H1/H2/body-floor checks. The extra same-blogger reread made real localized changes, but did not produce a clean hard-gate improvement over A.

## B2 change audit

B2 retained paragraph similarity `0.80` to B1 and changed three separate paragraphs.

Positive changes:

1. Removed `思い浮かべるかもしれません` reader-inference framing and returned the paragraph to exhibition actions.
2. Replaced `会社を発足` with `当社が発足しました`, restoring the responsible subject.
3. Restored the source-present `2026年春号` detail and reduced a broad `食をめぐらせる動き` phrase.

Negative change:

- B2 changed the exhibition paragraph to `展示会では、食材やメニューを紹介し、自社開発製品やサポートについてもご案内します。` The company subject is omitted after a paragraph boundary and after nearby `お客様` mentions. This violates the candidate's explicit zero-anaphora rule even though the likely subject remains inferable.

## Source-grounding audit

No new unsupported numbers, dates, prices, rankings, customer results, or awards were found.

Review concerns:

- A says exhibitions help create `新たな関係`; the source supports proposals and customer needs, but not this result claim directly.
- B treats the website's `自社開発製品・サポートの一覧` and contact navigation as activity performed at the exhibition. The source packet places these strings near the exhibition text but does not prove that exact event behavior.
- Both are bounded, low-severity inference concerns, but they prevent a `100% source-grounding pass` claim without human/source-location review.

## Language audit

- A is concrete and source-rich but contains a 101-character event-list sentence. It is long for the current 90-character watch boundary, though the length is caused by source-present proper names rather than filler.
- B has shorter sentences and fewer narrator repetitions.
- Both avoid `判断軸`, `判断材料`, `はじめの一歩`, `第一歩`, `効く`, `確認`, and `整理` as generic prose.
- Both still use source-derived mission language in their conclusions, so neither fully proves broad cross-source naturalness.

## Cost / latency judgment

B cost `1.937x` and took `1.474x` A. The second stage's mixed hard-gate result does not justify that increase in this run.

## Adoption decision

- Arm A: `keep as the simpler provisional candidate`
- Arm B: `do not adopt from this run`
- Route V: `unchanged`
- additional live API: `not authorized`
- next evidence: blind/manual review of the saved A/B bundle only
