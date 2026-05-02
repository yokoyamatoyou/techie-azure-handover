# separate window heading drift upstream current first hint pipeline triage note 2026-04-18

## Position

- この文書は `PIPELINE_UPSTREAM_CURRENT_FIRST_HINT_OWNER` の owner-local triage note である
- current source-of-truth update ではない
- implementation prompt ではない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- inherited local failure pattern
- candidate lever comparison
- conclusion
- exact hook location
- narrow hypothesis
- why this lever before others
- what this next phase will not touch
- rollback boundary
- next prompt type
- WEB search usage
- non-updates

## 読んだ参照ルールファイル

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\docs\separate_window_heading_drift_upstream_current_first_hint_management_planning_note_2026-04-18.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_upstream_current_first_hint_pipeline_triage_2026-04-18.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_reconstruction_simplification_first_2026-04-18.md`
- `C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_live_validation_note_2026-04-17.md`
- `C:\tetie\notecode\logs\heading_drift_reconstruction_simplification_first_20260418-121729\summary.json`
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py`
- `C:\tetie\notecode\note\tests\test_current_mainline_runner.py`
- `C:\tetie\notecode\note\tests\test_current_mainline_regressions.py`

## 実施範囲

- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` の中で、候補 hook を
  - `MinimalPipeline.generate()` の post-hydration / pre-plan slot
  - `MinimalPipeline._maybe_build_compact_plan()` の bridge-entry
  の 2 箇所に限定して比較した
- 今回の lever 判定は
  - `CONTRACT_HINT_BEFORE_DISCOURSE_PLAN`
  - `SOURCE_GROUNDING_ORDER_ONLY`
  - `COMPACT_PLAN_BRIDGE_ENTRY_ONLY`
  の 3 候補だけに閉じた
- code edit / test edit / live rerun / source-of-truth update には進んでいない

## inherited local failure pattern

- `prompt_builder.py` simplification pass は rollback 済みで kept diff なし
- reconstruction summary では
  - V1 partial / non-worse
  - V2 still awkward variance
  - G1 no visible regression
  - V3 mandatory gate fail
  だった
- exact read:
  - V3 run2 は title が history-first に戻った
  - V3 run3 は first section が history-first に戻った
- したがって、same owner の wording retry より upstream salience / ordering 側を先に切るほうが自然

## candidate lever comparison

### 1. `SOURCE_GROUNDING_ORDER_ONLY`

- location:
  - `MinimalPipeline.generate()`
  - `contract = _hydrate_compatibility_source_documents(...)` 後
  - `sections = list(build_discourse_plan(contract))` 前
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:2400-2441`
- good:
  - 1 diff を `generate()` の単一 slot に閉じられる
  - `contract["source_documents"]` / `contract["source_grounding_items"]` の順序だけを触るため、新 field 追加なしで済む
  - 同じ reordered contract が
    - `build_discourse_plan(contract)`
    - single-pass default の downstream `super().generate(contract)`
    - compatibility fallback
    にそのまま流れる
  - order-sensitive read が pipeline 内に既にある
    - `_section_fact_text(...)` は section source が無い場合に `source_grounding_items[index]` を使う
    - `_build_compatibility_body(...)` は contract の `source_grounding_items` を section index fallback に使う
    - `_select_source_grounding_fact(...)` は先頭から最初に合う fact を採る
    - `_bridge_claim_for_section(...)` は section の先頭 2 facts を優先する
- limit:
  - reorder rule は company intro current-first に narrow である必要がある
  - broad hardcode table にすると current rule に反する
- rank:
  - `first`

### 2. `CONTRACT_HINT_BEFORE_DISCOURSE_PLAN`

- location:
  - `MinimalPipeline.generate()`
  - `contract = _hydrate_compatibility_source_documents(...)` 後
  - `sections = list(build_discourse_plan(contract))` 前
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:2400-2441`
- good:
  - same slot に閉じられる
  - discourse plan telemetry には最短で効かせやすい
- limit:
  - company intro current path は `single_pass_default` かつ `writer_of_record = simple_note_pipeline` / `section_path_used = false` で、primary generation は section path に乗っていない
  - new hint field を足しても、`pipeline.py` 単独で primary single-pass へ効く既存 consumer が薄い
  - 実質的に build-discourse-plan 用の state 追加に寄ると、visible opener variance へ届かない恐れがある
- rank:
  - `second`

### 3. `COMPACT_PLAN_BRIDGE_ENTRY_ONLY`

- location:
  - `MinimalPipeline._maybe_build_compact_plan()`
  - `bridged_plan = _build_compact_plan_bridge_from_discourse_sections(...)`
  - `if bridged_plan:`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:2258-2269`
- good:
  - touched surface は非常に狭い
  - compact-plan bridge に乗れば opener anchor を強く寄せられる
- limit:
  - `_build_compact_plan_bridge_from_discourse_sections(...)` は `_upstream_discourse_plan_bridge_enabled(contract)` に gated されている
  - current gate は `article_type == branding` でも `semantic_key == branding` かつ `content_goal == trust` short route 向けで、`company_introduction` にはそのまま当たらない
  - company intro へ効かせるには bridge enable 条件まで広げる必要があり、今回の bridge-entry-only scope をはみ出しやすい
- rank:
  - `third`

## Conclusion

- conclusion:
  - `SOURCE_GROUNDING_ORDER_ONLY`

## exact hook location

- first hook:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:2401-2441`
- exact slot:
  - `MinimalPipeline.generate()` 内の post-hydration / pre-plan slot
  - `contract = _hydrate_compatibility_source_documents(dict(resolved.contract or {}))` の直後から
  - `sections = list(build_discourse_plan(contract))` の直前まで
- implementation shape:
  - 1 call で `contract["source_documents"]` と `contract["source_grounding_items"]` の company-intro current-first priority を narrow に並べ替える
  - hint field の追加や bridge enable 条件変更は first diff に含めない

## narrow hypothesis

- `pipeline.py` の post-hydration / pre-plan slot で、blank `branding/company_introduction` に限って `source_documents` と `source_grounding_items` を current-business-first priority へ narrow に並べ替えれば、prompt wording を増やさずに、discourse plan と downstream single-pass fallback の両方で history-first opener variance を減らせる。

## why this lever before others

- drift は wording 固定失敗というより、title と first section のどちらが崩れるかが run ごとに揺れている
- `CONTRACT_HINT_BEFORE_DISCOURSE_PLAN` は discourse plan には効いても、single-pass default の本文 owner `simple_note_pipeline` へ直接効く保証が弱い
- `SOURCE_GROUNDING_ORDER_ONLY` は new field を増やさず、既存 contract surface のままで
  - discourse plan
  - compatibility fallback
  - order-sensitive source consumption
  に同時に効く
- `COMPACT_PLAN_BRIDGE_ENTRY_ONLY` は current company intro path では enable gate の外側にあり、first lever としては遠い

## what this next phase will not touch

- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` の wording retry
- `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- compact-plan bridge enable 条件の拡張
- fixed routing table
- planning / skeleton default reopen
- AGENTS / WORKLOG / current package docs

## rollback boundary

- next implementation に進む場合も `pipeline.py` owner の 1 diff に閉じる
- first diff は source ordering only に留める
- new contract field 追加、bridge enable 条件変更、`discourse_planner.py` 同時編集は前提にしない
- order-only lever で V3 variance が減らなければ rollback し、次 lever を management 側へ返す

## next prompt type

- next prompt type:
  - `implementation prompt`
- exact read:
  - `SOURCE_GROUNDING_ORDER_ONLY` を `MinimalPipeline.generate()` の post-hydration / pre-plan slot へ 1 diff で入れ、
    blank `branding/company_introduction` の current-first priority が
    - discourse plan
    - single-pass default
    - compatibility fallback
    にどう伝播するかを focused tests で確認する prompt が妥当

## WEB search usage

- WEB search は使っていない
- local code / local docs / local tests の読取りだけで lever を 1 本に絞れた

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
