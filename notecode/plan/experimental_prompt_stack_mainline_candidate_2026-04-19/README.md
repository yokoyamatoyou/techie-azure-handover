# experimental_prompt_stack_mainline_candidate_2026-04-19 README

## Objective

- `experimental_prompt_stack` を current mainline 候補まで持っていく
- current work は `実装 -> slice-local self-test -> 次スライス` の反復に限定する
- current runtime mainline は promotion gate を通すまで維持する
- broad rewrite ではなく、既存の `experimental_prompt_stack` を mainline 候補へ育てる

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\README.md`
4. `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\TASK.md`
5. `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\PROGRESS.md`
6. `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\ROLLBACK.md`
7. `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\EXECUTION_PROMPT.md`
8. `C:\tetie\notecode\note\generation_request_builder.py`
9. `C:\tetie\notecode\note\current_mainline_runner.py`
10. `C:\tetie\notecode\note\current_mainline_ui_matrix.py`
11. `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
12. `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
13. `C:\tetie\notecode\note\tests\test_generation_request_builder.py`
14. `C:\tetie\notecode\note\tests\test_current_mainline_runner.py`
15. `C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py`
16. `C:\tetie\notecode\note\tests\test_current_mainline_genre_sweep.py`
17. `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
18. `C:\tetie\notecode\logs\latest_generation_output.txt`
19. `C:\tetie\notecode\logs\latest_generation_quality_report.json`
20. historical compare が必要なときだけ:
    - `C:\tetie\notecode\logs\ad_hoc_quality_compare\20260410-083045-prompt-only-vs-current-mainline-company-grounded\summary.json`
    - `C:\tetie\notecode\logs\direct_gpt54_prompt_only_same_source_2026-04-03.json`
    - `C:\tetie\notecode\logs\prompt_only_probe_2026-04-03_same_source.json`
    - `C:\tetie\notecode\logs\prompt_only_probe_2026-04-03_same_source_force_accept.json`

## Source Of Truth

- this package:
  - `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\README.md`
  - `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\TASK.md`
  - `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\PROGRESS.md`
  - `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\ROLLBACK.md`
  - `C:\tetie\notecode\plan\experimental_prompt_stack_mainline_candidate_2026-04-19\EXECUTION_PROMPT.md`
- implementation source:
  - `C:\tetie\notecode\note\generation_request_builder.py`
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\current_mainline_ui_matrix.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- reference only:
  - `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`

この lane では、古い docs-first package と conflict した場合は this package を優先する。

## Current State

- `body_generation_experiment` は current mainline contract / payload / UI matrix summary で保持される
- `experimental_prompt_stack` は `SOURCE_PACKET -> ARTICLE_CONTRACT -> writer -> suffix editor -> audit` に更新済み
- editor は全文 rewrite ではなく suffix 編集
- audit は `PASS / WARN / FAIL / next_action` を返す
- `prompt_injection_risks` / `fact_id` / `USED_FACT_IDS` / `edit_start_ratio` を導入済み
- current mainline default route はまだ切り替えていない
- current working directory `C:\tetie\notecode` は git root ではない。git 前提で進めない

## Verified Baseline

- passed:
  - `python -m pytest C:\tetie\notecode\note\tests\test_generation_request_builder.py -q`
  - `python -m pytest C:\tetie\notecode\note\tests\test_current_mainline_runner.py C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py C:\tetie\notecode\note\tests\test_current_mainline_genre_sweep.py C:\tetie\notecode\note\tests\test_simple_note_pipeline.py -q`
- note:
  - `pytest` は PATH にないので `python -m pytest` を使う

## Non-Goals

- giant rewrite
- new architecture の追加
- docs-first package の reopen
- unrelated quality_guard / routing / formatter から先に広げること
- `experimental_prompt_stack` を gate 前に default mainline へ強制昇格すること

## Next Legal Move

- current next move は `historical compare / success visibility / promotion gate hardening` の narrow slices
- 各スライスは `実装 -> 自己テスト -> pass なら次へ` で閉じる
- context が増えたら、clean boundary で止めて this package を handoff source に更新する
