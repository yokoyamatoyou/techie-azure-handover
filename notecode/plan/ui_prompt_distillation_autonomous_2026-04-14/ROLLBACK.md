# ui_prompt_distillation_autonomous_2026-04-14 ROLLBACK

## Restore Boundary

- current package source-of-truth remains:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- separate autonomous line source-of-truth:
  - `C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\`
- runtime path remains:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## Current Package Keep-State To Respect

- blank company intro best current line:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` current-business-first keep line
- prompt-only:
  - floor
- skeleton / planning:
  - conditional signal only
- current package do-not-retry:
  - `C:\tetie\notecode\note\natural_blog_core.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py` upstream distilled summary only

## Rollback Rule

- rollback if:
  - current runtime path fails regression
  - naturalness wins only by dropping must-cover / grounding / anchor
  - line needs heavy rewrite / large routing table / UI change
  - verdict does not produce enough stable pass categories
- stop if:
  - fail categories remain unresolved after bounded loops
  - required owner scope expands beyond reasonable modular boundary

## Compare Baselines

- current keep baseline:
  - current current-mainline artifacts under `C:\tetie\notecode\logs\`
- prompt-only floor:
  - existing floor artifacts under `C:\tetie\notecode\logs\`
- public web compare evidence:
  - `C:\tetie\notecode\research\新しいフォルダー (11)\新しいフォルダー (2)\shanai_rag_precision_review_article.md`
  - `C:\tetie\notecode\research\新しいフォルダー (11)\新しいフォルダー (2)\hankyu_hanshin_real_estate_company_article.md`
  - `C:\tetie\notecode\research\新しいフォルダー (11)\新しいフォルダー (2)\阪急阪神不動産株式会社_会社紹介記事.md`

## Failure Modes To Watch

- raw UI phrasing leaks into lead / title
- company intro drifts into history-first
- brochure / card feel rises after style tightening
- company-name or topic repetition rises
- category-specific must-cover drops under generic polish
- direct GPT web compare remains unavailable

## Recorded Boundaries During Execution

- invalid representative selection:
  - `C:\tetie\notecode\logs\ui_prompt_distillation_autonomous_20260414\aggregate_eval.json`
  - source-less case を representative に使うと current runtime gate と矛盾する
  - rollback point:
    - representative case freeze を `source_backed_only` へ補正
- comparative repair boundary:
  - only comparative title / lead surface guidance was changed
  - if future reruns regress another category, rollback target is:
    - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
    - `C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py`
  - formatter / heavy editor reopen はしない
