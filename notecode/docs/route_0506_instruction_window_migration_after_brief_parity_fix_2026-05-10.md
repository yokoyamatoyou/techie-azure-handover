# Route 0506 指示ウインドウ移行 after article_brief parity fix 2026-05-10

この文書は指示ウインドウ移行用です。  
このウインドウでは product code 変更、API 実行、Route A 再生成、URL refetch は行わない。

## 参照確認

確認済み read order:

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. `C:\tetie\notecode\docs\route_0506_native_vs_notecode_stage_parity_audit_report_to_instruction_window_2026-05-10.md`
5. `C:\tetie\notecode\logs\route_0506_article_brief_payload_parity_fix_20260510\decision.md`
6. `C:\tetie\notecode\logs\route_0506_article_brief_payload_parity_fix_20260510\deterministic_trace.json`
7. `C:\tetie\notecode\logs\route_0506_article_brief_payload_parity_fix_20260510\test_result.txt`
8. `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
9. `C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py`
10. `C:\tetie\notecode\0506\docs\CURRENT_ALGORITHM.md`
11. `C:\tetie\notecode\0506\docs\PIPELINE_SPEC.md`
12. `C:\tetie\notecode\0506\docs\CONFIG_AND_PERSONA_POLICY.md`

## 現状

- Route 0506 remains `shadow-only`
- Route A current mainline は frozen / immutable
- Route A replacement / adoption 判断は未実施
- URL refetch なし
- Route A fallback なし
- old rejected routes reopen なし
- QA threshold / `repair_acceptance` relaxation なし
- stable reference は `C:\tetie\notecode\0506`
- Desktop absolute runtime dependency は直近 audit で `false`

## 直近 audit

- owner: `route_0506_native_vs_notecode_same_source_stage_parity_audit`
- decision: `needs_next_owner`
- first_divergence: `article_brief`
- source input / source packet text は native 0506 direct と notecode Route 0506 adapter で実質同一
- first confirmed route-handling gap は `article_brief` normalization / postprocess
- native 0506 direct: `target_length_chars=3000`, `section_count=5`
- notecode adapter: `target_length_chars=1800`, `section_count=3`
- compact output は `draft_writer` 前に始まっていた

## 直近 fix

- owner: `route_0506_article_brief_payload_parity_fix`
- decision: `fixed_continue_shadow`
- artifact_root: `C:\tetie\notecode\logs\route_0506_article_brief_payload_parity_fix_20260510`
- product_code_changed: `true`
- api_send_count: `0`
- changed_files:
  - `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
  - `C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py`

修正内容:

- `company_service_intro` article_brief policy を修正
- shortage guard は維持
- non-shortage では adapter floor を下回る場合だけ補正
- native 由来の `3000 / 5 sections` を `1800 / 3` に縮めない
- native-like `3000 / 5 / 15 claims` fixture を追加

検証:

- `py -3 -m py_compile note\route_0506_structured_blog_adapter.py note\tests\test_route_0506_structured_blog_adapter.py`: pass
- `py -3 -m pytest note\tests\test_route_0506_structured_blog_adapter.py -q`: `40 passed`

deterministic result:

- article_brief_target_before: `1800`
- article_brief_target_after: `3000`
- section_count_before: `3`
- section_count_after: `5`
- native_planning_preserved: `true`
- claim_ids_preserved: `true`
- claim_allocation_consistent: `true`
- source_shortage_guard_preserved: `true`
- density_metadata_preserved: `true`

## 次の one owner

owner:

```text
route_0506_company_service_intro_post_brief_parity_api_validation
```

目的:

- article_brief parity fix 後、`company_service_intro` 1case を actual API で再生成する
- compact 問題が改善したかを visible body quality で確認する
- 改善実装はしない。validation のみで止める

API:

- `OPENAI_API_KEY` environment 使用を許可する
- model: `gpt-5.4-mini`
- reasoning effort: `high`
- API send max: `1`
- case: `company_service_intro` only

判定観点:

- `article_brief` が `3000 / 5 sections` で維持されるか
- `body_char_count` が直近の `1183` から明確に改善するか
- `max_claims_in_one_section` が過集中しないか
- QA pass / score / issues
- 日本語自然さが local 0506 reference 相当に近づくか
- source-grounding が保たれるか
- Route A regenerated false / URL refetched false / Route A fallback false

## 次作業ウインドウ用 copy-paste prompt

```text
C:\tetie\notecode の Route 0506 post-brief-parity API validation を行ってください。

日本語で出力してください。
このウインドウは通常モードです。ただし 1 owner のみです。
owner: route_0506_company_service_intro_post_brief_parity_api_validation

目的:
article_brief parity fix 後、company_service_intro 1case を actual API で再生成し、compact 問題が改善したか確認する。
改善実装は禁止です。product code patch、prompt tuning、persona 追加、repair loop 追加、QA threshold relaxation、repair_acceptance relaxation はしないでください。
API生成 validation のみで、結果を artifact に保存して closeout してください。

Required Read Order:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\WORKLOG.md
4. C:\tetie\notecode\docs\route_0506_instruction_window_migration_after_brief_parity_fix_2026-05-10.md
5. C:\tetie\notecode\docs\route_0506_native_vs_notecode_stage_parity_audit_report_to_instruction_window_2026-05-10.md
6. C:\tetie\notecode\logs\route_0506_article_brief_payload_parity_fix_20260510\decision.md
7. C:\tetie\notecode\logs\route_0506_article_brief_payload_parity_fix_20260510\deterministic_trace.json
8. C:\tetie\notecode\logs\route_0506_article_brief_payload_parity_fix_20260510\test_result.txt
9. C:\tetie\notecode\note\route_0506_structured_blog_adapter.py
10. C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py
11. C:\tetie\notecode\0506\docs\CURRENT_ALGORITHM.md
12. C:\tetie\notecode\0506\docs\PIPELINE_SPEC.md
13. C:\tetie\notecode\0506\docs\CONFIG_AND_PERSONA_POLICY.md

現状:
- Route 0506 remains shadow-only
- Route A current mainline は frozen / immutable
- Route A replacement / adoption 判断は未実施
- stable reference は C:\tetie\notecode\0506
- Desktop absolute runtime dependency は直近 audit で false
- first confirmed compact gap は article_brief normalization / postprocess
- route_0506_article_brief_payload_parity_fix で deterministic parity は fixed
- native-like 3000 / 5 / 15 claims fixture は pass
- focused pytest は 40 passed

API許可:
- OPENAI_API_KEY environment 使用を許可します
- model は gpt-5.4-mini
- reasoning effort は high
- API send max 1
- company_service_intro 1case only

禁止:
- Route A regenerated
- URL refetch
- Route A fallback
- old rejected routes reopen
- raw full source_documents pass を成功扱いにすること
- product code patch
- prompt tuning
- persona 追加
- repair loop 追加
- QA threshold relaxation
- repair_acceptance relaxation
- Route A replacement / adoption 判断

保存する artifact:
推奨 artifact_root:
C:\tetie\notecode\logs\route_0506_company_service_intro_post_brief_parity_api_validation_20260510\

最低限保存:
- source_snapshot.json
- article_brief.json
- stage_length_trace.json
- claim_allocation_trace.json
- final_quality.json
- api_validation_summary.json
- manual_japanese_naturalness_review.md
- decision.md

判定:
- article_brief が 3000 / 5 sections で維持されるか
- body_char_count が 1183 から明確に改善するか
- max_claims_in_one_section が過集中しないか
- QA pass / score / issues
- 日本語自然さが local 0506 reference 相当に近づくか
- source-grounding が保たれるか
- Route A regenerated false
- URL refetched false
- Route A fallback false

closeout decision は次のいずれか:
ready_for_saved_route_a_ab_test | continue_shadow | needs_next_owner | blocked | reject

完了報告には最低限これを含めてください:
decision:
artifact_root:
local_reference_path: C:\tetie\notecode\0506
product_code_changed:
api_send_count:
model:
reasoning_effort:
company_service_intro_case_only:
article_brief_target:
article_brief_section_count:
body_char_count_before_reference: 1183
body_char_count_after:
max_claims_in_one_section:
qa_pass:
qa_score:
qa_issues:
manual_japanese_naturalness_note:
source_grounding_note:
changed_files:
tests:
next_one_owner:
route_a_regenerated: false
url_refetched: false
route_a_fallback_used: false
old_routes_reopened: false
raw_full_source_documents_passed: false
threshold_relaxed: false
repair_acceptance_relaxed: false
prompt_bloat: none | found
module_bloat: none | found
AGENTS_update_needed:
WORKLOG_update_needed:
```

## この指示ウインドウの closeout

decision: `needs_next_owner`  
artifact_root: `C:\tetie\notecode\docs\route_0506_instruction_window_migration_after_brief_parity_fix_2026-05-10.md`  
local_reference_path: `C:\tetie\notecode\0506`  
product_code_changed: `false`  
api_send_count: `0`  
diff_inventory_completed: `not_applicable_instruction_window`  
first_confirmed_gap: `article_brief normalization / postprocess compacted native 3000/5 planning to 1800/3 before draft_writer; deterministic parity now fixed`  
changed_files: `C:\tetie\notecode\docs\route_0506_instruction_window_migration_after_brief_parity_fix_2026-05-10.md`  
tests: `not run; docs-only instruction migration`  
manual_japanese_naturalness_note: `このウインドウでは API 生成を行っていないため、可視本文の自然さ判定は次の validation owner に残す。`  
next_one_owner: `route_0506_company_service_intro_post_brief_parity_api_validation`  
route_a_regenerated: `false`  
url_refetched: `false`  
route_a_fallback_used: `false`  
old_routes_reopened: `false`  
raw_full_source_documents_passed: `false`  
threshold_relaxed: `false`  
repair_acceptance_relaxed: `false`  
prompt_bloat: `none`  
module_bloat: `none`  
AGENTS_update_needed: `false`  
WORKLOG_update_needed: `false`
