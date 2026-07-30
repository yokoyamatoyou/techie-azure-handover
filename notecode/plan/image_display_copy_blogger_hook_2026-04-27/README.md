# Image Display Copy Blogger Hook

## Objective

Improve GPT Image 2 `with_text` cover-image `display_text` so it reads less like an explanation label and more like a short note / Hatena blog cover copy that gives readers a reason to open the article.

## Scope

- Runtime owner: `C:\tetie\notecode\note\image_cover_strategy.py`
- Test owner: `C:\tetie\notecode\note\tests\test_blog_image_auto.py`
- Artifact: `C:\tetie\notecode\logs\image_display_copy_blogger_hook_20260427-104613\`

## Non Goals

- Do not change GPT Image 2 API contract, model, size, quality, retry count, or output format.
- Do not change `blog_image_auto.py` prompt body.
- Do not change article generation, persona, source contract, quality guard, output guard, UI, or pipeline.
- Do not introduce source-outside claims or advertising-style overclaims into image copy.

## Outcome

- `display_text` prompt now asks for a short cover copy that is not a plain label.
- Deterministic fallback now prefers bounded article-type hook shapes before falling back to `subject + focus` labels.
- Validation rejects label-like copy, generic slogans, and unsupported overclaims while allowing source-supported question / decision-axis copy.
