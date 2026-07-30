# Writer-only UI Port 2026-06-02

## Purpose

`C:\Users\横山裕明\Desktop\ブログ` のMVP経路を、`C:\tetie\notecode` の既存UIへ小さく接続する。

既存の Route 0506、Route A、repair、quality pipeline、image generation は削除しない。本文生成の軽量経路では、それらを呼ばずに writer-only で記事を作る。

## Runtime Path

UIの `記事を生成` ボタンから次が動く。

```text
state.sources
  -> strict URL policy / robots / redirect fail-closed
  -> data/writer_only_sources/<run_id>/source_*.json
  -> source_bundle.json metadata / excerpt / claims only
  -> brief
  -> writer-only OpenAI Responses call
  -> Markdown draft with H1 title and H2 sections
  -> LinkedIn post generated from extracted article points in the same writer response
  -> rule-based smoke evaluator
  -> Markdown preview / logs/writer_only_generation/<run_id>/draft.md
```

## Boundaries

- OpenAIへ実際に発火するroleは writer だけ。
- `source_bundle` には `full_text` を入れない。
- writer instructionは短い固定文だけを使い、外部sourceをcontrol instructionへ混ぜない。
- モデル名とパラメータは `config.json` の `writer_only` から読む。
- `gpt-4.1` と `gpt-5.4` は別familyとしてvalidationし、未対応パラメータは送信前にエラーにする。
- ログには `writer_only=true`、`route_0506_used=false`、`route_a_used=false`、`repair_used=false` を残す。
- Writer output is checked for a Markdown H1 title and H2 section structure.
- Source intake uses embedded HTML/XML charset declarations when server-declared encoding is a low-confidence Latin-1 fallback.
- Source intake removes common page chrome before building `source_bundle` excerpts and claims.
- SNS output is generated in the same writer API call as the article body.
- Article body contract uses a source-aware deterministic minimum: thin source bundles keep the 300 character floor, two-source/thicker bundles use 900 characters, and source_count >= 3 / source_char_total >= 3000 / claims_count >= 12 use 1300 characters. The 2000 character ceiling and no forced padding rule remain.
- When multiple source URLs are available, the smoke evaluator requires source URL coverage in the body or reference links: 2 URLs for 2-3 sources and 3 URLs for 4+ sources.
- SNS output uses `linkedin_short_text` as the primary UI/copy compatibility key and keeps it within 700 Japanese characters.
- The compatibility `linkedin_text` key is retained for existing artifacts/callers, but writer-only runtime normalizes it to the same SNS post text as `linkedin_short_text`.
- SNS fallback recomposition is used when the model omits the SNS fields, exceeds 700 characters, or omits company-side first person such as `私たち` / `当社`.
- The primary SNS text area is visible outside the generated-output detail expansion. Only the compatibility SNS field remains in the detail expansion.
- UX decision for the next UI owner: move the image tone selector before generation so the selected tone can affect the first automatic post-success image run.
- UX decision for the next UI owner: keep one main generation progress bar and update user-facing copy through blog creation, SNS text creation, image generation, image success, or image failure.

## Verification

Focused commands:

```powershell
py -3.11 scripts\validate_writer_only_config.py
py -3.11 -m pytest note\tests\test_writer_only_generation.py -q
py -3.11 -m pytest note\tests\test_note_writer_app_generation_execution_helpers.py note\tests\test_note_writer_app_post_success_helpers.py -q
```

Live validation artifact:

```text
C:\tetie\notecode\logs\writer_only_generation\writer_only_openai_validation_20260602\draft.md
```

The validation used one OpenAI writer call and did not use Route 0506, Route A, repair, quality pipeline, or image generation.

## 2026-06-02 UI Simplification

Route 0506 is treated as a failed/non-MVP algorithm for this UI. The old Route 0506/current-mainline preparation wizard and old body-generation button are hidden from the main page. The visible generation button is writer-only.

Existing Route 0506 files are not deleted in this change. They are left as dormant legacy code to avoid a broad destructive cleanup.

The visible generation UI now hides the old current-mainline preparation wizard. The visible buttons are source add and writer-only article generation.

Startup import isolation followup:

- `note_writer_app.py` no longer imports `note.route_0506_ui_bridge` at startup.
- `import note.note_writer_app` leaves no `route_0506` modules in `sys.modules`.
- The Route 0506 files are still present on disk as dormant legacy code.

Writer-only refactor followup:

- `note_writer_app.py` no longer imports `note.current_mainline_runner` or `note.simple_note_pipeline.pipeline.MinimalPipeline` at startup.
- Legacy Route A/current-mainline helper names remain as lazy compatibility wrappers so the hidden old route can fail or run only when explicitly reached.
- Route 0506 files were not moved or deleted. Archive candidates are recorded under `logs/writer_only_refactor_route_0506_isolation_20260602/`.

Current-mainline UI adapter startup isolation followup:

- `note_writer_app.py`, `note_text_format_helpers.py`, and `generation_exception_helpers.py` now keep old current-mainline UI adapter calls behind lazy compatibility wrappers.
- `import note.note_writer_app` reports no matching startup modules for `route_0506`, `current_mainline`, `newalgorithm_pipeline`, or `simple_note_pipeline`.
- This does not delete Route 0506, Route A, current-mainline, or newalgorithm files. Those remain archive candidates until an explicit archive move owner is approved.

Archive move followup:

- With explicit user approval, old body-generation file groups were moved to `C:\tetie\notecode\archive\writer_only_deadcode_archive_20260602\`.
- The move covered Route 0506 product modules/tests, Route A current-mainline modules/tests, `newalgorithm_pipeline`, `simple_note_pipeline`, owned-media experiment files, and related old pipeline tests.
- `C:\tetie\notecode\0506` was not moved; it remains a large historical reference package, not normal UI runtime.
- Move artifacts are in `C:\tetie\notecode\logs\writer_only_deadcode_archive_20260602\`.

Live generation quality followup:

- REJP source intake was verified after archive with readable Japanese text and non-empty claims.
- The writer-only prompt now requires a Markdown H1 title and 3-5 H2 sections.
- The smoke evaluator now checks Markdown title and section structure in addition to self perspective and legacy-route flags.
- Final validation artifact: `C:\tetie\notecode\logs\writer_only_generation\writer_only_archive_validation_final_20260602\draft.md`.
- Final validation used one OpenAI writer call with `gpt-4.1-mini-2025-04-14`; Route 0506, Route A, repair, quality pipeline, and image generation were not used.

Writer-only contract/evaluator followup:

- Added compact `writer_contract` fields for audience anchoring, consultation-based company voice, reader-relevant H2 starts, and source-claim grounding.
- Kept fixed writer instructions short; the only new instruction is to obey `writer_contract` and avoid unsupported general claims outside source claims.
- The smoke evaluator now checks:
  - `audience_anchor`
  - `voice_consistency`
  - `section_reader_relevance`
  - `source_grounding`
- Prior comparison draft `writer_only_comparison_20260602_162427` now fails the current evaluator on `section_reader_relevance` and `source_grounding`.
- Live comparison after the contract change: `C:\tetie\notecode\logs\writer_only_generation\writer_only_comparison_after_contract_20260602_170609\draft.md`.
- The after-contract run used one OpenAI writer call, passed smoke evaluation, kept `writer_only=true`, and did not use Route 0506, Route A, repair, quality pipeline, or image generation.

Writer-only SNS followup:

- Added a same-call output contract for `article_markdown`, `linkedin_text`, and `linkedin_short_text`.
- `article_markdown` is checked against the source-aware body contract.
- `linkedin_short_text` is the primary SNS post text shown in the UI.
- The SNS smoke check requires a present post, 700 characters or fewer, company first-person voice, and preservation of article point terms.
- If the model response omits SNS fields, exceeds 700 characters, or lacks company first person, the UI uses a deterministic article-to-SNS recomposition fallback without an additional API call.
- Artifacts are saved as `linkedin_post.md`, `linkedin_short_post.md`, and `sns_evaluation.json` under each writer-only run directory.

Writer-only UI handler extraction followup:

- The visible writer-only generation card and writer-only click handler now live in `note\note_writer_app_writer_only_ui.py`.
- `note_writer_app.py` keeps the page shell, shared source/result widgets, hidden legacy handler, image panel, and manual legal utility.
- The extracted helper receives only the required writer-only controls, result widgets, status widgets, and refresh callbacks.
- LinkedIn result mapping treats `linkedin_short_text` as the primary UI/copy text; `linkedin_text` remains as a compatibility field with the same normalized value.
- Route 0506, Route A, `newalgorithm_pipeline`, `simple_note_pipeline`, image generation, and manual legal behavior were not changed or restored by this extraction.

Writer-only image handoff helper followup:

- `note\writer_only_image_handoff.py` builds a small post-success image context from a successful writer-only result and optional artifact root.
- The helper resolves `title`, `lead`, `body`, and `article_type`, preferring `brief.json.internal_category` for `article_type`.
- It reads source claims from `source_bundle.json` or `brief.json.source_bundle`, capped at 6 claims, with URL/title metadata only.
- It does not call image generation and does not connect the writer-only button to post-success image work yet.
- It does not restore or import Route 0506, Route A, `newalgorithm_pipeline`, or `simple_note_pipeline`.

Image touch profile option followup:

- The existing image `pattern_key` selector is now shown as `タッチ / 画像の方向性`.
- UI options are limited to `シンプル`, `ブログ見出し画像風`, `フラットイラスト`, and `温かい手描き風`.
- `pattern_key` remains as the compatibility argument, but prompts resolve it to a touch profile.
- Touch profile wording is prompt direction only. It must not override article content or source claims.
- The writer-only button still does not call post-success image generation in this followup.
- SNS / LinkedIn behavior is unchanged.

Writer-only post-success image connection followup:

- After a successful writer-only result, the visible writer-only button now starts the existing GPT Image 2 blog image flow as fail-open post-success work.
- The connection uses `note\writer_only_image_handoff.py` to build `title`, `lead`, `body`, and `article_type` from the writer-only result and artifacts.
- The selected `タッチ / 画像の方向性` key is passed as the existing `pattern_key` compatibility argument.
- UI image state is updated through `state.generated_image_variants`, `state.generated_images`, and `state.image_generation_status`, then the generated image panel is refreshed.
- If image generation fails, writer-only article output and SNS / LinkedIn fields stay intact and the image status becomes `failed`.
- The image generator is injected into `note\note_writer_app_writer_only_ui.py` for stubbed tests; this followup used no live API send.
- Route 0506, Route A, `newalgorithm_pipeline`, and `simple_note_pipeline` remain disconnected from the writer-only visible route.

## 2026-06-04 UX Decision: Pre-generation Image Tone And Lean Writer-only Inputs

Current implementation state:

- The image tone selector is rendered inside the generated-output image panel, so it is not practically selectable before the first writer-only generation run.
- The selected tone is wired correctly after a value is available: UI label -> `IMAGE_PATTERN_LABEL_TO_KEY` -> `selected_image_pattern_key` -> `pattern_key` -> `generate_blog_images_for_article(...)`.
- Because the selector is in the result area, the first automatic image run effectively uses the default `シンプル` tone unless a previous visible result area already allowed a selection.
- The writer-only visible input card still asks for `会社側の語り手`, `記事目的`, and `読者の課題`, although these are weak or confusing as repeated user-facing inputs.

Next UI owner decision:

- Move `画像のトーン` into the pre-generation writer-only card, near `温度感`, so it is selected before the first post-success image generation starts.
- Keep the four current tone labels only: `シンプル`, `ブログ見出し画像風`, `フラットイラスト`, `温かい手描き風`.
- Do not change `blog_image_auto.py`, `image_prompt_helpers.py`, `writer_only_image_handoff.py`, or the two-variant image contract unless a focused test proves a narrow need.
- Hide or remove `会社側の語り手` from the normal UI. Use a stable internal default such as `会社側の担当者` to preserve the writer-only service contract.
- Hide or remove `記事目的` from the normal UI. It overlaps with the short instruction and can conflict with it. Derive the internal value from the short instruction or a safe default.
- Hide or relabel `読者の課題`; the current wording is unclear outside problem-solving articles. Prefer keeping it out of the normal UI, with a safe internal default, unless a later owner designs a clearer optional advanced field.
- Keep `想定読者` optional or advanced. It can improve output, but it should not be a required-looking field in the common path.
- Keep a single visible progress bar. Update the status text in stages such as source checking, blog body creation, SNS text creation, image generation, image success, and image fail-open failure. Do not reset the bar from complete back to an earlier value.

Non-goals:

- Do not restore Route 0506, Route A, `newalgorithm_pipeline`, `simple_note_pipeline`, repair loop, or quality pipeline.
- Do not change writer prompt wording, smoke thresholds, source policy, SNS / LinkedIn generation, image prompt wording, GPT Image 2 API parameters, image output size, manual legal UI, or source upload behavior.
- Do not call live APIs for this UI cleanup owner.
