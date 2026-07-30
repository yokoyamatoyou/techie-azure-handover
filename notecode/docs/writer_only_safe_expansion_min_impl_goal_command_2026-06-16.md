# Writer-only Safe Expansion Minimum Implementation Goal Command 2026-06-16

対象: `writer_only_safe_expansion_brief_evaluator_min_impl_owner`

このファイルは、次の作業ウインドウでそのまま貼って長時間自走するための実装ゴールコマンドです。前 owner が確定した schema を、writer-only の `brief` / `evaluator` / focused tests に最小実装します。

## Goal Objective

```text
現行 writer-only を通常UIの本線として保持したまま、safe-expansion schema を `writer_only_brief.py` と `writer_only_evaluator.py` と focused tests に最小実装し、A/B/C/D fact layer、safe_expansion contract、default empty verified_external_context、prohibited claim guard、editorial bridge / Japanese style warning details を追加する。live API、通常UI接続、B本文生成、Route 0506 / Route A / repair / quality pipeline 復帰は行わない。
```

## ゴールコマンド

```text
あなたは TECHIE / notecode / コトメイクの `writer_only_safe_expansion_brief_evaluator_min_impl_owner` です。

目的:
`writer_only_new_algorithm_offline_ab_variant_schema_owner` が決めた schema だけを product code へ最小実装する。現行 writer-only を通常UIの本線として保持し、live API、B variant本文生成、通常UI接続は行わない。

参照ルール:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\notecode\docs\writer_only_safe_expansion_policy_proposal_2026-06-16.md
5. C:\tetie\notecode\docs\writer_only_new_algorithm_ab_test_plan_2026-06-16.md
6. C:\tetie\notecode\docs\writer_only_new_algorithm_deep_route_plan_2026-06-16.md
7. C:\tetie\notecode\docs\writer_only_offline_ab_variant_schema_goal_command_2026-06-16.md
8. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\variant_schema_plan.md
9. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\safe_expansion_schema_final.json
10. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\evaluator_guard_schema.json
11. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\manual_review_gate_schema.md
12. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\implementation_scope_decision.md
13. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\implementation_owner_prompt.md
14. C:\tetie\notecode\note\writer_only_brief.py
15. C:\tetie\notecode\note\writer_only_evaluator.py
16. C:\tetie\notecode\note\writer_only_openai_adapter.py
17. C:\tetie\notecode\note\writer_only_source_bundle.py
18. C:\tetie\notecode\note\tests\test_writer_only_generation.py

許可する変更:
- `C:\tetie\notecode\note\writer_only_brief.py`
  - `brief["writer_contract"]["safe_expansion"]` を追加。
  - `brief["expansion_policy"]` を追加。
  - `brief["verified_external_context"] = []` をdefault追加。
  - `article_body_contract.min_chars` はグローバル変更しない。
  - `article_body_contract.do_not_pad = true` を維持。
- `C:\tetie\notecode\note\writer_only_evaluator.py`
  - prohibited claim guard を追加。
  - editorial bridge marker warning details を追加。
  - Japanese style warning details を追加。
  - 日本語文体 warning は auto-fail にしない。
- `C:\tetie\notecode\note\tests\test_writer_only_generation.py`
  - 上記 brief / evaluator の focused tests を追加。

原則変更しない:
- `writer_only_openai_adapter.py`
  - 既存 `WRITER_INSTRUCTIONS` が brief の writer_contract を守る指示を含むため、原則変更しない。
  - どうしても必要なら、1文だけ短く追加し、prompt bloat を `minor` として記録する。

禁止:
- live APIを呼ばない。
- B variant本文を生成しない。
- 通常UIからB variantを呼ばない。
- latest visible outputへB variantを投影しない。
- Route 0506 / Route A / repair loop / quality pipeline を戻さない。
- raw full source pass をしない。
- source groundingを緩めない。
- fixed promptへ長文safe-expansion contractを入れない。
- persona tableを増やさない。
- external orchestration frameworkを導入しない。
- verified external context の runtime取得やWEB検索連携を実装しない。

必須 contract:
`brief["writer_contract"]["safe_expansion"]` には次を入れる。

source factsは断定してよい。読者の場面・たとえ・相談前チェックはeditorial bridgeとして足してよいが、事実断定ではなく「〜のような場面」「〜を考えるきっかけ」で書く。verified external contextは出典付きで渡された場合だけ使う。数値・価格・成果・法律/医療/金融助言・地域市場動向・事例・比較優位はsourceまたは出典付きcontextなしで書かない。

`brief["expansion_policy"]` には少なくとも次を入れる。
- `policy_id`
- `fact_layers`
  - A / source_fact
  - B / verified_external_context
  - C / editorial_bridge
  - D / prohibited_claim
- `prohibited_claim_classes`
- `thin_source_review_expectation`
  - min: 700
  - max: 1200
  - do_not_pad: true
  - note: review expectation only, not global article_body_contract change

Evaluator要件:
- D prohibited claim guard は fail。
- visible media name / source URL coverage / article length / route flags は既存挙動を維持。
- C editorial bridge の factual/absolute language は warning details。
- 日本語文体 guard は warning details。
- warning は初回実装では auto-fail にしない。

対象 prohibited claim classes:
- unsupported_number
- unsupported_price
- unsupported_outcome
- unsupported_legal_advice
- unsupported_medical_advice
- unsupported_financial_advice
- unsupported_local_market_trend
- unsupported_customer_case
- unsupported_superiority_claim
- unsupported_public_procedure

slice plan:
Slice 0: 参照doc、schema artifact、現行 code/tests を読む。
Self-test: 変更候補ファイル、変更しないファイル、禁止境界を作業メモに確認。

Slice 1: `writer_only_brief.py` に safe-expansion schema を最小追加する。
Self-test: build_writer_only_brief の戻り値に `writer_contract.safe_expansion`, `expansion_policy`, `verified_external_context=[]` があること。

Slice 2: `writer_only_evaluator.py` に prohibited claim guard / warning details を追加する。
Self-test: source/B evidenceなしのD claimが fail になり、C bridge phrasing は fail ではなく warning/details になること。

Slice 3: focused tests を追加する。
Self-test: safe_expansion contract、fact layers、verified_external_context default、thin_source do_not_pad、D claim fail、C bridge allowed、Japanese warning non-fail をテストする。

Slice 4: no-API validation を実行する。
Self-test:
- py_compile changed modules
- `py -3.11 -m pytest note\tests\test_writer_only_generation.py -q`
- `py -3.11 scripts\validate_writer_only_config.py` 可能なら実行
- api_send_count 0

Slice 5: artifact note を追加する。
追加先:
`C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\min_impl_summary.md`
内容:
- changed files
- tests
- prompt bloat
- module bloat
- route flags
- next owner

Slice 6: WORKLOG を必要最小限で更新する。
Self-test: WORKLOG読み戻し、route flags確認。

停止条件:
- 同じエラーが3回連続。
- prompt long-form expansion が必要。
- source grounding relaxation が必要。
- raw full source pass が必要。
- live API が必要。
- UI接続が必要。
- Route 0506 / Route A / repair / quality pipeline が必要。
- evaluator と manual review の境界が壊れる。

ファイル不足時:
- D:\Rescue_Yokoyama\C_root\tetie を read-only で確認してよい。
- コピーは「C側に存在しない不足分だけ」に限定する。
- 既存ファイルの上書きは禁止。

完了報告フォーマット:
参照ルールファイル:
今回の実施範囲:
decision: min_impl_ready | needs_next_owner | blocked | reject
artifact_root:
changed_files:
brief_schema:
evaluator_schema:
tests:
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

通常は次の owner を推奨する。

```text
writer_only_safe_expansion_offline_ab_generation_stub_owner
```

目的:

- live APIなしで、fixtureを使った B variant stub / deterministic draft scaffold または review-only comparison を作る。
- 実装済み brief/evaluator schema が fixture 5ケースでどう見えるか確認する。

live API が必要な場合は、ユーザー承認後にのみ次候補:

```text
writer_only_new_algorithm_approved_live_ab_owner
```
