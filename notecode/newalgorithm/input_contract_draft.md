# Input Contract Draft v1（Phase01確定）

## Required
- `source` (string | list[string])
- `topic` (string)
- `article_type` (enum)
  - `explanatory_article`
  - `daily_story`
  - `branding`
  - `announcement`
  - `case_study`
  - `industry_analysis`
  - `comparative_review`
- `media` (enum: `note`, `hatena`, `seo`)

## Optional
- `audience_profile` (string)
- `speaker_profile` (string)
- `writer_role` (string)
- `perspective` (string)
- `content_goal` (string)
- `writing_focus` (string)
- `structure` (string)
- `length_mode` (string)
- `tone_profile` (string)
- `allow_experience` (bool)
- `interview_answers` (dict[str, string])
- `image_generation.enabled` (bool)
- `image_generation.mode` (enum)

## Normalized Fields（system-owned）
- `style_compact_for_seo` (bool)
  - `article_type=daily_story` かつ `media=seo` の場合のみ `true`
  - それ以外は `false`
- `question_mode` (enum)
  - `article_type=announcement` の場合 `skip_default`
  - それ以外は `standard`
- `contract_version` (string)
  - `input_contract_v1` を付与

## Validation Rules
- unknown `article_type` は `validation_error` として reject
- unknown `media` は `validation_error` として reject
- `source` と `topic` の両方が空の場合は `validation_error` として reject
- normalized fields（`style_compact_for_seo`, `question_mode`, `contract_version`）はUI編集不可

## エラーコード（v1）
- `INP_UNSUPPORTED_ARTICLE_TYPE`
- `INP_UNSUPPORTED_MEDIA`
- `INP_MISSING_REQUIRED`

