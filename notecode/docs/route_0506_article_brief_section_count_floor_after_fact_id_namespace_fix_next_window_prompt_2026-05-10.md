# Route 0506 article_brief section-count floor after fact-id namespace fix next window prompt 2026-05-10

この文書は、次の作業ウインドウへ貼るための prompt です。  
目的は、`source_card fact_id` namespace fix 後に残った `article_brief.section_count=4` の根本原因を精査し、local 0506 native parity に近づけることです。前回報告で気になった `WORKLOG.md` の更新状態も、この window で確認・記録します。

## Copy-paste prompt

```text
C:\tetie\notecode の Route 0506 article_brief section-count floor after fact-id namespace fix を行ってください。

日本語で出力してください。
このウインドウは通常モードです。
owner: route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix

目的:
前回 root-cause window で OpenAI source_card の source-local fact_id 衝突は修正され、confirmed_claim_count / final body は改善した。
しかし article_brief は target_length_chars=3000 のまま section_count が 5 ではなく 4 に落ちたため、AB test ready ではない。
今回は `fact_id namespace fix` 後に、なぜ article_brief が local 0506 native parity の 5 sections を維持しないのかを根本原因として精査し、対症療法ではなく local 0506 native の section planning contract に寄せる。

最重要方針:
- 対症療法は禁止。
- `section_count=5` だけを無条件上書きする、文字数だけ増やす、QA green だけを成功扱いにする、prompt 文を広く継ぎ足す、特定 fixture だけ通す hard-code は禁止。
- `fact_id namespace fix` は再オープンしない。今回の owner は、その後段の article_brief section-count / section planning contract に限定する。
- 1 issue = 1 narrow hypothesis = 1 owner scope。
- 最大10 attempts まで許可。
- 悪化した attempt、根拠のない小幅改善、対症療法に見える attempt は破棄する。
- 改善した attempt だけ keep する。

Required Read Order:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\WORKLOG.md
4. C:\tetie\notecode\docs\route_0506_native_desktop_local_notecode_full_pipeline_parity_root_cause_next_window_prompt_2026-05-10.md
5. C:\tetie\notecode\logs\route_0506_native_desktop_local_notecode_full_pipeline_parity_root_cause_20260510\decision.md
6. C:\tetie\notecode\logs\route_0506_native_desktop_local_notecode_full_pipeline_parity_root_cause_20260510\root_cause_diagnosis.md
7. C:\tetie\notecode\logs\route_0506_native_desktop_local_notecode_full_pipeline_parity_root_cause_20260510\source_card_compare.json
8. C:\tetie\notecode\logs\route_0506_native_desktop_local_notecode_full_pipeline_parity_root_cause_20260510\knowledge_pack_compare.json
9. C:\tetie\notecode\logs\route_0506_native_desktop_local_notecode_full_pipeline_parity_root_cause_20260510\article_brief_compare.json
10. C:\tetie\notecode\logs\route_0506_native_desktop_local_notecode_full_pipeline_parity_root_cause_20260510\stage_length_compare.json
11. C:\tetie\notecode\logs\route_0506_native_desktop_local_notecode_full_pipeline_parity_root_cause_20260510\final_quality_compare.json
12. C:\tetie\notecode\logs\route_0506_native_desktop_local_notecode_full_pipeline_parity_root_cause_20260510\attempt_01\article_brief.json
13. C:\tetie\notecode\logs\route_0506_native_desktop_local_notecode_full_pipeline_parity_root_cause_20260510\attempt_01\claim_allocation_trace.json
14. C:\tetie\notecode\logs\route_0506_native_desktop_local_notecode_full_pipeline_parity_root_cause_20260510\attempt_01\stage_length_trace.json
15. C:\tetie\notecode\note\route_0506_structured_blog_adapter.py
16. C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py
17. C:\tetie\notecode\note\tests\test_route_0506_ui_bridge.py
18. C:\tetie\notecode\note\tests\test_route_0506_saved_source_cli_validation.py
19. C:\tetie\notecode\0506\docs\CURRENT_ALGORITHM.md
20. C:\tetie\notecode\0506\docs\PIPELINE_SPEC.md
21. C:\tetie\notecode\0506\docs\ARTICLE_GENRE_POLICY.md
22. C:\tetie\notecode\0506\docs\CONFIG_AND_PERSONA_POLICY.md
23. C:\tetie\notecode\0506\docs\JAPANESE_STYLE_POLICY.md

現状:
- Route 0506 remains shadow-only
- Route A current mainline は frozen / immutable
- Route A replacement / adoption 判断は未実施
- stable reference は C:\tetie\notecode\0506
- Desktop 0506 は比較対象として使用可。ただし notecode runtime を Desktop 絶対依存へ戻さない。
- 前回 owner:
  - owner: route_0506_native_desktop_local_notecode_full_pipeline_parity_root_cause
  - decision: fixed_continue_shadow
  - root cause: OpenAI source_card outputs reused source-local fact IDs such as F111 across different source cards
  - fix: source-card fact IDs を F0101 / F0201 のような cross-source namespace に正規化
  - product_code_changed: true
  - api_send_count: 1
  - source_card_fact_ids_unique: true
  - supporting_fact_ids_known: true
  - confirmed_claim_count: 16
  - article_brief_target: 3000
  - article_brief_section_count: 4
  - assigned_claim_count: 16
  - draft_raw_chars: 1734
  - final_raw_chars: 1810
  - QA: pass=true / score=100 / issues=[]
- 残差:
  - section_count が native parity の 5 ではなく 4
  - AB test ready ではない
  - next_one_owner: article_brief_section_count_floor_after_fact_id_namespace_fix

今回の確認対象:
- fact_id namespace fix 後の source_card / knowledge_pack / article_brief の渡り方
- article_brief input に section_count=5 を導く十分な claim volume / source thickness / genre policy が渡っているか
- local 0506 native の company_service_intro section planning と notecode Route 0506 の article_brief generation contract の差
- article_brief schema / config / persona / genre policy / prompt template / rendered prompt の差
- source_thickness=thick, target_length_chars=3000, assigned_claim_count=16 でも 4 sections になる直接原因
- shortage guard や density policy が誤って section floor を下げていないか
- adapter postprocess が 5 sections を縮めていないか
- OpenAI article_brief response 自体が 4 sections を返したのか、それとも adapter normalize 後に 4 になったのか
- 5 sections にする場合、単純上書きではなく section planning contract と claim allocation が自然に一致するか

WORKLOG 確認:
- 前回報告では `changed_files` に C:\tetie\WORKLOG.md が含まれている一方、`WORKLOG_update_needed=false` と報告されていた。
- この window では、実際に WORKLOG が更新済みなのか、未更新なのか、または `WORKLOG_update_needed=false after update` と書くべき状態なのかを確認し、artifact に記録する。
- `worklog_update_status.md` を作成し、次を明記する:
  - WORKLOG_changed_in_previous_window: true | false | unknown
  - WORKLOG_current_state_matches_latest_route_0506: true | false
  - WORKLOG_update_needed_now: true | false
  - WORKLOG_updated_this_window: true | false
  - wording_fix_needed_for_report_contract: true | false
- WORKLOG が肥大化している場合は、5月3日以前の dated entries を archive に圧縮してよい。
- 圧縮する場合:
  - current source-of-truth / Route 0506 current state / 5月4日以降の recent entries は main WORKLOG に残す。
  - 5月3日以前の dated entries は C:\tetie\archive\worklog\ 配下へ移す。
  - archive filename 例: C:\tetie\archive\worklog\WORKLOG_2026-05-03_and_earlier_archived_2026-05-10.md
  - maintenance-only とし、Route 0506 product code 変更とは混ぜない。
  - archive_manifest.md または worklog_archive_summary.md を残す。
  - ただし WORKLOG が十分に小さい場合は、圧縮せず `not_needed` と記録する。

API / 実行許可:
- OPENAI_API_KEY environment 使用を許可する。
- model: gpt-5.4-mini
- reasoning effort: high
- API sends: 最大10 total
- notecode Route 0506 CLI validation: 許可
- notecode Route 0506 UI validation: 必要なら許可
- local 0506 native comparison: 許可
- Desktop 0506 comparison: 必要なら許可。ただし runtime dependency を Desktop path に戻さない。
- product code patch: 許可。ただし section-count / article_brief planning contract の root cause に対応する narrow fix のみ。
- tests 追加・更新: 許可。
- WORKLOG maintenance / archive: 上記条件内で許可。

禁止:
- Route A regeneration
- Route A fallback
- Route A replacement / adoption 判断
- URL refetch を同一 source 比較として扱うこと
- old rejected routes reopen
- raw full source_documents pass を成功扱いにすること
- QA threshold relaxation
- repair_acceptance relaxation
- persona sprawl
- broad prompt tuning
- new repair loop
- section_count だけの強制上書き
- target_length_chars だけの強制上書き
- 文字数だけ増やす対症療法
- fact_id namespace fix の再オープン
- 0506 native core の大改造
- notecode Route 0506 runtime を Desktop 絶対パス依存に戻すこと

推奨 artifact_root:
C:\tetie\notecode\logs\route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix_20260510\

必須 artifact:
- read_order_confirmation.md
- worklog_update_status.md
- worklog_archive_summary.md または worklog_archive_not_needed.md
- baseline_after_fact_id_namespace_fix.json
- local_0506_section_planning_reference.json
- source_card_after_namespace_fix_compare.json
- knowledge_pack_after_namespace_fix_compare.json
- article_brief_input_compare.json
- article_brief_output_compare.json
- rendered_prompt_compare.json
- section_count_policy_trace.json
- claim_allocation_trace.json
- stage_length_compare.json
- final_quality_compare.json
- root_cause_diagnosis.md
- attempts_summary.json
- decision.md

各 attempt の artifact:
- attempt_01\hypothesis.md
- attempt_01\root_cause_scope.md
- attempt_01\code_diff_summary.md
- attempt_01\deterministic_trace.json
- attempt_01\test_result.txt
- attempt_01\api_validation_summary.json または api_not_run_reason.md
- attempt_01\article_brief.json
- attempt_01\section_count_policy_trace.json
- attempt_01\claim_allocation_trace.json
- attempt_01\stage_length_trace.json
- attempt_01\final_quality.json
- attempt_01\manual_japanese_naturalness_review.md
- attempt_01\rollback_note.md または keep_note.md

attempt_02 以降も同じ構造で保存する。

最大 attempt:
- max_attempts: 10
- api_send_max: 10
- 1 attempt = 1 hypothesis
- attempt ごとに `hypothesis -> edit -> deterministic/local validation -> API validation if needed -> native comparison -> keep/rollback` を記録する

悪化・破棄条件:
- section_count が 5 になっても、claim allocation が不自然・過集中なら破棄
- section_count だけ揃って、本文品質・source-grounding・claim coverage が改善しないなら破棄
- final だけ小幅改善して、article_brief / draft / claim allocation が悪化したら破棄
- QA green だけでは keep しない
- company/service focus が不動産売却一般ガイドへ戻ったら破棄
- prompt bloat / module bloat が増えたら破棄

keep 条件:
- root cause が明確
- article_brief が target=3000 / section_count=5 を自然に満たす
- assigned_claim_count が 16 以上を維持または native reference に近づく
- max_claims_in_one_section が過集中しない
- draft_writer / final body が source-grounded に改善する
- QA pass / score / issues が悪化しない
- manual Japanese naturalness が local 0506 reference に近づく
- Route A / URL refetch / fallback / threshold / repair_acceptance の guardrail が維持される

ABテスト準備へ進める条件:
- decision: ready_for_saved_route_a_ab_test
- article_brief target=3000 / section_count=5 / claim allocation が native parity 相当
- final visible output が QA green かつ manual naturalness で local 0506 reference 同品質相当
- source-grounding が保たれる
- UI/CLI どちらでも同じ Route 0506 behavior
- WORKLOG update/maintenance 状態が明確に記録されている

closeout decision:
ready_for_saved_route_a_ab_test | fixed_continue_shadow | continue_shadow | needs_next_owner | blocked | reject

完了報告には最低限これを含めてください:
decision:
artifact_root:
local_reference_path: C:\tetie\notecode\0506
product_code_changed:
api_send_count:
model:
reasoning_effort:
attempts_used:
attempts_kept:
attempts_rolled_back:
article_brief_target_before: 3000
article_brief_target_after:
section_count_before: 4
section_count_after:
assigned_claim_count_before: 16
assigned_claim_count_after:
max_claims_in_one_section:
draft_raw_chars_before: 1734
draft_raw_chars_after:
final_raw_chars_before: 1810
final_raw_chars_after:
qa_pass:
qa_score:
qa_issues:
manual_japanese_naturalness_note:
source_grounding_note:
first_confirmed_root_cause:
changed_files:
tests:
WORKLOG_changed_in_previous_window:
WORKLOG_update_needed_now:
WORKLOG_updated_this_window:
WORKLOG_archived_2026_05_03_and_earlier:
ready_for_saved_route_a_ab_test: true | false
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

## この prompt の意図

- `fact_id namespace` 修正の成果を維持しつつ、次の残差である `section_count=4` を根本原因として扱う。
- `section_count=5` だけを強制する対症療法を避け、local 0506 native の section planning contract に寄せる。
- 前回報告の WORKLOG 状態の曖昧さを次 window で検証・記録する。
- WORKLOG が肥大化している場合のみ、5月3日以前を archive へ圧縮する。
