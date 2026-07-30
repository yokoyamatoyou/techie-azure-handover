# note_writer_app_split_2026-04-23 README

## Objective

- `C:\tetie\notecode\note\note_writer_app.py` を壊さず、責務境界を崩さず、current mainline success path を変えずに段階分割できる separate initiative を正本化する
- `naturalness_recovery_2026-04-07` current source of truth は維持したまま、`note_writer_app.py` 分割専用の phase ladder と rollback boundary を固定する
- 別ウインドウ実装者が `Phase 01` からそのまま安全着手できる docs / handoff / execution prompt を揃える

## Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
4. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
5. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
6. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\README.md`
7. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\TASK.md`
8. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md`
9. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\ROLLBACK.md`
10. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\EXECUTION_PROMPT.md`
11. `C:\tetie\notecode\current_mainline_owner_split\PROGRESS.md`
12. `C:\tetie\notecode\current_mainline_owner_split\EXECUTION_RULES.md`
13. `C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md`
14. `C:\tetie\notecode\current_mainline_owner_split\TEST_AND_SAFETY_MATRIX.md`
15. `C:\tetie\notecode\current_mainline_owner_split\NOTE_WRITER_APP_WINDOW_HANDOFF_2026-04-23.md`
16. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`
   - `## 13. GPT Image 2 Image Generation Algorithm`
17. `C:\tetie\notecode\note\note_writer_app.py`
18. `C:\tetie\WORKLOG.md`

## Source Of Truth

- global current source of truth remains:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- split initiative source of truth:
  - `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\README.md`
  - `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\TASK.md`
  - `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md`
- boundary / invariant references:
  - `C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md`
  - `C:\tetie\notecode\current_mainline_owner_split\EXECUTION_RULES.md`
  - `C:\tetie\notecode\current_mainline_owner_split\TEST_AND_SAFETY_MATRIX.md`
  - `C:\tetie\notecode\current_mainline_owner_split\NOTE_WRITER_APP_WINDOW_HANDOFF_2026-04-23.md`
  - `C:\tetie\notecode\ALGORITHM.md`
  - `C:\tetie\notecode\note\note_writer_app.py`
- runtime success path to preserve:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## Current File Facts

- target file:
  - `C:\tetie\notecode\note\note_writer_app.py`
- fixed baseline facts at package creation:
  - total lines: `9201`
  - `main_page()`: `4798`
  - `run_generation()`: `7775`
  - manual legal local handler `run_legal_check()`: `9103`
  - upload / source helpers: `3599-3702`
  - head assets block: `3752-4730`
- current structural observation:
  - `main_page()` is the largest block and contains most UI-local nested helpers
  - `run_generation()` remains a high-risk timing owner and is not an initial split target
  - upload cleanup currently has import-time side effects and must be isolated carefully

## Owner Boundary Summary

- `note_writer_app.py` remains the UI shell owner:
  - confirm-before-generate flow
  - actual widget mutation
  - confirm state mutation
  - logging trigger timing
- `input_decision` and final contract resolve remain outside the UI shell:
  - source of truth stays in `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
- logging schema and file persistence remain outside the UI shell:
  - source of truth stays in `C:\tetie\notecode\note\current_mainline_runtime_logging.py`
- `current_mainline_runner.py` remains the generation orchestration owner:
  - `note_writer_app.py` must not pull final route or contract decisions back into UI-local logic

## Split Purpose

- safe slimming of `note_writer_app.py`
- clearer phase-local rollback units
- separate-window implementation without reopening completed `current_mainline_owner_split`
- easier ownership reading for UI shell helper extraction

## Split Candidate Priority

1. `ui.add_head_html` の巨大 CSS / JS / theme 設定の外出し
2. upload / source 操作 / 起動時 cleanup helper の外出し
3. サブ UI コンテナ群の外出し
4. 手動 legal postcheck 周辺ローカル関数の外出し
5. `main_page()` の section builder 化
6. late-phase only:
   - `run_generation()` 周辺
   - completion / exception / finally cleanup timing
   - image prompt / auto legal postcheck
   - confirm state mutation

## Planned Internal Module Names

- `note\note_writer_app_head_assets.py`
- `note\note_writer_app_source_helpers.py`
- `note\note_writer_app_subviews.py`
- `note\note_writer_app_manual_legal_helpers.py`
- `note\note_writer_app_main_page_sections.py`

## Non-Goals

- `naturalness_recovery_2026-04-07` current source of truth を置き換えること
- `current_mainline_owner_split` completed judgment を reopen すること
- current success path を変えること
- `input_decision` source of truth を UI 側へ戻すこと
- logging schema / file persistence owner を `current_mainline_runtime_logging.py` から動かすこと
- GPT Image 2 を本文 mainline に昇格させること
- persona / editor / trial names を runtime prompt や visible output に戻すこと
- `single-pass + optional single repair 1回` を崩すこと
- `run_generation()` / completion timing / image prompt / auto legal postcheck を初手で触ること

## Minimal Directory Map

```text
C:\tetie\
├── AGENTS.md
├── WORKLOG.md
└── notecode\
    ├── AGENTS.md
    ├── ALGORITHM.md
    ├── current_mainline_owner_split\
    ├── note\
    │   └── note_writer_app.py
    └── plan\
        ├── naturalness_recovery_2026-04-07\
        └── note_writer_app_split_2026-04-23\
```

## Package State

- package status:
  - active
  - docs_lock_created
- current phase:
  - phase 00 docs lock / separate-window handoff ready
- next action:
  - `Phase 01: head assets` only
  - if green, update this package `PROGRESS.md` and `C:\tetie\WORKLOG.md`, then stop
