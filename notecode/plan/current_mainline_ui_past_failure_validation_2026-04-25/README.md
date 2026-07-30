# current_mainline_ui_past_failure_validation_2026-04-25 README

## Objective

- UI -> current mainline 経路で、過去ログで失敗した source / 入力条件が現在どう扱われるかを実操作で確認する。
- 生成成功だけでなく、本文品質が薄すぎる、source 外 claim がある、runtime/internal term が本文に漏れる場合は問題として扱う。
- UI 経路の問題と本文 realization の問題を分け、UI 経路の defect だけをこの package の narrow fix 対象にする。

## Source Of Truth

- current naturalness source of truth:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- predecessor:
  - `C:\tetie\notecode\plan\company_intro_source_packet_thickness_2026-04-25\`
  - `C:\tetie\notecode\logs\company_intro_source_packet_thickness_20260425-103407\`

This package does not replace `naturalness_recovery_2026-04-07` as the global current source of truth.

## Required Read Order

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
9. `C:\tetie\notecode\plan\company_intro_length_source_diagnosis_2026-04-25\PROGRESS.md`
10. `C:\tetie\notecode\plan\company_intro_source_packet_thickness_2026-04-25\README.md`
11. `C:\tetie\notecode\plan\company_intro_source_packet_thickness_2026-04-25\TASK.md`
12. `C:\tetie\notecode\plan\company_intro_source_packet_thickness_2026-04-25\PROGRESS.md`
13. `C:\tetie\notecode\plan\company_intro_source_packet_thickness_2026-04-25\ROLLBACK.md`
14. specified prior logs under `C:\tetie\notecode\logs\`
15. `C:\tetie\WORKLOG.md`

## Validation Cases

- Case 1:
  - `article_type=branding`
  - `semantic_article_key=company_introduction`
  - `source_mode=grounded`
  - Kyoto Kogyo source-rich URLs
- Case 2:
  - company-profile style source restored from `bl-branding-company-overview`
  - text-source UI input
  - expected fail-closed or clear boundary, not weak success
- Case 3:
  - `case_study / implementation_case`
  - insufficient source restored from `bl-case-introduction`
  - expected input-boundary stop
- Case 4:
  - `case_study / implementation_case`
  - rich source restored from `rerun-case-study-rich-source`
  - expected success
- Optional:
  - announcement from `bl-announcement-spec-change`
  - comparative_review from `bl-comparative-selection-criteria`

## Non-Goals

- Do not change `ALGORITHM.md` persona-based design.
- Do not change `single-pass + optional single repair 1回`.
- Do not increase repair count.
- Do not relax `quality_guard.py` thresholds.
- Do not change `target_chars` / `length_mode` estimation in this package.
- Do not broaden source packet thickness.
- Do not grow `prompt_builder.py` or `blog_image_auto.py`.
- Do not create a persona registry or central management module.
- Do not expose `source_limit`, `persona`, `editor`, `trial`, `hidden`, `PATCH_SCOPE`, `SEMANTIC_LEDGER`, `SECTION_SHADOW`, or validation wording in visible article text.
- Do not reopen pre-2026-04-02 archive or frozen architecture package.
