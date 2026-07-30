# Route 0506 native length expectation and parameter parity next window prompt 2026-05-10

この文書は、次の作業ウインドウへ貼るための prompt です。  
目的は、`2227 chars` を機械的に「短い」と扱っていないかを検証し、`C:\tetie\notecode\0506` native generation との同条件比較、推論深さ・モデル・出力パラメータ設定の差分確認を行ったうえで、次に直すべき root cause を決めることです。

## Copy-paste prompt

```text
C:\tetie\notecode の Route 0506 native length expectation and parameter parity を行ってください。

日本語で出力してください。
このウインドウは通常モードです。
owner: route_0506_native_length_expectation_and_parameter_parity

目的:
前回 window では article_brief target=3000 / section_count=5 / assigned_claim_count=20 / final_raw_chars=2227 / QA green まで改善した。
しかし「2227字だから native 3000字 fullness 未達」と判定している可能性がある。
文字数は source量・claim量・article genre・section purpose・native 0506 の同条件出力によって変動するため、2000字台であることだけを短い・未達の根拠にしない。
今回は `C:\tetie\notecode\0506` native generation を手本に、同一または比較可能 source で実生成比較を行い、推論深さ・モデル・出力上限・パラメータ設定が notecode Route 0506 と一致しているか確認する。

最重要方針:
- 対症療法は禁止。
- 文字数だけを増やす修正は禁止。
- `target_length_chars=3000` を絶対文字数ノルマとして扱わない。
- `2000字台だから短い` という判定は禁止。必ず source/claim/native比較で判断する。
- local 0506 native が同条件で 2000字台なら、notecode Route 0506 の 2227字は未達とは限らない。
- local 0506 native が同条件で明確に長く、かつ claim coverage / naturalness / source-grounding も上なら、その差分を root cause として扱う。
- 1 issue = 1 narrow hypothesis = 1 owner scope。

Required Read Order:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\WORKLOG.md
4. C:\tetie\notecode\docs\route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix_next_window_prompt_2026-05-10.md
5. C:\tetie\notecode\logs\route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix_20260510\decision.md
6. C:\tetie\notecode\logs\route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix_20260510\root_cause_diagnosis.md
7. C:\tetie\notecode\logs\route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix_20260510\local_0506_section_planning_reference.json
8. C:\tetie\notecode\logs\route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix_20260510\rendered_prompt_compare.json
9. C:\tetie\notecode\logs\route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix_20260510\stage_length_compare.json
10. C:\tetie\notecode\logs\route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix_20260510\attempt_02\article_brief.json
11. C:\tetie\notecode\logs\route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix_20260510\attempt_02\api_validation_summary.json
12. C:\tetie\notecode\logs\route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix_20260510\attempt_02\final_quality.json
13. C:\tetie\notecode\logs\route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix_20260510\attempt_02\manual_japanese_naturalness_review.md
14. C:\tetie\notecode\note\route_0506_structured_blog_adapter.py
15. C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py
16. C:\tetie\notecode\0506\AGENTS.md
17. C:\tetie\notecode\0506\docs\CURRENT_ALGORITHM.md
18. C:\tetie\notecode\0506\docs\PIPELINE_SPEC.md
19. C:\tetie\notecode\0506\docs\ARTICLE_GENRE_POLICY.md
20. C:\tetie\notecode\0506\docs\CONFIG_AND_PERSONA_POLICY.md
21. C:\tetie\notecode\0506\docs\JAPANESE_STYLE_POLICY.md

現状:
- Route 0506 remains shadow-only
- Route A current mainline は frozen / immutable
- Route A replacement / adoption 判断は未実施
- stable reference は C:\tetie\notecode\0506
- 前回 accepted attempt_02:
  - article_brief_target: 3000
  - section_count: 5
  - assigned_claim_count: 20
  - max_claims_in_one_section: 4
  - draft_raw_chars: 1606
  - final_raw_chars: 2227
  - paragraph_count: 25
  - sentence_count: 65
  - QA: pass=true / score=100 / issues=[]
  - source_snapshot_hash preserved
  - no URL refetch / no Route A fallback / no raw full source pass
- 懸念:
  - manual review が「final 2227 chars なので 3000字相当 fullness 未達」と書いている。
  - しかし `target_length_chars=3000` は絶対文字数ではなく article_brief の目安。
  - source量や claim量によって最適な本文量は変動する。
  - local 0506 native 同条件生成との実比較、推論深さ・パラメータ差分確認が必要。

必ず確認すること:
1. local 0506 native generation を同一 saved source または比較可能 source で実行・確認する。
2. local 0506 native の final length / draft length / section count / paragraph count / claim coverage / QA / manual naturalness を保存する。
3. notecode Route 0506 attempt_02 と local 0506 native を同じ指標で比較する。
4. モデル設定を比較する:
   - model
   - reasoning effort
   - max output tokens / max completion tokens 相当
   - temperature 等が存在する場合の設定
   - OpenAI SDK / Responses API / Chat Completions 経路
   - env default
   - local deterministic vs OpenAI mode の切替
5. notecode adapter が 0506 native の generation parameters を変えていないか確認する。
6. `3000字目安の5セクションでは、本文全体を2600字以上に近づける。` という style rule が対症療法化していないか確認する。
7. 文字数ではなく、source-grounding / claim coverage / section completeness / naturalness で不足を判定する。

今回の判断基準:
- `2227 chars` は単独では未達判定にしない。
- local 0506 native が同条件で同程度なら、次 owner は draft length ではなく AB test readiness / repeatability / UI validation へ寄せる。
- local 0506 native が同条件で明確に長く、より自然で、claim coverage も高い場合のみ、draft_writer target adherence / generation contract parity を next owner とする。
- local 0506 native と notecode Route 0506 の model/reasoning/output token/env が違う場合は、まず parameter parity を next owner とする。

API / 実行許可:
- OPENAI_API_KEY environment 使用を許可する。
- model: gpt-5.4-mini
- reasoning effort: high
- API sends: 最大4 total
- local 0506 native generation: 許可
- notecode Route 0506 CLI validation: 必要なら許可
- notecode Route 0506 UI validation: 必要なら許可
- product code patch: 原則この window では行わない。parameter mismatch のように原因が明確で狭い場合のみ、user指示範囲内で narrow fix 可。
- tests: 確認や narrow fix に必要なら実行可。

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
- 文字数だけ増やす修正
- target_length_chars だけの強制
- 2600字以上 rule を根拠なしに強化すること
- notecode Route 0506 runtime を Desktop 絶対パス依存に戻すこと

推奨 artifact_root:
C:\tetie\notecode\logs\route_0506_native_length_expectation_and_parameter_parity_20260510\

必須 artifact:
- read_order_confirmation.md
- local_0506_native_generation_run.md
- local_0506_native_generation_artifacts.json
- notecode_attempt_02_summary.json
- native_vs_notecode_length_and_quality_compare.json
- generation_parameter_compare.json
- model_reasoning_env_compare.json
- output_token_limit_compare.json
- source_claim_coverage_compare.json
- style_rule_review.md
- decision_before_edit.md
- decision.md

必要なら追加:
- notecode_rerun_summary.json
- ui_validation_summary.json
- test_result.txt
- code_diff_summary.md

closeout decision:
ready_for_saved_route_a_ab_test | ready_for_repeatability_check | needs_parameter_parity_fix | needs_draft_contract_owner | continue_shadow | blocked | reject

完了報告には最低限これを含めてください:
decision:
artifact_root:
local_reference_path: C:\tetie\notecode\0506
product_code_changed:
api_send_count:
local_0506_native_run_performed:
same_source_or_comparable_source:
model:
reasoning_effort:
model_parameter_parity:
output_token_limit_parity:
env_default_parity:
notecode_final_raw_chars: 2227
native_final_raw_chars:
notecode_draft_raw_chars: 1606
native_draft_raw_chars:
notecode_section_count: 5
native_section_count:
notecode_assigned_claim_count: 20
native_assigned_claim_count:
qa_pass:
qa_score:
qa_issues:
manual_japanese_naturalness_note:
is_2227_actually_short: true | false | undetermined
reason_2227_short_or_not:
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

- `2000字台だから短い` という誤判定を避ける。
- local 0506 native の同条件生成を確認してから、draft writer を直すべきか判断する。
- 推論深さ・モデル・出力上限・env default の差分を確認する。
- 文字数ではなく、source-grounding / claim coverage / naturalness / native parity で判断する。
