# ROLLBACK

## Rollback Boundary

This workspace is not currently inside a git repository. Rollback is file-based.

Do not use `git reset` assumptions for this package. Restore explicit backup files or manually reverse the listed changes.

## Backup Location

Pre-change backups were created here:

- `C:\tetie\notecode\logs\gpt_image2_blog_image_auto_2026-04-22\rollback_backup\`

Backed-up files:

- `tetie__notecode__config.json`
- `tetie__notecode__requirements.txt`
- `tetie__notecode__core__app_config.py`
- `tetie__notecode__core__token_tracker.py`
- `tetie__notecode__note__image_config.py`
- `tetie__notecode__note__llm_client.py`
- `tetie__notecode__note__note_writer_app.py`
- `tetie__notecode__note__image_prompt_helpers.py`
- `tetie__notecode__note__tests__test_llm_client_runtime.py`
- `tetie__notecode__note__tests__test_note_writer_app_post_success_helpers.py`

No pre-change backup exists for newly added files, `ALGORITHM.md`, or for `note\tests\test_newalgorithm_phase07_acceptance.py`; manually reverse those updates if rolling back.

## Actual Touched Files

- `C:\tetie\notecode\config.json`
- `C:\tetie\notecode\requirements.txt`
- `C:\tetie\notecode\core\app_config.py`
- `C:\tetie\notecode\core\token_tracker.py`
- `C:\tetie\notecode\note\image_config.py`
- `C:\tetie\notecode\note\llm_client.py`
- `C:\tetie\notecode\note\blog_image_auto.py`
- `C:\tetie\notecode\note\image_prompt_helpers.py`
- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\tests\test_llm_client_runtime.py`
- `C:\tetie\notecode\note\tests\test_blog_image_auto.py`
- `C:\tetie\notecode\note\tests\test_note_writer_app_post_success_helpers.py`
- `C:\tetie\notecode\note\tests\test_newalgorithm_phase07_acceptance.py`
- `C:\tetie\notecode\ALGORITHM.md`
- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\README.md`
- `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\TASK.md`
- `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\PROGRESS.md`
- `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\ROLLBACK.md`
- `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\EXECUTION_PROMPT.md`
- `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\DECISIONS.md`

Generated validation artifacts:

- `C:\tetie\notecode\logs\gpt_image2_blog_image_auto_2026-04-22\*.json`
- `C:\tetie\notecode\logs\gpt_image2_blog_image_auto_2026-04-22\live_articles\*.md`
- `C:\tetie\notecode\note\generated_images\gen_*`

## Safe Rollback Procedure

1. Restore backed-up files from `rollback_backup`.
   - Example mapping:
     - `tetie__notecode__config.json` -> `C:\tetie\notecode\config.json`
     - `tetie__notecode__note__llm_client.py` -> `C:\tetie\notecode\note\llm_client.py`
2. Restore `config.json` image settings to the prior values if doing a manual rollback:
   - `model_name`: `gpt-image-1.5`
   - `fallback_model`: `gpt-image-1`
   - `quality`: `low`
   - `size`: `1536x1024`
     - If rolling back only the 2026-04-24 size follow-up, restore from current `1280x672` to `1536x1024`.
   - `count`: `2`
   - remove `text_quality`, `output_format`, `background`, `moderation`
3. Restore `requirements.txt` OpenAI SDK pin if needed:
   - `openai==1.54.5`
4. Remove new implementation/test files:
   - `C:\tetie\notecode\note\blog_image_auto.py`
   - `C:\tetie\notecode\note\tests\test_blog_image_auto.py`
5. Restore `note\image_prompt_helpers.py` and `note\tests\test_note_writer_app_post_success_helpers.py` from backup if rolling back the 2026-04-23 density follow-up.
6. Manually reverse `ALGORITHM.md` section 13, the AGENTS route additions, `WORKLOG.md` route-sync entry, and `note\tests\test_newalgorithm_phase07_acceptance.py` to their previous expectations if needed.
7. Remove generated live-validation artifacts only if they are no longer useful.
8. Rerun:
   - `py -m pytest note/tests/test_llm_client_runtime.py note/tests/test_note_writer_app_post_success_helpers.py note/tests/test_newalgorithm_phase07_acceptance.py -q`
   - `py -m pytest note/tests/test_current_mainline_runner.py note/tests/test_simple_note_pipeline.py note/tests/test_current_mainline_ui_generation_state_adapter.py note/tests/test_current_mainline_ui_result_adapter.py note/tests/test_current_mainline_ui_matrix.py note/tests/test_image_prompt_mixin_structure.py -q`

## Do Not Roll Back

- Do not reopen or modify pre-2026-04-02 archive records.
- Do not reopen completed reference packages.
- Do not reopen frozen architecture package.
- Do not change the current article mainline path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
