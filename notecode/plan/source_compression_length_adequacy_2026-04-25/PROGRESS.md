# source_compression_length_adequacy_2026-04-25 PROGRESS

## Current Status

- Package status: active
- Current phase: Phase 5 closeout
- Behavior change: no
- Current hypothesis:
  - Source compression may be reducing visible explanation material for some article types, but previous 8-type validation was overall OK. Treat this as measurement first, not a length-increase task.
- Current verdict:
  - `OK_with_watch_items`
  - Runtime fix is not recommended in this package window.

## Phase Ledger

| Phase | Owner files | Moved/changed responsibility | Behavior change | Tests run | Result | Failure attempts | Next phase |
|---|---|---|---|---|---|---|---|
| 0 | `plan/source_compression_length_adequacy_2026-04-25/*` | new audit package only | no | `pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q`; `pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q` | `255 passed`; `343 passed` | 0 | Phase 1 |
| 1 | `logs/source_compression_length_adequacy_20260425-092448/*` | previous validation metrics extraction | no | generated metrics only | `previous_validation_metrics.json` / `.md` written | 0 | Phase 2 |
| 2 | `plan/source_compression_length_adequacy_2026-04-25/audit_runner.py`, `logs/source_compression_length_adequacy_20260425-093131/*` | audit runner and live audit metrics | no runtime change | `python plan\source_compression_length_adequacy_2026-04-25\audit_runner.py --watch-repeats 2` | 14 runs, 13 success, 1 fail-closed OK, leakage 0 | 0 | Phase 3 |
| 3 | `logs/source_compression_length_adequacy_20260425-093131/classification.*` | classification by type and cause | no | manual Codex visual review of generated txt artifacts | `OK_with_watch_items`; no regression | 0 | Phase 4 |
| 4 | none | no fix selected | no | not run | evidence does not isolate one owner; no runtime change | 0 | Phase 5 |
| 5 | `PROGRESS.md`, `C:\tetie\WORKLOG.md` | closeout record | no | baseline tests already green | complete | 0 | close |

## Baseline Notes

- Current success path remains:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Current mainline remains `single-pass + optional single repair 1回`.
- Previous multi-type validation had `8/8` final success and no visible internal-term leakage.
- Previous company intro 10-run validation had `9/10 OK`; old source-clearing final-reflection failure shape was `0/10`.

## Phase 1 Previous Metrics

- Output:
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-092448\previous_validation_metrics.json`
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-092448\previous_validation_metrics.md`
- Previous logs did not expose `target_chars`, so `body_chars / target_chars` remains `not available`.
- Generic grounding rows did not expose a source fact reflected count; company introduction source slot coverage was available.

## Phase 2 Audit Metrics

- Output:
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\audit_metrics.json`
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\audit_metrics.md`
  - generated `.json` / `.txt` per run
- Runs:
  - 8 baseline article-type rows
  - 2 additional repeats each for `industry_analysis`, `branding/company_introduction`, and `case_study`
- Result:
  - `14` runs
  - `13` success
  - `1` fail-closed OK for company introduction
  - visible internal-term leakage `0`

## Phase 3 Classification

- Output:
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\classification.json`
  - `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\classification.md`
- Type classifications:
  - `explanatory_article`: OK. 1830 chars, source is short but explanation range is sufficient.
  - `industry_analysis`: thin_due_to_source. Source was only 127 chars; 3 runs produced 948 / 1521 / 1350 chars.
  - `branding/company_introduction`: acceptable_but_watch. Source was 3242 chars and packet 638 chars; successful audit runs were 1274 and 933 chars, with one fail-closed run. Required operational slots were covered, but explanation depth stays low.
  - `branding/product_introduction`: thin_due_to_source. Source was 146 chars; body was natural but 1208 chars.
  - `announcement`: OK. 609 chars is natural for announcement.
  - `case_study`: thin_due_to_source. Source was 261 chars; runs were 979 / 1138 / 1475 chars.
  - `comparative_review`: thin_due_to_source. Source was 172 chars; 1548 chars is near range but source-limited.
  - `daily_story`: OK. 923 chars is natural for daily story.

## Phase 4 Decision

- No narrow runtime fix selected.
- Reason:
  - Most low-length outputs are explained by very thin source material.
  - `company_introduction` is the only source-rich low-length watch item, but this package did not isolate whether the cause is source packet compression, target/length estimation, or article-type acceptance.
  - `target_chars` is not currently present in the captured previous/audit artifacts.
- Next evidence needed before a fix:
  - capture `target_chars` or equivalent length-mode decision
  - capture source packet composition before/after compression for company introduction
  - compare whether company introduction short outputs omit concrete source material or merely compress all required slots tersely

## Next Action

- Proceed to next engineering phase without a runtime change from this package.
- If reopened, start with diagnostics capture for company introduction length/source packet adequacy, not with a broad length increase.
