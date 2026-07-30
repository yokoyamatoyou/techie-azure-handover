# company_intro_polish_spinout_2026-04-13 EXECUTION PROMPT

## prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\notecode\docs\management_window_route_policy_coordinator_2026-04-12.md
- C:\tetie\notecode\docs\separate_experiment_prompt_runtime_distillation_handoff_2026-04-13.md
- C:\tetie\notecode\docs\separate_experiment_fixed3_naturalness_final_report_2026-04-13.md
- C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\README.md
- C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\TASK.md
- C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\PROGRESS.md
- C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\ROLLBACK.md
- C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\EXECUTION_PROMPT.md

この window は current package management ではなく spin-out separate implementation line である。

実施範囲:
- blank `branding/company_introduction` のみ
- paired owner set:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- current package source-of-truth は更新しない
- current package docs / AGENTS / WORKLOG は更新しない
- `output_formatter.py` を main owner にしない
- `natural_blog_core.py` を reopen しない
- `pipeline.py` route default を変えない
- UI は触らない
- labeled block 露出を増やさない
- long persona を足さない

必須比較:
- keep baseline:
  - C:\tetie\notecode\logs\codex_blank_company_intro_prompt_builder_first_section_20260413-200211\summary.json
  - C:\tetie\notecode\logs\codex_blank_company_intro_prompt_builder_first_section_20260413-200211\comparison_to_baselines.json
- prompt-only floor:
  - C:\tetie\notecode\logs\codex_parallel_evidence_sprint_blank_company_intro_20260413-213955\combined_summary.json
- input-contract-only rollback:
  - C:\tetie\notecode\logs\codex_blank_company_intro_input_contract_distilled_20260413-220007\summary.json
  - C:\tetie\notecode\logs\codex_blank_company_intro_input_contract_distilled_20260413-220007\comparison_to_baselines.json

core hypothesis:
- blank company intro residual is at the boundary between current-business distilled summary and writer-facing handoff
- contract side must keep history as background
- prompt side must hand off the distilled focus briefly and naturally

pass condition:
- current-business-first first heading stays
- ai_index beats keep baseline and prompt-only floor, or ties on naturalness while clearly winning on grounding / consistency
- must-cover / grounding / anchor do not drop
- public web compare pattern is closer

stop condition:
- same paired hypothesis fails 3 times
- requires third owner
- only wins by dropping must-cover / grounding / anchor

最終報告で必ず示すこと:
1. created spin-out package files
2. touched owner files
3. hypothesis
4. 実施した変更
5. 実行した tests
6. compare / rerun artifact
7. keep baseline に対して勝った点 / 負けた点
8. prompt-only floor に対して勝った点 / 負けた点
9. public web compare に対して勝った点 / 負けた点
10. separate line として keep / rollback / stop の判定
11. current package docs / AGENTS / WORKLOG を更新していないこと
```
