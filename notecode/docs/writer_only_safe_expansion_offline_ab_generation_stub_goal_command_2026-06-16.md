# Writer-only Safe Expansion Offline AB Generation Stub Goal Command 2026-06-16

対象: `writer_only_safe_expansion_offline_ab_generation_stub_owner`

このファイルは、次の作業ウインドウでそのまま貼って長時間自走するための no-API / offline AB 検証ゴールコマンドです。前 owner が最小実装した safe-expansion brief / evaluator schema を、既存 fixture 5ケース上で deterministic stub / review-only comparison として確認します。

## Goal Objective

```text
現行 writer-only を通常UIの本線として保持したまま、`logs\writer_only_new_algorithm_ab_20260616\` の5 fixtureを使い、live APIなしで safe-expansion B variant の brief/evaluator schema がどう見えるかを deterministic artifact として確認する。B variant の実本文生成、通常UI接続、latest visible output反映、Route 0506 / Route A / repair / quality pipeline 復帰は行わない。
```

## ゴールコマンド

```text
あなたは TECHIE / notecode / コトメイクの `writer_only_safe_expansion_offline_ab_generation_stub_owner` です。

目的:
`writer_only_safe_expansion_brief_evaluator_min_impl_owner` が product code に最小実装した safe-expansion schema を、offline fixture 5ケースで no-API 検証する。実本文生成ではなく、deterministic B variant stub / draft scaffold / review-only comparison を artifact として作り、次に live API 承認が必要か、まだ offline で詰めるべきかを判定する。

参照ルール:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\notecode\WORKLOG.md
5. C:\tetie\notecode\docs\writer_only_safe_expansion_policy_proposal_2026-06-16.md
6. C:\tetie\notecode\docs\writer_only_new_algorithm_ab_test_plan_2026-06-16.md
7. C:\tetie\notecode\docs\writer_only_new_algorithm_deep_route_plan_2026-06-16.md
8. C:\tetie\notecode\docs\writer_only_safe_expansion_min_impl_goal_command_2026-06-16.md
9. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\min_impl_summary.md
10. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\fixture_index.json
11. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\safe_expansion_schema_final.json
12. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\evaluator_guard_schema.json
13. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\manual_review_gate_schema.md
14. C:\tetie\notecode\note\writer_only_brief.py
15. C:\tetie\notecode\note\writer_only_evaluator.py
16. C:\tetie\notecode\note\tests\test_writer_only_generation.py

許可する変更:
- `C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\` 配下の artifact 追加・更新
  - `offline_ab_generation_stub_plan.md`
  - `offline_ab_generation_stub_summary.md`
  - `offline_ab_stub_comparison.json`
  - 各 case の `variant_b\brief_safe_expansion.json`
  - 各 case の `variant_b\draft_stub.md` または `variant_b\review_only_scaffold.md`
  - 各 case の `variant_b\evaluation_stub.json`
  - 各 case の `decision.md` 更新
- artifact-local helper の追加が必要な場合のみ:
  - `C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\tools\run_offline_ab_generation_stub.py`
- `C:\tetie\notecode\WORKLOG.md`
  - 作業結果を必要最小限で記録する。

原則変更しない:
- product runtime code
  - `writer_only_brief.py`
  - `writer_only_evaluator.py`
  - `writer_only_openai_adapter.py`
  - `writer_only_service.py`
  - `writer_only_source_bundle.py`
- normal UI code
- fixed writer prompt / `WRITER_INSTRUCTIONS`
- tests

禁止:
- live APIを呼ばない。
- OpenAI API / Images API / external web fetch を呼ばない。
- B variant の実本文をLLM生成しない。
- `variant_b_body_generated=true` にしない。
- 通常UIからB variantを呼ばない。
- latest visible outputへB variantを投影しない。
- Route 0506 / Route A / repair loop / quality pipeline を戻さない。
- raw full source pass をしない。
- source groundingを緩めない。
- fixed promptを長文化しない。
- persona tableを増やさない。
- verified external context の runtime取得やWEB検索連携を実装しない。
- external orchestration frameworkを導入しない。

期待する artifact 形:
- `brief_safe_expansion.json`
  - fixtureの既存 input brief / source_bundle を読み、現行 code の safe-expansion schema 形を確認できる形で保存する。
  - source facts / verified_external_context / editorial_bridge / prohibited_claim の境界が読めること。
- `review_only_scaffold.md` または `draft_stub.md`
  - 実本文ではなく、記事生成前レビュー用の deterministic scaffold とする。
  - H2候補、使える source facts、C bridge候補、禁止D claim watchlist、manual review notes を記録する。
  - 読者向け完成本文のふりをしない。
- `evaluation_stub.json`
  - prohibited claim guard と Japanese style warning details の入力期待を no-API で確認する。
  - warning は fail にしない。
- `offline_ab_stub_comparison.json`
  - 5ケース横断で、A baseline artifact / B stub の差分、risk、次判定をまとめる。

判定候補:
- `offline_stub_ready`
  - 5ケースで B schema / stub / review-only comparison が揃い、live API 承認に進める材料がある。
- `needs_offline_revision`
  - live API前に schema / evaluator / scaffold の小修正が必要。
- `needs_live_api_approval`
  - offlineでは十分に確認でき、次は最大3caseの承認付き live AB が必要。
- `blocked`
  - 同じエラー3回、依存欠損、または境界違反リスクで停止。
- `reject`
  - B案が source grounding / prompt bloat / route boundary を壊すため破棄または再設計。

slice plan:
Slice 0: 参照doc、min_impl_summary、fixture_index、5 case inputを読む。
Self-test: 5 caseの input brief/source_bundle と prior review/decision が読めること。

Slice 1: offline stub artifact plan を作る。
Self-test: live APIなし、product code変更なし、B実本文生成なしの出力形になっていること。

Slice 2: artifact-local helper が必要か判断する。
Self-test:
- helperなしで手作業artifactが十分なら helperを作らない。
- helperを作る場合は artifact-local `tools` 配下のみ。

Slice 3: 5 case それぞれに B safe-expansion stubを作る。
Self-test:
- `brief_safe_expansion.json` が JSON parse 可能。
- `review_only_scaffold.md` または `draft_stub.md` が「完成本文」ではなく review-only である。
- prohibited D claim watchlist がある。

Slice 4: 横断 comparison を作る。
Self-test:
- A baseline / B stub の比較軸が fact grounding、blog naturalness、information gain、Japanese readability、SEO usefulness、risk を含む。
- prompt_bloat / module_bloat / route flags が明示される。

Slice 5: no-API validation を実行する。
Self-test:
- JSON parse
- Markdown readback
- artifact-local helperがある場合は `py_compile`
- 可能なら `scripts\validate_writer_only_config.py`
- api_send_count 0

Slice 6: summary と WORKLOG を更新する。
Self-test: WORKLOG読み戻し、route flags確認。

停止条件:
- 同じエラーが3回連続。
- product code変更が必要。
- prompt long-form expansion が必要。
- source grounding relaxation が必要。
- raw full source pass が必要。
- live API が必要になったが承認がない。
- UI接続が必要。
- Route 0506 / Route A / repair / quality pipeline が必要。
- B stub が完成本文として誤解される形になる。

完了報告フォーマット:
参照ルールファイル:
今回の実施範囲:
decision: offline_stub_ready | needs_offline_revision | needs_live_api_approval | blocked | reject
artifact_root:
changed_files_or_docs:
case_artifacts:
tests_or_validation:
api_send_count: 0
route_0506_restored: false
route_a_restored: false
repair_restored: false
quality_pipeline_restored: false
raw_full_source_passed: false
normal_ui_connected_to_variant_b: false
variant_b_body_generated: false
prompt_bloat: none | minor | found
module_bloat: none | minor | found
next_one_owner:
AGENTS_update_needed:
WORKLOG_update_needed:
```

## Expected Next Owner

`offline_stub_ready` または `needs_live_api_approval` の場合、通常の次候補:

```text
writer_only_new_algorithm_approved_live_ab_owner
```

ただし live API はユーザー承認後のみ。

承認文:

```text
safe-expansion B variant の live AB validation を最大3 caseだけ実行してよいですか。OpenAI APIを呼び、api_send_count / model / run_id / artifact_root を記録します。通常UIの表示結果には反映しません。
```

`needs_offline_revision` の場合は、報告内容から one-owner の revision goal command を指揮ウインドウ側で作成する。
