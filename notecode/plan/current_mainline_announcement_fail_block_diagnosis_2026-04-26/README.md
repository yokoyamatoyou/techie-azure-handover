# current_mainline_announcement_fail_block_diagnosis_2026-04-26 README

## Objective

- `current_mainline_post_full_flow_issue_triage_2026-04-26` で first fix 候補になった `bl-announcement-spec-change` 2/2 `input_required_block` を診断する。
- source は sufficient と扱い、source不足では片づけない。
- runtime quality / UX classification / source reflection / announcement contract / UI harness or snapshot issue を分ける。
- 次の実装が必要な場合は、1 owner / 1 hypothesis に絞る。

## Source Of Truth

- Triage package:
  - `C:\tetie\notecode\plan\current_mainline_post_full_flow_issue_triage_2026-04-26\`
- Source artifact root:
  - `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\`
- Fail-closed UX policy:
  - `C:\tetie\notecode\plan\current_mainline_fail_closed_ux_policy_2026-04-25\PROGRESS.md`
- Current runtime mainline:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- This diagnosis package:
  - `C:\tetie\notecode\plan\current_mainline_announcement_fail_block_diagnosis_2026-04-26\`

## Non-Goals

- No product code change.
- No threshold change.
- No prompt text addition.
- No repair count addition.
- No UI demote expansion.
- No broad fail-closed draft display.
- No source-shortage conclusion.
- No mixing validation-script classification with product UI classification.

## Diagnosis Conclusion

`bl-announcement-spec-change` is not a true UI `input_required_block` product failure.

- The log-source regression script classified both attempts as `input_required_block` because `_outcome()` maps `blocked_output_redacted=True` to `input_required_block`.
- The UI visible text for both attempts contains `確認が必要なドラフトです` and rendered the generated article preview.
- Passing the same artifacts through `note_writer_app.py` output-guard block preparation returns `review_required_draft` for both attempts.

Separate remaining product issue:

- Both attempts omit FAQ source facts:
  - `承認者の再設定`
  - `通知先の確認`
  - `下書き保存`
  - `差し戻し通知`
  - `公開日時の再指定`
- The cause is an `announcement_contract_gap`: announcement runtime source contract does not activate and does not carry FAQ facts into `source_grounding_items` / `must_cover`.

## Owner Decision

First owner:

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

Narrow hypothesis:

- announcement runtime source contract availability is too strict and fails to activate from source text fallback, so FAQ action/checklist facts never become source-grounding or must-cover items.

