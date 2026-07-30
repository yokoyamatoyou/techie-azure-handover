# DECISIONS

## Independent Decisions

- Runtime uses the `gpt-image-2` alias instead of pinning `gpt-image-2-2026-04-21`.
  - Reason: the model page exposes both alias and snapshot; alias keeps runtime on the current supported GPT Image 2 release while docs record the snapshot used for this work.
- `images.text_quality` defaults to `medium`.
  - Reason: text-bearing cover images need better Japanese text readability than the existing no-text `low` quality posture.
- No-text images keep `images.quality = low`.
  - Reason: the existing cost/latency posture should remain for the text-free variant.
- `images.size` defaults to `1280x672`.
  - Reason: note recommends `1280x670` cover images, while GPT Image 2 requires edges to be multiples of 16. `1280x672` is the nearest valid blog-cover ratio and avoids generating the larger previous `1536x1024` raw asset.
- The auto-image flow lives in `note\blog_image_auto.py` instead of expanding the article pipeline.
  - Reason: image generation must remain post-success and fail-open; article generation success must not depend on image generation.
- GPT Image 2 usage/cost is recorded only when API usage is returned.
  - Reason: permanent accounting should not silently write calculator estimates as actual usage. Live validation records returned usage and notes dimensions/quality directly.
- `output_format` defaults to `jpeg`.
  - Reason: official docs note JPEG is faster than PNG when latency matters, and the app already writes note-facing resized JPEG outputs.
- The generated-image text editing dialog was removed, not merely hidden.
  - Reason: text placement is now owned by GPT Image 2 in the text-bearing variant; keeping a hidden edit path would preserve the old feature surface.
- Text-bearing image prompts keep exact-copy and no-extra-text constraints, but delegate typography and placement to GPT Image 2.
  - Reason: GPT Image 2 can render Japanese text directly; over-specifying sans-serif / bold / contrast / safe margins can make covers less natural. GPT-5.4-mini owns only the short display copy inference.
- Image display copy inference rejects generic or awkward copy when it does not carry article-specific anchors.
  - Reason: `迷わない導入導線` was readable but too detached from the article title. The helper now prefers title/lead anchors such as `導入初期`, `小規模SaaS`, `生成AI`, or concrete comparison terms, and falls back to a title-derived phrase when the inferred copy is too slogan-like.
- Image display copy inference now passes structured data, not only raw title/lead/body.
  - Reason: GPT follows the prompt strongly, but raw article text let the model overweight reader pain (`迷いを減らす`) and underweight the core subject (`小規模SaaS`). The prompt now includes `主題エンティティ`, `主要焦点`, and `推奨コピー候補`; candidate validation requires the core subject when one is extracted.
- Image composition now allows higher information density and uses `at least 15% clean breathing room` instead of broad negative-space targets.
  - Reason: with GPT Image 2 rendering the text directly, the image does not need a large empty overlay zone. Article-specific supporting context is more useful as long as the cover retains at least 15% visual breathing room and avoids clutter.
- Fixed supporting-element counts were removed from active image prompts.
  - Reason: GPT Image 2 follows prompt structure strongly enough that `1-3`, `2-4`, and `4-7` can become artificial budgets. The prompt now asks GPT Image 2 to choose article-adaptive information density while preserving the core subject, readability, no-clutter constraint, and at least 15% clean breathing room.
- Image retry is now conditional on plausibly recoverable errors.
  - Reason: prompt simplification can help content/prompt/transient failures, but authentication, permission, billing, or API-key errors are not fixed by another image prompt. Those are logged and left fail-open without spending a retry.
- `ALGORITHM.md` now includes the image generation algorithm as section 13.
  - Reason: article generation already had a source-of-truth algorithm. The image path now also has a stable contract for trigger timing, two-variant generation, display-copy inference, GPT Image 2 responsibility, retry/regeneration, fail-open behavior, and logging.

## UI Decisions

- Place the image panel directly after article preview / post-result image card.
- Show two stable result slots:
  - `文字入り画像`
  - `文字なし画像`
- Keep save/download actions for generated assets.
- Remove manual prompt/edit/regenerate entrypoints from the visible generated-image surface.
- Show image-generation failure as a non-blocking warning in the image panel while keeping article copy/export usable.

## Prompt Responsibility Split

- GPT-5.4-mini:
  - infer the short Japanese image display copy from generated article title, lead, body, article type, and structured subject/focus hints
  - keep the extracted core subject visible in the display copy when present
- GPT Image 2:
  - decide natural typography, placement, visual composition, and relationship between copy and subject
  - decide article-adaptive information density and include enough article-specific supporting context; large blank areas and fixed element budgets are no longer required
- Prompt constraints retained:
  - render the exact display copy once
  - keep the text readable after note resize
  - keep at least 15% clean breathing room
  - do not add any extra text, letters, numbers, logos, signatures, or watermarks

## Docs / API Notes

- Official GPT Image 2 model docs confirm:
  - model id `gpt-image-2`
  - snapshot `gpt-image-2-2026-04-21`
  - image generation endpoint `v1/images/generations`
  - image edit endpoint `v1/images/edits`
- Image generation docs confirm:
  - output format can be `png`, `jpeg`, or `webp`
  - custom GPT Image 2 sizes are valid when both edges are multiples of 16, the long/short ratio is at most `3:1`, and total pixels are within the documented range
  - moderation supports `auto` and `low`
  - GPT Image model limitations still include possible text-placement/clarity issues
  - GPT Image 2 cost should be estimated from quality/size when API usage is unavailable, but this implementation records returned usage when present
- GPT Image 2-specific safety decisions:
  - never send `input_fidelity`
  - never send `background = transparent`
  - sanitize params through SDK signature filtering to support older/newer SDK call surfaces

## Live Validation Decisions

- The third comparative live case initially failed the current-mainline input gate because comparative reviews require two concrete comparison sources.
- Same-phase self-fix attempt 1 converted the comparison memo into two labeled source documents, but the extractor still did not count enough comparison substance.
- Same-phase self-fix attempt 2 added explicit `比較条件`, `差分`, `用途別の結論`, and `料金条件` labels per source; the gate passed and live validation completed.
- This was kept as a Plan-doc decision because it reflects current-mainline source-fit requirements, not a GPT Image 2 code change.

## Dependency Notes

- Installed `openai==2.32.0` in the active environment after changing `requirements.txt` to `openai>=2.32.0,<3`.
- Pip reported dependency conflicts:
  - `instructor 0.6.8 requires openai<2.0.0,>=1.1.0`
  - `langchain-openai 0.3.28 requires openai<2.0.0,>=1.86.0`
- Focused and shared checks still passed after the SDK upgrade.

## Remaining Risks

- Full test collection is blocked locally by missing `selenium`.
- Full non-Selenium suite still has three unrelated baseline failures listed in `PROGRESS.md`.
- Image API latency can take up to minutes for complex prompts.
- GPT Image 2 text rendering is improved but not guaranteed; live validation passed for the three generated Japanese display copies.
- Current app is not in a git repository; rollback relies on explicit backups and manual reversal for new files / unbacked test changes.
