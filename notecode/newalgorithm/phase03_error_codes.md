# Phase03 Minimal Error Codes

## Input
- `INP_UNSUPPORTED_ARTICLE_TYPE`
  - unknown article_type
- `INP_UNSUPPORTED_MEDIA`
  - unknown media
- `INP_MISSING_REQUIRED`
  - source/topic の必須入力不足

## System
- `SYS_LLM_RETRY_EXHAUSTED`
  - section generation で LLM retry が上限到達（fallback適用）
- `SYS_PIPELINE_FAILURE`
  - 想定外例外によるパイプライン失敗

## Security/Policy
- `SEC_PROMPT_INJECTION_BLOCKED`
  - topic から指示上書き注入パターンを検出し無効化
- `SEC_LEGAL_ASSERTION_SOFTENED`
  - 危険な法務断定表現を緩和

