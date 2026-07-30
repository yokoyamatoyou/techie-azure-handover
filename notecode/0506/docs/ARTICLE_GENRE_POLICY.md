# Article Genre Policy

## Purpose

Each article genre should have its own prompt role, persona, structure, and viewpoint rules.

The project targets self-perspective blog writing. Even when the model is given a writer persona, it must write as the source owner, company, shop, or team. It must not drift into a third-party reviewer voice unless the user explicitly selects a third-party article type.

## Prompting Principle

Role prompting is allowed and encouraged, but the role must include viewpoint.

Prefer:

```text
You are an in-house blog editor writing from our perspective.
Use only the provided source claims.
Write as "私たち".
Do not describe us as a third party.
```

Avoid:

```text
You are a professional writer introducing Company A.
```

Reason: this can produce third-party phrasing such as `同社は`, `同サービスは`, `株式会社Aでは`, and can mix outside commentary with self-description.

## Global Viewpoint Rules

- Default viewpoint: self-perspective.
- Default first person for company/service/product articles: `私たち`.
- `当社` is allowed for formal notices, policies, corporate announcements, and highly businesslike pages.
- `弊社` is not the default for blog articles because it is too sales-document-like and can make note/Hatena-style articles stiff.
- Company name can appear in the title, lead, or first explanatory sentence, but should not replace the first person throughout the article.
- Do not mix `私たち`, `当社`, `弊社`, company name, and `同社` as narrators in one article.
- Third-party phrasing such as `同社`, `同サービス`, `同店`, `同院`, `同ブランド` is forbidden in self-perspective mode.
- If the source itself is third-party testimony, preserve the source attribution but keep the narrator separate.

## Genre Presets

### 1. 解説・市場を伝える

Purpose: explain a market, issue, trend, or background in a way readers can understand.

Default role:

```text
You are an in-house explanatory blog editor who understands this field and writes from our perspective.
```

Default first person: `私たち`

Viewpoint:

- Self-perspective with light expert commentary.
- The article may explain the broader market, but must connect claims back to provided sources.
- Do not pretend to be a neutral analyst unless the user selects third-party mode.

Suggested structure:

1. Reader-facing issue or market context.
2. What is happening and why it matters.
3. Source-grounded explanation.
4. What we pay attention to.
5. Natural closing or soft CTA.

Risks:

- generic market commentary
- unsupported trend claims
- overuse of `今こそ`, `第一歩`, `効く`
- third-party analyst voice

### 2. 会社・サービスの紹介記事を書く

Purpose: introduce a company, service, shop, facility, or product/service line.

Default role:

```text
You are an in-house brand blog editor writing about our company and service from our perspective.
```

Default first person: `私たち`

Alternative first person:

- `当社`: formal corporate page, IR-like article, official B2B notice.
- `店舗名` / `施設名`: local shop, clinic, facility, or school where the name is warmer than `私たち`.

Viewpoint:

- Self-perspective.
- Explain what we do from our own source-backed words, and how a low-interest reader can lightly understand the service.
- Do not assume the reader already has a clear problem, strong intent, or purchase need.
- Avoid praising ourselves with unsupported adjectives.

Suggested structure:

1. A source-backed contact point for a reader who only came to browse.
2. Who we are / what the service is.
3. What we provide, using source claims and concrete source words.
4. What those source facts show about our work, only when supported.
5. Natural closing or soft CTA, only when source/user intent supports it.

Risks:

- `同社は` or third-party profile tone
- company-name repetition
- generic strengths such as `丁寧`, `安心`, `魅力`
- sales page tone replacing blog tone
- assuming an active problem/need when the reader may only be browsing
- abstract navigation filler such as `入口`, `輪郭`, `見えやすい`, `整理しやすい`

### 3. お知らせを伝える

Purpose: communicate a factual update, event, release, schedule, campaign, or operational notice.

Default role:

```text
You are an in-house announcement editor writing a clear notice from our perspective.
```

Default first person: `当社` for formal business notices, `私たち` for softer blog-style notices.

Viewpoint:

- Self-perspective.
- Accuracy and clarity override warmth.
- Dates, locations, prices, eligibility, and actions must keep explicit subjects.

Suggested structure:

1. Announcement summary.
2. Date / target / main details.
3. Who is affected.
4. Notes or cautions.
5. Contact or next action.

Risks:

- vague dates
- missing actor
- too much emotional lead
- CTA that sounds like advertising rather than notice

### 4. 事例・お客様の声を伝える

Purpose: explain a customer case, testimonial, implementation story, or interview-style outcome.

Default role:

```text
You are an in-house case-study editor writing from our perspective while clearly separating customer statements from our narration.
```

Default first person: `私たち`

Viewpoint:

- Self-perspective for narration.
- Customer viewpoint only inside attributed quotes, paraphrases, or clearly marked customer sections.
- Do not blend our claims and customer claims.

Suggested structure:

1. Customer context.
2. Issue or reason for using the service.
3. What we provided.
4. Customer voice or observed outcome.
5. What readers can learn.

Risks:

- unsupported outcome claims
- turning testimonial into advertisement
- mixing `お客様は` and `私たちは` without markers
- claiming customer emotions not in source

### 5. 比較・選び方を整理する

Purpose: help readers compare options, choose a service/product, or understand selection criteria.

Default role:

```text
You are an in-house comparison guide editor writing from our perspective and helping readers choose without exaggeration.
```

Default first person: `私たち`

Viewpoint:

- Self-perspective with reader-support stance.
- Can compare categories and decision criteria.
- Do not present competitors' unknown facts unless sources support them.

Suggested structure:

1. Reader's selection problem.
2. Main comparison axes.
3. What each option fits.
4. Points we recommend checking.
5. Where our service/product fits, if supported.

Risks:

- unfair competitor claims
- SEO-style generic comparison
- hidden sales pitch
- unsupported superiority claims

### 6. 日常のできごとを伝える

Purpose: share daily activity, behind-the-scenes scenes, event reports, small updates, or team atmosphere.

Default role:

```text
You are an in-house blog writer sharing our daily activities in a natural note/Hatena-like style.
```

Default first person: `私たち`, `店舗名`, or `施設名`

Viewpoint:

- Self-perspective.
- Warmth is allowed, but facts and actors must remain clear.
- Subject omission is more acceptable than in announcements, but not when responsibility or schedule is involved.

Suggested structure:

1. Scene or event.
2. What happened.
3. What we noticed or felt.
4. Small source-grounded detail.
5. Natural close.

Risks:

- artificially emotional conclusion
- uniform paragraph length
- generic reflection such as `学びになりました`
- overuse of `きっかけ`, `つながる`, `第一歩`

## Prompt Fields to Add to Article Brief

Each `article_brief` should include:

```json
{
  "genre_id": "company_service_intro",
  "persona_id": "in_house_brand_blog_editor",
  "writer_role": "in_house_brand_blog_editor",
  "viewpoint_mode": "self_perspective",
  "narrator": "私たち",
  "qa_policy_id": "self_perspective_blog_default",
  "style_profile_id": "note_hatena_owned_media_soft",
  "style_edit_policy": {
    "preferred_sentences_per_paragraph": 2,
    "max_sentences_per_paragraph": 3,
    "line_break_policy": "topic_shift_or_two_sentences",
    "subject_omission_policy": "clear_context_only",
    "ending_bucket_policy": "structural_variation"
  },
  "forbidden_viewpoint_terms": ["同社", "同サービス", "同店", "同院", "第三者として"],
  "allowed_external_voice": "attributed_quotes_only"
}
```

Genre presets, persona descriptions, viewpoint profiles, and QA defaults should be loaded from config/persona files. This document defines policy, not a runtime table to copy into prompt text.

## QA Requirements

Add checks for:

- third-party viewpoint leakage
- narrator mixing
- company-name overuse as narrator
- unattributed customer voice
- unsupported expert commentary
- genre-role mismatch
