# Route 0506 native/Desktop/local/notecode full-pipeline parity root-cause next window prompt 2026-05-10

この文書は、次の作業ウインドウへ貼るための prompt です。  
目的は、`C:\tetie\notecode\0506` / `C:\Users\横山裕明\Desktop\0506` / notecode Route 0506 CLI / notecode Route 0506 UI の全工程差分を比較し、移行後に品質が変わる根本原因を特定・修正することです。

## Copy-paste prompt

```text
C:\tetie\notecode の Route 0506 native/Desktop/local/notecode full-pipeline parity root-cause work を行ってください。

日本語で出力してください。
このウインドウは通常モードです。
owner: route_0506_native_desktop_local_notecode_full_pipeline_parity_root_cause

目的:
C:\tetie\notecode\0506 では問題ない品質の記事生成ができるのに、notecode Route 0506 へアルゴリズムを移行すると結果が変わる根本原因を特定し、対症療法ではなく 0506 native の挙動へ寄せる。
ABテスト準備へ進む前に、Desktop 0506 / local 0506 / notecode Route 0506 CLI / notecode Route 0506 UI の全工程差分をログで確認し、品質差を生む root cause を潰す。

最重要方針:
- 対症療法は禁止。
- 少し本文が長くなるだけ、QA green だけ、target_length_chars だけの強制、文字数だけ増やす、prompt 文の継ぎ足し、特定例だけ通す hard-code は成功扱いにしない。
- `C:\tetie\notecode\0506` と結果が異なるなら、source / config / persona / prompt / article_brief / draft / editor / QA / final / UI firing のどこかに差分がある前提で調べる。
- `C:\Users\横山裕明\Desktop\0506` は比較対象・由来確認・挙動確認として稼働してよい。ただし notecode Route 0506 の runtime dependency を Desktop 絶対パスへ戻してはいけない。
- 最終的な stable reference は原則 `C:\tetie\notecode\0506`。
- 1 attempt = 1 hypothesis。
- 最大10 attempts まで許可。
- 悪化した attempt、根拠のない小幅改善、対症療法に見える attempt は破棄する。
- 改善した attempt だけ keep する。

Required Read Order:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\WORKLOG.md
4. C:\tetie\notecode\docs\route_0506_native_quality_root_parity_full_trial_report_to_instruction_window_2026-05-10.md
5. C:\tetie\notecode\logs\route_0506_native_quality_root_parity_full_trial_20260510\decision.md
6. C:\tetie\notecode\logs\route_0506_native_quality_root_parity_full_trial_20260510\root_cause_diagnosis.md
7. C:\tetie\notecode\logs\route_0506_native_quality_root_parity_full_trial_20260510\article_brief_compare.json
8. C:\tetie\notecode\logs\route_0506_native_quality_root_parity_full_trial_20260510\stage_length_compare.json
9. C:\tetie\notecode\logs\route_0506_native_quality_root_parity_full_trial_20260510\final_quality_compare.json
10. C:\tetie\notecode\logs\route_0506_native_quality_root_parity_full_trial_20260510\native_0506_quality_confirmation.md
11. C:\tetie\notecode\logs\route_0506_native_quality_root_parity_full_trial_20260510\route_dispatch_compare.json
12. C:\tetie\notecode\logs\route_0506_native_quality_root_parity_full_trial_20260510\ui_bridge_compare.json
13. C:\tetie\notecode\note\route_0506_ui_bridge.py
14. C:\tetie\notecode\note\route_0506_structured_blog_adapter.py
15. C:\tetie\notecode\note\route_0506_structured_blog_result_adapter.py
16. C:\tetie\notecode\note\route_0506_stage_output_guard.py
17. C:\tetie\notecode\note\route_0506_security_gate.py
18. C:\tetie\notecode\note\route_0506_usage_ledger.py
19. C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py
20. C:\tetie\notecode\note\tests\test_route_0506_ui_bridge.py
21. C:\tetie\notecode\note\tests\test_route_0506_saved_source_cli_validation.py
22. C:\tetie\notecode\0506\AGENTS.md
23. C:\tetie\notecode\0506\README.md
24. C:\tetie\notecode\0506\TASK.md
25. C:\tetie\notecode\0506\PROGRESS.md
26. C:\tetie\notecode\0506\ARCHITECTURE.md
27. C:\tetie\notecode\0506\docs\CURRENT_ALGORITHM.md
28. C:\tetie\notecode\0506\docs\PIPELINE_SPEC.md
29. C:\tetie\notecode\0506\docs\SOURCE_ACQUISITION_POLICY.md
30. C:\tetie\notecode\0506\docs\ARTICLE_GENRE_POLICY.md
31. C:\tetie\notecode\0506\docs\CONFIG_AND_PERSONA_POLICY.md
32. C:\tetie\notecode\0506\docs\JAPANESE_STYLE_POLICY.md
33. C:\tetie\notecode\0506\WORKLOG.md

Desktop 0506 も比較に使う場合は追加で読む:
34. C:\Users\横山裕明\Desktop\0506\AGENTS.md
35. C:\Users\横山裕明\Desktop\0506\README.md
36. C:\Users\横山裕明\Desktop\0506\TASK.md
37. C:\Users\横山裕明\Desktop\0506\PROGRESS.md
38. C:\Users\横山裕明\Desktop\0506\ARCHITECTURE.md
39. C:\Users\横山裕明\Desktop\0506\docs\CURRENT_ALGORITHM.md
40. C:\Users\横山裕明\Desktop\0506\docs\PIPELINE_SPEC.md
41. C:\Users\横山裕明\Desktop\0506\docs\CONFIG_AND_PERSONA_POLICY.md
42. C:\Users\横山裕明\Desktop\0506\WORKLOG.md

現状:
- Route 0506 remains shadow-only
- Route A current mainline は frozen / immutable
- Route A replacement / adoption 判断は未実施
- stable reference は原則 C:\tetie\notecode\0506
- Desktop 0506 は比較対象として使用可。ただし notecode runtime を Desktop 絶対依存へ戻さない。
- 直近の full trial では:
  - decision: needs_next_owner
  - product_code_changed: false
  - api_send_count: 1
  - attempts_used: 1
  - attempts_kept: 0
  - attempts_rolled_back: 1
  - article_brief_target は 3000 に到達済み
  - section_count は 5
  - accepted baseline は assigned_claim_count 21 / draft_writer 1991 chars / final 1683 chars
  - attempt 01 は assigned_claim_count 13 / draft_writer 1554 chars / final 1749 raw chars で、draft stage と claim volume が悪化したため rollback
- いまの焦点は `article_brief target=3000` ではなく、draft_writer が generation contract に従わないこと、または 0506 native と異なる persona/prompt/config/timing が draft に入っていること。

確認対象:
1. Desktop 0506 native
2. local 0506 native: C:\tetie\notecode\0506
3. notecode Route 0506 CLI / saved-source validation
4. notecode Route 0506 UI

比較対象 stage:
- source acquisition / saved source
- source snapshot
- route dispatch
- UI input / UI selection snapshot
- explicit generation trigger
- route_0506_ui_bridge
- input_contract
- genre mapping
- target_reader / article_goal
- persona / writer_role / viewpoint / narrator
- persona 発火タイミング
- style_profile / editor_profile / qa_policy
- config loading
- prompt template
- rendered prompt
- OpenAI model / reasoning / env default
- source packets
- source cards
- knowledge pack
- article_brief
- draft_writer
- opening editor
- global consistency editor
- style editor
- structural editor
- QA
- targeted rewriter
- visible output guard
- final visible output
- artifact write timing
- async / UI event timing

特に検証する問い:
- UI が原因で input_contract / source_snapshot / route_id / persona / target_reader / article_goal が変わっていないか。
- CLI 経由と UI 経由で Route 0506 の発火条件や artifact が変わっていないか。
- persona の発火タイミングをずらした変更は実際に draft_writer に効いているか。
- notecode Route 0506 の persona / writer_role / style_profile / editor_profile は local 0506 native と同じ意味・同じ stage で効いているか。
- `C:\tetie\notecode\0506` と Desktop 0506 の参照パス違い、config 読み込み違い、prompt 読み込み違い、env default 違いがないか。
- notecode adapter が 0506 native の prompt contract を変質させていないか。
- rendered prompt のサイズ、変数、persona lines、target length instruction、claim allocation の渡り方が native 0506 と一致しているか。
- article_brief は同じでも draft_writer に渡る contract が同じではない可能性がないか。
- editor / structural editor / guard が draft を削っていないか。削っていない場合、draft_writer の root cause として分ける。

API / Web / 実行許可:
- OPENAI_API_KEY environment 使用を許可する。
- model: gpt-5.4-mini
- reasoning effort: high
- API sends: 最大10 total
- Desktop 0506 native run: 許可
- local 0506 native run: 許可
- notecode Route 0506 CLI validation: 許可
- notecode Route 0506 UI validation: 必要なら許可
- Web検索: 許可。ただし記事 source として使わない。技術確認のみ。
- product code patch: 許可。ただし root cause に対応する narrow fix のみ。
- tests 追加・更新: 許可。

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
- target_length_chars だけの強制
- 文字数だけ増やす対症療法
- 0506 native core の大改造
- notecode Route 0506 runtime を Desktop 絶対パス依存に戻すこと

推奨 artifact_root:
C:\tetie\notecode\logs\route_0506_native_desktop_local_notecode_full_pipeline_parity_root_cause_20260510\

必須 artifact:
- read_order_confirmation.md
- absolute_reference_scan.txt
- desktop_vs_local_0506_file_inventory.json
- desktop_vs_local_0506_config_prompt_persona_compare.json
- native_desktop_quality_confirmation.md
- native_local_quality_confirmation.md
- notecode_cli_quality_confirmation.md
- notecode_ui_quality_confirmation.md または ui_not_run_reason.md
- source_snapshot_compare.json
- route_dispatch_compare.json
- ui_bridge_compare.json
- input_contract_compare.json
- persona_timing_compare.json
- config_loading_compare.json
- rendered_prompt_compare.json
- source_card_compare.json
- knowledge_pack_compare.json
- article_brief_compare.json
- draft_writer_contract_compare.json
- editor_stage_compare.json
- stage_length_compare.json
- stage_timing_compare.json
- final_quality_compare.json
- root_cause_diagnosis.md
- attempts_summary.json
- decision.md

各 attempt の artifact:
- attempt_01\hypothesis.md
- attempt_01\root_cause_scope.md
- attempt_01\code_diff_summary.md
- attempt_01\desktop_vs_local_vs_notecode_compare.json
- attempt_01\deterministic_trace.json
- attempt_01\test_result.txt
- attempt_01\api_validation_summary.json または api_not_run_reason.md
- attempt_01\article_brief.json
- attempt_01\draft_writer_contract.json
- attempt_01\stage_length_trace.json
- attempt_01\claim_allocation_trace.json
- attempt_01\final_quality.json
- attempt_01\manual_japanese_naturalness_review.md
- attempt_01\rollback_note.md または keep_note.md

attempt_02 以降も同じ構造で保存する。

最大 attempt:
- max_attempts: 10
- api_send_max: 10
- 1 attempt = 1 hypothesis
- 1 attempt で複数問題を同時に直さない
- attempt ごとに `hypothesis -> edit -> local validation -> API/UI validation if needed -> native comparison -> keep/rollback` を記録する

悪化・破棄条件:
- final だけ小幅改善しても、draft_writer / claim volume / source-grounding / native parity が悪化したら破棄
- QA green だけでは keep しない
- 文字数だけ増えた場合は keep しない
- target_length_chars だけ揃った場合は keep しない
- company/service focus が不動産売却一般ガイドへ戻ったら破棄
- UI/CLI/native の差分説明ができない patch は破棄
- prompt bloat / module bloat が増えたら破棄

keep 条件:
- root cause が明確で、その差分が local/Desktop 0506 native に近づく
- draft_writer contract が native 0506 と同じ意味で渡る
- persona / style / target length / claim allocation が正しい stage で効く
- draft_writer の target adherence が改善する
- assigned_claim_count / paragraph density / body fullness が native reference に近づく
- final visible output が QA green かつ manual naturalness で改善
- source-grounding が保たれる
- Route A / URL refetch / fallback / threshold / repair_acceptance の guardrail が維持される

ABテスト準備へ進める条件:
- decision: ready_for_saved_route_a_ab_test
- local 0506 native と notecode Route 0506 の root 差分が解消または説明可能
- UI / CLI どちらでも同じ Route 0506 behavior
- persona 発火タイミングと draft_writer contract が native 0506 と同等
- final visible output が local 0506 reference 同品質相当
- source-grounding が保たれる

closeout decision:
ready_for_saved_route_a_ab_test | fixed_continue_shadow | continue_shadow | needs_next_owner | blocked | reject

完了報告には最低限これを含めてください:
decision:
artifact_root:
local_reference_path: C:\tetie\notecode\0506
desktop_reference_path: C:\Users\横山裕明\Desktop\0506
product_code_changed:
api_send_count:
web_search_performed:
model:
reasoning_effort:
attempts_used:
attempts_kept:
attempts_rolled_back:
desktop_0506_run_performed:
local_0506_run_performed:
notecode_cli_run_performed:
notecode_ui_run_performed:
native_0506_quality_confirmed:
desktop_local_path_difference_found:
ui_conflict_found:
persona_timing_effective:
persona_behavior_same_as_native:
first_confirmed_root_cause:
changed_files:
tests:
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

- `C:\tetie\notecode\0506` で品質が出るのに notecode Route 0506 で結果が変わる根本原因を探す。
- UI 原因、persona 発火タイミング、persona 挙動差、path/config/prompt 差、draft_writer 契約差を決め打ちせず比較する。
- Desktop 0506 は比較対象として使うが、runtime dependency を Desktop 絶対パスへ戻さない。
- 最大10 attempts まで許可し、対症療法・悪化・根拠なし小幅改善は破棄する。
