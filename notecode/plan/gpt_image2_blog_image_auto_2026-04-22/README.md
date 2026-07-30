# GPT Image 2 Blog Image Auto Flow

## Objective

GPT Image 2 (`gpt-image-2`) に対応し、記事生成成功後に note 用カバー画像を自動生成する。
本文生成は current mainline のまま維持し、画像生成は fail-open の後続処理として扱う。

## Source Of Truth

- Runtime path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- Image runtime/UI owner:
  - `C:\tetie\notecode\note\blog_image_auto.py`
  - `C:\tetie\notecode\note\llm_client.py`
  - `C:\tetie\notecode\note\note_writer_app.py`
  - `C:\tetie\notecode\note\image_prompt_helpers.py`
  - `C:\tetie\notecode\note\image_config.py`
  - `C:\tetie\notecode\core\app_config.py`
  - `C:\tetie\notecode\core\token_tracker.py`
- This plan package:
  - `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\`

## Scope

- `images.model_name` / defaults を `gpt-image-2` に移行する。
- ブログ生成後に「文字入り画像」と「文字なし画像」を同じ画像サイズで各1枚生成する。
- 文字入り画像は GPT Image 2 の文字描画を使い、既存の後処理テキストオーバーレイ UI は削除する。
- 画像生成失敗時は、プロンプト簡略化で回復しそうな場合だけ1回再生成する。
- リトライ後も失敗した場合、記事生成は成功のまま保持し、画像パネルだけ失敗表示にする。
- 実行ログ、画像パス、プロンプト、リトライ有無、使用量/コスト情報を `logs` 配下に保存する。

## Non Goals

- 本文生成アルゴリズム、source contract、persona contract の変更。
- pre-2026-04-02 records、completed reference package、frozen architecture package の reopen。
- 画像 edits endpoint を使う編集機能の再設計。
- 永続的な精密コスト課金 UI の追加。

## OpenAI Docs Summary

- GPT Image 2 model page:
  - model id: `gpt-image-2`
  - snapshot: `gpt-image-2-2026-04-21`
  - endpoints: `v1/images/generations`, `v1/images/edits`
- Image generation guide:
  - `quality`: `low`, `medium`, `high`, `auto`
  - `output_format`: default `png`; `jpeg` / `webp` supported
  - `background`: `opaque` or `auto`; `transparent` is not supported for `gpt-image-2`
  - `moderation`: `auto` or `low`
  - `input_fidelity`: omit for `gpt-image-2`; image inputs are high fidelity by default
  - cost = input text tokens + edit input image tokens + image output tokens
- Prompting guide:
  - write structured prompts with scene, subject, visual details, and constraints
  - for in-image text, quote exact copy and specify typography, placement, contrast, and no extra characters
  - use `medium` or `high` quality for small/dense text; this package uses `medium` for text-bearing cover images

Sources:

- https://developers.openai.com/api/docs/models/gpt-image-2
- https://developers.openai.com/api/docs/guides/image-generation
- https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide

## UI Decision Summary

Reference products place generated images near the editor/result surface, not as an unrelated primary workflow.

- Jetpack AI generates from post content in the block editor and then shows the result in the featured image position.
- WordPress AI Featured Image keeps generation in the post editor / media flow and supports text-free vs text-allowed choices.
- Canva Text to Image keeps prompt input and generated options close to the design/editor surface.

Decision:

- Keep article output primary.
- Convert the existing post-result image card into an automatic result panel immediately after article preview.
- Remove the manual image generation button and generated-image text editing controls.
- Show two fixed result slots: `文字入り画像` and `文字なし画像`.
- Show image errors only in the image panel; article copy/export remains usable.

UI references:

- https://jetpack.com/resources/generating-featured-images-for-your-posts-using-jetpack-ai/
- https://wordpress.org/plugins/ai-featured-image-generator/
- https://www.canva.com/learn/how-to-convert-text-images-ai-magic/

## Outcome

- GPT Image 2 config/API safety implemented.
- Blog post-success auto image generation implemented as fail-open helper flow.
- `with_text` and `without_text` variants are generated at configured raw size `1280x672`.
- Note-facing resized outputs remain `1280x670`.
- Manual image generation button and generated-image text editing dialog removed.
- Follow-up: fixed element-count density instructions were removed; GPT Image 2 now owns article-adaptive supporting detail while retaining at least 15% clean breathing room.
- Follow-up: `ALGORITHM.md` now records the image generation algorithm, trigger timing, retry/regeneration rule, and logging contract.
- Live validation completed for 3 current-mainline articles and 6 images.
- Detailed results are recorded in:
  - `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\PROGRESS.md`
  - `C:\tetie\notecode\logs\gpt_image2_blog_image_auto_2026-04-22\live_validation_summary.json`
