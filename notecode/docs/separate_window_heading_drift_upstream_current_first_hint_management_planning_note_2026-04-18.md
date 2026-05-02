# separate window heading drift upstream current first hint management planning note 2026-04-18

## Position

- この文書は `PROMPT_BUILDER_SIMPLIFICATION_FIRST` failed 後の next-owner management planning note である
- current source-of-truth update ではない
- implementation prompt ではない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- inherited local failure pattern
- candidate comparison
- conclusion
- first owner と narrow hypothesis
- why this owner before others
- what this phase will not touch
- rollback boundary
- next prompt
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
- `C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_reconstruction_simplification_first_2026-04-18.md`
- `C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_live_validation_note_2026-04-17.md`
- `C:\tetie\notecode\logs\heading_drift_reconstruction_simplification_first_20260418-121729\summary.json`
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`

## 実施範囲

- latest reconstruction result を current package constraints と突き合わせ、next owner を 1 file に閉じられるかを planning した
- 今回の判断対象は
  - `prompt_builder.py` retry を続けるか
  - `newalgorithm_pipeline/pipeline.py` 側で upstream minimal current-first hint / source ordering triage に進むか
  - それとも replan が先か
  に限定した
- code / tests / docs の更新には進んでいない

## inherited local failure pattern

- `prompt_builder.py` simplification pass は rollback 済みで kept diff なし
- validation matrix は 3 cycle 実施
  - `V1 x2 / V2 x1 / V3 x3 / G1 x2`
- result は
  - `V1`: partial / non-worse
  - `V2`: still awkward variance
  - `G1`: no visible regression
  - `V3`: mandatory gate fail
- exact read:
  - V3 run2 は title が history-first に戻った
  - V3 run3 は first section が history-first に戻った
- したがって
  - prompt wording simplification 単独では current-business-first opener variance を止め切れない
  - next retry を同 owner の wording 調整へ戻す理由は薄い

## candidate comparison

### 1. `PIPELINE_UPSTREAM_CURRENT_FIRST_HINT_OWNER`

- good:
  - `pipeline.py` は `resolve_input_contract(...)` 後の contract を持ち、`build_discourse_plan(contract)` に入る直前の owner である
  - `source_documents` / `source_grounding_items` / compact-plan bridge / compatibility fallback への入口が同 file に集まっている
  - minimal current-first hint や source ordering を 1 file に閉じて試せる余地がある
- limit:
  - まだ first lever が 1 本に絞れていないので、いきなり implementation prompt にすると広がる
- rank:
  - `first`

### 2. `PROMPT_BUILDER_RETRY`

- good:
  - touched surface は見えやすい
- limit:
  - same hypothesis を 3 cycle で fail 済み
  - local result 自体が `next owner recommendation only = pipeline.py side` を返している
  - wording 調整の continuation は `prompt accretion` 側へ戻りやすい
- rank:
  - `third`

### 3. `REPLAN_BEFORE_OWNER`

- good:
  - 保守的ではある
- limit:
  - next owner recommendation はすでに `pipeline.py`
  - owner を 1 file に閉じられないほど論点は拡散していない
  - 今不足しているのは広い planning ではなく、`pipeline.py` の first lever narrowing
- rank:
  - `second`

## Conclusion

- conclusion:
  - `PIPELINE_UPSTREAM_CURRENT_FIRST_HINT_OWNER`

## first owner と narrow hypothesis

- first owner file:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- next hypothesis:
  - `pipeline.py` で company intro の current-business evidence を upstream で先頭優先に寄せる最小 hint または source ordering を、`build_discourse_plan(contract)` 前の 1 lever に閉じて入れれば、prompt wording の再追加なしで V3 opener variance を減らせる。

## why this owner before others

- `prompt_builder.py` 側は rollback 済みかつ same hypothesis fail で止まっている
- 直近 summary では drift が完全に history-first へ固定されたわけではなく、run ごとに title / first section のどちらが崩れるかが揺れている
- この揺れは wording の微調整不足より、source salience / upstream ordering の揺れとして読むほうが自然
- `pipeline.py` は
  - contract hydration
  - discourse plan entry
  - compact-plan bridge
  - source-grounding fallback
  をまとめて持つため、upstream minimal hint の triage owner として最短である

## what this phase will not touch

- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` の wording retry
- `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- fixed routing table
- planning / skeleton default reopen
- AGENTS / WORKLOG / current package docs

## rollback boundary

- first triage は docs-only に留める
- next implementation に進む場合も `pipeline.py` owner の 1 diff に閉じる
- `discourse_planner.py` や `input_contract.py` を同時編集する前提にはしない

## Next Prompt

- next prompt type:
  - `owner-local triage prompt`
- exact read:
  - 次は `pipeline.py` の中で
    - contract-level current-first hint
    - `source_grounding_items` / `source_documents` ordering
    - compact-plan bridge 直前の company-intro bias
    のどれを first lever にするかを絞る triage prompt が妥当
- not yet:
  - implementation prompt

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない
