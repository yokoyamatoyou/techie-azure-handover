# Route 0506 native quality root parity full trial next window prompt 2026-05-10

この文書は、次の作業ウインドウへ貼るための prompt です。  
前回の一部改善を踏まえ、対症療法ではなく `C:\tetie\notecode\0506` の高品質生成へ根本的に寄せることを目的にします。

## Copy-paste prompt

```text
C:\tetie\notecode の Route 0506 native-quality root parity full trial を行ってください。

日本語で出力してください。
このウインドウは通常モードです。
目的は、Route 0506 を C:\tetie\notecode\0506 の記事生成品質に根本的に寄せ、ABテスト準備へ進める状態を作ることです。

owner:
route_0506_native_quality_root_parity_full_trial

最重要方針:
- 対症療法は禁止です。
- `target_length_chars` だけを無理に上書きする、文字数だけ増やす、QA を通すためだけの patch、特定例だけ通す hard-code、広い prompt 文の継ぎ足しは禁止です。
- 既存の `C:\tetie\notecode\0506` が高品質に出せることをまず確認し、その生成プロセスとの差分を根本原因として潰してください。
- UIとの衝突、route dispatch、UI bridge、adapter、source snapshot、source-card、knowledge-pack、article_brief、draft_writer、editor timing、stage artifact 保存、発火タイミング、OpenAI client/model/reasoning/env default、guard/QA/rewriter の全工程を確認してください。
- WEB検索も行ってください。ただし記事生成の source を汚染しないこと。Web検索は OpenAI API / structured output / Responses SDK / UI発火や非同期実行 / NiceGUI等の技術確認、または 0506 実装理解の補助に限定し、記事本文用の追加 source として使わないでください。

Required Read Order:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\WORKLOG.md
4. C:\tetie\notecode\docs\route_0506_instruction_window_migration_after_brief_parity_fix_2026-05-10.md
5. C:\tetie\notecode\docs\route_0506_native_vs_notecode_stage_parity_audit_report_to_instruction_window_2026-05-10.md
6. C:\tetie\notecode\docs\route_0506_openai_article_brief_target_and_claim_volume_parity_next_window_prompt_2026-05-10.md
7. C:\tetie\notecode\logs\route_0506_article_brief_payload_parity_fix_20260510\decision.md
8. C:\tetie\notecode\logs\route_0506_article_brief_payload_parity_fix_20260510\deterministic_trace.json
9. C:\tetie\notecode\logs\route_0506_company_service_intro_post_brief_parity_api_validation_20260510\decision.md
10. C:\tetie\notecode\logs\route_0506_company_service_intro_post_brief_parity_api_validation_20260510\api_validation_summary.json
11. C:\tetie\notecode\logs\route_0506_company_service_intro_post_brief_parity_api_validation_20260510\article_brief.json
12. C:\tetie\notecode\logs\route_0506_company_service_intro_post_brief_parity_api_validation_20260510\stage_length_trace.json
13. C:\tetie\notecode\logs\route_0506_company_service_intro_post_brief_parity_api_validation_20260510\claim_allocation_trace.json
14. C:\tetie\notecode\logs\route_0506_company_service_intro_post_brief_parity_api_validation_20260510\manual_japanese_naturalness_review.md
15. C:\tetie\notecode\note\route_0506_ui_bridge.py
16. C:\tetie\notecode\note\route_0506_structured_blog_adapter.py
17. C:\tetie\notecode\note\route_0506_structured_blog_result_adapter.py
18. C:\tetie\notecode\note\route_0506_stage_output_guard.py
19. C:\tetie\notecode\note\route_0506_security_gate.py
20. C:\tetie\notecode\note\route_0506_usage_ledger.py
21. C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py
22. C:\tetie\notecode\note\tests\test_route_0506_ui_bridge.py
23. C:\tetie\notecode\note\tests\test_route_0506_saved_source_cli_validation.py
24. C:\tetie\notecode\0506\AGENTS.md
25. C:\tetie\notecode\0506\README.md
26. C:\tetie\notecode\0506\TASK.md
27. C:\tetie\notecode\0506\PROGRESS.md
28. C:\tetie\notecode\0506\ARCHITECTURE.md
29. C:\tetie\notecode\0506\docs\CURRENT_ALGORITHM.md
30. C:\tetie\notecode\0506\docs\PIPELINE_SPEC.md
31. C:\tetie\notecode\0506\docs\SOURCE_ACQUISITION_POLICY.md
32. C:\tetie\notecode\0506\docs\ARTICLE_GENRE_POLICY.md
33. C:\tetie\notecode\0506\docs\CONFIG_AND_PERSONA_POLICY.md
34. C:\tetie\notecode\0506\docs\JAPANESE_STYLE_POLICY.md
35. C:\tetie\notecode\0506\WORKLOG.md

現状:
- Route 0506 remains shadow-only
- Route A current mainline は frozen / immutable
- Route A replacement / adoption 判断は未実施
- stable reference は C:\tetie\notecode\0506
- Desktop absolute runtime dependency は直近 audit で false
- C:\tetie\notecode\0506 では良い評価・高品質生成が出る前提。ただしこの window で実際に確認し、artifact に残す。
- native-vs-notecode same-source stage audit では first_divergence は article_brief
- source input / source packet text は native 0506 direct と notecode Route 0506 adapter で実質同一という判断があった
- native 0506 direct は article_brief で 3000 / 5 sections / 15 claims 相当
- notecode Route 0506 は以前 1800 / 3 sections に縮めていた
- article_brief payload parity fix で deterministic parity は一部 fixed
- post-brief-parity API validation では:
  - article_brief_target: 1800
  - article_brief_section_count: 5
  - assigned_claim_count: 11
  - body_char_count: 1478
  - QA: pass=true / score=100 / issues=[]
  - decision: needs_next_owner
- つまり一部解消だが、local 0506 reference 同品質には未達。

この window の目的:
1. `C:\tetie\notecode\0506` native generation が本当に高品質であることを、同条件または比較可能条件で確認する。
2. notecode Route 0506 との差分を、UI入力から final visible output まで stage-by-stage に比較する。
3. 対症療法ではなく、品質差を生む root cause を特定する。
4. root cause に対して narrow fix を行う。
5. 修正確認を行い、悪化した attempt は破棄する。
6. 最大10 attempts まで trial-and-error し、改善したものだけ残す。
7. local 0506 reference 同品質に近づいたら、ABテスト準備へ進める。

API / Web / 実行許可:
- OPENAI_API_KEY environment 使用を許可する。
- model: gpt-5.4-mini
- reasoning effort: high
- API sends: 最大10 total。
- Web検索: 許可。ただし記事生成 source として使わない。検索結果は `web_research.md` に要約し、参照URLと使った目的を記録する。
- native 0506 direct run: 許可。ただし URL refetch なし・saved source 由来を優先する。どうしても native reference の既存高品質 artifact を使う場合は、その artifact path と比較条件を明記する。
- notecode Route 0506 validation run: 許可。
- product code patch: 許可。ただし root cause に対応する narrow fix のみ。
- tests 追加・更新: 許可。

禁止:
- Route A regeneration
- Route A fallback
- Route A replacement / adoption 判断
- old rejected routes reopen
- raw full source_documents pass を成功扱いにすること
- URL refetch を同一 source 比較として扱うこと
- QA threshold relaxation
- repair_acceptance relaxation
- persona sprawl
- broad prompt tuning
- new repair loop
- 文字数だけを増やす対症療法
- `target_length_chars=3000` だけの強制上書きを成功扱いすること
- source-grounding を弱めること
- local 0506 native core の大改造

必ず確認する観点:
- UI入力:
  - UI selection snapshot
  - selected route
  - article_type / semantic_article_key
  - target_reader / article_goal
  - explicit generation trigger と確認ボタンの混線
- route dispatch:
  - Route A に流れていないか
  - Route 0506 opt-in が正しく効いているか
  - current mainline に副作用がないか
- UI bridge:
  - source_documents / input_contract / saved source handoff
  - source snapshot hash
  - genre mapping
  - narrator / persona / target_reader
- adapter:
  - source surface construction
  - selected saved spans
  - source-card input
  - knowledge-pack normalization
  - article_brief postprocess
  - shortage guard
  - density / claim volume
  - schema normalization
- native 0506 reference:
  - same saved source or比較可能な source
  - generation source packets
  - source cards
  - article knowledge pack
  - article brief
  - draft / editors / QA / final
- generation process:
  - stage order
  - OpenAI model/reasoning/env defaults
  - prompt templates / rendered prompt size
  - config/persona loading
  - artifact write timing
  - async or UI event timing
  - retry/fail-open/guard behavior
- final quality:
  - body length
  - section count
  - paragraph count
  - claim count
  - source-grounding
  - Japanese naturalness
  - company/service focus
  - QA pass / score / issues

推奨 artifact_root:
C:\tetie\notecode\logs\route_0506_native_quality_root_parity_full_trial_20260510\

必須 artifact:
- read_order_confirmation.md
- web_research.md
- native_0506_quality_confirmation.md
- native_0506_artifact_inventory.json
- notecode_route_0506_artifact_inventory.json
- ui_bridge_compare.json
- route_dispatch_compare.json
- source_snapshot_compare.json
- source_surface_compare.json
- source_card_compare.json
- knowledge_pack_compare.json
- article_brief_compare.json
- rendered_prompt_compare.json
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
- attempt_01\deterministic_trace.json
- attempt_01\native_vs_notecode_compare.json
- attempt_01\test_result.txt
- attempt_01\api_validation_summary.json または api_not_run_reason.md
- attempt_01\article_brief.json
- attempt_01\stage_length_trace.json
- attempt_01\claim_allocation_trace.json
- attempt_01\final_quality.json
- attempt_01\manual_japanese_naturalness_review.md
- attempt_01\rollback_note.md または keep_note.md

attempt_02 以降も同じ構造で保存する。

最大 attempt:
- max_attempts: 10
- API send max: 10
- 1 attempt で複数問題を同時に直さない。
- attempt ごとに `hypothesis -> edit -> local validation -> API validation if needed -> compare -> keep/rollback` を記録する。

悪化時の扱い:
- 悪化した attempt は破棄する。
- 破棄対象は、その attempt で自分が加えた変更だけ。
- user の既存変更、過去 window の fixed changes、別 attempt の keep 済み改善は戻さない。
- rollback したら `rollback_note.md` に理由と戻したファイルを記録する。

改善判定:
- local 0506 reference の高品質生成に近づくこと。
- article_brief target / section / claim volume が native reference に近づく。
- body length と paragraph density が改善する。
- company/service introduction focus が保たれる。
- source-grounding が保たれる。
- QA pass / score / issues が悪化しない。
- manual Japanese naturalness が local 0506 reference に近づく。
- UI経由でも CLI/direct でも同じ route behavior になる。
- Route A regenerated false / URL refetched false / Route A fallback false。

ABテスト準備へ進める条件:
- decision が `ready_for_saved_route_a_ab_test`
- local 0506 reference と notecode Route 0506 の差分が説明可能な範囲に収まる
- final visible output が QA green かつ manual naturalness で同品質相当
- source-grounding が保たれる
- UI/bridge/adapter/発火タイミングに未解決の品質劣化 root cause が残っていない
- prompt_bloat / module_bloat が増えていない

closeout decision:
ready_for_saved_route_a_ab_test | fixed_continue_shadow | continue_shadow | needs_next_owner | blocked | reject

decision の目安:
- ready_for_saved_route_a_ab_test:
  - local 0506 reference 同品質相当まで到達し、Route A AB test 準備へ進める
- fixed_continue_shadow:
  - 根本原因の一部を修正し明確に改善したが、AB test はまだ早い
- continue_shadow:
  - QA green だが local 0506 reference 同品質には未達
- needs_next_owner:
  - 根本原因は絞れたが、この window で安全に直しきれない
- blocked:
  - API / SDK / schema / environment / Web調査不能などで確認不能
- reject:
  - 試行が品質・source-grounding・focus を悪化させた

完了報告には最低限これを含めてください:
decision:
artifact_root:
local_reference_path: C:\tetie\notecode\0506
product_code_changed:
api_send_count:
web_search_performed:
web_search_scope:
model:
reasoning_effort:
attempts_used:
attempts_kept:
attempts_rolled_back:
native_0506_quality_confirmed:
native_0506_reference_artifacts:
same_source_or_comparable_source:
first_confirmed_root_cause:
ui_conflict_checked:
route_dispatch_checked:
ui_bridge_checked:
adapter_checked:
generation_timing_checked:
article_brief_target_before:
article_brief_target_after:
assigned_claim_count_before:
assigned_claim_count_after:
body_char_count_before:
body_char_count_after:
qa_pass:
qa_score:
qa_issues:
manual_japanese_naturalness_note:
source_grounding_note:
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

- 一部解消ではなく、local 0506 reference の高品質生成に根本的に寄せる。
- `target_length_chars` や文字数だけの対症療法を禁止する。
- UI/bridge/adapter/発火タイミング/生成プロセスを全工程で比較する。
- Web検索は技術調査に使うが、記事 source を汚染しない。
- 最大10回の attempt を許可し、悪化した attempt は破棄する。
