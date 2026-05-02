# article_generator helper split handoff (2026-03-15)

## 1. Current state

- `current mainline owner split` is already `completed`.
- `comparative_review` quality slice is already closed.
- `note_writer_app.py` side split is largely stabilized:
  - confirm projection -> `current_mainline_ui_confirm_adapter.py`
  - result / blocked projection -> `current_mainline_ui_result_adapter.py`
  - generation telemetry input assembly -> `current_mainline_ui_generation_telemetry_adapter.py`
  - pre-run / exception / finally / complete transition plans -> `current_mainline_ui_generation_state_adapter.py`
- Active physical slimming track is now `note/article_generator.py`.

## 2. Confirmed latest repo state

- Latest confirmed split in `WORKLOG.md` head:
  - `article_final_consistency_mixin.py` was added.
  - final consistency / style normalize / dedupe utility cluster was moved out of `article_generator.py`.
  - `generate()`, zero-base orchestration, and `_apply_compacted_postprocess_pipeline()` remain in `article_generator.py`.
- `zero_base_section_helper_mixin.py` is also already split.
- `AGENTS.md` and `notecode/ALGORITHM.md` already reflect the latest split.
- `article_generator.py` current size is about `8453` lines.
- `note_writer_app.py` current size is about `5490` lines.

## 3. article_generator mixins already extracted

- `zero_base_contract_mixin.py`
- `article_output_mixin.py`
- `article_style_persona_mixin.py`
- `article_prompt_contract_mixin.py`
- `article_length_planning_mixin.py`
- `article_perspective_audience_mixin.py`
- `article_cognitive_drift_mixin.py`
- `zero_base_section_helper_mixin.py`
- `article_final_consistency_mixin.py`

## 4. Still important in article_generator.py

- orchestration owner remains in `article_generator.py`
  - `generate()`
  - `_generate_zero_base_scaffold()`
  - `_zero_base_generate_section()`
  - `_apply_compacted_postprocess_pipeline()`
  - `_generate_section()` / paragraph-mode orchestration
- remaining helper-heavy cluster still visible around the novelty / redundancy / feedback area:
  - `_normalize_similarity_text()`
  - `_to_char_ngram_set()`
  - `_similarity_overlap_scores()`
  - `_is_redundant_expansion()`
  - `_build_section_overlap_memory()`
  - `_get_redundancy_thresholds()`
  - `_extract_content_terms()`
  - `_build_lexical_priming_feedback()`
  - `_build_fingerprint_feedback()`
  - `_lookup_fingerprint_prompt_hint()`
  - `_build_section_generation_feedback()`
  - `_render_section_feedback_block()`
  - `_is_redundant_section()`
  - `_check_redundancy_with_reason()`
  - `_compute_section_novelty_report()`
  - `_get_novelty_threshold()`
  - `_should_retry_due_to_low_novelty()`

## 5. Recommended next action

- Next work should start in a **new window**.
- Mode should be **PLAN mode**.
- Reason:
  - context is already large
  - current slice is complete and recorded
  - next step is not implementation first, but selecting the next true split target

## 6. Likely next target

Primary candidate:
- novelty / redundancy / section feedback utility cluster

Why it is the next likely candidate:
- it still looks like a cohesive helper cluster inside `article_generator.py`
- it is separate from the already-split final consistency utility
- it can be evaluated without reopening current mainline runtime owners

Risk / caution:
- this cluster shares primitives across multiple downstream helpers, so do not start implementation before owner shape is confirmed
- avoid mixing it with postprocess orchestration or zero-base generation orchestration

## 7. Known note from latest verification

- `test_offline.py::test_r19_cap_colloquial_allows_two` still disagrees with current constant shape.
- Latest slice did not change tuning and excluded that case from the focused run.
- Treat that as a separate tuning/test-alignment issue, not as the next split target by default.

## 8. Files to read first tomorrow

- `C:\tetie\AGENTS.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\ALGORITHM.md`
- `C:\tetie\notecode\note\article_generator.py`
- `C:\tetie\notecode\note\article_final_consistency_mixin.py`
- `C:\tetie\notecode\note\zero_base_section_helper_mixin.py`
- `C:\tetie\notecode\note\article_cognitive_drift_mixin.py`
- `C:\tetie\notecode\note\article_perspective_audience_mixin.py`
- `C:\tetie\notecode\note\article_length_planning_mixin.py`
- `C:\tetie\notecode\note\article_prompt_contract_mixin.py`
- `C:\tetie\notecode\note\article_output_mixin.py`
- `C:\tetie\notecode\note\article_style_persona_mixin.py`
- `C:\tetie\notecode\note\zero_base_contract_mixin.py`
- `C:\tetie\notecode\note\article_helper_facade.py`
- `C:\tetie\notecode\note\tests\test_article_final_consistency_mixin_structure.py`
- `C:\tetie\notecode\note\tests\test_zero_base_section_helper_mixin_structure.py`
- `C:\tetie\notecode\note\tests\test_article_cognitive_drift_mixin_structure.py`
- `C:\tetie\notecode\note\tests\test_article_perspective_audience_mixin_structure.py`
- `C:\tetie\notecode\note\tests\test_article_length_planning_mixin_structure.py`
- `C:\tetie\notecode\note\tests\test_article_prompt_contract_mixin_structure.py`
- `C:\tetie\notecode\note\tests\test_article_output_mixin_structure.py`
- `C:\tetie\notecode\note\tests\test_article_style_persona_mixin_structure.py`
- `C:\tetie\notecode\note\tests\test_zero_base_contract_structure.py`
- `C:\tetie\notecode\note\tests\test_article_helper_facade.py`

## 9. Copy-paste prompt for tomorrow

```text
C:\tetie\notecode の current mainline を主対象に進めてください。
PLANモードで作業してください。

この再開の正本:
- C:\tetie\notecode\docs\article_generator_helper_split_handoff_2026-03-15.md

【今回のテーマ】
- current mainline owner split は completed のまま
- note_writer_app.py の current mainline split は一旦安定
- article_generator.py では
  - zero_base_contract_mixin.py
  - article_output_mixin.py
  - article_style_persona_mixin.py
  - article_prompt_contract_mixin.py
  - article_length_planning_mixin.py
  - article_perspective_audience_mixin.py
  - article_cognitive_drift_mixin.py
  - zero_base_section_helper_mixin.py
  - article_final_consistency_mixin.py
  まで分離済み
- 今回は article_generator.py に残る helper / compatibility owner の次の最小 split target を決める
- まだコード編集しない

【最初に読む】
- C:\tetie\AGENTS.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\notecode\docs\article_generator_helper_split_handoff_2026-03-15.md
- C:\tetie\notecode\note\article_generator.py
- C:\tetie\notecode\note\article_final_consistency_mixin.py
- C:\tetie\notecode\note\zero_base_section_helper_mixin.py
- C:\tetie\notecode\note\article_cognitive_drift_mixin.py
- C:\tetie\notecode\note\article_perspective_audience_mixin.py
- C:\tetie\notecode\note\article_length_planning_mixin.py
- C:\tetie\notecode\note\article_prompt_contract_mixin.py
- C:\tetie\notecode\note\article_output_mixin.py
- C:\tetie\notecode\note\article_style_persona_mixin.py
- C:\tetie\notecode\note\zero_base_contract_mixin.py
- C:\tetie\notecode\note\article_helper_facade.py
- C:\tetie\notecode\note\tests\test_article_final_consistency_mixin_structure.py
- C:\tetie\notecode\note\tests\test_zero_base_section_helper_mixin_structure.py
- C:\tetie\notecode\note\tests\test_article_cognitive_drift_mixin_structure.py
- C:\tetie\notecode\note\tests\test_article_perspective_audience_mixin_structure.py
- C:\tetie\notecode\note\tests\test_article_length_planning_mixin_structure.py
- C:\tetie\notecode\note\tests\test_article_prompt_contract_mixin_structure.py
- C:\tetie\notecode\note\tests\test_article_output_mixin_structure.py
- C:\tetie\notecode\note\tests\test_article_style_persona_mixin_structure.py
- C:\tetie\notecode\note\tests\test_zero_base_contract_structure.py
- C:\tetie\notecode\note\tests\test_article_helper_facade.py

【今回の目的】
- article_generator.py に残る helper / compatibility cluster を再分類する
- novelty / redundancy / section feedback utility を次 slice にするべきかを判断する
- 既存 mixin 群と責務重複しない next cluster を 1 つに絞る
- 実装前の判断材料を固める

【主な確認対象】
- novelty / redundancy / feedback cluster
  - _normalize_similarity_text
  - _to_char_ngram_set
  - _similarity_overlap_scores
  - _is_redundant_expansion
  - _build_section_overlap_memory
  - _get_redundancy_thresholds
  - _extract_content_terms
  - _build_lexical_priming_feedback
  - _build_fingerprint_feedback
  - _lookup_fingerprint_prompt_hint
  - _build_section_generation_feedback
  - _render_section_feedback_block
  - _is_redundant_section
  - _check_redundancy_with_reason
  - _compute_section_novelty_report
  - _get_novelty_threshold
  - _should_retry_due_to_low_novelty
- generate() / zero-base orchestration / current mainline 境界と混線しないか
- final consistency / postprocess orchestration と混線しないか
- より小さい別 cluster が先にあるか

【進め方】
- 最初に update_plan で 4〜6 steps の作業計画を出す
- まずはコード編集しない
- 次の順で確認する
  - article_generator.py の残 helper 群を cluster ごとに分類する
  - novelty / redundancy / feedback cluster の凝集度を確認する
  - 既存 mixin と current mainline 境界への影響を確認する
  - 次の最小 split target を 1 つに絞る
- その後に
  - novelty / redundancy / feedback cluster に進む
  - まだ owner 確定できない
  - より小さい別 cluster を先に切るべき
  のどれかを根拠つきで決める

【最終的に出してほしい内容】
1. 現状認識
2. findings
- 事実と推測を分ける
- owner を明記する
3. article_generator.py の次の true split target
4. novelty / redundancy / feedback cluster を先に切るべきか
5. 直すならどの関数群をどこへ分けるか
6. 検証計画
7. AGENTS/WORKLOG 更新要否
```
