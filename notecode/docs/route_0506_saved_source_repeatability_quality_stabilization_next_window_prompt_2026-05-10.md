# Route 0506 saved-source repeatability quality stabilization next window prompt 2026-05-10

この文書は、次の作業ウインドウへ貼るための prompt です。  
目的は、Route 0506 の saved-source 生成が複数回で安定するかを確認し、必要な場合だけ narrow fix を行うことです。文字数だけを増やす対応や prompt / module 肥大化は禁止します。

## Copy-paste prompt

```text
C:\tetie\notecode の Route 0506 saved-source repeatability quality stabilization を行ってください。

日本語で出力してください。
このウインドウは通常モードです。
owner: route_0506_saved_source_repeatability_quality_stabilization

目的:
前回の native length expectation / parameter parity では、notecode Route 0506 attempt_02 の 2227 chars を単独で短いとは判定できないことが分かった。
次は同じ saved source で複数回生成し、Route 0506 が品質・構成・source-grounding・日本語自然さを安定して出せるか確認する。
必要な場合のみ、1 issue = 1 narrow hypothesis = 1 owner scope で小さく修正し、再生成で確認する。

最重要方針:
- 肥大化に注意する。
- 対症療法は禁止。
- 文字数だけ増やす修正は禁止。
- `target_length_chars=3000` を絶対文字数ノルマとして扱わない。
- `2000字台だから短い` という判定は禁止。
- prompt 文の継ぎ足し、persona sprawl、new repair loop、threshold relaxation、repair_acceptance relaxationは禁止。
- 改善実装は、repeatability を崩す root cause が artifact で確認できた場合だけ。
- 悪化した attempt は自分の変更だけ戻す。

Required Read Order:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\WORKLOG.md
4. C:\tetie\notecode\docs\route_0506_native_length_expectation_and_parameter_parity_next_window_prompt_2026-05-10.md
5. C:\tetie\notecode\logs\route_0506_native_length_expectation_and_parameter_parity_20260510\decision.md
6. C:\tetie\notecode\logs\route_0506_native_length_expectation_and_parameter_parity_20260510\native_vs_notecode_length_and_quality_compare.json
7. C:\tetie\notecode\logs\route_0506_native_length_expectation_and_parameter_parity_20260510\generation_parameter_compare.json
8. C:\tetie\notecode\logs\route_0506_native_length_expectation_and_parameter_parity_20260510\model_reasoning_env_compare.json
9. C:\tetie\notecode\logs\route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix_20260510\attempt_02\article_brief.json
10. C:\tetie\notecode\logs\route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix_20260510\attempt_02\api_validation_summary.json
11. C:\tetie\notecode\logs\route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix_20260510\attempt_02\final_quality.json
12. C:\tetie\notecode\logs\route_0506_article_brief_section_count_floor_after_fact_id_namespace_fix_20260510\attempt_02\manual_japanese_naturalness_review.md
13. C:\tetie\notecode\note\route_0506_structured_blog_adapter.py
14. C:\tetie\notecode\note\route_0506_ui_bridge.py
15. C:\tetie\notecode\note\route_0506_stage_output_guard.py
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
- 前回確認:
  - model_parameter_parity: true
  - output_token_limit_parity: true
  - env_default_parity: true
  - raw native OpenAI は schema 400 で blocked
  - schema-compat native probe は 897 chars / QA red
  - notecode attempt_02 は 2227 chars / 5 sections / 20 claims / QA green
  - `2227 chars` を短いとは断定できない
- 次に見るべきは、同じ saved source で安定して良い品質が出るか。

生成条件:
- OPENAI_API_KEY environment 使用を許可する。
- model: gpt-5.4-mini
- reasoning effort: high
- API sends: 原則 5 generation runs。修正確認が必要な場合も total max 8 sends まで。
- source: 保存済み source_snapshot / input_contract を固定して使う。
- URL refetch 禁止。
- Route A regeneration 禁止。
- Route A fallback 禁止。
- raw full source_documents pass を成功扱いにしない。

比較用ブログ配置:
- ユーザー比較用に次のフォルダを使う:
  C:\tetie\notecode\docs\新しいフォルダー
- フォルダがなければ作成してよい。
- ここには、修正後・再生成後のブログ記事本文だけを配置する。
- JSON、ログ、source snapshot、品質レポート、trace、decision、比較表は置かない。
- ファイル名例:
  - route_0506_repeatability_run_01_article.md
  - route_0506_repeatability_run_02_article.md
  - route_0506_repeatability_run_03_article.md
  - route_0506_repeatability_run_04_article.md
  - route_0506_repeatability_run_05_article.md
- rejected / rollback になった run の記事を置く場合は、本文だけにし、ファイル名に `_rejected` を付ける。判断に迷う場合は accepted / QA green の記事だけ置く。
- 既存ファイルがある場合は削除しない。必要なら今回 run 用のサブフォルダを作る:
  C:\tetie\notecode\docs\新しいフォルダー\route_0506_repeatability_20260510

Codex 側の品質確認:
- Codex も各 run の品質を確認する。
- 各記事について、最低限次を確認:
  - company/service introduction focus
  - source-grounding
  - section_count
  - assigned_claim_count
  - max_claims_in_one_section
  - QA pass / score / issues
  - wrapper leakage なし
  - first_person consistency
  - model_frequent_word recurrence
  - 日本語自然さ
  - 問い合わせ導線が急に強すぎないか
  - 不動産売却一般ガイドへ戻っていないか
- 文字数は参考値として記録するが、単独の合否判定にしない。

安定判定:
- 5 runs のうち少なくとも 4 runs が QA green。
- 5 runs のうち少なくとも 4 runs が 5 sections。
- assigned_claim_count が極端に落ちない。
- source-grounding warning が出ない。
- wrapper leakage が出ない。
- company/service focus が保たれる。
- manual Japanese naturalness で破綻 run がない。
- body length の揺れは許容するが、極端な underfill や構成崩れがあれば原因を切る。

修正方針:
- まず 5 generation runs を実施し、repeatability を観察する。
- 失敗パターンが1つに絞れた場合のみ narrow fix を行う。
- 修正した場合は、同じ saved source で再生成して確認する。
- 最大でも 5 fix attempts まで。
- 悪化した fix attempt は自分の変更だけ戻す。
- prompt / module 肥大化が出たら止める。

禁止:
- broad prompt tuning
- persona 追加
- new repair loop
- QA threshold relaxation
- repair_acceptance relaxation
- target_length_chars だけの強制
- 文字数だけ増やす対応
- Route A generation / fallback
- URL refetch
- old rejected route reopen
- 0506 native core の大改造
- Desktop 絶対パスを runtime dependency に戻すこと

推奨 artifact_root:
C:\tetie\notecode\logs\route_0506_saved_source_repeatability_quality_stabilization_20260510\

必須 artifact:
- read_order_confirmation.md
- preflight_source_lock.json
- generation_parameter_check.json
- run_01\article.md
- run_01\api_validation_summary.json
- run_01\article_brief.json
- run_01\stage_length_trace.json
- run_01\final_quality.json
- run_01\manual_japanese_naturalness_review.md
- run_02\...
- run_03\...
- run_04\...
- run_05\...
- repeatability_summary.json
- codex_quality_review.md
- user_comparison_folder_manifest.md
- root_cause_if_unstable.md または no_fix_needed_reason.md
- attempts_summary.json
- decision.md

closeout decision:
ready_for_saved_route_a_ab_test | ready_for_user_side_article_review | fixed_continue_shadow | continue_shadow | needs_next_owner | blocked | reject

decision の目安:
- ready_for_saved_route_a_ab_test:
  - repeatability が安定し、Route A AB test に進める
- ready_for_user_side_article_review:
  - AB test 前に、ユーザーが C:\tetie\notecode\docs\新しいフォルダー の記事を読む段階へ進める
- fixed_continue_shadow:
  - 不安定原因を1つ修正し、安定性が改善したがまだ追加観察が必要
- continue_shadow:
  - 大きく悪くはないが、安定とは言い切れない
- needs_next_owner:
  - 不安定原因は特定できたが、この owner で直しきれない
- blocked:
  - API / schema / environment で確認不能
- reject:
  - 品質・source-grounding・focus が悪化した

完了報告には最低限これを含めてください:
decision:
artifact_root:
user_comparison_folder:
product_code_changed:
api_send_count:
model:
reasoning_effort:
runs_completed:
stable_runs:
qa_green_runs:
five_section_runs:
wrapper_leakage_runs:
source_grounding_warning_runs:
average_body_chars:
min_body_chars:
max_body_chars:
body_chars_judged_as_primary_metric: false
manual_japanese_naturalness_summary:
codex_quality_review_summary:
changed_files:
tests:
next_one_owner:
ready_for_saved_route_a_ab_test: true | false
ready_for_user_side_article_review: true | false
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

- 文字数ではなく、複数回の品質安定性を見る。
- reasoning effort high の同条件で、Route 0506 が安定して出せるか確認する。
- ユーザー比較用にはブログ記事本文だけを `C:\tetie\notecode\docs\新しいフォルダー` に配置する。
- Codex 側も品質レビューを行い、AB test に進めるか判断する。
- 肥大化を避け、必要な修正だけを narrow に行う。
