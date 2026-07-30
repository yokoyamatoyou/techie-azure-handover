# company_intro_source_packet_thickness_2026-04-25 README

## Objective

- `branding/company_introduction` の source-rich 条件で、required slot は `5/5` visible なのに本文が `900-1300` 字へ寄り、target `1800` に対して説明量が浅くなる問題を narrow に直す。
- 前段 diagnosis の主因 `compression_loss_suspected` を受け、会社紹介の required slot ごとに source-backed explanation material を少し厚く保持する。
- 文字数増加そのものは目的にしない。source-backed な説明材料を増やし、本文で支援範囲 / 進め方 / 相談前判断が浅く終わる状態を減らす。

## Source Of Truth

- current naturalness source of truth:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- predecessor diagnosis:
  - `C:\tetie\notecode\plan\company_intro_length_source_diagnosis_2026-04-25\`
  - `C:\tetie\notecode\logs\company_intro_length_source_diagnosis_20260425-095537\`

This package does not replace `naturalness_recovery_2026-04-07` as the global current source of truth.

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
8. `C:\tetie\notecode\plan\pipeline_responsibility_split_2026-04-24\PROGRESS.md`
9. `C:\tetie\notecode\plan\source_compression_length_adequacy_2026-04-25\PROGRESS.md`
10. `C:\tetie\notecode\plan\company_intro_length_source_diagnosis_2026-04-25\README.md`
11. `C:\tetie\notecode\plan\company_intro_length_source_diagnosis_2026-04-25\TASK.md`
12. `C:\tetie\notecode\plan\company_intro_length_source_diagnosis_2026-04-25\PROGRESS.md`
13. `C:\tetie\notecode\plan\company_intro_length_source_diagnosis_2026-04-25\ROLLBACK.md`
14. `C:\tetie\WORKLOG.md`
15. specified prior logs under `C:\tetie\notecode\logs\`

## Baseline Evidence

- Kyoto Kogyo source-rich diagnosis:
  - `15` runs
  - `13` success / `2` fail-closed
  - successful body chars: `803-1288`
  - successful average body chars: `1106.23`
  - target chars: `1800`
  - average body / target ratio: `0.6146`
  - source total chars: `3242`
  - source summary chars: `452`
  - source packet chars: `638`
  - source packet facts: `5`
  - grounding item count: `5`
  - must-cover count: `8`
  - required source slots visible in successful runs: `5/5`
- Slot text lengths:
  - `current_business`: `19`
  - `customer_situation_or_entry_point`: `5`
  - `support_scope_boundary`: `35`
  - `operating_process_steps`: `46`
  - `pre_contact_decision`: `63`
- Diagnosis classification:
  - primary: `compression_loss_suspected`
  - secondary: `realization_shallow_suspected`
  - not primary: `target_low_suspected`
  - not primary: `repair_rejection_suspected`

## Current Hypothesis

The company introduction runtime currently extracts enough slot labels to satisfy `5/5` coverage, but the writer-facing material for each required slot is too terse. The narrow fix is to keep bounded source-backed explanation material per required slot before generation, scoped only to `article_type=branding` and `semantic_article_key=company_introduction`.

## Non-Goals

- Do not change `ALGORITHM.md` persona-based design.
- Do not change `single-pass + optional single repair 1回`.
- Do not increase repair count.
- Do not relax `quality_guard.py` thresholds.
- Do not change `target_chars` / `length_mode` estimation in this package.
- Do not change repair acceptance in this package.
- Do not grow `prompt_builder.py` or `blog_image_auto.py`.
- Do not create a persona registry or central management module.
- Do not expose runtime/internal terms in visible article text.
- Do not reopen pre-2026-04-02 archive or frozen architecture package.
- Do not change source compression globally across article types.
- Do not add source-outside claims, generic padding, or redundant filler.
