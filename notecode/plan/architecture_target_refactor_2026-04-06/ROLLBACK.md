# architecture_target_refactor_2026-04-06 ROLLBACK

## Baseline

- restore target:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- current package boundary:
  - implementation package completed
  - runtime owner diffs:
    - `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py`
    - `C:\tetie\notecode\note\newalgorithm_pipeline\section_generator.py`
    - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
    - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - closeout docs:
    - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md`
    - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md`
    - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md`
    - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md`
- rollback cost:
  - runtime は phase owner の narrow diff 単位で戻す
  - closeout 文面は package docs only で戻せる

## Rollback Rule

- architecture package の verdict が変わっても、runtime を先に動かさない
- 各 implementation phase は runtime diff を owner 1 file に閉じる
- rollback は phase owner の narrow diff 単位で行う

## Do-Not-Retry Hypotheses

- `keep as-is` を前提に後段補修だけ増やすこと
- `replace architecture` を初手で採ること
- planner を使わず single-pass を本流 quality spine に据え続けること
- `section_generator.py` prompt 強化だけを未変更のまま再投入すること
- proposition density gate を quality blocker にすること
- Anthropic emotion 論文を prompt echo の主因説明として採用すること

## Expected Failure Modes

- canonical plan state を増やしたつもりで duplicate plan representation が残る
- attributed fact slots が prompt accretion に変質する
- section state を generator owner だけで抱え、planner-owned state に上がらない
- micro-revision が hidden writer に逆戻りする
- wrapper demotion 前に current success path regression を起こす

## Per-Phase Rollback Intention

### Phase 01 Canonical Plan State

- rollback:
  - `discourse_planner.py` の `DiscourseSection` canonical field constants / `from_section_plan()` / `normalize()` / `to_canonical_state()` / `_canonicalize_sections()` diff を戻す

### Phase 02 Attributed Fact Slots

- rollback:
  - `discourse_planner.py` の `DiscourseSection.CANONICAL_SOURCE_GROUNDING_FIELDS` / generic-case_study slot spec constants / `_normalize_source_grounding_item()` / `_prepare_route_source_grounding_items()` / intent-aware `_pick_grounding_item()` diff を戻す
  - backup は `C:\tetie\notecode\backups\2026-04-06_arch_target_phase02_pre\discourse_planner.py`

### Phase 03 Section State Promotion

- rollback:
  - `section_generator.py` の `_SectionGenerationState` / `_build_owner_local_state_lines()` / `_advance_section_generation_state()` / `used_fact_slots` を含む ledger diff を戻す
  - backup は `C:\tetie\notecode\backups\2026-04-06_arch_target_phase03_pre\section_generator.py`

### Phase 04 Route-Gated Section-First Mainline

- rollback:
  - `pipeline.py` の promoted route gate / `hierarchical_ab` telemetry fields / section-first failure 時の fail-open fallback diff を戻す
  - backup は `C:\tetie\notecode\backups\2026-04-06_arch_target_phase04_pre\pipeline.py`

### Phase 05 Constrained Micro-Revision

- rollback:
  - `simple_note_pipeline/pipeline.py` の `_repair_preserves_flagged_scope()` / revision section compare helper / patch-path acceptance diff を戻す
  - backup は `C:\tetie\notecode\backups\2026-04-06_arch_target_phase05_pre\pipeline.py`

### Phase 06 Wrapper Demotion

- rollback:
  - `newalgorithm_pipeline/pipeline.py` の `_extract_runtime_check()` / `_extract_primary_call()` / `_build_primary_generation_summary()` / `_build_wrapper_quality_spine()` と `quality_spine` telemetry diff を戻す
  - backup は `C:\tetie\notecode\backups\2026-04-06_arch_target_phase06_pre\pipeline.py`

## Closeout Rollback Intention

- rollback:
  - `README.md` / `PROGRESS.md` / `ROLLBACK.md` / `EXECUTION_PROMPT.md` の closeout wording を implementation completed 直後の状態へ戻す
  - runtime code は reopen しない

## Freeze Rollback Intention

- rollback:
  - `README.md` / `PROGRESS.md` / `ROLLBACK.md` / `EXECUTION_PROMPT.md` / `WORKLOG.md` の frozen / archive-ready wording を closeout completed 状態へ戻す
  - package phase や runtime code は reopen しない
