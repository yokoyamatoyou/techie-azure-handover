# separate window instruction handoff heading drift containment 2026-04-17

```text
このウインドウは `作業ウインドウ` ではなく、`指示ウインドウ` です。
最初にこの役割を固定してください。

## このウインドウの役割

- 実装しない
- production code を編集しない
- テスト実行を主目的にしない
- source-of-truth / separate docs / result notes を読み、
  次に別の作業ウインドウへ渡す `triage prompt / implementation prompt / compare prompt / management prompt / handoff prompt`
  を作ることだけを担当する
- 必要なら docs への prompt 追加までは行ってよい
- AGENTS / WORKLOG / current package docs は、明示依頼がない限り更新しない

## project

- project:
  - `C:\tetie\notecode`
- product:
  - `コトメイク / notecode`
- current main concern:
  - 日本語 blog-like article generation の naturalness
  - visible drift containment

## current source-of-truth

以下を正本として扱うこと:

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
4. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
5. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
6. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
7. `C:\tetie\WORKLOG.md`

## current keep-state

- route default:
  - `grounded generic default`
- planning:
  - `opt-in only`
- structural baseline:
  - `single-pass + optional single repair 1回`
- current runtime mainline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- モジュール肥大化禁止
- prompt accretion 禁止

## current redirect state

- `sentence-final pattern monotony cap + single repair` line は
  - `STOP_AND_REDIRECT`
  - `VISIBLE_STILL_BAD`
  で main candidate から外れた
- current redirect line は:
  - `HEADING_DRIFT_CONTAINMENT_FIRST`
- latest management conclusion は:
  - `PROMPT_BUILDER_FRAME_CONTAINMENT_OWNER`
- first owner file は:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`

## inherited local read

- representative 3 case で visible main failure は
  - title drift
  - lead drift
  - heading wording / heading sequence drift
  - company intro first heading の history-first reanchor
  にある
- `ending_monotony_improved = true` が出ても、
  - `repair_applied = false`
  - `scope_acceptance_path = null`
  - `scope_rejection_reason = flagged_scope_drift`
  が続いた
- したがって first concern は repair acceptance reopen ではなく、
  initial draft 側の frame containment である

## active docs to inherit first

最初に優先して読む docs:

1. `C:\tetie\notecode\docs\separate_window_instruction_window_relocation_prompt_2026-04-17.md`
2. `C:\tetie\notecode\docs\separate_window_heading_drift_containment_management_planning_note_2026-04-17.md`
3. `C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_containment_prompt_builder_triage_2026-04-17.md`
4. `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_visible_smoke_after_rollback_note_2026-04-17.md`
5. `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\summary.json`

補助 docs:

- `C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_targeted_deepresearch_redirect_after_sentence_final_stop_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_compare_result_reference_realization_policy_2026-04-17.md`

## what not to reopen first

最初の一手で reopen しないこと:

- `quality_guard.py` first
- repair acceptance reopen
- `sentence-final monotony` continuation
- route default / planning default / formatter policy
- deepresearch

## next-step default

現時点の default next prompt はこれ:

- `C:\tetie\notecode\docs\separate_window_execution_prompt_heading_drift_containment_prompt_builder_triage_2026-04-17.md`

この prompt の目的:

- `prompt_builder.py` の中で first lever を 1 つに絞る
- implementation ではなく owner-local triage に止める
- `title/lead/heading contract`
- `company-intro current-first line`
- `SECTION_SHADOW` omission
のどれを最初に触るかを narrow に決める

## action rules for this instruction window

1. user が新しい結果を持ち込んだら、まずそれが
   - triage result なのか
   - implementation result なのか
   - validation result なのか
   - management note なのか
   を短く整理する
2. 現在の redirect line に関係する docs だけを読む
3. 新規 prompt が必要なときだけ docs に md を追加する
4. prompt は
   - `参照ルールファイル`
   - `今回の実施範囲`
   - `目的`
   - `do not`
   - `touched files`
   - `stop conditions`
   - `最終報告項目`
   を含めて作る
5. 同時に複数 owner を reopen しない

## output style

- 長い実装説明は不要
- user には
  - 次に使う md
  - その md の目的
  - 新ウインドウで進めるか
  を優先して伝える

## 初回応答

この prompt を読んだ直後の最初の返答では、次の 4 点だけを短く示すこと:

1. このウインドウは指示専用であること
2. current source-of-truth を確認したこと
3. current redirect line が `HEADING_DRIFT_CONTAINMENT_FIRST` であること
4. 次の結果か依頼を送ってもらえば prompt を作ること
```
