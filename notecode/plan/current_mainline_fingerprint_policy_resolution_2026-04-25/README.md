# current_mainline_fingerprint_policy_resolution_2026-04-25 README

## Objective

- `current_mainline_fingerprint_guard_remaining_2026-04-25` の残課題を引き継ぎ、fingerprint-only residual を hard stop ではなく scoped soft warning / observability に落とせる条件を明文化する。
- Case 4 のように source-grounded / contract-aligned / leak-free / acceptable な本文は UI で warning-only success として返す。
- Case 1 は fingerprint-only の場合だけ同じ扱いにし、`source_grounding:weak_reflection` が混じる場合は従来通り止める。

## Source Of Truth

- global current package:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- predecessor evidence:
  - `C:\tetie\notecode\logs\current_mainline_fingerprint_guard_remaining_20260425-163600\`
  - `C:\tetie\notecode\logs\current_mainline_ui_backend_divergence_20260425-155544\`
  - `C:\tetie\notecode\logs\current_mainline_fail_closed_fix_20260425-144208\`

## Decision

- Adopt `B. scoped soft warning / observability`.
- This is not a fingerprint threshold relaxation.
- This is not stale/non-strict guard reuse.
- The strict final guard may still compute fingerprint warnings, but the UI final guard connection may show the article with warning-only state when every blocking reason is fingerprint-only and source / contract / leak checks are green.

## Non-Goals

- Do not change `ALGORITHM.md` persona / source packet design.
- Do not increase repair count.
- Do not relax `quality_guard.py` or fingerprint thresholds.
- Do not tune target chars / length mode.
- Do not change prompts or source packet thickness.
- Do not expose runtime/internal terms in visible body or UI.
- Do not reopen pre-2026-04-02 archive or frozen architecture package.
