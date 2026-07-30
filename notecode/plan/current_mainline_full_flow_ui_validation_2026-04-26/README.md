# current_mainline_full_flow_ui_validation_2026-04-26 README

## Objective

- current mainline の実UI full-flow validation を、本文 / title / fail-closed UX / 自動画像生成まで同一 artifact root に記録する。
- 過去に出た本文0、fail-closed、source不足、記事タイプ不一致、route mismatch、image generation failure、UI stale / empty / wait brittle を、実行前に再テスト計画へ固定する。
- source gate を最初に置き、clean source が足りない article type は実UI生成を開始せず、必要 source を列挙して停止する。

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`
   - `## 13. GPT Image 2 Image Generation Algorithm`
4. `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\`
5. `C:\tetie\notecode\plan\current_mainline_fail_closed_ux_policy_2026-04-25\`
6. `C:\tetie\notecode\plan\current_mainline_article_type_source_inventory_2026-04-25\`
7. `C:\tetie\notecode\plan\current_mainline_article_type_ui_quality_validation_2026-04-25\`
8. `C:\tetie\WORKLOG.md`

## Source Of Truth

- current success path remains:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- this package:
  - `C:\tetie\notecode\plan\current_mainline_full_flow_ui_validation_2026-04-26\`
- artifact root for this execution:
  - `C:\tetie\notecode\logs\current_mainline_full_flow_ui_validation_20260426-005456\`

## Scope

- Create package docs and validation artifacts.
- Record source inventory used, historical error retest plan, source precheck, and source gate stop result.
- Do not start the UI server while full-flow source gate is failing.
- Do not change product code, prompt, threshold, repair count, `quality_guard.py`, `output_guard.py`, or GPT Image 2 implementation.

## Required Artifact Layout

- `source_inventory_used.json`
- `historical_error_retest_plan.json`
- `per_attempt_summary.jsonl`
- `full_flow_summary.json`
- `screenshots\`
- `outputs\`
- `quality_reports\`
- `image_outputs\`
- `error_retests\`
- `source_precheck\`

## Source Gate Policy

Full-flow UI generation starts only after every target article type has source that is:

- present
- article-type fit
- not mismatched by UI route
- sufficient or rich for production-quality judgment
- clean enough to support title / body / image alignment review

Current gate result is `stop_for_sources`.

Generation is not started because these full-flow targets still need clean source:

- `product_introduction / service overview`
- `non-company branding / values stance`
- `case_study`
- `comparative_review`
- `industry_analysis`
- `daily_story` for production-quality judgment

## Historical Error Buckets

- Body 0 / route mismatch:
  - `bl-branding-values-stance` resolved to `semantic_article_key=company_introduction` and `SYS_PIPELINE_FAILURE`.
- Fail-closed with body:
  - `company_introduction_kyoto_4urls`
  - `bl-announcement-spec-change`
  - `bl-daily-learning-log-grounded`
- Source shortage / unsuitable source:
  - `bl-case-introduction`
  - thin product / comparative / industry sources
  - mojibake / encoded-title case study UI source
- UI brittle:
  - company introduction historical wait timeout before fresh snapshot collection.
- Image generation:
  - latest GPT Image 2 runs are successful, but fresh full-flow validation must still verify each variant separately.

## Non-Goals

- No runtime fix.
- No threshold or guard relaxation.
- No prompt accretion.
- No repair count increase.
- No warning-only demote expansion.
- No fail-closed to success conversion.
- No source不足 body forced display.
- No image-generation failure mixed into body-quality judgment.
- No AGENTS update unless routing changes.
