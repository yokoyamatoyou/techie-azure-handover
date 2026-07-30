# current_mainline_bloat_control_priority_2026-04-26 EXECUTION_PROMPT

`C:\tetie\notecode` の current mainline bloat control next priority は、既存 `note_writer_app.py` split package への復帰です。

この execution window は `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\` の `Phase 05: Main Page Pre-Generation Builders` だけに閉じてください。`pipeline.py` source contract cleanup、observability cleanup、output guard cleanup、full-flow user-trial readiness を混ぜないでください。

## 最初に読む

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
4. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\README.md`
5. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\TASK.md`
6. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md`
7. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\ROLLBACK.md`
8. `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\EXECUTION_PROMPT.md`
9. `C:\tetie\notecode\plan\current_mainline_bloat_control_priority_2026-04-26\PROGRESS.md`
10. `C:\tetie\notecode\plan\pipeline_source_contract_split_planning_2026-04-26\PROGRESS.md`
11. `C:\tetie\notecode\current_mainline_owner_split\EXECUTION_RULES.md`
12. `C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md`
13. `C:\tetie\notecode\current_mainline_owner_split\TEST_AND_SAFETY_MATRIX.md`
14. `C:\tetie\notecode\ALGORITHM.md`
    - `## 4. Single-Pass Generation`
    - `## 5. Repair Algorithm`
    - `## 12. Persona / Source Packet / Editing Persona Contract`
    - `## 13. GPT Image 2 Image Generation Algorithm`
15. `C:\tetie\WORKLOG.md`

## この window の目的

- `note_writer_app_split_2026-04-23` Phase 05 だけを実装する。
- header / journey / source-mode / required-input wizard の layout builder を `note\note_writer_app_main_page_sections.py` へ安全に外出しする。
- callback と state mutation は `note_writer_app.py` に残す。
- current success path と UI shell timing owner を変えない。

## Current Baseline

- source contract extraction completed for:
  - `announcement`
  - `comparative_review`
  - `company_introduction`
- post-extraction UI smoke:
  - `company_introduction`: 2/2 `publishable_success`
  - `announcement`: 2/2 `publishable_success`
  - `comparative_review`: 2/2 `publishable_success`
  - image auto generation: 6/6 success
  - leakage: 0
- further `pipeline.py` extraction is parked.
- `note_writer_app.py` is the largest remaining owner at `8352` lines.
- `note_writer_app_split_2026-04-23` Phase 04 is completed; Phase 05 is next.

## Explicit Non-Goals

- `pipeline.py` source contract extraction
- branding / case_study / explanatory_article / common helper extraction
- source contract behavior change
- prompt change
- threshold change
- repair count change
- output guard / quality guard change
- image auto generation behavior change
- UI behavior policy change
- `run_generation()` body split
- completion / exception / finally cleanup timing changes
- auto legal postcheck changes
- confirm state mutation changes
- persona registry or central source contract registry
- pre-2026-04-02 archive / frozen architecture package reopen

## Required Implementation Rule

Use the authoritative Phase 05 prompt in:

- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\EXECUTION_PROMPT.md`

That prompt defines:

- files allowed to touch
- files forbidden to touch
- implementation boundary
- required py_compile command
- required pytest command
- log shape checks
- rollback and stop conditions

Do not widen beyond that prompt.

## Stop Conditions

- Phase 05 cannot be completed without touching `run_generation()` body.
- Phase 05 cannot be completed without changing confirm state mutation.
- Phase 05 requires prompt / threshold / repair / guard / source contract changes.
- Phase 05 requires `pipeline.py`, `output_guard.py`, `quality_observability_mixin.py`, or `blog_image_auto.py` edits.
- same issue fails `2/2` within the split package retry-stop rule.

## Closeout

- Update `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md`.
- Update `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\EXECUTION_PROMPT.md` for the next phase only if Phase 05 is green.
- Update `C:\tetie\WORKLOG.md`.
- Do not proceed to Phase 06 automatically.

