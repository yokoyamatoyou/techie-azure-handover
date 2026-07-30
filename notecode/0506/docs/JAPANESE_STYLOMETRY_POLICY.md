# Japanese Stylometry Policy

## Purpose

Stylometry is used to detect unnatural, repetitive, or GPT-like Japanese blog writing.

It is not used to force every article into one numeric target. Metrics should create review signals and targeted rewrite instructions.

## Background

Japanese stylometry and quantitative linguistics commonly use features such as:

- morphemes
- parts of speech
- POS n-grams
- function words and function phrases
- phrase or bunsetsu-level patterns
- sentence length
- punctuation
- comma usage
- character-type ratios
- sentence-final forms
- lexical diversity
- genre differences

This project uses those ideas pragmatically for blog quality checks, not for full academic authorship attribution.

## Tokenization Basis

- Tokenizer: SudachiPy
- Dictionary: `sudachidict_core`
- Default split mode: `SplitMode.C`

Use `SplitMode.C` as the default because blog-level QA benefits from preserving longer compounds and proper nouns. If a metric needs shorter units, add a metric-local tokenizer mode instead of changing the global default.

## Metric Groups

### 1. Sentence Metrics

Track sentence count, average sentence length, median sentence length, max sentence length, long sentence ratio, very short sentence ratio, and sentence length variance.

Use for:

- detecting flat rhythm
- detecting overly long explanatory sentences
- detecting short-fragment overuse

Initial issue links:

- `sentence_too_long`
- `sentence_rhythm_monotony`

### 2. Paragraph and Line-Break Metrics

Track paragraph count, sentences per paragraph, paragraph length distribution, blank-line interval distribution, repeated paragraph shape, and section-level paragraph symmetry.

Use for:

- detecting uniform AI-like formatting
- detecting note/Hatena-unfriendly block rhythm
- detecting every section having the same shape

Initial issue links:

- `paragraph_rhythm_monotony`
- `line_break_monotony`

### 3. Ending Metrics

Track sentence-final surface forms, normalized ending buckets, ending repetition windows, late-half ending concentration, and `です` / `ます` / noun-ending / plain-style balance.

Example ending buckets:

```text
です
ます
ました
できます
でしょう
ください
名詞止め
体言止め
問いかけ
余韻短文
```

Use for:

- detecting repetitive closing rhythm
- detecting GPT-like late-half summaries
- detecting monotonous `です/ます` endings

Initial issue links:

- `ending_repetition`
- `ending_bucket_monotony`

### 4. Connector Metrics

Track repeated connectors, connector position, paragraph-initial connector ratio, and overuse of `また`, `さらに`, `一方で`, `そのため`, `このように`.

Use for:

- detecting mechanical transitions
- detecting generic essay structure

Initial issue links:

- `connector_repetition`
- `ai_like_phrase`

### 5. Morphological and POS Metrics

Track POS distribution, content word ratio, function word ratio, noun-heavy ratio, verb/adjective balance, nominalization ratio, auxiliary and particle patterns, and POS n-gram repetition.

Use for:

- detecting abstract noun stacking
- detecting translation-like nominalization
- detecting repeated grammatical templates

Initial issue links:

- `style_mismatch`
- `ai_like_phrase`
- `nominalization_overuse`

### 6. Lexical Diversity Metrics

Track token count, unique token count, type-token ratio, Guiraud-like diversity score, repeated content-word clusters, and repeated abstract nouns.

Use for:

- detecting thin articles
- detecting repeated claims
- detecting GPT-like paraphrase loops

Initial issue links:

- `duplication`
- `model_frequent_word`

### 7. Character-Type Metrics

Track kanji ratio, hiragana ratio, katakana ratio, alphabet ratio, digit ratio, and punctuation ratio.

Use for:

- detecting excessive stiffness
- detecting foreign-word overuse
- detecting unnatural symbol or list-heavy output

Initial issue links:

- `style_mismatch`
- `formatting_mismatch`

### 8. Viewpoint and Narrator Metrics

Track first-person variants, third-party viewpoint terms, company-name-as-narrator count, customer voice markers, and unattributed testimonial-like phrases.

Use for:

- detecting `私たち` / `当社` / company-name mixing
- detecting `同社` leakage
- detecting customer voice blending

Initial issue links:

- `first_person_inconsistency`
- `third_party_viewpoint_leakage`
- `narrator_mixing`
- `unattributed_customer_voice`

### 9. Model-Frequent Word Metrics

Track watchlist terms from `docs/JAPANESE_STYLE_POLICY.md`, including:

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

Use for:

- detecting generic encouragement
- detecting unsupported emotional inflation
- detecting GPT-like closing vocabulary

Initial issue links:

- `model_frequent_word`
- `generic_encouragement_phrase`

## Stylometry Output Contract

The stylometry service should return structured measurements and issue candidates.

```json
{
  "stylometry": {
    "sentence_count": 18,
    "avg_sentence_length": 48.2,
    "sentence_length_variance": 120.4,
    "paragraph_count": 7,
    "paragraph_shape": [2, 2, 3, 2, 2, 3, 1],
    "ending_distribution": {
      "ます": 8,
      "です": 5,
      "ました": 3,
      "noun_ending": 2
    },
    "repeated_connectors": ["また"],
    "first_person_variants": ["私たち"],
    "third_party_terms": [],
    "model_frequent_words": [
      {
        "term": "第一歩",
        "count": 2,
        "risk": "medium"
      }
    ],
    "issue_candidates": [
      {
        "type": "ending_bucket_monotony",
        "severity": "medium",
        "reason": "late-half sentences concentrate in the same ending bucket"
      }
    ]
  }
}
```

## Implementation Ownership

Expected module:

```text
app/services/stylometry.py
```

Expected config:

```text
app/config/stylometry.yaml
```

The service should be deterministic and must not call an LLM.

The quality checker may use stylometry output to create QA issues, but stylometry itself should not rewrite text.

## Cautions

- Metrics are signals, not publication decisions by themselves.
- Do not enforce one universal sentence length target across all genres.
- Do not hard-ban model-frequent words globally.
- Do not make generated text unnaturally varied just to satisfy variance metrics.
- Use genre-specific thresholds from config.
