# Route 0506 openai article_brief target and claim volume parity next window prompt 2026-05-10

この文書は、次の作業ウインドウへ貼るための prompt です。  
目的は `C:\tetie\notecode\0506` native reference 相当の article_brief planning / claim volume / visible fullness に寄せてから、Route A AB test 準備へ進めることです。

## Copy-paste prompt

```text
C:\tetie\notecode の Route 0506 openai article_brief target and claim volume parity を行ってください。

日本語で出力してください。
このウインドウは通常モードです。1 owner のみです。
owner: route_0506_openai_article_brief_target_and_claim_volume_parity

目的:
company_service_intro の live API validation で、section_count は 5 に戻ったが article_brief.target_length_chars が 3000 ではなく 1800 のままで、assigned_claim_count も 11、本文も 1478 chars に留まった原因を精査し、C:\tetie\notecode\0506 native reference 相当の article_brief planning / claim volume / visible fullness に近づける。
ABテストへ進む前に、Route 0506 が local 0506 reference と同品質に近い出力を出せる状態にする。

実行方針:
- 原因精査 -> narrow fix -> 修正確認を行う。
- 最大 5 fix attempts まで許可する。
- 各 attempt は `1 issue = 1 narrow hypothesis = 1 owner scope` を守る。
- attempt ごとに artifact を分ける。
- 悪化した attempt は、自分がその attempt で加えた変更だけ戻す。
- 改善した場合のみ次 attempt または closeout へ進む。
- 5 attempts を使い切って未達なら、追加で広げず `needs_next_owner` または `blocked` で止める。

Required Read Order:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\WORKLOG.md
4. C:\tetie\notecode\docs\route_0506_instruction_window_migration_after_brief_parity_fix_2026-05-10.md
5. C:\tetie\notecode\docs\route_0506_native_vs_notecode_stage_parity_audit_report_to_instruction_window_2026-05-10.md
6. C:\tetie\notecode\logs\route_0506_article_brief_payload_parity_fix_20260510\decision.md
7. C:\tetie\notecode\logs\route_0506_article_brief_payload_parity_fix_20260510\deterministic_trace.json
8. C:\tetie\notecode\logs\route_0506_company_service_intro_post_brief_parity_api_validation_20260510\decision.md
9. C:\tetie\notecode\logs\route_0506_company_service_intro_post_brief_parity_api_validation_20260510\api_validation_summary.json
10. C:\tetie\notecode\logs\route_0506_company_service_intro_post_brief_parity_api_validation_20260510\article_brief.json
11. C:\tetie\notecode\logs\route_0506_company_service_intro_post_brief_parity_api_validation_20260510\stage_length_trace.json
12. C:\tetie\notecode\logs\route_0506_company_service_intro_post_brief_parity_api_validation_20260510\claim_allocation_trace.json
13. C:\tetie\notecode\logs\route_0506_company_service_intro_post_brief_parity_api_validation_20260510\manual_japanese_naturalness_review.md
14. C:\tetie\notecode\note\route_0506_structured_blog_adapter.py
15. C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py
16. C:\tetie\notecode\0506\docs\CURRENT_ALGORITHM.md
17. C:\tetie\notecode\0506\docs\PIPELINE_SPEC.md
18. C:\tetie\notecode\0506\docs\CONFIG_AND_PERSONA_POLICY.md

現状:
- Route 0506 remains shadow-only
- Route A current mainline は frozen / immutable
- Route A replacement / adoption 判断は未実施
- stable reference は C:\tetie\notecode\0506
- Desktop absolute runtime dependency は直近 audit で false
- native-vs-notecode same-source stage audit の first_divergence は article_brief
- source input / source packet text は native 0506 direct と notecode Route 0506 adapter で実質同一
- native 0506 direct は article_brief で 3000 / 5 sections / 15 claims 相当
- notecode adapter は以前 1800 / 3 sections に縮めていた
- route_0506_article_brief_payload_parity_fix で deterministic parity は fixed
- post-brief-parity API validation では:
  - article_brief_target: 1800
  - article_brief_section_count: 5
  - assigned_claim_count: 11
  - max_claims_in_one_section: 3
  - body_char_count: 1183 -> 1478
  - QA: pass=true / score=100 / issues=[]
  - decision: needs_next_owner

重要な解釈:
- target=1800 は、本文実長ではなく draft_writer に入る前の article_brief 設計契約が 1800 chars だったという意味。
- 今回の短さは editor が削った問題ではない。stage trace では draft_writer が 1471 chars、final が 1478 chars。
- 次に見るべきは draft prompt tuning ではなく、live OpenAI article_brief がなぜ 3000 / 5 / 15 claims 相当ではなく 1800 / 5 / 11 claims に落ちるか。

今回の許可:
- product code patch: 許可。ただしこの owner に必要な narrow adapter-side fix のみ。
- tests: focused tests を追加・更新してよい。
- OPENAI_API_KEY environment 使用: 許可。
- model: gpt-5.4-mini
- reasoning effort: high
- API sends: 最大 5 total。ただし毎 attempt で必ず API を送る必要はない。
- 先に saved artifacts / deterministic trace / local preflight で原因を絞る。
- API は「その attempt の仮説が local preflight で通った後」の確認に使う。

禁止:
- Route A regeneration
- URL refetch
- Route A fallback
- old rejected routes reopen
- raw full source_documents pass を成功扱いにすること
- Route A replacement / adoption 判断
- broad prompt tuning
- persona 追加
- new repair loop 追加
- QA threshold relaxation
- repair_acceptance relaxation
- source handoff owner の再オープン
- knowledge_pack single-fact conflict owner の再オープン
- visible-output shape guard owner の再オープン
- 0506 native core の大改造

調査で最低限見ること:
- post-brief-parity run の article_brief が 1800 / 5 / 11 claims になった直接原因
- native 0506 direct の 3000 / 5 / 15 claims と比較して、claim candidate / source cards / knowledge pack / article_brief input のどこで claim volume が減っているか
- deterministic parity fix が live OpenAI article_brief response に対して期待通り働いているか
- adapter postprocess が 3000 を縮めていないことだけでなく、source_thickness=thick / selected source density / company_service_intro に対して 3000 target へ lift できる条件が揃っているか
- shortage guard が誤って効いていないか
- max_claims_in_one_section を増やさず、claim volume を増やせるか
- prompt bloat / module bloat を増やしていないか

推奨 artifact_root:
C:\tetie\notecode\logs\route_0506_openai_article_brief_target_and_claim_volume_parity_20260510\

最低限作る artifact:
- diagnosis.md
- baseline_compare.json
- attempt_01\hypothesis.md
- attempt_01\code_diff_summary.md
- attempt_01\deterministic_trace.json
- attempt_01\test_result.txt
- attempt_01\api_validation_summary.json または api_not_run_reason.md
- attempt_01\article_brief.json
- attempt_01\stage_length_trace.json
- attempt_01\claim_allocation_trace.json
- attempt_01\final_quality.json
- attempt_01\manual_japanese_naturalness_review.md
- attempts_summary.json
- decision.md

attempt_02 以降を行う場合も同じ構造で保存する。

改善判定:
- article_brief.target_length_chars が 3000 へ戻る、または local 0506 reference と比較して合理的に同等と説明できる
- section_count は 5 を維持
- assigned_claim_count が native reference の 15 claims 相当に近づく
- max_claims_in_one_section が過集中しない
- body_char_count が 1478 から明確に改善する
- QA pass / score / issues が悪化しない
- 日本語自然さが local 0506 reference 相当に近づく
- source-grounding が保たれる
- Route A regenerated false
- URL refetched false
- Route A fallback false

悪化判定:
- article_brief.target_length_chars が 1800 以下のまま、かつ claim volume も増えない
- section_count が 5 から減る
- assigned_claim が特定 section に過集中する
- QA red になる
- 会社・サービス紹介から不動産売却一般ガイドへ戻る
- source-grounding が弱くなる
- prompt bloat / module bloat が増える

悪化時の戻し:
- その attempt で自分が加えた product code 変更のみ戻す。
- user の既存変更や過去 window の fixed changes は戻さない。
- 戻した場合は attempt artifact に rollback_note.md を残す。

closeout decision は次のいずれか:
ready_for_saved_route_a_ab_test | fixed_continue_shadow | continue_shadow | needs_next_owner | blocked | reject

decision の目安:
- ready_for_saved_route_a_ab_test:
  - target / sections / claim volume / body fullness / QA / naturalness が local 0506 reference 相当に到達し、AB test 準備へ進める
- fixed_continue_shadow:
  - 明確に改善したが、AB test にはまだ手前
- continue_shadow:
  - QA green だが fullness parity は未達で、追加の別 owner が必要
- needs_next_owner:
  - 原因は絞れたが、この owner で安全に直しきれない
- blocked:
  - API / SDK / schema / environment などで確認不能
- reject:
  - 改善方向が誤り、品質・source-grounding・focus が悪化

完了報告には最低限これを含めてください:
decision:
artifact_root:
local_reference_path: C:\tetie\notecode\0506
product_code_changed:
api_send_count:
model:
reasoning_effort:
attempts_used:
attempts_rolled_back:
company_service_intro_case_only:
article_brief_target_before: 1800
article_brief_target_after:
article_brief_section_count_before: 5
article_brief_section_count_after:
assigned_claim_count_before: 11
assigned_claim_count_after:
max_claims_in_one_section_before: 3
max_claims_in_one_section_after:
body_char_count_before: 1478
body_char_count_after:
qa_pass:
qa_score:
qa_issues:
manual_japanese_naturalness_note:
source_grounding_note:
first_confirmed_cause:
changed_files:
tests:
next_one_owner:
ready_for_saved_route_a_ab_test: true | false
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

- AB テストへ進む前に、Route 0506 の company_service_intro が local 0506 reference 相当の planning / fullness に到達するかを確認する。
- `target=1800` は本文長ではなく article_brief の設計契約なので、原因 owner は draft/editor ではなく article_brief target と claim volume。
- 最大5回の trial は許可するが、同じ owner の範囲内に限定する。
- 悪化した attempt は戻し、改善した attempt だけ残す。
