# PHASE 02: Burstiness

## Objective
Control sentence-length rhythm so text feels human while staying readable and stable.

## Inputs
- article body text
- config keys:
  - `phase02_burstiness_enabled`
  - `burstiness_target_min`
  - `burstiness_target_max`
  - `max_sentence_split_ratio`

## Outputs
- `burstiness_score`
- `length_profile` (sentence and paragraph level)
- `rhythm_adjustments` (minimal)

## Tasks (GPT-5 mini granularity)
1. Measure sentence-length distribution per paragraph.
2. Detect monotonous zones (too uniform / too fragmented).
3. Propose minimal split/merge candidates with readability guard.
4. Keep adjustment ratio under `max_sentence_split_ratio`.
5. Preserve factual order and heading structure.

## DoD
1. Output rhythm profile is deterministic for same input.
2. Uniform text is adjusted toward target range without over-edit.
3. Heading and section boundaries are unchanged.

## Test View
1. Flat sentence-length sample -> score improves after adjustments.
2. Already natural sample -> no unnecessary edits.
3. Confirm no list/heading corruption.

## Rollback
Disable `phase02_burstiness_enabled`.

## Failure Handling
1. Try one correction for boundary parsing or split logic.
2. If unresolved, stop phase and report failing sample and reason.

