# company_intro_polish_spinout_2026-04-13 README

## Objective

- current package を reopen せず、blank `branding/company_introduction` だけで WEB company intro に実用上勝てる separate line があるかを判定する
- `input_contract.py + prompt_builder.py` の bounded paired line だけを許可し、upstream summary と writer-facing handoff の境界を narrow に検証する
- current-business-first keep line は壊さず、brochure/card feel と company-name repetition を増やさず、grounding / consistency / repeatability を上げる

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
4. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
5. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
6. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
7. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md`
8. `C:\tetie\notecode\docs\management_window_route_policy_coordinator_2026-04-12.md`
9. `C:\tetie\notecode\docs\separate_experiment_prompt_runtime_distillation_handoff_2026-04-13.md`
10. `C:\tetie\notecode\docs\separate_experiment_fixed3_naturalness_final_report_2026-04-13.md`
11. `C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\README.md`
12. `C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\TASK.md`
13. `C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\PROGRESS.md`
14. `C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\ROLLBACK.md`
15. `C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\EXECUTION_PROMPT.md`
16. `C:\tetie\notecode\ALGORITHM.md`
17. `C:\tetie\WORKLOG.md`

## Source Of Truth Boundary

- current package source-of-truth remains:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- separate line source-of-truth for this experiment:
  - `C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\`
- runtime baseline path stays unchanged:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## Management Lock Inherited

- final management decision for current package:
  - `SPIN_OUT_SEPARATE_LINE`
- current package keep-state:
  - `prompt_builder.py` current-business-first keep line
- prompt-only:
  - `floor`
- skeleton / planning:
  - `conditional signal only`
- current package do-not-retry:
  - `natural_blog_core.py` first section history clamp
  - `newalgorithm_pipeline/output_formatter.py` formatter-only surface polish
  - `newalgorithm_pipeline/input_contract.py` upstream distilled summary only
- public web compare:
  - current-business-first pattern support only
- direct GPT web compare:
  - unavailable

## Baseline Artifacts

- current package keep baseline:
  - `C:\tetie\notecode\logs\codex_blank_company_intro_prompt_builder_first_section_20260413-200211\summary.json`
  - `C:\tetie\notecode\logs\codex_blank_company_intro_prompt_builder_first_section_20260413-200211\comparison_to_baselines.json`
- prompt-only floor baseline:
  - `C:\tetie\notecode\logs\codex_parallel_evidence_sprint_blank_company_intro_20260413-213955\combined_summary.json`
- formatter rollback line:
  - `C:\tetie\notecode\logs\codex_blank_company_intro_output_formatter_surface_polish_retry2_20260413-205831\comparison_to_baselines.json`
  - `C:\tetie\notecode\logs\codex_blank_company_intro_output_formatter_surface_polish_retry3_20260413-210223\comparison_to_baselines.json`
- input-contract-only rollback line:
  - `C:\tetie\notecode\logs\codex_blank_company_intro_input_contract_distilled_20260413-220007\summary.json`
  - `C:\tetie\notecode\logs\codex_blank_company_intro_input_contract_distilled_20260413-220007\comparison_to_baselines.json`

## Observed Pattern

- keep baseline:
  - current-business-first lead was preserved
  - company-name repetition stayed low
  - ai_index improved versus older history-led baseline, but overall naturalness / polish / repeatability remained open
- prompt-only floor:
  - useful floor only
  - company-name repetition rose
  - must-cover / anchor weakened
- skeleton / planning:
  - some conditional signal only
  - not safe default for this package
- input-contract-only rollback:
  - topic statement, main focus, and must-cover drifted toward history-led
  - must-cover / grounding looked strong, but first-heading direction and ai_index worsened
- public web compare pattern:
  - current business first
  - history later as background
  - short paragraphs
  - reduced company-name repetition after lead

## Spin-Out Hypothesis

- blank company intro residual is not formatter-only polish and not upstream distillation alone
- if `input_contract.py` distills blank company intro into current-business-first `topic_statement / core_message / focus_bundle / must_cover` without exposing labeled blocks, and `prompt_builder.py` hands that off as a short natural writer brief, then:
  - first heading can stay current-business-first
  - history can remain background instead of primary main focus
  - brochure/card feel can drop
  - grounding / anchor / must-cover can stay intact
  - repeatability can improve against the keep baseline

## Allowed Owner Set

- primary owners only:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- supporting tests only:
  - `C:\tetie\notecode\note\tests\test_newalgorithm_phase01_contract.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- do not reopen as owner:
  - `natural_blog_core.py`
  - `output_formatter.py`
  - `pipeline.py`
  - `note_writer_app.py`

## Acceptance

- blank `branding/company_introduction` only
- current-business-first lead / first heading remains
- brochure/card feel does not worsen
- company-name repetition does not worsen
- paragraph breathing is at least as natural as keep baseline
- ai_index beats current package keep baseline and prompt-only floor, or ties on naturalness while winning on grounding / consistency
- must-cover / grounding / prompt-anchor do not drop to buy naturalness
- public web compare pattern is closer than current package keep baseline

## Non-Goals

- current package source-of-truth rewrite
- current package management decision rewrite
- direct GPT web compare claim
- article-type routing table expansion
- technical explain / explanatory recovery
- UI change
