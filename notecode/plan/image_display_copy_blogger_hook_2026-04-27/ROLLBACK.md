# ROLLBACK

## Boundary

This workspace is not a git repository. Rollback is file-based.

## Product/Test Files

- `C:\tetie\notecode\note\image_cover_strategy.py`
- `C:\tetie\notecode\note\tests\test_blog_image_auto.py`

## Hashes

Before and after hashes are saved in:

- `C:\tetie\notecode\logs\image_display_copy_blogger_hook_20260427-104613\product_code_hash_before.json`
- `C:\tetie\notecode\logs\image_display_copy_blogger_hook_20260427-104613\product_code_hash_after.json`

## Manual Rollback

Restore the previous versions of the two files above from local backup or editor history, then rerun:

- `C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile C:\tetie\notecode\note\image_cover_strategy.py`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest C:\tetie\notecode\note\tests\test_blog_image_auto.py -q`

Do not change `blog_image_auto.py`, image API parameters, UI, article generation, or guards as part of rollback.
