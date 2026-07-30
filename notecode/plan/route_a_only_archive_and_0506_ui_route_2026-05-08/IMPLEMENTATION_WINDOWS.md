# IMPLEMENTATION_WINDOWS

Date: 2026-05-08 JST

## Window 1: Archive / Code Move Only

Goal: remove rejected non-Route-A experiments from current execution surface, then archive them with manifest.

Owner scope:

- old `materialized_*`
- deepresearch vNext compare tools
- Route D / Route E generation-only experiments
- old vnext/materialized tests and fixtures
- rejected route plan package references

Do not:

- add new 0506 route
- touch Route A prompt, repair, thresholds, or acceptance
- regenerate Route A
- send API requests

Exit criteria:

- current references removed or neutralized
- archive target manifest created
- moved files are restorable
- Route A current owner tests pass
- `note.route_b_0506_adapter` still imports if it is kept for Window 2

Copy-paste prompt:

```text
C:\tetie\notecode で作業してください。Window 1: archive/code move only です。AGENTS.md と plan\route_a_only_archive_and_0506_ui_route_2026-05-08\README.md / ARCHIVE_INVENTORY.md / SECURITY_GATE.md を読んでください。Route A current success path は保持し、Route A prompt / repair / threshold / acceptance / saved artifact は触らないでください。old materialized_* / deepresearch / Route D / Route E / old vnext 実験 route を current 実行面から外し、事前 manifest と hash/size inventory を作ってから C:\tetie\notecode\archive\route_experiments_rejected_2026-05-08\ へ archive-only move してください。同名衝突、.env/.venv/secret系、current Route A owner test failure があれば停止して報告してください。API送信とRoute A再生成は禁止です。
```

## Window 2: New Route Skeleton / Adapter Only

Goal: introduce `route_0506_structured_blog_ui_v1` skeleton and adapter boundaries without UI-live generation.

Owner scope:

- generation adapter module
- result adapter module
- route contract tests
- security gate scaffolding
- usage ledger writer

Do not:

- wire current UI live button yet
- call OpenAI
- tune 0506 quality
- use Route A fallback
- revive old routes

Exit criteria:

- adapter maps current `input_contract` to 0506 `ExtractedSource`
- mapping tests cover all listed genre mappings
- source_documents-only grounding is enforced
- URL refetch and local file reads are blocked
- invalid schema output fails closed
- usage ledger writes one row per mocked API call

Copy-paste prompt:

```text
C:\tetie\notecode で作業してください。Window 2: new route skeleton / adapter only です。plan\route_a_only_archive_and_0506_ui_route_2026-05-08\README.md / NEW_ROUTE_CONTRACT.md / SECURITY_GATE.md を読んでください。Route ID は route_0506_structured_blog_ui_v1。0506 staged algorithm を note_writer_app.py に混ぜず、generation adapter / result adapter / usage ledger / security gate scaffold だけを実装してください。source_documents だけを grounding source とし、URL refetch、local file reads、Route A fallback、old materialized/deepresearch/Route D/Route E fallbackは禁止。OpenAI API送信とUI-live生成は禁止。schema compatibility blocker は adapter/schema owner として fail-closed test にしてください。
```

## Window 3: Saved-Source CLI Validation Only

Goal: validate the new route against the same saved source snapshot without UI-live generation.

Owner scope:

- saved-source CLI runner
- artifact contract
- security gate artifact
- usage ledger with actual API usage only after explicit approval

Do not:

- refetch URL
- regenerate Route A
- use Route A fallback
- tune quality
- run broad matrix

Exit criteria:

- `source_snapshot.json` hash matches saved baseline source
- `input_contract.json` is written
- `route_0506/latest_generation_output.md` or `blocked.json` is written
- `latest_generation_quality_report.json` is written when article exists
- `usage_ledger.jsonl` has one row per API call
- `security_gate.json` is `pass`, `hold`, or `blocked` with reasons

Copy-paste prompt:

```text
C:\tetie\notecode で作業してください。Window 3: saved-source CLI validation only です。plan\route_a_only_archive_and_0506_ui_route_2026-05-08\NEW_ROUTE_CONTRACT.md / SECURITY_GATE.md / IMPLEMENTATION_WINDOWS.md を読んでください。Route A は saved artifact のみ参照し、再生成しないでください。source は logs\latest_generation_output.json の input_contract/source_documents 由来に固定し、URL refetchは禁止。OpenAI API送信が必要な場合は、local preflight と artifact root 準備を終えてから scope を明示して承認を取ってください。品質チューニングは禁止。結果は saved-source artifact contract に従って保存してください。
```

## Window 4: Current UI Body Generation 1 Case Only

Goal: connect the new route to current UI for one body-generation case only.

Owner scope:

- UI route selection
- current UI input collection
- UI selection snapshot
- visible result projection

Do not:

- change Route A default
- run multiple cases
- tune quality
- change 0506 internals
- use Route A fallback

Exit criteria:

- exactly one UI-live body generation attempt
- `article_type`, `semantic_article_key`, and `ui_journey` snapshot written
- visible output or blocked state is shown safely
- security gate artifact written
- if quality drops, report mapping collision hypothesis first

Copy-paste prompt:

```text
C:\tetie\notecode で作業してください。Window 4: current UI body generation 1case only です。plan\route_a_only_archive_and_0506_ui_route_2026-05-08\NEW_ROUTE_CONTRACT.md / SECURITY_GATE.md / IMPLEMENTATION_WINDOWS.md を読んでください。Route A default は変更しないでください。route_0506_structured_blog_ui_v1 を UI から1caseだけ本文生成できるよう接続し、ui_selection_snapshot に article_type / semantic_article_key / ui_journey を保存してください。Route A fallback、URL refetch、品質チューニング、複数case実行は禁止。品質低下時はまず mapping collision として報告してください。
```

## Window 5: Route A Saved Artifact vs New Route Same Source Compare Only

Goal: compare saved Route A artifact against new route output with identical source snapshot.

Owner scope:

- compare tool
- source snapshot hash proof
- manual Japanese blog naturalness note
- compare summary

Do not:

- regenerate Route A
- run broad matrix
- tune quality
- change thresholds
- use old routes

Exit criteria:

- Route A source is saved artifact only
- Route A changed/regenerated flags are false
- source snapshot hashes match
- new route artifact is separable
- decision is `reject | continue_shadow | blocked`

Copy-paste prompt:

```text
C:\tetie\notecode で作業してください。Window 5: Route A saved artifact vs new route same source compare only です。Route A は logs\latest_generation_output.json の saved artifact のみ使い、再生成しないでください。new route は route_0506_structured_blog_ui_v1。source snapshot hash 一致、Route A changed/regenerated=false、usage ledger、security_gate、manual Japanese blog naturalness note を compare_summary に残してください。decision は reject | continue_shadow | blocked のいずれか。品質チューニング、threshold緩和、repair_acceptance緩和、URL refetch、old route復活は禁止です。
```

## Window 6+: Quality Tuning Only If Needed

Goal: tune quality only after archive, adapter, saved-source, UI, compare, and security gates are green.

Owner scope:

- one quality issue
- one owner module
- one narrow hypothesis

Do not:

- combine mapping fixes and quality tuning
- add prompt bloat
- loosen thresholds
- loosen repair acceptance
- change Route A

Exit criteria:

- mapping collision ruled out first
- source adequacy checked
- one quality owner selected
- before/after artifacts show improvement
- security gate remains pass/hold with no high/critical unresolved

Copy-paste prompt:

```text
C:\tetie\notecode で作業してください。Window 6以降: quality tuning only if needed です。先に Window 1-5 の artifact と SECURITY_GATE を読み、mapping collision / source adequacy / schema compatibility が原因でないことを確認してください。1 issue = 1 narrow hypothesis = 1 owner scope。prompt追加、threshold緩和、repair_acceptance緩和、Route A変更は禁止。before/after artifact と manual Japanese blog naturalness note を残してください。
```
