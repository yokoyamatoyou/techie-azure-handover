# current_mainline_fail_closed_ux_policy_2026-04-25 ROLLBACK

## Baseline

- Current success path remains:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Product owner for this package:
  - `C:\tetie\notecode\note\note_writer_app.py`
- Tests may be added under:
  - `C:\tetie\notecode\note\tests\`

## Rollback Boundary

- Roll back only the review-draft eligibility / UI branch wiring in `note_writer_app.py`.
- Roll back only tests added for this package.
- Docs package can remain as record unless the product decision itself is reversed.

## Do Not Roll Back

- Existing `fingerprint-only` warning policy.
- Source grounding metric correction.
- Existing final quality guard thresholds.
- Existing source contract / leakage / source outside claim checks.

## Do-Not-Retry

- threshold relaxation.
- prompt additions for this symptom.
- repair count or repair trigger additions.
- fail-closed to success conversion.
- showing source不足 / source外 claim / internal leakage bodies.
- moving the implementation into multiple product owners without stopping.

## Stop Boundary

- If a safe draft requires changing output guard semantics, stop.
- If UI cannot render a draft without unredacting unsafe bodies, stop.
- If internal codes are needed in user-facing copy, stop.
