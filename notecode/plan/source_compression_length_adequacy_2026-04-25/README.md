# source_compression_length_adequacy_2026-04-25 README

## Objective

- source compression 後の本文が、source 量と記事タイプに対して note 記事として必要な説明量に届いているかを監査する。
- 初手で文字数を増やす修正はしない。まず `source が薄い` / `compression loss 疑い` / `target_chars 疑い` / `repair acceptance 疑い` / `記事タイプとして自然に短い` を分類する。
- 問題が複数回再現し、source が十分ある場合だけ、抽出済み責務を壊さない 1 narrow fix を検討する。

## Source Of Truth

- current naturalness source of truth:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- behavior-preserving split reference:
  - `C:\tetie\notecode\plan\pipeline_responsibility_split_2026-04-24\`
- previous validation input:
  - `C:\tetie\notecode\logs\multi_type_current_mainline_validation_20260425-013935\post_evaluations.jsonl`
  - `C:\tetie\notecode\logs\multi_type_current_mainline_validation_20260425-013935\post_evaluation_summary.json`
  - `C:\tetie\notecode\logs\pipeline_responsibility_split_live_validation_20260425-001548\summary_enriched.json`

## Read Order

1. `C:\tetie\notecode\AGENTS.md`
2. `C:\tetie\AGENTS.md`
3. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`
4. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
5. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
6. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
7. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
8. `C:\tetie\notecode\plan\pipeline_responsibility_split_2026-04-24\README.md`
9. `C:\tetie\notecode\plan\pipeline_responsibility_split_2026-04-24\TASK.md`
10. `C:\tetie\notecode\plan\pipeline_responsibility_split_2026-04-24\PROGRESS.md`
11. `C:\tetie\notecode\plan\pipeline_responsibility_split_2026-04-24\ROLLBACK.md`
12. `C:\tetie\WORKLOG.md`
13. previous multi-type validation logs
14. previous company intro validation logs

## Audit Metrics

- run id / article_type / semantic_article_key / source_mode
- source_document_count / source_total_chars
- source_summary_chars / source_packet_chars / grounding item count / must_cover count when available
- target_chars / body_chars / body_chars_to_target_ratio
- section_count / section char distribution / shortest_section_chars / longest_section_chars
- source facts reflected count / required source slot coverage when available
- soft_warning_count / repair_required / repair_applied / repair_rejected / repair reject reason
- output_guard reasons / visible internal-term leakage
- Codex visible evaluation
- thinness reason and regression classification

## Article Type Range Hints

These are audit hints, not hard thresholds.

- `announcement`: 600-1000 chars can be natural.
- `daily_story`: 700-1200 chars can be natural.
- `company_introduction` / `case_study`: 1200-1800 chars is often natural, unless source is thin.
- `explanatory_article` / `industry_analysis` / `product_introduction` / `comparative_review`: 1600-2400 chars is often natural.
- Source density and section density are prioritized over padding.

## Non-Goals

- Do not make length increase the goal.
- Do not relax `quality_guard.py` thresholds.
- Do not increase repair count.
- Do not grow `prompt_builder.py` / `blog_image_auto.py`.
- Do not create persona registry / central management modules.
- Do not expose runtime/internal terms in visible text.
- Do not reopen pre-2026-04-02 archive or frozen architecture package.
- Do not change persona-based design in `ALGORITHM.md`.
