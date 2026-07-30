# Live A/B Preflight — One Approved Run

- approval: explicit user approval received 2026-07-10 JST
- scope: one saved Sanrei source packet, isolated package only
- model: `gpt-5.6-luna`
- official model page: `https://developers.openai.com/api/docs/models/gpt-5.6-luna`
- API surface: Responses API
- reasoning effort: `low` for all three calls
- retries: `0`
- total send cap: `3`

## Arms

- A: same compact company-side blogger contract, one full-article call
- B1: same compact company-side blogger contract, one full-article call
- B2: same contract and same source ledger, bounded self-reread of B1; rewrite only failed paragraph plus one adjacent sentence, return full article

## Frozen inputs

- source packet: saved `selected_source_excerpts.json` for `01_sanrei_foods`
- excerpt count: `4`
- claim IDs: preserved from the saved excerpts
- raw full source: not sent
- source URLs: not sent as instructions or retrieval targets
- Route V UI/service: not invoked

## Reasoning

The second stage keeps the blogger identity and changes only the task. This isolates whether a bounded self-reread improves low-interest opening, self-perspective, zero-anaphora clarity, and source-specific lexical material. It avoids the historical editor-role switch that reached floor/H1 but still scored 84 with `sentence_too_long` and `model_frequent_word`.

## Stop conditions

Stop immediately on preflight mismatch, missing key, API error, malformed response, A failure, or B1 failure. Do not retry. Do not run image generation, source refetch, Route V, fallback, or a second source.
