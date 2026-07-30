# current_mainline_fail_closed_ux_policy_2026-04-25 TASK

## Global Rules

- final quality guard / thresholds / source contract / leakage checks は変更しない。
- prompt / repair count / repair trigger は変更しない。
- `review_required_draft` は success ではない。telemetry outcome も success にしない。
- draft のコピー / 保存は警告付きで許可する。
- product owner は `C:\tetie\notecode\note\note_writer_app.py` の 1 file に限定する。
- `current_mainline_ui_result_adapter.py` が必要になったら product 変更前に停止する。

## Guard Boundary

`review_required_draft` は次をすべて満たす場合だけ許可する。

- `SYS_QUALITY_WARNINGS_UNRESOLVED` で止まっている。
- title / body が存在し、body は redacted placeholder ではない。
- resolved semantic route が input contract と一致する。
- source input が存在する。
- hard reasons / manual hits / needs input items がない。
- internal term leakage / source outside claim が記録されていない。
- legal / guarantee / unsupported / contract / missing required / prompt injection / route mismatch を含まない。
- 残りの理由が style flatness / rhythm / weak source reflection / repair-applied review などの確認可能な warning に閉じる。

`input_required_block` は次のいずれかで固定する。

- empty body / `SYS_PIPELINE_FAILURE` / route mismatch。
- source不足 / fetch failure / no valid sources / input required。
- source outside claim / unsupported claim / legal risk / internal leakage / manual instruction leakage。
- company/source contract failure / required source slot missing。
- must-cover/detail reflection が実質 absent。

## Phase Map

| Phase | Owner | Hypothesis | Exit |
| --- | --- | --- | --- |
| 0 Docs package | plan package + WORKLOG | UX boundary を source evidence から固定できる | README / TASK / PROGRESS / ROLLBACK / EXECUTION_PROMPT / WORKLOG updated |
| 1 Eligibility helper | `note_writer_app.py` | blocked final guard branch の前で safe draft eligibility を判定できる | focused unit tests pass |
| 2 UI branch wiring | `note_writer_app.py` | eligible draft を warning non-success として既存 text areas に表示できる | blocked unsafe behavior remains unchanged |
| 3 Regression | tests only | final guard semantics are unchanged | focused + shared checks pass |

## Required Tests

- company introduction rich-source body is `review_required_draft`.
- announcement weak-reflection body is `review_required_draft`.
- daily synthetic non-legal warning body is `review_required_draft`.
- branding route mismatch / empty body is `input_required_block`.
- source outside claim, internal leakage, manual hits, legal guarantee, unsupported claim are `input_required_block`.
- draft UI wording contains no internal terms.
- draft result does not set success or runtime reason `OK`.
- existing blocked non-draft output remains blocked.

## Stop Gate

- `current_mainline_ui_result_adapter.py` is required for product behavior.
- More than one product owner is required.
- Final guard thresholds or output guard semantics would need to change.
- Unsafe body display would be required to satisfy the UX.
- Focused tests cannot pass after 3 attempts.
