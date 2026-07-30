# Writer-only Safe Expansion B Rerun Same Source Compare Goal Command 2026-06-16

対象: `writer_only_safe_expansion_b_rerun_same_source_compare_owner`

このファイルは、別作業ウインドウでそのまま貼って長時間自走するための、承認前提 live B rerun / same-source compare ゴールコマンドです。既存Aログをbaselineとして使い、同じsourceでBだけを再生成し、各記事ごとにA/B Markdownを同一フォルダへ保存します。

## Approval Gate

この owner は OpenAI API を呼ぶため、作業開始前にユーザーの明示承認が必要です。未承認の場合は実行せず、次の承認文をユーザーへ提示して停止してください。

```text
既存Aログをbaselineとして使い、同じソースで safe-expansion B variant だけを2 source cases x 2 variantsで再生成してよいですか。OpenAI APIを呼び、api_send_count / model / parameters / response_id / artifact_root を記録します。通常UIの表示結果や latest visible output には反映しません。対象は `case_01_thin_company_url` と `case_03_local_service_url`、B候補は `B1=gpt-5.4-mini` と `B2=gpt-5.4` です。見込み api_send_count は最大4です。
```

## Goal Objective

```text
既存A0ログを再利用し、同じsource_bundleでsafe-expansion B1/B2だけを承認付きlive APIで再生成する。生成後は各記事ケースごとに、A0既存本文・B1新規本文・B2新規本文を同一compareフォルダにMarkdownで保存し、00_compare_index.md と evaluation_summary.json で比較できる状態にする。通常UI接続、latest visible output反映、Route 0506 / Route A / repair / quality pipeline復帰は行わない。
```

## ゴールコマンド

```text
あなたは TECHIE / notecode / コトメイクの `writer_only_safe_expansion_b_rerun_same_source_compare_owner` です。

目的:
既存Aログを使い、同じソースでBだけを再生成して自然なブログ品質を比較する。Aは再生成しない。Bはpreflight修正後のproduction-shaped safe-expansion briefを使う。結果は各caseごとの同一フォルダにMarkdownで並べ、読み比べやすくする。

開始前必須:
- ユーザーの明示承認がない場合、APIを呼ばずに Approval Gate の承認文を提示して停止する。
- 承認がある場合のみ、最大 `2 source cases x 2 B variants = 4 API sends` まで実行してよい。

参照ルール:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\notecode\WORKLOG.md
5. C:\tetie\notecode\docs\writer_only_ab_preflight_fix_and_compare_layout_goal_command_2026-06-16.md
6. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\live_ab_quality_first_20260616_200725\preflight_repair_summary.json
7. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\live_ab_quality_first_20260616_200725\compare_md\compare_md_summary.json
8. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\live_ab_quality_first_20260616_200725\case_01_thin_company_url\A0\brief.json
9. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\live_ab_quality_first_20260616_200725\case_01_thin_company_url\A0\draft.md
10. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\live_ab_quality_first_20260616_200725\case_03_local_service_url\A0\brief.json
11. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\live_ab_quality_first_20260616_200725\case_03_local_service_url\A0\draft.md
12. C:\tetie\notecode\note\writer_only_brief.py
13. C:\tetie\notecode\note\writer_only_evaluator.py
14. C:\tetie\notecode\note\writer_only_openai_adapter.py
15. C:\tetie\notecode\note\writer_only_config.py

対象 source cases:
1. `case_01_thin_company_url`
   - A0 existing log is available and passed.
   - Use A0 `brief.json` / `source_bundle` as same-source baseline.
2. `case_03_local_service_url`
   - A0 existing log is available and passed.
   - Use A0 `brief.json` / `source_bundle` as same-source baseline.

対象外:
- `case_02_rich_company_url`
  - まだ source_url_coverage / visible media 周りが比較を曇らせるため、この2-case rerunでは扱わない。

Live B variants:
- B1:
  - route: safe-expansion
  - model: `gpt-5.4-mini`
  - family: `gpt-5.4`
  - parameters:
    - `reasoning.effort=medium`
    - `text.verbosity=high`
    - `max_output_tokens=7000`
    - `store=false`
- B2:
  - route: safe-expansion
  - model: `gpt-5.4`
  - family: `gpt-5.4`
  - parameters:
    - `reasoning.effort=medium`
    - `text.verbosity=high`
    - `max_output_tokens=7000`
    - `store=false`

許可する変更:
- 新しいartifact root作成:
  - `C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\b_rerun_same_source_compare_YYYYMMDD_HHMMSS\`
- artifact配下:
  - `run_plan.md`
  - `api_send_ledger.jsonl`
  - `comparison_summary.json`
  - `manual_quality_review.md`
  - 各case / B variant の `brief.json`, `draft.md`, `evaluation.json`, `run.json`
  - `compare_md\<case_id>\00_compare_index.md`
  - `compare_md\<case_id>\A0_existing_current_gpt41mini.md`
  - `compare_md\<case_id>\B1_safe_expansion_gpt54mini.md`
  - `compare_md\<case_id>\B2_safe_expansion_gpt54.md`
  - `compare_md\<case_id>\evaluation_summary.json`
- artifact-local helperが必要な場合のみ:
  - `C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\tools\run_b_rerun_same_source_compare.py`
- `C:\tetie\notecode\WORKLOG.md`
  - 結果を必要最小限で記録する。

原則変更しない:
- product runtime code
- `config.json`
- `writer_only_config.py`
- normal UI code
- latest visible output files
- fixed writer prompt

禁止:
- ユーザー承認なしにOpenAI APIを呼ばない。
- A0を再生成しない。
- 4 API sendsを超えない。
- 通常UIからB variantを呼ばない。
- latest visible outputへB variantを投影しない。
- Route 0506 / Route A / repair loop / quality pipeline を戻さない。
- raw full source pass をしない。
- source groundingを緩めない。
- fixed promptを長文化しない。
- persona tableを増やさない。
- GPT-5.5をこのownerで使わない。
- case_02をこのownerで扱わない。

B brief作成ルール:
- 既存A0 `brief.json` の `source_bundle` を保持する。
- `writer_contract.safe_expansion`, `expansion_policy`, `verified_external_context=[]` を入れる。
- preflight修正後の production-shaped B brief を使う。
- review-only surface を writer input と混ぜない。
- visible media name は reader-facing targetとして `企業note` / `note` / `はてなブログ` / `Hatena Blog` を出さず、必要なら `企業ブログ` / `ブログ` へ正規化する。

compare Markdown layout:

```text
b_rerun_same_source_compare_YYYYMMDD_HHMMSS\
  compare_md\
    case_01_thin_company_url\
      00_compare_index.md
      A0_existing_current_gpt41mini.md
      B1_safe_expansion_gpt54mini.md
      B2_safe_expansion_gpt54.md
      evaluation_summary.json
    case_03_local_service_url\
      00_compare_index.md
      A0_existing_current_gpt41mini.md
      B1_safe_expansion_gpt54mini.md
      B2_safe_expansion_gpt54.md
      evaluation_summary.json
```

Markdown front matter:

```text
---
case_id:
variant:
source: existing A0 baseline | live B rerun
model:
parameters:
evaluation_passed:
failed_checks:
article_char_count:
response_id:
---
```

評価軸:
- source grounding:
  - prohibited claim hits
  - unsupported generalizations
  - source URL coverage
- natural blog quality:
  - 冒頭が要約臭くない
  - 読者の場面が自然
  - 見出しと段落のリズム
  - 終盤の着地
- information gain:
  - sourceの言い換えだけでない
  - C editorial bridgeが事実断定に見えない
- Japanese readability:
  - 文末同型
  - 段落長
  - 抽象語
  - 読点密度
- production readiness:
  - normal UIへ出せるか
  - source_bundle shape
  - cost / latency

slice plan:
Slice 0: 承認確認、A0ログ、preflight summary、compare_mdを読む。
Self-test: 承認がなければAPIを呼ばず停止。

Slice 1: artifact rootとrun_planを作る。
Self-test: 対象caseは2つ、対象variantはB1/B2のみ、api_send上限4を記録。

Slice 2: 既存A0 baselineをコピーする。
Self-test: A0 existing draft/evaluation/run/briefを新artifactにも参照またはコピーし、再生成していないことを記録。

Slice 3: B1/B2を同一sourceでlive生成する。
Self-test: 各sendを `api_send_ledger.jsonl` に status/model/parameters/response_id付きで記録。

Slice 4: evaluatorを実行し、caseごとにA0/B1/B2をcompare_mdへ配置する。
Self-test: 各caseの同一フォルダに3本のmdとindex、summary JSONがある。

Slice 5: manual reviewとcomparison_summaryを作る。
Self-test: case別winner、総合winner、promotion readiness、riskを明記。

Slice 6: no-API validationを実行する。
Self-test:
- JSON parse
- Markdown readback
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .\.venv\Scripts\python.exe -m pytest -p no:cacheprovider note\tests\test_writer_only_generation.py -q`
- `scripts\validate_writer_only_config.py`
- latest visible output未更新確認

Slice 7: WORKLOGを必要最小限で更新する。
Self-test: route flags / api_send_count / normal UI未接続を確認。

完了判定:
- `b_rerun_compare_ready`
  - B1/B2が2caseで生成され、同一フォルダMarkdown比較まで完了。
- `needs_revision`
  - Bがsource groundingまたは自然さでまだ弱く、別owner修正が必要。
- `blocked`
  - API承認なし、同じエラー3回、または境界違反リスク。
- `reject`
  - B案の安全性が崩れた。

完了報告フォーマット:
参照ルールファイル:
今回の実施範囲:
decision: b_rerun_compare_ready | needs_revision | blocked | reject
artifact_root:
compare_md_root:
api_send_count:
models_and_parameters:
cases:
winner_summary:
source_grounding_findings:
naturalness_findings:
risk_findings:
changed_files_or_docs:
tests_or_validation:
route_0506_restored: false
route_a_restored: false
repair_restored: false
quality_pipeline_restored: false
raw_full_source_passed: false
normal_ui_connected_to_variant_b: false
latest_visible_output_updated_from_variant_b: false
prompt_bloat: none | minor | found
module_bloat: none | minor | found
next_one_owner:
AGENTS_update_needed:
WORKLOG_update_needed:
```

## Expected Next Owner

BがAより明確に自然で安全な場合:

```text
writer_only_safe_expansion_promotion_decision_owner
```

Bが一部良いが修正が必要な場合:

```text
writer_only_safe_expansion_revision_owner
```

Bがsource groundingを壊す場合:

```text
writer_only_safe_expansion_reject_owner
```
