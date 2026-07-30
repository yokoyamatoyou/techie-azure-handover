# architecture_target_refactor_2026-04-06 PROGRESS

## Current Goal

- completed implementation package を frozen reference として固定し、次回再開時の許可された入口だけを残す

## Current Status

- Package status: completed
- Current phase: Handoff / Freeze
- Status: completed
- Hypothesis:
  - closeout 済み package を frozen reference に落とせば、次回は新 package か明示 artifact review 以外へ拡張せずに済む
- Owner scope:
  - package docs only
- Attempts used: 1/3
- Next phase:
  - frozen archive-ready package

## Baseline

- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- current implementation status:
  - `discourse_planner.py` owner に canonical plan state normalization と attributed fact slot normalization を追加
  - `section_generator.py` owner に owner-local section state schema と state-fed ledger/prompt bridge を追加
  - `pipeline.py` owner に announcement dense route の promoted section-first gate と fail-open fallback を追加
  - `simple_note_pipeline/pipeline.py` owner に patch-path repair の flagged-scope acceptance check を追加
  - `newalgorithm_pipeline/pipeline.py` owner に wrapper-local quality spine summary と primary generation normalization helper を追加
  - current success path は unchanged

## Architecture Verdict

- adopted:
  - `hybrid target architecture`
  - repo-level interpretation: `keep core, refactor boundaries`
- core target:
  - canonical plan state
  - attributed fact slots
  - section-first writer
  - constrained micro-revision
- rejected:
  - `keep as-is`
  - `replace architecture`

## Closeout Decision

- narrow task:
  - `package closeout`
- owner scope:
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md`
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md`
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md`
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md`
- decision:
  - final visual loop は本 package の completion gate ではない
  - 実生成物 review が必要なら current mainline artifact review として別タスクで扱う
  - package 自体は closeout 後に handoff / freeze ready とする
- closeout evidence:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q`
    - `209 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `66 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `14 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `83 passed`

## Handoff / Freeze Decision

- narrow task:
  - `handoff / freeze`
- owner scope:
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md`
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md`
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\ROLLBACK.md`
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\EXECUTION_PROMPT.md`
  - `C:\tetie\WORKLOG.md`
- decision:
  - package は `frozen / archive-ready` とする
  - この package に新しい implementation phase は追加しない
  - 次回以降に許可する作業は
    - 新 package の作成
    - 明示依頼のある current mainline artifact review
    のみとする
- evidence:
  - implementation phase 01-06 completed
  - package closeout completed
  - shared checks green の closeout evidence を保持

## Evidence Summary

- local research `(3)`:
  - 現行アルゴリズムのゼロベース評価と対象コード抽出
- local research `(4)`:
  - 既存レポート差分込みの arbitration prompt
- local research `(5)`:
  - `hybrid target architecture` 判断
  - `keep core, refactor boundaries` 優勢
  - core primitive 再利用の妥当性
- Web:
  - Plan-and-Write / Re3 / PlotMachines / LongWriter / CogWriter / WriteHERE
  - Attribute First, then Generate
  - self-revision limits

## Blocked Hypotheses

- current mainline を `keep as-is` で延長すること
- `replace architecture` を初手で採ること
- `section_generator.py` prompt 強化だけで押し切ること
- repair/guard を増やして quality spine を救うこと
- proposition density を hard gate にすること
- Anthropic emotion 論文を architecture 主根拠にすること

## Phase Ledger

| Phase | Status | Hypothesis | Owner scope | Attempts | Evidence | Next phase |
|------|--------|------------|-------------|----------|----------|------------|
| 00 Package Freeze | completed | target architecture verdict と blocked hypotheses を package に固定する | package docs only | 1/3 | `README.md` / `TASK.md` / `PROGRESS.md` / `ROLLBACK.md` に decision を固定 | 01 |
| 01 Canonical Plan State | completed | `DiscourseSection` の contract を runtime spine に昇格させるだけで、plan の支配点が明確になる | `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py` | 1/3 | `DiscourseSection` に canonical field 定義 / `from_section_plan()` / `normalize()` / `to_canonical_state()` を追加し、final normalization pass を builder owner に閉じた | 02 |
| 02 Attributed Fact Slots | completed | section intent と fact slot を 1:1 ではなく bounded set にすると、source starvation と source drift を同時に減らせる | `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py` | 1/3 | `source_grounding_items` に canonical slot metadata を追加し、case_study `change / condition` の explicit slot 種別と intent-aware pick を owner-local に固定した | 03 |
| 03 Section State Promotion | completed | `previous_summary` だけでなく `remaining_must_cover` / `used_fact_slots` / `section_ledger` を外化すると、後半失速を抑えやすい | `C:\tetie\notecode\note\newalgorithm_pipeline\section_generator.py` | 1/3 | `_SectionGenerationState` を追加し、bridge summary を keep したまま state-fed `remaining_must_cover / used_fact_slots / section_ledger` 更新へ寄せた | 04 |
| 04 Route-Gated Section-First Mainline | completed | 1 route だけ section-first を本流化しても fail-open を維持できる | `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` | 1/3 | announcement dense route を explicit experiment なしでも section-first path へ昇格し、section generation failure 時は super runtime へ fail-open fallback するようにした | 05 |
| 05 Constrained Micro-Revision | completed | source と plan に anchored な micro-revision は、現行 repair より安全に働く | `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` | 1/3 | patch-path repair では flagged heading 以外の section / lead / hashtags を維持する acceptance check を追加し、scope drift repair を reject するようにした | 06 |
| 06 Wrapper Demotion | completed | planner/state/writer/revision の spine が立てば、wrapper は validator / adapter に縮退できる | `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` | 1/3 | wrapper が nested runtime field を都度のぞく代わりに normalized primary generation summary を使い、`quality_spine` telemetry で owner/path ごとの品質支配点を明示するようにした | completed |

## Next Phase Slice

- phase:
  - handoff / freeze completed
- narrow hypothesis:
  - package を frozen reference として固定すれば、以後の reopen 判断を明示依頼ベースに限定できる
- owner scope:
  - package docs only
- entry note:
  - 次回は新 package 作成か、明示依頼がある場合だけ current mainline artifact review を扱う

## Phase 01 Evidence

- status:
  - completed
- evidence:
  - `DiscourseSection.CANONICAL_PLAN_FIELDS` / `CANONICAL_ROUTE_EXTENSION_FIELDS` を追加し、planner-owned required fields を固定
  - `DiscourseSection.from_section_plan()` で base plan -> runtime section 変換を 1 か所へ集約
  - `DiscourseSection.normalize()` と `_canonicalize_sections()` を追加し、route-local mutation 後の section state を 1 schema へ収束させた
  - `to_canonical_state()` を追加し、次 phase が plan export を owner-local に参照できる形を用意した
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st05ab7_product_intro_discourse_keeps_focus_out_of_first_hook_objective or st05ab7a_product_intro_discourse_assigns_history_after_service_facts or st05ab7b_product_intro_discourse_stabilizes_later_section_instructions or st05ab7c_discourse_section_canonical_state_lists_required_fields or st05ab7d_build_discourse_plan_returns_canonicalized_route_state" -q`
    - `5 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `65 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `14 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `83 passed`
- rollback note:
  - `discourse_planner.py` の canonical field constants / `from_section_plan()` / `normalize()` / `_canonicalize_sections()` を戻せば baseline へ復帰可能
- note:
  - `note\tests\test_newalgorithm_phase03_pipeline.py -q` の既存 3 failures は確認したが、変更前 backup planner 差し替えでも再現したため Phase 01 diff には含めない

## Phase 02 Evidence

- status:
  - completed
- evidence:
  - `DiscourseSection.CANONICAL_SOURCE_GROUNDING_FIELDS` を追加し、`source_grounding_items` の canonical nested schema を固定
  - generic / case_study の bounded source slot spec を `discourse_planner.py` owner に閉じ、`slot_key / slot_label / slot_role / slot_optional / slot_intents` を正規化
  - `_prepare_route_source_grounding_items()` で case_study bucket 推定後に slot metadata を再計算し、`change / condition` の explicit slot 種別を planner 出力へ埋め込んだ
  - `_pick_grounding_item()` を section intent aware にし、bucket fallback を残しつつ usable slot を先に拾うようにした
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st05ab7_product_intro_discourse_keeps_focus_out_of_first_hook_objective or st05ab7a_product_intro_discourse_assigns_history_after_service_facts or st05ab7b_product_intro_discourse_stabilizes_later_section_instructions or st05ab7c_discourse_section_canonical_state_lists_required_fields or st05ab7d_build_discourse_plan_returns_canonicalized_route_state or st05ab7c_case_study_discourse_assigns_sparse_grounding_to_change_and_condition or st05ab7d_case_study_discourse_prefers_explicit_condition_fact_for_condition_section or st07g6_case_study_compatibility_body_reuses_source_facts_for_change_and_condition" -q`
    - `8 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q`
    - `201 passed, 3 failed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `65 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `14 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `83 passed`
- rollback note:
  - `discourse_planner.py` の source slot spec constants / `_normalize_source_grounding_item()` / `_prepare_route_source_grounding_items()` / intent-aware `_pick_grounding_item()` diff を戻せば baseline へ復帰可能
- note:
  - `note\tests\test_newalgorithm_phase03_pipeline.py -q` の failures は `test_st05af_editor_guard_repairs_modal_collision_and_duplicate_tail` / `test_st07d_case_study_pipeline_keeps_condition_section_body` / `test_st07f_case_study_pipeline_keeps_condition_body_when_dedupe_truncates` の 3 件で、Phase 01 時点と同じ残件のまま増えていない

## Phase 03 Evidence

- status:
  - completed
- evidence:
  - `_SectionGenerationState` を追加し、`previous_summary / section_summaries / remaining_must_cover / used_fact_slots / section_ledger` を owner-local schema に固定
  - `generate_sections()` は raw local vars ではなく state carrier を通して prompt bridge と ledger 更新を行う形へ整理
  - LLM prompt には owner-local `SECTION_STATE` block を追加し、`remaining_must_cover / used_fact_slots / latest ledger / current fact_slot` を narrow に外化
  - section ledger は `used_fact_slots_before/after` と `selected_summary` を持ち、summary bridge を keep したまま ledger 側を主 state として参照できる形にした
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st05ab1c or st05ab1f" -q`
    - `2 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q`
    - `202 passed, 3 failed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `65 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `14 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `83 passed`
- rollback note:
  - `section_generator.py` の `_SectionGenerationState` / state-fed prompt block / state advance helpers diff を戻せば baseline へ復帰可能
  - backup は `C:\tetie\notecode\backups\2026-04-06_arch_target_phase03_pre\section_generator.py`
- note:
  - `note\tests\test_newalgorithm_phase03_pipeline.py -q` の failures は `test_st05af_editor_guard_repairs_modal_collision_and_duplicate_tail` / `test_st07d_case_study_pipeline_keeps_condition_section_body` / `test_st07f_case_study_pipeline_keeps_condition_body_when_dedupe_truncates` の既存 3 件で、Phase 03 diff による新規回帰は増えていない

## Phase 04 Evidence

- status:
  - completed
- evidence:
  - `_resolve_section_generation_state()` を追加し、announcement dense route を explicit experiment なしでも promoted route として section-first path に載せる gate を `pipeline.py` owner に閉じた
  - `hierarchical_ab` summary に `selection_mode / fallback_to_super / fallback_reason` を追加し、requested experiment と promoted route を同じ telemetry で追えるようにした
  - section-first path で `SectionGenerationRuntimeError` が起きた場合は error return せず、super runtime へ fail-open fallback するように変更した
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st07aa or st07aaa or st07aaab or st07ab" -q`
    - `4 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q`
    - `204 passed, 3 failed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `65 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `14 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `83 passed`
- rollback note:
  - `pipeline.py` の promoted route gate / `hierarchical_ab` summary fields / fail-open fallback diff を戻せば baseline へ復帰可能
  - backup は `C:\tetie\notecode\backups\2026-04-06_arch_target_phase04_pre\pipeline.py`
- note:
  - `note\tests\test_newalgorithm_phase03_pipeline.py -q` の failures は `test_st05af_editor_guard_repairs_modal_collision_and_duplicate_tail` / `test_st07d_case_study_pipeline_keeps_condition_section_body` / `test_st07f_case_study_pipeline_keeps_condition_body_when_dedupe_truncates` の既存 3 件で、Phase 04 diff による新規回帰は増えていない

## Phase 05 Evidence

- status:
  - completed
- evidence:
  - `_repair_preserves_flagged_scope()` を追加し、patch-path repair では `flagged_spans` に含まれない section body と `title / lead / hashtags` の drift を reject するようにした
  - heading order/count は維持したまま、flagged heading だけを変える constrained micro-revision を accept する owner-local policy を `simple_note_pipeline/pipeline.py` に閉じた
  - repair telemetry に `scope_preserved / scope_rejection_reason` を追加し、patch-path repair が hidden rewrite に戻っていないかを結果から追えるようにした
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "shadow_section_drift or unflagged_section or omission_repair_only_in_safe_scope or uses_compare_thin_section_patch_path or rejects_repair_that_drops_alignment or repairs_short_rhythm_flatness_cluster" -q`
    - `6 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `66 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `14 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `83 passed`
- rollback note:
  - `simple_note_pipeline/pipeline.py` の `_repair_preserves_flagged_scope()` と patch-path acceptance diff を戻せば baseline へ復帰可能
  - backup は `C:\tetie\notecode\backups\2026-04-06_arch_target_phase05_pre\pipeline.py`

## Phase 06 Evidence

- status:
  - completed
- evidence:
  - `_extract_runtime_check()` / `_extract_primary_call()` / `_build_primary_generation_summary()` を追加し、wrapper が super runtime / section-first writer の nested field を都度読む hidden coupling を owner-local helper に寄せた
  - `_build_wrapper_quality_spine()` を追加し、`primary_generation -> compatibility_rebuild -> semantic_dedupe -> editor_guard -> resonance_pass -> quality_pass -> legal_postcheck -> output_formatter` の品質支配点を telemetry で固定した
  - `pipeline_check.body_generation.quality_spine` に `wrapper_role=adapter_validator` と primary owner/path を載せ、wrapper が恒久本体ではなく adapter/validator として振る舞うことを結果上でも確認できる形にした
- tests:
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st07aaa or st07aaab" -q`
    - `2 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q`
    - `209 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q`
    - `66 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q`
    - `14 passed`
  - `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
    - `83 passed`
- rollback note:
  - `newalgorithm_pipeline/pipeline.py` の primary generation summary helper / `quality_spine` telemetry diff を戻せば baseline へ復帰可能
  - backup は `C:\tetie\notecode\backups\2026-04-06_arch_target_phase06_pre\pipeline.py`
