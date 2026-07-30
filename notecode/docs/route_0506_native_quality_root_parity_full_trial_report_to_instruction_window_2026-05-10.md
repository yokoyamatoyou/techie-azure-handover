# Route 0506 native quality root parity full trial 報告 2026-05-10

この文書は指示ウインドウへの持ち帰り用です。Route A current mainline は immutable、Route 0506 は shadow-only のままです。

## 結論

- decision: `needs_next_owner`
- artifact_root: `C:\tetie\notecode\logs\route_0506_native_quality_root_parity_full_trial_20260510`
- product_code_changed: `false`（attempt 01 は rollback 済み）
- api_send_count: `1`
- attempts_used: `1`
- attempts_kept: `0`
- attempts_rolled_back: `1`
- next_one_owner: `route_0506_draft_writer_target_length_adherence_and_generation_contract_parity`

## 実施内容

- AGENTS / WORKLOG / local 0506 docs / current implementation / latest Route 0506 artifacts を確認。
- Web検索は OpenAI Structured Outputs / Responses API / NiceGUI の技術確認に限定し、記事 source には使っていない。
- local 0506 reference は `.venv` の pytest で `55 passed` を確認。
- 既存 quality package `C:\tetie\notecode\0506\artifacts\quality_review_package_pdf_1371322` の QA green artifact を native quality reference として確認。
- same saved source で notecode Route 0506 attempt 01 を 1 API run 実施。

## Baseline と Attempt

前回 accepted baseline:
- article_brief_target: `3000`
- section_count: `5`
- assigned_claim_count: `21`
- draft_writer: `1991 chars`
- final body: `1683 chars`
- QA: `pass=true / score=100 / issues=[]`

attempt 01:
- article_brief_target: `3000`
- section_count: `5`
- assigned_claim_count: `13`
- draft_writer: `1554 chars`
- final body: `1749 raw chars`
- QA: `pass=true / score=100 / issues=[]`

判断:
- final は小幅に増えたが、draft stage は悪化し、claim volume も落ちた。
- 根本改善とは言えないため、attempt 01 の code change は rollback。

## Root Cause

article_brief target / section / claim volume は一度 `3000 / 5 / 21 claims` まで改善したが、final body はまだ native-quality fullness に届かない。今回の draft handoff では target adherence が安定せず、OpenAI article_brief / draft の variability も残った。

first_confirmed_root_cause:
`draft_writer` target-length adherence and generation contract parity remains unresolved after article_brief normalization.

## Guardrails

- route_a_regenerated: `false`
- url_refetched: `false`
- route_a_fallback_used: `false`
- old_routes_reopened: `false`
- raw_full_source_documents_passed: `false`
- threshold_relaxed: `false`
- repair_acceptance_relaxed: `false`
- prompt_bloat: `none` final（attempt prompt handoff は rollback）
- module_bloat: `none`

## Tests

- `C:\tetie\notecode\0506\.venv\Scripts\python.exe -m pytest -q`: `55 passed`
- post-rollback `py -3 -m py_compile note\route_0506_structured_blog_adapter.py note\tests\test_route_0506_structured_blog_adapter.py`: pass
- post-rollback `py -3 -m pytest note\tests\test_route_0506_structured_blog_adapter.py -q`: `41 passed`
- post-rollback `py -3 -m pytest note\tests\test_route_0506_structured_blog_adapter.py note\tests\test_route_0506_ui_bridge.py note\tests\test_route_0506_saved_source_cli_validation.py -q`: `51 passed`

## AGENTS / WORKLOG

- AGENTS_update_needed: `false`
- WORKLOG_update_needed: `false`
