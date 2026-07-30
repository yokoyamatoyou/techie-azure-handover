# current_mainline_explanatory_article_regression_diagnosis_2026-04-26 ROLLBACK

## Rollback Boundary

This package is docs-only.

Rollback consists of:

1. Delete `C:\tetie\notecode\plan\current_mainline_explanatory_article_regression_diagnosis_2026-04-26\`.
2. Remove the corresponding `2026-04-26` entry from `C:\tetie\WORKLOG.md`.

No runtime rollback is required because no product code changed.

## Files In Scope

- `C:\tetie\notecode\plan\current_mainline_explanatory_article_regression_diagnosis_2026-04-26\README.md`
- `C:\tetie\notecode\plan\current_mainline_explanatory_article_regression_diagnosis_2026-04-26\TASK.md`
- `C:\tetie\notecode\plan\current_mainline_explanatory_article_regression_diagnosis_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_explanatory_article_regression_diagnosis_2026-04-26\ROLLBACK.md`
- `C:\tetie\WORKLOG.md`

## Do Not Retry In This Package

Do not change:

- thresholds
- prompts
- repair behavior
- UI demotion behavior
- `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py`
- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

Do not classify source shortage alone as a runtime defect. The diagnosis is specifically about polluted source grounding denominator and harness/summary classification mismatch.

## Future Fix Boundary

Any future implementation must be opened separately with one owner and one hypothesis.

Recommended first owner if approved:

- `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`

Recommended hypothesis:

- Ignore path/hash-like metadata source items in source grounding denominator while preserving thresholds and unsupported-claim safety.
