# TASK

Status: completed. See `PROGRESS.md` for final test and live-validation results.

## Phase 0: Research And Baseline Package

Owner scope: docs and current implementation mapping.

Gate:

- Plan package exists.
- `PROGRESS.md` records read-order completion, docs findings, UI decision, current files, SDK/config baseline.

## Phase 1: GPT Image 2 API Safety

Owner scope: config, SDK requirement, image API params, token tracking.

Tasks:

- Change default/config image model to `gpt-image-2`.
- Add text image quality default `medium` while keeping no-text image quality from existing config.
- Update OpenAI SDK requirement to a GPT Image 2 capable range.
- Ensure `input_fidelity` and `background: transparent` are never sent for `gpt-image-2`.
- Support `output_format`, `background`, and `moderation` only when accepted by the SDK/API call surface.
- Add GPT Image 2 image cost/rate support.

Gate:

- Unit tests prove GPT Image 2 params are safe and current `1280x672` size is preserved.

## Phase 2: Automatic Image Flow

Owner scope: post-generation image orchestration.

Tasks:

- Add a small helper module for article-image request planning, prompt building, logging, retry, and fail-open result handling.
- After article generation success and legal postcheck, run automatic image generation.
- Generate exactly one `with_text` image and one `without_text` image.
- Retry each failed variant once with a simplified prompt when the error is plausibly recoverable by prompt repair/regeneration.
- Keep article success when image generation fails.

Gate:

- Tests cover image success, one-retry success, and retry-exhausted fail-open.

## Phase 3: GPT Image 2 Prompt Refresh

Owner scope: prompt construction.

Tasks:

- Build article-aware prompts from title, lead/body, article type, and selected visual pattern.
- Text image prompt includes exact quoted Japanese copy and delegates typography/placement/density to GPT Image 2.
- No-text prompt includes no text / letters / numbers / logos / watermark constraints.
- `simple` / `balanced` / `rich` are weak visual-direction guides, not fixed element-count budgets.
- Avoid persona names, source contract leakage, or visible runtime trial names.

Gate:

- Deterministic prompt tests pass for Japanese article input and both variants.

## Phase 4: UI Cleanup

Owner scope: visible image UI.

Tasks:

- Remove manual generated-image button from the post-result card.
- Remove generated-image text editing entrypoint/dialog from visible UI.
- Replace output with automatic image status/result panel.
- Keep save/download controls for generated images.

Gate:

- UI import/smoke tests pass.
- No visible generated-image edit entrypoint remains.

## Phase 5: Live Validation

Owner scope: API-backed validation after tests pass.

Tasks:

- Generate 3 different article genres.
- Produce 6 images total: 3 text-bearing and 3 text-free.
- Check article alignment, Japanese text readability, no-text cleanliness, and note resize integrity.
- Record paths, prompts, retry status, quality notes, and observed usage/cost.

Gate:

- `logs\gpt_image2_blog_image_auto_2026-04-22\` contains validation records.
- `PROGRESS.md` records pass/fail and any blockers.

## Phase 6: Closeout

Owner scope: shared checks and docs completion.

Tasks:

- Run owner-local and shared checks.
- Update `PROGRESS.md`, `ROLLBACK.md`, and `DECISIONS.md`.
- Report independent decisions, remaining risks, and validation status.

Gate:

- Docs reflect actual changed files and test/live validation outcome.

## Retry Stop

- Same phase self-fix limit: 3 attempts.
- Stop and report only if the phase still fails after 3 attempts or external credentials/services make validation impossible.

## Shared Checks

- Current mainline runner tests.
- Simple pipeline tests.
- UI generation state/result adapter tests.
- Image API/prompt tests.
- No live API calls until owner-local tests pass.
