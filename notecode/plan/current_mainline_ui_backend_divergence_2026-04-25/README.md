# current_mainline_ui_backend_divergence_2026-04-25 README

## Objective

- Backend live rerun では OK になった Case 1 / Case 4 が、実 UI 操作ではまだ `SYS_QUALITY_WARNINGS_UNRESOLVED` で fail-closed する差分を特定する。
- Runtime を広く直す前に、backend payload と UI payload / input_contract / source trace / pipeline_check の差分を比較し、UI 経由だけで残る原因を narrow に分類する。
- UI input mapping / source handoff / resolved contract の差分で説明できる場合は、runtime realization を触らず UI / runner 接続または validation harness を直す。

## Source Of Truth

- global current source of truth:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- predecessor package:
  - `C:\tetie\notecode\plan\current_mainline_fail_closed_fix_2026-04-25\`
  - `C:\tetie\notecode\logs\current_mainline_fail_closed_fix_20260425-144208\`

This package does not replace `naturalness_recovery_2026-04-07`.

## Initial Finding

- Plan-mode inspection found concrete backend/UI non-equivalence before any new runtime change:
  - backend Case 1 / Case 4 OK runs used `length_mode=short`
  - UI rerun4 Case 1 / Case 4 used `length_mode=adaptive`
  - backend Case 1 speaker was `企業広報として語る`
  - UI Case 1 speaker was `自動判定`
  - backend Case 4 speaker was `導入支援担当として語る`
  - UI Case 4 speaker was `編集担当として語る`
- Source inputs, source document counts, grounding item counts, and must-cover counts were broadly aligned.
- First hypothesis is therefore `ui_input_mapping_diff`, not runtime realization.

## Non-Goals

- Do not change `ALGORITHM.md` persona design.
- Do not change `single-pass + optional single repair 1回`.
- Do not increase repair count.
- Do not relax `quality_guard.py`.
- Do not change target length / length mode estimation logic as a quality tuning.
- Do not broaden source packet thickness.
- Do not add prompt accretion, persona registry, or article-type fixed routing.
- Do not expose internal terms in body or visible UI.
- Do not reopen pre-2026-04-02 archive or frozen architecture package.
