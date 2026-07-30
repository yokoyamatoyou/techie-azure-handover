# EXECUTION_PROMPT

## Purpose

Use this prompt only if the next window implements `company_introduction` patch-scope handling. Do not implement from this docs-only window.

## Prompt

```text
モード: 通常モード
作業場所: C:\tetie\notecode

目的:
company_introduction repair で original draft の lead / heading に `相談の入口` / `相談前` などの route drift phrase がある場合だけ、repair patch scope を lead / affected heading へ最小拡張する。

参照:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
  - ## 4. Single-Pass Generation
  - ## 5. Repair Algorithm
  - ## 12. Persona / Source Packet / Editing Persona Contract
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\
- C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\
- C:\tetie\notecode\plan\company_intro_patch_scope_handling_2026-04-28\
- C:\tetie\notecode\logs\company_intro_repair_prompt_assembly_20260428-112438\
- C:\tetie\WORKLOG.md

Owner:
- owner は `company_intro patch-scope helper` 1つに固定する。
- `pipeline.py` に直接条件を積まない。
- helper を小さく切り出し、existing pipeline hook に差し込む。

Product code scope:
- add:
  - C:\tetie\notecode\note\simple_note_pipeline\company_intro_patch_scope.py
- minimal hook only:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- minimal existing wording replacement only if required:
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- tests:
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

Do not touch:
- C:\tetie\notecode\note\simple_note_pipeline\repair_acceptance.py
- quality thresholds
- fingerprint thresholds
- source grounding thresholds
- repair count
- output formatter
- UI
- image generation
- broad source contract rewrite

Patch-scope handling:
- active only for `article_type=branding` and `semantic_article_key=company_introduction`
- activate only when original draft lead or affected heading contains route drift phrase
- allow change only to:
  - lead with route drift phrase
  - affected heading whose own text contains route drift phrase
- keep title and hashtags stable
- do not allow body-wide rewrite
- do not allow unflagged heading rename
- do not allow heading addition / deletion / reorder
- do not use a simple forbidden-word-only solution
- source-backed short inquiry/contact mention may remain, but company introduction must not become a consultation funnel article

Acceptance conditions:
- output contract remains complete tagged article
- body is non-empty
- output guard / internal leakage is green
- hard source contract is not broken
- source grounding is not worse
- current business remains visible
- product/service or handled field remains visible
- support scope / response boundary remains visible
- source-backed information is not dropped just to remove a route phrase
- heading change removes route-drift framing and keeps section role aligned
- lead change removes route-drift framing and keeps company-introduction role aligned

Reject conditions:
- source-backed current business / product-service / support scope is removed
- lead or heading remains consultation-route centered
- unflagged heading changes
- body-wide rewrite occurs
- source-outside price / result / customer / award / superiority / legal / guarantee claim appears
- internal terms appear in visible article or UI
- candidate only clears one phrase while retaining the same consultation-route axis

Tests:
- add helper unit tests for:
  - inactive for non-company_introduction
  - inactive when no lead / heading route phrase exists
  - lead change allowed only when lead has route drift phrase
  - affected heading rename allowed only when that heading has route drift phrase
  - unflagged heading rename rejected
  - source-backed business material drop rejected
  - body-wide rewrite rejected
  - source-backed short inquiry/contact mention not rejected by word alone
- update repair prompt patch-scope tests only for the conditional wording replacement
- run:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "company_intro or company_introduction or patch_scope or repair_prompt" -q
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py -k "company_intro or company_introduction" -q
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q

Rerun gate:
- company_introduction 3回 rerun
- pass only if:
  - body present 3/3
  - SYS_PIPELINE_FAILURE 0/3
  - blocked_output_redacted=true 0/3
  - internal leakage 0/3
  - lead / heading route drift phrase 0/3
  - source grounding not worse
  - current business / product-service / support scope retained
  - no source-outside claim
- non-target smoke:
  - announcement smoke
  - comparative_review smoke

Updates:
- update C:\tetie\WORKLOG.md
- update C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\PROGRESS.md
- update this package PROGRESS/ROLLBACK if implementation starts
- AGENTS.md は入口導線が変わらなければ更新不要

Stop:
- stop after 3 failed owner-local attempts
- stop if implementation requires repair_acceptance.py before clean candidate evidence exists
- stop if owner scope expands beyond helper + minimal hook + tests
```

