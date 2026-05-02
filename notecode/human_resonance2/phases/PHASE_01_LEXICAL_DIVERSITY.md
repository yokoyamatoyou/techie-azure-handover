# PHASE 01: Lexical Diversity

## Objective
Detect repetition-heavy outputs and prevent unnatural synonym over-correction.

## Inputs
- article body text
- config keys:
  - `phase01_lexical_enabled`
  - `lexical_threshold`
  - `max_rewrite_ratio`

## Outputs
- `lexical_diversity_score`
- `repetition_signals`
- `rewrite_suggestions` (minimal)

## Tasks (GPT-5 mini granularity)
1. Implement token normalization for Japanese + ASCII words.
2. Add lightweight diversity metric (length-normalized).
3. Detect local repetition windows (sentence/paragraph scope).
4. Generate minimal rewrite suggestions (not full rewrite).
5. Respect `max_rewrite_ratio` cap.

## DoD
1. Score is produced deterministically for same input.
2. Repetition alerts are explainable (with positions).
3. Suggestions do not exceed rewrite cap.

## Test View
1. High repetition text -> low score + alerts.
2. Normal explanatory text -> stable score, no over-alert.
3. Ensure no heading deletion in suggestion path.

## Rollback
Disable `phase01_lexical_enabled`.

## Failure Handling
1. Try one fix for parsing/scoring errors.
2. If unresolved, stop phase and report with failing sample.

