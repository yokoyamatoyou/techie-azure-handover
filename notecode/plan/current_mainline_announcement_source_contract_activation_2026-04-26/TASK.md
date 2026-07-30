# TASK

## Phase 01 - Focused Reproduction

Status: completed

- Add a focused failing test for announcement source documents containing the approval flow notice and FAQ facts.
- Assert FAQ facts enter runtime `source_grounding_items` and `must_cover`.
- Add a non-announcement control showing the fallback does not activate for other article types.

## Phase 02 - Owner-Local Fix

Status: completed

- Read announcement contract preparation, source grounding merge, and must-cover construction in `pipeline.py`.
- Keep the fix inside announcement runtime source contract preparation.
- Activate announcement source contract from fallback source sentences when required slots are discoverable.
- Carry FAQ facts into bounded `source_grounding_items` / `must_cover`.

## Phase 03 - Validation

Status: completed

- Focused tests for announcement contract activation and non-announcement control.
- Existing simple pipeline and quality guard tests.
- Existing current mainline runner / regression / UI matrix tests.
- Two UI attempts for `bl-announcement-spec-change`.
- Artifact checks for body FAQ facts and internal term leakage.

## Stop Conditions

- Stop if the fix requires threshold relaxation.
- Stop if the fix requires prompt text addition.
- Stop if the fix requires extra repair attempts.
- Stop if the fix requires UI demote or output guard changes.
- Stop if non-announcement article types need behavior changes.

No stop condition was hit.
