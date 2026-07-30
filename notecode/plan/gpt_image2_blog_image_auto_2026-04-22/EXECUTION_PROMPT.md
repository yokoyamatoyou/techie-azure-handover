# EXECUTION_PROMPT

Work in `C:\tetie\notecode`.

Implement GPT Image 2 blog image auto flow:

- Keep article generation current mainline path unchanged.
- Update image model/config/API safety for `gpt-image-2`.
- Generate two images automatically after article success:
  - `with_text`
  - `without_text`
- Use same configured image size for both images.
- Use fail-open image handling; image failure must not fail article generation.
- Retry each failed image variant once with a simplified prompt.
- Remove manual generated-image button and generated-image text editing UI.
- Log prompts, paths, retry count, errors, and usage/cost under `logs\gpt_image2_blog_image_auto_2026-04-22\`.
- Update this plan package as each phase progresses.

Constraints:

- Do not alter current mainline article behavior.
- Do not reopen archive/completed/frozen packages.
- Use narrow owner-local tests and shared checks.
- Same phase self-fix limit is 3 attempts.

Execution status: completed in this package. See `PROGRESS.md`, `ROLLBACK.md`, and `DECISIONS.md`.
