# TASK

## Phase 01: Display Copy Hook Narrow Improvement

- Owner: `image_cover_strategy.py`
- Hypothesis: `display_text` can become more blog-cover-like by improving copy inference / validation / fallback only.
- Status: completed.

## Required Checks

- `C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile C:\tetie\notecode\note\image_cover_strategy.py`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest C:\tetie\notecode\note\tests\test_blog_image_auto.py -q`

## Gate

- Pass focused checks.
- Preserve fail-open image generation behavior.
- Do not touch image API parameters or article generation.
