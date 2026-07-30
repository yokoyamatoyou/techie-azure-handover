# Writer-only New Algorithm Goal Execution Prompt 2026-06-16

この文書は、次 window で実装に進む場合の copy-paste prompt です。実装にはユーザー承認が必要です。

```text
あなたは TECHIE / notecode / コトメイクの `writer_only_new_algorithm_offline_ab_fixture_owner` です。

目的:
現行 writer-only を通常UIの本線として維持したまま、safe-expansion writer-only B variant を offline AB test できる fixture / artifact harness まで準備する。live API は呼ばない。通常UIから B variant を呼ばない。Route 0506 / Route A / repair loop / quality pipeline は戻さない。

参照ルール:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\notecode\docs\writer_only_safe_expansion_policy_proposal_2026-06-16.md
5. C:\tetie\notecode\docs\writer_only_new_algorithm_ab_test_plan_2026-06-16.md
6. C:\tetie\notecode\docs\writer_only_new_algorithm_deep_route_plan_2026-06-16.md
7. C:\tetie\notecode\note\writer_only_service.py
8. C:\tetie\notecode\note\writer_only_brief.py
9. C:\tetie\notecode\note\writer_only_openai_adapter.py
10. C:\tetie\notecode\note\writer_only_evaluator.py
11. C:\tetie\notecode\note\writer_only_source_bundle.py
12. C:\tetie\notecode\logs\writer_only_generation\writer_only_20260604_233416_91272e8c\

実装範囲:
- まず artifact root を作る:
  C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\
- `README.md`, `fixture_index.json`, `source_research_summary.md`, `case_*/decision.md` を作る。
- 既存 artifact `writer_only_20260604_233416_91272e8c` を `rich_company_url` seed として登録する。
- 不足ケースは、実 source fetch や live API ではなく、保存済み/手作りの minimal `source_bundle.json` と `brief.json` fixture として作る。
- B variant の safe-expansion policy はまず artifact schema と review checklist に置く。product codeへ入れるのは次 owner以降。
- 必要な場合のみ no-API pure helper を追加する。追加するなら 1 owner / 1 helper に限定し、通常UIから未使用にする。

禁止:
- live APIを呼ばない。
- product writer promptを長文化しない。
- Route 0506 / Route A / repair loop / quality pipelineを戻さない。
- raw full source passをしない。
- persona tableを増やさない。
- 通常UIの生成ボタンや visible routeを増やさない。
- latest visible outputへB variantを投影しない。

slice plan:
Slice 0: 参照docと現行 code を読む。
Self-test: 読んだファイル、実施範囲、非実装境界を artifact README に記録。

Slice 1: artifact root と fixture_index schema を作る。
Self-test: thin_company_url / rich_company_url / local_service_url / seasonal_theme / trivia_theme の5 case_idがあること。

Slice 2: 既存 artifactを rich_company_url seed として登録する。
Self-test: source_bundle / brief / draft / evaluation のパスが存在すること。古い `企業note` 表現は stale artifact note として扱うこと。

Slice 3: B variant の safe-expansion schema を artifact に置く。
Self-test: A source fact / B verified external context / C editorial bridge / D prohibited claim が混ざっていないこと。

Slice 4: no-API review checklist を作る。
Self-test: 文章が短くなりすぎない、AIぽさを過剰修正しない、source groundingを落とさない、の3点を確認。

Slice 5: 必要なら tests か validation script を追加する。
Self-test: no-API tests / py_compile を通す。API send count は0。

Slice 6: WORKLOG を必要最小限で更新する。
Self-test: docs読み戻し、WORKLOG読み戻し、route flags確認。

停止条件:
- 同じエラーが3回連続。
- prompt bloatなしで成立しない。
- source groundingを落とさないと膨らませられない。
- B variantを通常UIに出す必要が出た。

Live API承認ゲート:
live API はこの owner では禁止。次 owner で必要な場合は、事前に以下をユーザーへ確認する。

承認依頼文:
「safe-expansion B variant の live AB validation を最大3 caseだけ実行してよいですか。OpenAI APIを呼び、api_send_count / model / run_id / artifact_root を記録します。通常UIの表示結果には反映しません。」

完了報告フォーマット:
decision: needs_user_approval_before_code | fixture_ready | blocked | reject
artifact_root:
baseline_kept: true
route_0506_restored: false
route_a_restored: false
repair_restored: false
quality_pipeline_restored: false
raw_full_source_passed: false
prompt_bloat: none | minor | found
module_bloat: none | minor | found
api_send_count: 0
fixture_cases:
tests:
next_one_owner:
AGENTS_update_needed:
WORKLOG_update_needed:
```
