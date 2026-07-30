# Writer-only New Algorithm Approved Live AB Quality-first Goal Command 2026-06-16

対象: `writer_only_new_algorithm_approved_live_ab_owner`

このファイルは、次の作業ウインドウでそのまま貼って長時間自走するための、承認前提 live AB ゴールコマンドです。目的は「アルゴリズム差の厳密分離」よりも、現実に自然で読みやすい企業ブログを作る組み合わせを見つけることです。したがって A/B でモデルやパラメータが違っていてもよいものとして比較します。

## Approval Gate

この owner は OpenAI API を呼ぶため、作業開始前にユーザーの明示承認が必要です。未承認の場合は実行せず、次の承認文をユーザーへ提示して停止してください。

```text
safe-expansion B variant の quality-first live AB validation を最大3 source casesだけ実行してよいですか。OpenAI APIを呼び、api_send_count / model / parameters / run_id / artifact_root を記録します。通常UIの表示結果には反映しません。初回候補は A0=current writer-only gpt-4.1-mini、B1=safe-expansion gpt-5.4-mini、B2=safe-expansion gpt-5.4 です。全3 source cases x 3 variants の場合、見込み api_send_count は最大9です。
```

## Goal Objective

```text
現行 writer-only を通常UIの本線として保持したまま、承認付き live API で最大3 source cases x 3 variants の quality-first AB を実行し、自然な日本語ブログ、source grounding、information gain、読後感、リスクを比較する。A/Bでモデルやパラメータが違っていてもよい。通常UI接続、latest visible output反映、Route 0506 / Route A / repair / quality pipeline 復帰は行わない。
```

## ゴールコマンド

```text
あなたは TECHIE / notecode / コトメイクの `writer_only_new_algorithm_approved_live_ab_owner` です。

目的:
自然で読みやすい企業ブログを作るため、現行Aとsafe-expansion B候補を承認付きlive APIで比較する。比較目的は「A/Bのモデルを完全に揃えること」ではなく、実運用で勝つ組み合わせを探すことです。ただし source grounding と禁止claimは絶対に緩めない。

開始前必須:
- ユーザーの明示承認がない場合、APIを呼ばずに Approval Gate の承認文を提示して停止する。
- 承認がある場合のみ、最大 `3 source cases x 3 variants = 9 API sends` まで実行してよい。

参照ルール:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\notecode\WORKLOG.md
5. C:\tetie\notecode\docs\writer_only_new_algorithm_ab_test_plan_2026-06-16.md
6. C:\tetie\notecode\docs\writer_only_safe_expansion_model_parameter_audit_goal_command_2026-06-16.md
7. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\model_parameter_audit.md
8. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\model_parameter_matrix.json
9. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\approved_live_ab_candidate_plan.md
10. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\fixture_index.json
11. C:\tetie\notecode\note\writer_only_brief.py
12. C:\tetie\notecode\note\writer_only_evaluator.py
13. C:\tetie\notecode\note\writer_only_openai_adapter.py
14. C:\tetie\notecode\note\writer_only_config.py

Live AB variants:
- A0:
  - route: current writer-only
  - model: `gpt-4.1-mini-2025-04-14`
  - family: `gpt-4.1`
  - parameters: current writer-only config
  - purpose: current visible-quality baseline
- B1:
  - route: safe-expansion
  - model: `gpt-5.4-mini`
  - family: `gpt-5.4`
  - parameters:
    - `reasoning.effort=medium`
    - `text.verbosity=high`
    - `max_output_tokens=7000`
    - `store=false`
  - purpose: cost/speed balanced safe-expansion candidate
- B2:
  - route: safe-expansion
  - model: `gpt-5.4`
  - family: `gpt-5.4`
  - parameters:
    - `reasoning.effort=medium`
    - `text.verbosity=high`
    - `max_output_tokens=7000`
    - `store=false`
  - purpose: quality-first Japanese naturalness / final polish candidate

初回 source cases:
1. `case_01_thin_company_url`
2. `case_02_rich_company_url`
3. `case_03_local_service_url`

許可する変更:
- `C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\live_ab_quality_first_YYYYMMDD_HHMMSS\` 配下の artifact 作成
  - `run_plan.md`
  - `api_send_ledger.jsonl`
  - `comparison_summary.json`
  - `manual_quality_review.md`
  - 各 case / variant の `brief.json`, `draft.md`, `evaluation.json`, `run.json`
- 必要なら artifact-local helper:
  - `C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\tools\run_approved_live_ab_quality_first.py`
- `C:\tetie\notecode\WORKLOG.md`
  - 作業結果を必要最小限で記録する。

原則変更しない:
- product runtime code
- `config.json`
- `writer_only_config.py`
- normal UI code
- latest visible output files
- fixed writer prompt

禁止:
- ユーザー承認なしに live API を呼ばない。
- 9 API sends を超えない。
- 通常UIからB variantを呼ばない。
- latest visible outputへB variantを投影しない。
- Route 0506 / Route A / repair loop / quality pipeline を戻さない。
- raw full source pass をしない。
- source groundingを緩めない。
- fixed promptを長文化しない。
- persona tableを増やさない。
- GPT-5.5をこのownerで実行しない。GPT-5.5は validator owner 後に扱う。

評価軸:
- natural_blog_quality:
  - 冒頭が要約臭くない
  - 読者の場面が自然
  - 会社紹介が広告文に寄りすぎない
  - 見出しと段落のリズムが単調でない
  - 終盤が抽象語だけで閉じない
- source_grounding:
  - source factを断定してよい範囲で使う
  - source外の数値・価格・成果・法律/医療/金融助言・地域市場動向・事例・比較優位を断定しない
- information_gain:
  - sourceの言い換えだけでなく、読者の整理や相談前チェックに役立つ
  - C editorial bridge が事実断定に見えない
- Japanese_readability:
  - 文末・段落長・抽象語・読点密度が不自然でない
- operational_fit:
  - cost / latency / failure behavior / validator compatibility

slice plan:
Slice 0: 承認確認、参照doc、fixture、model matrixを読む。
Self-test: 承認がなければAPIを呼ばず停止。

Slice 1: run artifact root と run_plan を作る。
Self-test: source cases、variants、api_send_count上限、route flagsを記録。

Slice 2: A0/B1/B2を最大3caseで実行する。
Self-test: API送信ごとに `api_send_ledger.jsonl` へ model / parameters / case / variant / run_id を記録。

Slice 3: evaluator と manual review を行う。
Self-test: source grounding fail がある variant は自然さが良くても winner にしない。

Slice 4: comparison_summary と manual_quality_review を作る。
Self-test: case別winner、総合winner、risk、次ownerを明記。

Slice 5: WORKLOGを必要最小限で更新する。
Self-test: WORKLOG読み戻し、route flags、api_send_count確認。

停止条件:
- API承認がない。
- API送信が9回に達した。
- source grounding regression が出た。
- Route 0506 / Route A / repair / quality pipeline が必要になった。
- B outputを通常UIへ出したくなる。
- GPT-5.5を同ownerで使いたくなる。
- 同じエラーが3回連続。

完了報告フォーマット:
参照ルールファイル:
今回の実施範囲:
decision: live_ab_quality_first_ready | needs_model_config_validation | needs_next_owner | blocked | reject
artifact_root:
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

品質優先で B2 が明確に勝つが、通常UI反映前の安全確認が必要な場合:

```text
writer_only_safe_expansion_quality_first_promotion_decision_owner
```

GPT-5.5を比較に入れる必要が出た場合:

```text
writer_only_model_config_validation_update_owner
```

B候補が source grounding を壊した場合:

```text
writer_only_safe_expansion_revision_or_reject_owner
```
