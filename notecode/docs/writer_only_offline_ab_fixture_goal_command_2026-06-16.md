# Writer-only Offline AB Fixture Goal Command 2026-06-16

対象: `writer_only_new_algorithm_offline_ab_fixture_owner`

このファイルは、次の作業ウインドウでそのまま貼って長時間自走するためのゴールコマンドです。現行 writer-only は本線として残し、新 safe-expansion B variant は offline AB fixture / artifact harness まで準備します。

## Goal Objective

```text
現行コトメイク writer-only を通常UIの本線として保持したまま、safe-expansion writer-only B variant を live APIなし・通常UI非接続で offline AB test できる fixture / artifact harness まで準備し、5検証ケース、A/B評価schema、review checklist、次owner判断を記録する。
```

## ゴールコマンド

```text
あなたは TECHIE / notecode / コトメイクの `writer_only_new_algorithm_offline_ab_fixture_owner` です。

目的:
現行 writer-only を通常UIの本線として残したまま、新 safe-expansion writer-only B variant を offline AB test できる fixture / artifact harness まで準備する。live API は呼ばない。通常UIから B variant を呼ばない。Route 0506 / Route A / repair loop / quality pipeline は戻さない。

参照ルール:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\notecode\docs\writer_only_safe_expansion_policy_proposal_2026-06-16.md
5. C:\tetie\notecode\docs\writer_only_new_algorithm_ab_test_plan_2026-06-16.md
6. C:\tetie\notecode\docs\writer_only_new_algorithm_deep_route_plan_2026-06-16.md
7. C:\tetie\notecode\docs\writer_only_new_algorithm_goal_execution_prompt_2026-06-16.md
8. C:\tetie\notecode\note\writer_only_service.py
9. C:\tetie\notecode\note\writer_only_brief.py
10. C:\tetie\notecode\note\writer_only_openai_adapter.py
11. C:\tetie\notecode\note\writer_only_evaluator.py
12. C:\tetie\notecode\note\writer_only_source_bundle.py
13. C:\tetie\notecode\logs\writer_only_generation\writer_only_20260604_233416_91272e8c\

実施範囲:
- artifact root を作る:
  C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\
- `README.md`, `fixture_index.json`, `source_research_summary.md`, `summary.md` を作る。
- 5ケースの case directory を作る:
  - `case_01_thin_company_url`
  - `case_02_rich_company_url`
  - `case_03_local_service_url`
  - `case_04_seasonal_theme`
  - `case_05_trivia_theme`
- 既存 artifact `writer_only_20260604_233416_91272e8c` を `case_02_rich_company_url` の seed として登録する。
- 不足ケースは、live fetch / live API ではなく、保存済み情報または手作り minimal `source_bundle.json` / `brief.json` fixture として作る。
- B variant の safe-expansion policy は product code へ入れず、artifact schema / review checklist / decision.md に置く。
- 必要な検証は no-API の読み戻し、JSON parse、path existence、py_compile までにする。

禁止:
- live APIを呼ばない。
- product writer promptを長文化しない。
- product codeの生成本線を変更しない。
- 通常UIの生成ボタンや visible routeを増やさない。
- B variantを latest visible output に投影しない。
- Route 0506 / Route A / repair loop / quality pipeline を戻さない。
- raw full source pass をしない。
- persona table を増やさない。
- external orchestration framework を導入しない。

設計契約:
- A `source_fact`: sourceにある会社・商品・数値・実績・固有名詞。断定OK。
- B `verified_external_context`: 季節、地域、統計、制度、用語豆知識。出典URLと取得日付きで渡された場合のみ使用。
- C `editorial_bridge`: 読者の悩み、利用場面、判断軸、比喩、相談前チェック。断定せず「〜のような場面」「〜を考えるきっかけ」として書く。
- D `prohibited_claim`: 数値、価格、成果、法律/医療/金融助言、地域市場動向、顧客事例、比較優位。AまたはBなしでは禁止。
- thin source でも短すぎる紹介文にせず、B variant review では 700-1200字の自然な記事形を期待する。ただし `do_not_pad=true` は維持する。
- 体言止め、主語省略、文末分散、読点、段落長、抽象名詞は fixed prompt ではなく review checklist / evaluator候補で扱う。

slice plan:
Slice 0: 参照docと現行 code を読む。
Self-test: 読んだファイル、実施範囲、非実装境界を artifact README に記録。

Slice 1: artifact root と共通schemaを作る。
Self-test: `fixture_index.json` がJSON parseでき、5 case_id が揃っていること。

Slice 2: 既存 artifactを `case_02_rich_company_url` seed として登録する。
Self-test: `source_bundle.json` / `brief.json` / `draft.md` / `evaluation.json` の参照先が存在すること。古い `企業note` 表現は stale artifact note として記録すること。

Slice 3: 残り4ケースの minimal fixture を作る。
Self-test: 各 case の `input\brief.json` / `input\source_bundle.json` が存在し、source_count / claims_count / expected_risk が記録されていること。

Slice 4: B variant safe-expansion schema と review checklist を作る。
Self-test: A/B/C/D fact layer が混ざっていないこと。D prohibited claim の禁止例が checklist にあること。

Slice 5: A/B comparison schema を作る。
Self-test: 各 case に `variant_a\review.md`, `variant_b\review.md`, `decision.md` の雛形があり、manual review 5軸が入っていること。

Slice 6: no-API validation を実行する。
Self-test: path existence、JSON parse、Markdown読み戻し、必要なら py_compile。api_send_count は0。

Slice 7: WORKLOG を必要最小限で更新する。
Self-test: WORKLOG読み戻し、route flags確認、artifact root確認。

エラー処理:
- 同じエラーは最大3回まで自己修正する。
- 3回で直らない場合は停止し、block report を出す。
- ファイル不足時は D:\Rescue_Yokoyama\C_root\tetie を read-only で確認してよい。ただしコピーする場合は「存在しない不足分だけ」に限定する。
- WEB検索は、この owner では原則不要。計画文書の調査で不足が明確な場合のみ公式/一次情報を確認する。

停止条件:
- prompt bloatなしで成立しない。
- source groundingを落とさないと膨らませられない。
- B variantを通常UIに出す必要が出た。
- Route 0506 / Route A / repair / quality pipeline への依存が必要になった。
- live APIが必要になった。

Live API承認ゲート:
この owner では live API 禁止。次 owner で必要な場合のみ、次の文面でユーザー承認を取る。

「safe-expansion B variant の live AB validation を最大3 caseだけ実行してよいですか。OpenAI APIを呼び、api_send_count / model / run_id / artifact_root を記録します。通常UIの表示結果には反映しません。」

完了報告フォーマット:
参照ルールファイル:
今回の実施範囲:
decision: fixture_ready | needs_next_owner | blocked | reject
artifact_root:
baseline_kept: true
fixture_cases:
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

このゴールコマンドが完了した後の次 owner 候補:

```text
writer_only_new_algorithm_offline_ab_no_api_harness_owner
```

目的は、fixture を使って A/B の deterministic comparison と no-API evaluator候補を実際に動かすこと。
