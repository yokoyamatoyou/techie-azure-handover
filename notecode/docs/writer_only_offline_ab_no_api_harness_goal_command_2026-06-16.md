# Writer-only Offline AB No-API Harness Goal Command 2026-06-16

対象: `writer_only_new_algorithm_offline_ab_no_api_harness_owner`

このファイルは、次の作業ウインドウでそのまま貼って長時間自走するためのゴールコマンドです。前 owner が作成した offline fixture を使い、APIなしで deterministic comparison / risk scan / review prefill を動かせる artifact harness まで作ります。

## Goal Objective

```text
現行 writer-only を通常UIの本線として保持したまま、writer_only_new_algorithm_ab_20260616 fixture を使って safe-expansion B variant の no-API comparison harness を作成し、5ケースの source/brief/draft/evaluation を静的評価して、A/B比較schema、risk scan、manual review prefill、次の live/API owner 判断を記録する。
```

## ゴールコマンド

```text
あなたは TECHIE / notecode / コトメイクの `writer_only_new_algorithm_offline_ab_no_api_harness_owner` です。

目的:
既存 artifact `C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\` を使い、live APIなし・通常UI非接続で、safe-expansion B variant の比較準備を一段進める。Bの本文生成はまだ行わない。代わりに deterministic comparison / risk scan / review prefill / decision summary を作り、次に live API または no-API実装へ進むべきか判断できる状態にする。

参照ルール:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\notecode\docs\writer_only_safe_expansion_policy_proposal_2026-06-16.md
5. C:\tetie\notecode\docs\writer_only_new_algorithm_ab_test_plan_2026-06-16.md
6. C:\tetie\notecode\docs\writer_only_new_algorithm_deep_route_plan_2026-06-16.md
7. C:\tetie\notecode\docs\writer_only_offline_ab_fixture_goal_command_2026-06-16.md
8. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\README.md
9. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\fixture_index.json
10. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\safe_expansion_policy.json
11. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\review_checklist.md
12. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\ab_comparison_schema.json
13. C:\tetie\notecode\note\writer_only_brief.py
14. C:\tetie\notecode\note\writer_only_evaluator.py
15. C:\tetie\notecode\note\writer_only_openai_adapter.py

実施範囲:
- artifact root は既存のまま使う:
  C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\
- 追加 artifact を作る:
  - `no_api_harness_plan.md`
  - `no_api_static_scan.json`
  - `no_api_case_comparison.json`
  - `no_api_harness_summary.md`
  - 各 case の `decision.md` / `variant_a/review.md` / `variant_b/review.md` を静的情報で prefill
- 必要なら artifact root 配下にだけ helper script を置く:
  - `tools\run_no_api_static_scan.py`
  - `tools\README.md`
- product runtime code は原則変更しない。どうしても必要なら、通常UIから未使用の pure helper に限り、ユーザー承認なしでは実装しない。

禁止:
- live APIを呼ばない。
- B variant の本文をOpenAIで生成しない。
- 通常UIから B variant を呼ばない。
- latest visible outputへB variantを投影しない。
- Route 0506 / Route A / repair loop / quality pipeline を戻さない。
- raw full source pass をしない。
- fixed `WRITER_INSTRUCTIONS` を長文化しない。
- persona table を増やさない。
- external orchestration framework を導入しない。

no-API harness で行うこと:
1. `fixture_index.json` を読み、5ケースの入力が揃っているか検査する。
2. 各 `brief.json` / `source_bundle.json` を読み、source_count / claims_count / article_body_contract / risk_policy / expected_risk を抽出する。
3. `case_02_rich_company_url` の既存 baseline draft/evaluation を静的評価する。
4. 他ケースは baseline draft がないため、draft生成はせず、input risk と expected B review point を prefill する。
5. `safe_expansion_policy.json` と `review_checklist.md` を参照し、各caseの D prohibited claim watchlist を作る。
6. 日本語文体 guard を静的 checklist として prefill する:
   - 文末同型
   - 段落長均一化
   - 抽象名詞連続
   - 読点過多
   - H2冒頭同型
   - 体言止め過多
   - 主語省略によるfact attribution曖昧化
7. `no_api_case_comparison.json` に、A/B本文生成前に比較すべき観点を case別に記録する。
8. `no_api_harness_summary.md` に、次 owner を判断する。

slice plan:
Slice 0: 参照docと artifact root を読む。
Self-test: fixture root、5 case、policy、checklist、schema が存在すること。

Slice 1: no-API static scan schema を設計する。
Self-test: 5 case すべてに `case_id`, `source_count`, `claims_count`, `expected_risk`, `has_baseline_draft`, `has_baseline_evaluation` が出ること。

Slice 2: artifact root 配下に no-API helper を作る。
Self-test: helper は artifact root配下だけにあり、product runtime import pathから呼ばれないこと。

Slice 3: static scan を実行する。
Self-test: JSON parse、path existence、Markdown readback が pass。api_send_count は0。

Slice 4: 各 case の review / decision を prefill する。
Self-test: variant_a/review.md、variant_b/review.md、decision.md に manual review 6軸と prohibited claim watchlist が入っていること。

Slice 5: summary を作る。
Self-test: 次 owner が `writer_only_new_algorithm_offline_ab_variant_schema_owner` または `writer_only_new_algorithm_approved_live_ab_owner` のどちらかとして理由付きで示されていること。

Slice 6: tests / validation を実行する。
Self-test: helper py_compile、helper run、現行 writer-only modules py_compile。API send count 0。

Slice 7: WORKLOG を必要最小限で更新する。
Self-test: WORKLOG読み戻し、route flags確認、artifact summary確認。

評価基準:
- `fixture_ready` から `harness_ready` へ進める。
- Bの生成前に、どのcaseでどのリスクを見るべきか明確になる。
- 次に product code へ入れる前に、safe-expansion policy を brief/evaluatorへ入れる最小ownerが見える。
- live APIが必要な場合も、最大3case承認ゲートを残す。

停止条件:
- 同じエラーが3回連続。
- fixtureの欠損が多く、D:\Rescue_Yokoyama\C_root\tetie からも補完できない。
- no-APIでは判断できず、live APIなしで進める意味がないと分かった。
- product codeを触らないと成立しない。
- source groundingを落とす設計しか作れない。

ファイル不足時:
- D:\Rescue_Yokoyama\C_root\tetie を read-only で確認してよい。
- コピーは「C側に存在しない不足分だけ」に限定する。
- 既存ファイルの上書きは禁止。

Live API承認ゲート:
この owner では live API 禁止。次 owner で必要な場合のみ、次の文面でユーザー承認を取る。

「safe-expansion B variant の live AB validation を最大3 caseだけ実行してよいですか。OpenAI APIを呼び、api_send_count / model / run_id / artifact_root を記録します。通常UIの表示結果には反映しません。」

完了報告フォーマット:
参照ルールファイル:
今回の実施範囲:
decision: harness_ready | needs_live_api_approval | needs_next_owner | blocked | reject
artifact_root:
baseline_kept: true
fixture_cases:
static_scan:
reviews_prefilled:
tests:
api_send_count: 0
route_0506_restored: false
route_a_restored: false
repair_restored: false
quality_pipeline_restored: false
raw_full_source_passed: false
prompt_bloat: none | minor | found
module_bloat: none | minor | found
next_one_owner:
AGENTS_update_needed:
WORKLOG_update_needed:
```

## Expected Next Owner

通常は次の owner を推奨する。

```text
writer_only_new_algorithm_offline_ab_variant_schema_owner
```

目的:

- product codeに入れる前に、B variant の `safe_expansion_policy` を `brief` / `evaluator` / `manual_review` のどこへ置くかを final schema として決める。
- まだ live API は呼ばない。

ただし、static scan の結果、fixtureだけでは B の良し悪しが判断不能で、ユーザーが承認する場合のみ次候補:

```text
writer_only_new_algorithm_approved_live_ab_owner
```
