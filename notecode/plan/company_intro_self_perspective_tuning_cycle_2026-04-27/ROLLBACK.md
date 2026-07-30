# ROLLBACK

## Baseline

Before any product-code fix, record SHA256 for:

- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- current mainline and image-related product files included in the cycle hash snapshot

## Rollback Boundary

Only `prompt_builder.py` may be changed. If a fix is rejected or causes regression, restore that file to the pre-fix content and rerun the focused checks needed to confirm rollback.

## Rollback Record 2026-04-27

Fix 1 changed only `prompt_builder.py` and related test expectations, then was rejected because the validation cycle did not prove announcement/comparative non-regression and further progress would require harness/session owner work.

Rollback completed:

- `prompt_builder.py` restored to pre-fix SHA256 prefix `107FBA612F0D1F18...`.
- Focused py_compile passed.
- Focused `test_simple_note_pipeline.py` selection passed.
- Focused `test_current_mainline_runner.py` selection passed.

## Do Not Retry

- Do not retry by changing source contract, quality guard, output guard, pipeline, blog image auto, image prompt, threshold, repair count, UI default role, target chars, or length mode.
- Do not add persona routes.
- Do not increase first-person terms mechanically.
- Do not continue after two product-code fix attempts.
