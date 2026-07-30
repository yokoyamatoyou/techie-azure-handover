# Route 0506 self-perspective then category AB test next window prompt 2026-05-10

この文書は、次の作業ウインドウへ貼るための prompt です。  
自己視点 / 一人称の混入問題を先に狭く修正し、その後に UI 各カテゴリで保存済み Route A artifact と Route 0506 shadow output を比較します。

## Copy-paste prompt

```text
C:\tetie\notecode の Route 0506 self-perspective fix then category AB test を行ってください。

日本語で出力してください。
このウインドウは通常モードです。
フェーズを分けて安全に進めます。

owner:
route_0506_self_perspective_then_category_ab_test

目的:
Route 0506 の本文で第三者視点が混じる問題を、ABテスト前に自己視点 / 一人称の生成契約として狭く修正する。
その後、今の UI の各カテゴリごとに、保存済み Route A artifact と Route 0506 shadow route の出力を比較できるように本文だけをカテゴリ別フォルダへ配置する。

重要前提:
- Route A current mainline は frozen / immutable。
- Route A は再生成しない。
- A は保存済み Route A artifact を使う。
- B は Route 0506 shadow route の新規生成。
- Route 0506 はまだ shadow-only。Route A replacement / adoption 判断はしない。
- source は各カテゴリで同じ saved source を使う。
- URL refetch はしない。
- 出力配置は C:\tetie\notecode\docs\新しいフォルダー 配下。
- 配置フォルダには本文だけを置く。JSON / trace / logs / quality report は artifact 側に置く。

Required Read Order:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\WORKLOG.md
4. C:\tetie\notecode\docs\route_0506_saved_source_repeatability_quality_stabilization_next_window_prompt_2026-05-10.md
5. C:\tetie\notecode\logs\route_0506_saved_source_repeatability_quality_stabilization_20260510\decision.md
6. C:\tetie\notecode\logs\route_0506_saved_source_repeatability_quality_stabilization_20260510\repeatability_summary.json
7. C:\tetie\notecode\logs\route_0506_saved_source_repeatability_quality_stabilization_20260510\codex_quality_review.md
8. C:\tetie\notecode\note\route_0506_ui_bridge.py
9. C:\tetie\notecode\note\route_0506_structured_blog_adapter.py
10. C:\tetie\notecode\note\route_0506_structured_blog_result_adapter.py
11. C:\tetie\notecode\note\route_0506_stage_output_guard.py
12. C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py
13. C:\tetie\notecode\note\tests\test_route_0506_ui_bridge.py
14. C:\tetie\notecode\note\tests\test_route_0506_saved_source_cli_validation.py
15. C:\tetie\notecode\0506\docs\CURRENT_ALGORITHM.md
16. C:\tetie\notecode\0506\docs\PIPELINE_SPEC.md
17. C:\tetie\notecode\0506\docs\ARTICLE_GENRE_POLICY.md
18. C:\tetie\notecode\0506\docs\CONFIG_AND_PERSONA_POLICY.md
19. C:\tetie\notecode\0506\docs\JAPANESE_STYLE_POLICY.md

フェーズ構成:

Phase 0: inventory / preflight
- UI の現行カテゴリ一覧を code / UI 定義から取得する。
- 各 UI category に対応する article_type / semantic_article_key / Route 0506 genre_id を確認する。
- 各カテゴリの保存済み Route A artifact が存在するか確認する。
- 保存済み Route A artifact がないカテゴリは、Route A を再生成せず `route_a_saved_artifact_missing` として blocked/skip 記録する。
- 同じ saved source / source_snapshot をカテゴリごとに使えるか確認する。
- C:\tetie\notecode\docs\新しいフォルダー 配下の配置先を決める。

Phase 1: self-perspective / persona contract fix
- 第三者視点混入の原因を調べる。
- 原因候補:
  - generation prompt 段階で自己視点契約が弱い
  - persona / writer_role / viewpoint / narrator の渡り方が弱い
  - editor stage で第三者視点へ戻る
  - result adapter / visible guard で過去文が混ざる
- narrow fix のみ許可。
- broad prompt tuning 禁止。
- persona sprawl 禁止。
- category 全体を同じ文体に潰さない。
- 特に `お知らせ` は C:\tetie\notecode\0506 の設計どおり簡潔なはずなので、会社・サービス紹介向けの 5 section / fullness contract を全カテゴリへ流用しない。
- 各 genre の自然な長さ・構成・視点を尊重する。
- 修正後、少なくとも 1 category で自己視点が効いていることを validation する。
- Phase 1 が通らない場合、Phase 2 の AB test へ進まず `needs_next_owner` または `blocked` で止める。

Phase 2: category AB test generation
- UI 各カテゴリごとに AB 比較を作る。
- A: 保存済み Route A artifact の本文。
- B: Route 0506 shadow route の新規生成本文。
- Route A は絶対に再生成しない。
- Route 0506 は OPENAI_API_KEY environment 使用可。
- model: gpt-5.4-mini
- reasoning effort: high
- API send は原則「Route 0506 B を 1 category につき 1 run」。
- Phase 1 の修正確認で追加 run が必要な場合も、合計 API send はカテゴリ数 + 2 程度を目安にし、無駄に増やさない。

Phase 3: placement for user review
- ユーザー比較用フォルダ:
  C:\tetie\notecode\docs\新しいフォルダー
- カテゴリごとにサブフォルダを作る。
- フォルダ名は UI category label を安全なファイル名にしたものにする。
- 例:
  C:\tetie\notecode\docs\新しいフォルダー\category_01_company_service_intro\
  C:\tetie\notecode\docs\新しいフォルダー\category_02_announcement\
- 各カテゴリフォルダには本文だけ置く。
- 推奨ファイル名:
  - A_route_a_saved_article.md
  - B_route_0506_shadow_article.md
- JSON / trace / quality report / decision / source snapshot はこのフォルダへ置かない。
- artifact 側に category manifest を置き、どの folder がどの UI category か分かるようにする。

Phase 4: Codex quality review
- Codex も各カテゴリの A/B を確認する。
- 文字数だけで判定しない。
- カテゴリ別の自然な長さを尊重する。
- お知らせは簡潔でよい。
- 会社・サービス紹介は source-grounded な厚みが必要。
- 各カテゴリで確認する:
  - 自己視点 / 一人称が守られているか
  - 第三者視点が混じらないか
  - category intent に合っているか
  - source-grounding
  - QA pass / score / issues
  - wrapper leakage
  - first-person consistency
  - model_frequent_word recurrence
  - CTA が自然か
  - Route A と比べて明確に悪い点があるか

禁止:
- Route A regeneration
- Route A fallback
- Route A replacement / adoption 判断
- URL refetch
- old rejected routes reopen
- raw full source_documents pass を成功扱いにすること
- QA threshold relaxation
- repair_acceptance relaxation
- broad prompt tuning
- persona sprawl
- new repair loop
- 文字数だけ増やす対応
- company_service_intro の fullness/5-section contract を全カテゴリへ流用
- Desktop 絶対パスを runtime dependency に戻すこと

推奨 artifact_root:
C:\tetie\notecode\logs\route_0506_self_perspective_then_category_ab_test_20260510\

必須 artifact:
- read_order_confirmation.md
- phase0_inventory.md
- ui_category_inventory.json
- route_a_saved_artifact_inventory.json
- source_snapshot_reuse_plan.json
- phase1_self_perspective_diagnosis.md
- phase1_fix_summary.md または phase1_no_fix_reason.md
- phase1_test_result.txt
- phase1_validation_summary.json
- category_ab_manifest.json
- category_generation_summary.json
- codex_category_quality_review.md
- user_comparison_folder_manifest.md
- decision.md

カテゴリごとの artifact:
- category_<id>\input_contract.json
- category_<id>\source_snapshot.json
- category_<id>\A_route_a_saved_article.md
- category_<id>\B_route_0506_shadow_article.md
- category_<id>\B_article_brief.json
- category_<id>\B_final_quality.json
- category_<id>\B_stage_length_trace.json
- category_<id>\manual_review.md

ユーザー比較フォルダには本文だけ:
- C:\tetie\notecode\docs\新しいフォルダー\<category>\A_route_a_saved_article.md
- C:\tetie\notecode\docs\新しいフォルダー\<category>\B_route_0506_shadow_article.md

closeout decision:
ready_for_user_category_ab_review | ready_for_saved_route_a_ab_test_review | needs_viewpoint_owner | needs_category_specific_owner | continue_shadow | blocked | reject

decision の目安:
- ready_for_user_category_ab_review:
  - 各カテゴリの本文配置が完了し、ユーザーが読める状態
- ready_for_saved_route_a_ab_test_review:
  - Codex review でも大きな問題がなく、AB test review へ進める
- needs_viewpoint_owner:
  - 第三者視点混入が残り、AB 配置前に追加修正が必要
- needs_category_specific_owner:
  - 特定カテゴリだけ明確な問題がある
- continue_shadow:
  - 大きな破綻はないが、AB test 判断にはまだ観察が必要
- blocked:
  - 保存済み Route A artifact 欠落、API/schema/env 問題など
- reject:
  - Route 0506 が複数カテゴリで明確に悪い

完了報告には最低限これを含めてください:
decision:
artifact_root:
user_comparison_folder:
product_code_changed:
api_send_count:
model:
reasoning_effort:
ui_categories_total:
ui_categories_completed:
ui_categories_blocked:
route_a_saved_artifacts_used:
route_a_missing_categories:
self_perspective_fix_changed_files:
self_perspective_validation_result:
third_person_mixed_categories:
category_folders_created:
codex_quality_review_summary:
changed_files:
tests:
ready_for_user_category_ab_review: true | false
ready_for_saved_route_a_ab_test_review: true | false
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

- 自己視点 / 一人称の混入問題を ABテスト前に解消する。
- その後、UI 各カテゴリごとに保存済み Route A と Route 0506 を本文だけで比較できる形にする。
- カテゴリ別の自然な長さ・構成を尊重し、company_service_intro の契約を全カテゴリへ流用しない。
- ユーザー比較用フォルダには本文だけ置き、詳細ログは artifact 側に分離する。
