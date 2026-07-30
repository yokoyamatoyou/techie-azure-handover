# Pipeline Spec

## Article Pipeline

```text
Source Upload
  -> Text Extraction / Noise Removal
  -> Source Card Extraction
  -> Knowledge Pack Integration
  -> Article Brief Generation
  -> Draft Writer
  -> Style Editor
  -> Structural Editor
  -> Japanese Quality Checker
  -> Targeted Rewriter
  -> Final Article
```

## Source Card

Purpose: extract blog-usable facts, phrases, and warnings from one source.

Input shape:

```json
{
  "source_id": "pdf_001",
  "source_type": "pdf | url | word | manual",
  "source_text": "...",
  "metadata": {
    "title": "...",
    "url": "...",
    "published_or_updated_at": "..."
  }
}
```

Output shape:

```json
{
  "source_id": "pdf_001",
  "source_type": "pdf",
  "title": "会社案内2026",
  "published_or_updated_at": "2026-04-20",
  "reliability": "official | external | user_uploaded | unknown",
  "main_topics": ["事業内容", "沿革", "代表メッセージ"],
  "facts": [
    {
      "fact_id": "F001",
      "claim": "株式会社Aは2018年に創業した",
      "category": "company_profile",
      "importance": 5,
      "source_span": "p.2",
      "usable_in_article": true
    }
  ],
  "quotes_or_phrases": [
    {
      "text": "地域に根ざしたサービス",
      "usage": "tone_reference",
      "source_span": "p.4"
    }
  ],
  "warnings": ["売上高の記載は古い可能性あり"]
}
```

Rules:

- Extract usable material, not generic summaries.
- Do not infer missing facts.
- Preserve numbers, dates, and names.
- Mark old or ambiguous information as warnings.

## Knowledge Pack

Purpose: integrate multiple source cards into article-ready claims.

Output shape:

```json
{
  "article_knowledge_pack": {
    "confirmed_facts": [
      {
        "claim_id": "C001",
        "claim": "株式会社Aは2018年創業で、地域密着型のサービスを展開している",
        "supporting_fact_ids": ["F001", "F014"],
        "confidence": "high | medium | low",
        "preferred_expression": "2018年の創業以来、地域に根ざしたサービスを展開"
      }
    ],
    "conflicts": [
      {
        "issue": "従業員数がPDFでは30名、Webでは35名",
        "resolution": "Webの更新日が新しいため35名を採用",
        "do_not_mention": false
      }
    ],
    "deduped_themes": ["地域密着", "丁寧な対応"],
    "do_not_infer": ["業界No.1とは書かない"]
  }
}
```

Rules:

- Merge facts with the same meaning.
- Detect conflicts.
- Prefer newer official information when clearly available.
- Separate usable claims from risky or unsupported content.

## Article Brief

Purpose: create the article design contract from UI settings and knowledge pack.

Required contents:

- category
- genre ID
- persona ID
- writer role
- viewpoint mode
- target reader
- goal
- narrator / first person
- persona
- selected style profile
- style edit policy
- selected editor profile
- editor pass policy
- article structure
- assigned claim IDs
- section-level main subject
- discourse rules
- style rules
- forbidden or risky phrases
- config references
- QA policy ID

Rules:

- The article brief is the only design document for draft generation.
- Each heading must identify its claim IDs.
- Do not reuse claim IDs across sections unless explicitly allowed.
- First person and CTA must be explicit.
- Self-perspective is the default. Third-party viewpoint must be explicitly selected.
- Genre, persona, viewpoint, style profile, and QA defaults should be resolved before prompt rendering.

## Draft Writer

Purpose: write the first draft from the article brief and confirmed claims.

Rules:

- Use only source claims.
- Follow article brief structure.
- Use only the configured first person.
- Do not repeat the same claim in multiple sections.
- Prioritize accuracy and structure over polish.
- Output article body only.

## Style Editor

Purpose: improve Japanese style without changing facts.

Rules:

- Do not add facts.
- Do not change numbers, dates, or names.
- Do not add unsupported strengths or achievements.
- Improve sentence length, flow, paragraphing, endings, and AI-like phrasing.
- Use `article_brief.style_edit_policy` for line breaks, safe subject omission, and ending-bucket variation.
- Do not solve one observed failure with phrase-by-phrase replacements.

## Structural Editor

Purpose: perform a final editor pass focused on late-half structure and whole-article consistency.

Rules:

- Do not add facts.
- Do not change numbers, dates, or names.
- Do not change source-grounding or QA policy.
- Use `article_brief.editor_pass_policy`.
- Focus on the late half for paragraph splits and rhythm.
- Check first-person consistency across the whole article.
- Emit an editor-pass report with before/after stylometry signals.

## Japanese Quality Checker

Purpose: inspect the edited article and return structured issues.

The checker may consume deterministic stylometry output for rhythm, ending, connector, lexical, character-type, and viewpoint issue candidates.

Output shape:

```json
{
  "pass": false,
  "score": 82,
  "issues": [
    {
      "type": "subject_ambiguity",
      "severity": "medium",
      "text": "今後も改善を続けていきます。",
      "reason": "誰が改善するのか曖昧",
      "fix_instruction": "主語を当社として明示する"
    }
  ],
  "rewrite_needed": true
}
```

Issue types:

```text
unsupported_claim
first_person_inconsistency
subject_ambiguity
zero_anaphora_risk
duplication
ai_like_phrase
style_mismatch
cta_issue
forbidden_phrase
sentence_too_long
ending_repetition
connector_repetition
paragraph_rhythm_monotony
line_break_monotony
ending_bucket_monotony
model_frequent_word
generic_encouragement_phrase
third_party_viewpoint_leakage
narrator_mixing
company_name_overuse_as_narrator
unattributed_customer_voice
genre_role_mismatch
sentence_rhythm_monotony
nominalization_overuse
formatting_mismatch
```

## Targeted Rewriter

Purpose: fix only the issues identified by the quality checker.

Rules:

- Do not rewrite unflagged sections.
- Do not add facts.
- Do not change numbers, dates, or names.
- Keep first person consistent.
- Rerun quality check after rewriting.

## Article Category Presets

### 日々のできごと

- Tone: friendly, slightly warm.
- Goal: communicate the atmosphere of an activity.
- Structure: event introduction, concrete scene, feeling, natural close.
- Subject omission: high tolerance.
- CTA: none or soft.

### 企業紹介

- Tone: sincere and trustworthy.
- Goal: help first-time readers understand the company.
- Structure: overview, values, concrete strengths, inquiry path.
- Subject omission: medium tolerance.
- CTA: medium.

### お知らせ

- Tone: concise and accurate.
- Goal: communicate necessary information clearly.
- Structure: conclusion, details, target audience, notes, contact.
- Subject omission: low tolerance.
- CTA: low.

### 採用

- Tone: sincere and concrete.
- Goal: reduce pre-application anxiety.
- Structure: job overview, work environment, suitable candidates, application path.
- Subject omission: medium tolerance.
- CTA: medium.

## Risky Phrases

Initial risky phrase set:

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
効く
第一歩
```

These are not absolute bans in every context. They are quality risks, especially when repeated or used as generic filler.

See `docs/JAPANESE_STYLE_POLICY.md` for note/Hatena-style rhythm and broader model-frequent word policy.

## Publish Readiness

```json
{
  "publish_readiness": {
    "score": 86,
    "auto_publish_allowed": false,
    "reasons": [
      "一人称は統一済み",
      "根拠なし事実はなし",
      "主語省略リスクが2箇所残る",
      "CTAがやや定型的"
    ]
  }
}
```

Score policy:

- 90 or higher: auto-publish candidate.
- 80-89: human review.
- 70-79: automatic correction and recheck.
- 69 or lower: regenerate or redesign brief.

Never auto-publish medical, legal, financial, hiring-condition, price-sensitive, or high-risk content.
