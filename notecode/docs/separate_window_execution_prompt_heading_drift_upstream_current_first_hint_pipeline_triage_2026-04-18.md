# separate window execution prompt heading drift upstream current first hint pipeline triage 2026-04-18

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_heading_drift_upstream_current_first_hint_management_planning_note_2026-04-18.md
- C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_reconstruction_simplification_first_2026-04-18.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_live_validation_note_2026-04-17.md
- C:\tetie\notecode\logs\heading_drift_reconstruction_simplification_first_20260418-121729\summary.json
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py
- C:\tetie\notecode\note\tests\test_current_mainline_runner.py
- C:\tetie\notecode\note\tests\test_current_mainline_regressions.py

今回の依頼種別:
- owner-local triage prompt
- `PIPELINE_UPSTREAM_CURRENT_FIRST_HINT_OWNER`
- source-of-truth update ではない
- implementation prompt ではない

今回の実施範囲:
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` の中だけを読み、
  company intro opener variance を減らすための first lever を 1 本に絞る
- code edit / test edit / docs source-of-truth update はしない
- triage note 1 本だけを作る

inherited result:
- `prompt_builder.py` simplification pass は rollback 済み
- 3 cycle validation の summary:
  - V1 partial / non-worse
  - V2 still awkward variance
  - G1 no visible regression
  - V3 mandatory gate fail
- exact failure:
  - V3 run2:
    - title が history-first に戻る
  - V3 run3:
    - first section が history-first に戻る
- conclusion already fixed by management:
  - next owner is `pipeline.py`
  - next step is triage, not implementation

current keep-state:
- current default route:
  - `grounded generic default`
- planning / skeleton:
  - opt-in only
  - default reopen しない
- structural baseline:
  - `single-pass + optional single repair 1回`
- prompt accretion 禁止
- hidden reviser accretion 禁止
- fixed routing table 追加禁止
- `prompt_builder.py` retry を同 hypothesis で続けない

core triage question:
- `pipeline.py` のどこに最小の current-first hint / source ordering hook を置くと、
  `build_discourse_plan(contract)` に入る前の upstream state だけで V3 opener variance を抑えられるか

exact hook map:
- `CONTRACT_HINT_BEFORE_DISCOURSE_PLAN`
  - candidate location is only:
    - `MinimalPipeline.generate()`
    - after `contract = _hydrate_compatibility_source_documents(dict(resolved.contract or {}))`
    - before `sections = list(build_discourse_plan(contract))`
  - current reference:
    - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:2400-2441`
  - treat this as
    - post-hydration / pre-plan contract hook
  - do not spread this candidate into other functions
- `SOURCE_GROUNDING_ORDER_ONLY`
  - candidate location is also only:
    - `MinimalPipeline.generate()`
    - same post-hydration / pre-plan slot
  - current reference:
    - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:2400-2441`
  - exact operation boundary:
    - reorder only `contract["source_documents"]` and/or `contract["source_grounding_items"]`
    - do not add new prompt wording here
    - do not move this candidate into `_hydrate_compatibility_source_documents(...)` unless triage finds a hard reason
- `COMPACT_PLAN_BRIDGE_ENTRY_ONLY`
  - candidate location is only:
    - `MinimalPipeline._maybe_build_compact_plan()`
    - around `bridged_plan = _build_compact_plan_bridge_from_discourse_sections(contract, build_discourse_plan(contract))`
    - and the immediate `if bridged_plan:` branch
  - current reference:
    - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:2258-2269`
  - treat this as
    - bridge-entry-only hook
  - do not widen to `discourse_planner.py`

read-only downstream evidence, not first-hook candidates:
- `_hydrate_compatibility_source_documents(...)`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:838-873`
  - read as hydration boundary evidence
  - not a first implementation hook unless triage proves post-hydration is impossible
- `_build_compatibility_body(...)`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py:1091-1116`
  - read only as downstream order-sensitive evidence because `_section_fact_text(...)` can consume `source_grounding_items[index]`
  - not a first-hook candidate

candidate levers to compare explicitly:
1. `CONTRACT_HINT_BEFORE_DISCOURSE_PLAN`
   - `resolve_input_contract(...)` / `_hydrate_compatibility_source_documents(...)` 後、
     `build_discourse_plan(contract)` 前に
     company intro current-first hint を contract field として narrow に足す
2. `SOURCE_GROUNDING_ORDER_ONLY`
   - `source_documents` or `source_grounding_items` の順序だけを
     blank company intro current-business-first priority へ narrow に並べ替える
3. `COMPACT_PLAN_BRIDGE_ENTRY_ONLY`
   - `_maybe_build_compact_plan(...)` / discourse bridge 入口だけで
     first section anchor を current-first に寄せる
4. `REPLAN_BEFORE_LEVER`
   - 1 file 内でも lever を 1 本に閉じられない場合

strong bias:
- `prompt_builder.py` wording retry に戻らない
- `discourse_planner.py` を first owner にしない
- `input_contract.py` を first owner にしない
- `quality_guard.py` / acceptance reopen を first remedy にしない
- planning default reopen に戻らない
- company intro 専用の broad hardcode table を増やさない
- implementation に進まない

what to inspect in `pipeline.py`:
- `MinimalPipeline.generate()`
  - `resolve_input_contract(...)` 後
  - `_hydrate_compatibility_source_documents(...)` 後
  - `sections = list(build_discourse_plan(contract))` 前
- `MinimalPipeline._maybe_build_compact_plan(...)`
- `_hydrate_compatibility_source_documents(...)`
  - hydration boundary evidence としてだけ読む
- `_build_compatibility_body(...)`
  - downstream order-sensitive evidence としてだけ読む
- `source_grounding_items[0]` や `source_grounding_items[index]` のような order-sensitive fallback が opener に効きうる箇所

what to inspect in tests:
- `test_newalgorithm_phase03_pipeline.py`
  - source grounding / planning gate / company intro に近い tests
- `test_current_mainline_runner.py`
- `test_current_mainline_regressions.py`
- ただし読取りだけ

what to decide:
1. first lever 名
2. why this lever before the other 2
3. owner-local 1 diff に閉じられる理由
4. next prompt type
   - implementation prompt
   - or second triage if still too wide

preferred output shape:
- triage note 1 本
- conclusion は exactly one of:
  - `CONTRACT_HINT_BEFORE_DISCOURSE_PLAN`
  - `SOURCE_GROUNDING_ORDER_ONLY`
  - `COMPACT_PLAN_BRIDGE_ENTRY_ONLY`
  - `REPLAN_BEFORE_LEVER`
- if not `REPLAN_BEFORE_LEVER`:
  - chosen function and line block
  - exact hook location
  - narrow hypothesis 1 文
  - what not to touch
  - rollback boundary
  - next prompt type

recommended output file:
- C:\tetie\notecode\docs\separate_window_heading_drift_upstream_current_first_hint_pipeline_triage_note_2026-04-18.md

do not do:
- code edit
- test edit
- live rerun
- current package docs update
- AGENTS / WORKLOG update
- prompt wording案の再設計
- giant upstream reopen proposal

WEB search policy:
- 原則不要
- local code だけで lever を切れない場合のみ 1 回だけ許可
- 使った場合は query と採用理由を短く報告する

stopping conditions:
- lever を 1 本に絞れない
- `pipeline.py` だけでは閉じないと判明した
- implementation を始めたくなった
- conclusion を 2 本以上にぼかしたくなった

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. inherited local failure pattern の短い要約
4. candidate levers の比較
5. conclusion
6. exact hook location
7. narrow hypothesis
8. what this next phase will not touch
9. rollback boundary
10. next prompt type
11. WEB検索を使ったかどうか
12. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```
