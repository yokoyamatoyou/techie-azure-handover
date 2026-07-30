# current_mainline_announcement_fail_block_diagnosis_2026-04-26 PROGRESS

## Current Status

- Package status: completed
- Current phase: Phase 5 handoff prompt
- Product code change: no
- Prompt / threshold / repair / UI demote change: no
- Diagnosis target: `bl-announcement-spec-change` attempts 1-2
- Selected owner for next implementation: `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## Evidence Read

- `C:\tetie\notecode\plan\current_mainline_post_full_flow_issue_triage_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_post_full_flow_issue_triage_2026-04-26\EXECUTION_PROMPT.md`
- `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\ui_live\bl-announcement-spec-change\attempt_1\`
- `C:\tetie\notecode\logs\current_mainline_log_source_ui_regression_20260426-023257\ui_live\bl-announcement-spec-change\attempt_2\`
- `C:\tetie\notecode\plan\current_mainline_fail_closed_ux_policy_2026-04-25\PROGRESS.md`
- `C:\tetie\WORKLOG.md`

## Phase Ledger

| Phase | Result | Notes |
|---|---|---|
| 0 package creation | complete | README / TASK / PROGRESS / ROLLBACK / EXECUTION_PROMPT created |
| 1 evidence read | complete | referenced packages, artifacts, app classification path, and WORKLOG reviewed |
| 2 attempt diagnosis | complete | attempts 1 and 2 diagnosed |
| 3 classification | complete | validation-script block separated from product app draft classification |
| 4 owner selection | complete | `simple_note_pipeline\pipeline.py` selected |
| 5 handoff prompt | complete | next implementation prompt written |

## Attempt Diagnosis

| Field | Attempt 1 | Attempt 2 |
|---|---|---|
| route | `article_type=announcement`; `semantic_article_key=announcement`; expected `announcement` | `article_type=announcement`; `semantic_article_key=announcement`; expected `announcement` |
| title/body | title exists; body 411 chars | title exists; body 396 chars |
| validation script outcome | `input_required_block` | `input_required_block` |
| actual app classification | `review_required_draft` when same artifact is passed through `note_writer_app.py` output-guard block preparation | `review_required_draft` when same artifact is passed through `note_writer_app.py` output-guard block preparation |
| reason code | `SYS_QUALITY_WARNINGS_UNRESOLVED` | `SYS_QUALITY_WARNINGS_UNRESOLVED` |
| guard reasons | fingerprint/style warnings + `source_grounding:weak_reflection` | fingerprint/style warnings + `source_grounding:weak_reflection` |
| repair | `repair_required=false`; `repair_applied=false` | `repair_required=true`; `repair_applied=true`; `repair_rejected=false` |
| must-cover | `変更点`, `対象と時期`, `必要な行動`; reflection `1.0` | `変更点`, `対象と時期`, `必要な行動`; reflection `1.0` |
| source grounding | ratio `0.3333`; reflected first source group only | ratio `0.3333`; reflected first source group only |
| announcement contract | `_announcement_source_contract.scope_match=false`; `source_contract_available=false` | `_announcement_source_contract.scope_match=false`; `source_contract_available=false` |
| body risk | FAQ facts missing | FAQ facts missing |

## Source Fact Coverage

| Source fact | Attempt 1 | Attempt 2 | Judgment |
|---|---|---|---|
| `2026年4月15日10時` | reflected | reflected | body side OK |
| `一段階から二段階へ変更` | reflected | reflected | body side OK |
| `編集担当者と承認者` | reflected | reflected | body side OK |
| `旧手順は2026年4月30日まで参照専用` | reflected | reflected | body side OK |
| `承認者の再設定` | missing | missing | source packet / contract gap |
| `通知先の確認` | missing | missing | source packet / contract gap |
| `下書き保存` | missing | missing | source packet / contract gap |
| `差し戻し通知` | missing | missing | source packet / contract gap |
| `公開日時の再指定` | missing | missing | source packet / contract gap |

## Classification

Reported `input_required_block`:

- Classification: `UI_harness_or_snapshot_issue`
- Cause: validation script `_outcome()` maps `blocked_output_redacted=True` to `input_required_block`.
- Product app behavior: the same artifacts are eligible for `review_required_draft`.
- UI visible evidence: both attempts show `確認が必要なドラフトです` and render article preview text.

Underlying article-quality issue:

- Classification: `announcement_contract_gap`
- Cause: announcement runtime contract / source packet does not activate and does not carry FAQ facts into `source_grounding_items` / `must_cover`.
- This is not source shortage.
- This is not threshold, prompt, repair-count, or UI demote behavior.

## Owner Decision

First owner:

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

Narrow hypothesis:

- announcement runtime source contract availability is too strict and fails to activate from source text fallback, so FAQ action/checklist facts never become source-grounding or must-cover items.

Non-owners for the next fix:

- `note_writer_app.py`: not first owner because actual app classification already returns `review_required_draft`.
- `newalgorithm_pipeline\quality_observability_mixin.py`: not first owner because the metric is reacting to missing source-grounding inputs.
- `prompt_builder.py`: not an owner because prompt text addition is prohibited; treat the issue as contract/source-packet input, not prompt wording.

## Verification

- Docs-only package.
- Product code unchanged.
- No tests run because no product code changed.

