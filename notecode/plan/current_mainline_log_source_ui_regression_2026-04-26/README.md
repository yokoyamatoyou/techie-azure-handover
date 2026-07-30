# current_mainline_log_source_ui_regression_2026-04-26 README

## Objective

- current mainline を、過去ログに残っている source から復元して実 UI で再実行する。
- 過去ログで問題があった case と問題がなかった case を、同じ source caveat 付きで比較する。
- source 品質問題と runtime / UI 問題を分けて分類する。
- 本文生成と GPT Image 2 post-success image generation を混ぜずに記録する。

## Source Of Truth

- Runtime mainline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- This package:
  - `C:\tetie\notecode\plan\current_mainline_log_source_ui_regression_2026-04-26\`
- Artifact root:
  - `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\`

## Scope

- Create docs and artifacts only.
- Reconstruct source from historical logs / fixture-derived prior artifacts.
- Run 9 article types x 2 attempts through the UI.
- Run image generation for 2 eligible generated articles.
- Update package `PROGRESS.md` and `C:\tetie\WORKLOG.md`.

## Non-Goals

- No product code change.
- No prompt / threshold / repair / guard / UI implementation change.
- No output demotion or fail-closed policy change.
- No source replacement or new source preparation.
- No runtime defect conclusion from source shortage alone.
- No image failure mixed into body quality judgment.

## Target Article Types

1. `company_introduction`
2. `product_introduction / service overview`
3. `non-company branding / values stance`
4. `announcement`
5. `case_study`
6. `comparative_review`
7. `explanatory_article`
8. `industry_analysis`
9. `daily_story`

## Primary Historical Sources

- `C:\tetie\notecode\logs\multi_type_current_mainline_validation_20260425-013935\`
- `C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\`
- `C:\tetie\notecode\logs\current_mainline_article_type_ui_quality_validation_20260425-223000\`
- `C:\tetie\notecode\logs\latest_generation_output.json`

## Classification Rules

- `reproduced_existing_issue`: same failure shape as historical baseline.
- `regression_candidate`: historical OK but current attempt fails without source-only explanation.
- `improved_or_ux_recovered`: historical failure but current attempt is `publishable_success` or `review_required_draft`.
- `source_caveat`: source is thin, synthetic, mismatched, encoded, or otherwise caveated.
- `ui_harness_issue`: click, wait, stale snapshot, or browser automation caused the failure.
- `empty_body`: body is empty; classify further as source shortage, route mismatch, parse failure, technical failure, or UI harness issue.

## Artifact Layout

- `source_inventory.json`
- `historical_baseline.json`
- `per_attempt_summary.jsonl`
- `ui_validation_summary.json`
- `image_validation_summary.json`
- `source_files\`
- `ui_live\<case_id>\attempt_<n>\`
- `server\`
- `summaries\`
