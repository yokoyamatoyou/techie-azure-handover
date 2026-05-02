# separate window heading drift pipeline contract hint consumer triage note 2026-04-18

## Position

- この文書は `pipeline.py` owner の contract-hint consumer triage note である
- current source-of-truth update ではない
- implementation prompt ではない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- inherited stop result
- candidate lever comparison
- conclusion
- exact field
- exact owner slot
- narrow hypothesis
- why this lever reaches title / lead
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
- `C:\tetie\notecode\docs\separate_window_heading_drift_upstream_current_first_hint_pipeline_triage_note_2026-04-18.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_upstream_current_first_hint_pipeline_implementation_2026-04-18.md`
- `C:\tetie\notecode\logs\heading_drift_upstream_current_first_hint_live_validation_20260418-142418\summary.json`
- `C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json`
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py`
- `C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py`
- `C:\tetie\notecode\note\tests\test_current_mainline_runner.py`
- `C:\tetie\notecode\note\tests\test_current_mainline_regressions.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

## 実施範囲

- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` owner を維持したまま、
  existing contract fields の consumer surface だけを read-only で比較した
- 比較対象は prompt 指定どおり
  - `TOPIC_STATEMENT_CURRENT_FIRST_HINT_ONLY`
  - `CORE_MESSAGE_CURRENT_FIRST_HINT_ONLY`
  - `MUST_COVER_PRIORITY_ONLY`
  - `REPLAN_BEFORE_LEVER`
  に固定した
- code edit / test edit / live rerun には進んでいない

## inherited stop result

- `SOURCE_GROUNDING_ORDER_ONLY` は phase rule どおり stop / rollback 済み
- rollback 後 checks は
  - focused: `10 passed`
  - `test_current_mainline_ui_matrix.py -q`: `25 passed`
  - shared: `318 passed / 1 failed`
  - remaining fail は known owner-outside `test_st08b4_industry_analysis_title_and_lead_do_not_echo_prompt`
- live validation では
  - V3 first heading は current-first に改善した
  - しかし title は 2/3 run で history-frontloaded のままだった
- よって次の問いは `source order を続けるか` ではなく、
  `pipeline.py` から single-pass title / lead consumer へ届く既存 contract field はどれか`
  に変わった

## candidate lever comparison

### 1. `TOPIC_STATEMENT_CURRENT_FIRST_HINT_ONLY`

- consumer read:
  - `prompt_builder.py:1984-1986`
  - raw topic は `topic -> prompt_raw -> topic_statement -> core_message` の順で解決される
- limit:
  - V3 は nonblank company intro なので、`topic` / `prompt_raw` がある限り `topic_statement` は raw topic consumer の前に出ない
  - `pipeline.py:2657` の `super().generate(contract)` へ流れる primary single-pass prompt surface に対して、`topic_statement` 単独補正は弱い
- rank:
  - `third`

### 2. `CORE_MESSAGE_CURRENT_FIRST_HINT_ONLY`

- consumer read:
  - `prompt_builder.py:955-956`
    - explicit `core_message` は `core=...` として `HARD_CONTRACT` に入る
  - `prompt_builder.py:848-863` と `793-821`
    - company intro の `topic=` line は writer brief に置換され、`core_message` はその brief 末尾へ付与される
  - `pipeline.py:2412`
    - compatibility side でも `writing_intent = core_message or topic_statement`
  - `ui_prompt_distillation.py:269-277`
    - company intro default core は already current-first
- good:
  - title / lead に近い `HARD_CONTRACT` と company-intro writer brief の両方へ届く
  - new field 追加なしで `pipeline.py` 1 slot に閉じられる
  - V3 log では `core_message` が blank なので、追加の salience を実際に増やせる
- limit:
  - wording を増やしすぎると prompt accretion に寄る
  - したがって、blank or generic company-intro intent に限る narrow fill が必要
- rank:
  - `first`

### 3. `MUST_COVER_PRIORITY_ONLY`

- consumer read:
  - `prompt_builder.py:805-818`
    - writer brief は `must_cover` を current/history に split して使う
  - `prompt_builder.py:957-958`
    - `must_cover=...` が `HARD_CONTRACT` に入る
  - `prompt_builder.py:729-733`
    - heading progress rule にも入る
- limit:
  - V3 input contract はすでに `must_cover = 事業内容 / 選ばれる理由 / 歩み` で current-first だった
  - つまり `priority only` では新しい signal がほぼ増えない
  - `must_cover` は heading / body-wide recovery には効いても、title をさらに押す lever としては弱い
- rank:
  - `second`

### 4. `REPLAN_BEFORE_LEVER`

- judgment:
  - replan は不要
  - `core_message` に既存 consumer が十分あり、owner も `pipeline.py` のままで保てる
- rank:
  - `not needed`

## Conclusion

- conclusion:
  - `CORE_MESSAGE_CURRENT_FIRST_HINT_ONLY`

## exact field

- chosen field:
  - `contract["core_message"]`
- narrow shape:
  - blank or generic self-intro `branding/company_introduction` で
    existing `core_message` が空か弱い場合だけ、
    current-business-first / history-background の 1 line intent を入れる

## exact owner slot

- owner file:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- current exact slot:
  - `MinimalPipeline.generate()`
  - `resolve_input_contract(normalized_payload)` 後
  - `contract = _hydrate_compatibility_source_documents(dict(resolved.contract or {}))` の直後
  - `sections = list(build_discourse_plan(contract))` の直前
- current line block:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:2519-2563`

## narrow hypothesis

- `pipeline.py` の post-hydration / pre-plan slot で、blank or generic self-intro の `branding/company_introduction` に限って `contract["core_message"]` を current-business-first hint へ narrow に補うと、existing consumer の `core=` と company-intro writer brief が title / lead / first heading を history-first へ戻しにくくする。

## why this lever reaches title / lead

- `topic_statement` は raw topic consumer の優先順位で後ろにあり、nonblank V3 では primary consumer に届きにくい
- `must_cover` は current-first order が V3 ですでに入っており、priority-only では新 signal が増えない
- `core_message` はまだ空なので、同じ current-first 意味を
  - `HARD_CONTRACT` の `core=...`
  - company intro の `topic=` replacement brief
  - compatibility `writing_intent`
  に重ねて渡せる
- source ordering stop の結果でも first heading は動いたため、残る title / lead 側には source order より intent consumer のほうが近い

## what this next phase will not touch

- `contract["topic"]`
- `contract["prompt_raw"]`
- `contract["topic_statement"]`
- `contract["must_cover"]` の reorder retry
- `source_documents` / `source_grounding_items` reorder retry
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
- compact-plan bridge enable 拡張
- new field 追加
- prompt wording redesign

## rollback boundary

- next implementation に進む場合も `pipeline.py` owner の 1 diff に閉じる
- first diff は `core_message` fill only に留める
- `topic` / `must_cover` / source ordering / bridge enable を同時に触らない
- visible gate を満たせなければ、この `core_message` fill だけ rollback して stop する

## next prompt type

- next prompt type:
  - `implementation prompt`
- exact read:
  - `pipeline.py` の post-hydration / pre-plan slot で
    `contract["core_message"]` だけを narrow に current-first hint 化し、
    company intro nonblank guard を含む focused tests で
    title / lead / first heading の consumer reach を確認する prompt が妥当

## WEB search usage

- WEB search は使っていない
- local code / local docs / local logs / local tests の読取りだけで lever を 1 本に絞れた

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
