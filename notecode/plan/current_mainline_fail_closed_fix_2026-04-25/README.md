# current_mainline_fail_closed_fix_2026-04-25 README

## Objective

- UI 経由で確認された fail-closed のうち、Kyoto `company_introduction` と rich `case_study` の 2 件だけを runtime 側で narrow に改善する。
- UI source handoff / error display ではなく、current mainline の realization / runtime 接続を対象にする。
- `insufficient case_study` の precheck boundary は今回直さず follow-up に残す。

## Source Of Truth

- current naturalness package:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- predecessor validation:
  - `C:\tetie\notecode\plan\current_mainline_ui_past_failure_validation_2026-04-25\`
  - `C:\tetie\notecode\logs\current_mainline_ui_past_failure_validation_20260425-110220\`

This package does not replace `naturalness_recovery_2026-04-07` as the global current source of truth.

## Target Cases

- Case 1:
  - `article_type=branding`
  - `semantic_article_key=company_introduction`
  - Kyoto Kogyo URLs
  - prior UI result: `SYS_QUALITY_WARNINGS_UNRESOLVED`
- Case 4:
  - `article_type=case_study`
  - `semantic_article_key=implementation_case`
  - rich restored case-study source
  - prior UI result: `SYS_QUALITY_WARNINGS_UNRESOLVED`

## Non-Goals

- Do not change `ALGORITHM.md` persona design.
- Do not change `single-pass + optional single repair 1回`.
- Do not increase repair count.
- Do not relax `quality_guard.py`.
- Do not change target length / length mode estimation.
- Do not broaden source packet thickness again.
- Do not add prompt accretion, persona registry, or article-type fixed routing.
- Do not expose runtime/internal terms in visible article text or UI.
- Do not reopen pre-2026-04-02 archive or frozen architecture package.
