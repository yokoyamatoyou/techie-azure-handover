# Japanese Style Policy

## Target Feel

The generated article should read like a natural Japanese blog article suitable for note or Hatena Blog, while still respecting the selected article category.

The target is not casualness alone. It is:

- clear source-grounded content
- human-like paragraph rhythm
- uneven but intentional line breaks
- non-uniform sentence length
- no generic AI conclusion
- no unsupported emotional inflation

## Paragraph Rhythm

Avoid uniform paragraphing.

Risk patterns:

- every paragraph has the same number of sentences
- every section has the same paragraph count
- every heading ends with the same kind of summary sentence
- line breaks appear at mechanically regular intervals
- late-half paragraphs repeatedly end with the same bucket of expressions

Quality checks should include paragraph rhythm and ending-bucket monotony.

Runtime style control should come from compact style profiles, not from adding more one-off prompt text. The active `article_brief` should expose:

- `style_profile_id`
- preferred and maximum sentences per paragraph
- line-break policy
- subject-omission policy
- ending-bucket policy
- protected terms where the responsible subject must remain explicit

For Japanese subject omission, repeated first-person subjects may be omitted only after the actor is clear. Dates, prices, schedules, responsibilities, promises, requests, and other protected facts should keep the responsible subject explicit.

## Structural Editor Pass

After the style editor, run a narrow structural editor pass when available.

The pass should focus on:

- the late half of the article, where instruction following often degrades
- paragraphs that become too dense near the end
- first-person consistency across the whole article
- abrupt CTA escalation
- heading-to-body continuity

This pass is not a second draft writer. It must not add source claims or rewrite the whole article.

## Model-Frequent Words

Some words are not forbidden, but are high-risk when they appear as generic GPT filler.

Initial watchlist:

```text
効く
第一歩
寄り添う
見える化
大切
魅力
さまざま
多くの方
しっかり
丁寧に
安心
つながる
きっかけ
広がる
支える
```

Rules:

- Do not hard-ban these words globally.
- Flag them when repeated, unsupported by source, or used as generic closing language.
- Prefer article-specific nouns and source-grounded verbs over abstract encouragement.

## Existing Risky Phrases

Keep the initial risky phrase list:

```text
いかがでしたでしょうか
〜と言えるでしょう
〜することができます
この記事では
ぜひ参考にしてみてください
このように
また、
さらに、
大切にしています
魅力があります
さまざまな
多くの方に
```

These are quality risks, not absolute bans. Context and repetition matter.

## QA Issue Types

Style QA should support these additional issue types:

```text
paragraph_rhythm_monotony
line_break_monotony
ending_bucket_monotony
model_frequent_word
generic_encouragement_phrase
```

## Rewrite Rule

When fixing style issues, targeted rewriting must preserve:

- facts
- claim IDs
- section purpose
- speaker / first person
- non-target paragraphs

Do not fix rhythm by rewriting the entire article.
