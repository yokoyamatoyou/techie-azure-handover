# Route 0506 Instruction Window Migration To Category AB Test

作成日: 2026-05-10 JST

## Copy-Paste Prompt For Next Work Window

通常モードで実行してください。日本語で報告してください。

参照ルールファイル:

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`

今回の owner は 1 つだけです。

```text
owner: route_0506_category_ab_test_after_self_perspective_guard
```

## 目的

Route 0506 は、直近のユーザー確認で AI ぽさが少なく、Route A replacement 候補として AB テストに進める状態に近い。

この作業ウインドウでは、次を安全にフェーズ分けして実施する。

1. 直近 artifact の記録ズレ・紛らわしい表現を修正する。
2. 過去ログから各 UI カテゴリの source を棚卸しする。
3. source が確保できるカテゴリだけ、同一 source で Route A と Route 0506 を生成して AB 比較する。
4. ユーザー比較用に本文だけを `C:\tetie\notecode\docs\新しいフォルダー` 配下へ配置する。

## Current State

- Route 0506 remains shadow-only.
- Route A replacement / adoption 判断はこの window では最終決定しない。
- ただし、今回の AB テストでは user 明示許可により、同一 source で Route A を新規生成してよい。
- URL refetch はしない。
- source は過去ログ artifact から拾う。
- source が過去ログから拾えないカテゴリは生成せず、どのカテゴリが missing か報告する。
- OPENAI_API_KEY environment 使用可。
- model は `gpt-5.4-mini`。
- reasoning effort は `high`。

## Important Correction From Prior Window

直近 window:

```text
artifact_root: C:\tetie\notecode\logs\route_0506_self_perspective_then_category_ab_test_20260510
decision: ready_for_user_category_ab_review
completed category: category_03_company_service_intro
```

確認済み:

- B本文は `私たち` の自己視点で統一。
- `同社`, `同サービス`, `同店`, `同院` は検出なし。
- wrapper / review leakage なし。
- QA pass=true / score=100 / issues=[]。
- focused pytest: 57 passed。

修正が必要な記録ズレ:

- `decision.md` では `api_send_count: 1`。
- `latest_generation_output.json` は `usage_summary.api_send=true`, `status=openai_generation_candidate`, `model=gpt-5.4-mini`, `reasoning_effort=high`。
- 一方で `usage_ledger.jsonl` / `api_usage_ledger.jsonl` には `status: not_sent` が残っている。
- 次 window では、実 API send count と usage ledger / validation summary の記録契約を確認し、必要なら narrow fix する。
- 実際に送信していないものを `api_send_count: 1` と書かない。
- 実際に送信したのに ledger が `not_sent` になる場合は、ledger 側の narrow bug として修正する。

紛らわしい表現:

- prior report の `fail-open` は誤解を招く。
- 実態は「editor が review/meta/third-party leakage を返したとき、bad output を採用せず previous article を返す guard」。
- 今後の artifact では `reject_to_previous_article`, `guard_rejected_bad_editor_output`, `previous_article_preserved` のように明確に書く。

## Phase 0: Read Order And Source Inventory

最初に読む:

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. `C:\tetie\notecode\docs\route_0506_instruction_window_migration_to_category_ab_test_2026-05-10.md`
5. `C:\tetie\notecode\logs\route_0506_self_perspective_then_category_ab_test_20260510\decision.md`
6. `C:\tetie\notecode\logs\route_0506_self_perspective_then_category_ab_test_20260510\category_generation_summary.json`
7. `C:\tetie\notecode\logs\route_0506_self_perspective_then_category_ab_test_20260510\category_ab_manifest.json`
8. `C:\tetie\notecode\logs\route_0506_self_perspective_then_category_ab_test_20260510\category_03_company_service_intro\validation_summary.json`
9. `C:\tetie\notecode\logs\route_0506_self_perspective_then_category_ab_test_20260510\category_03_company_service_intro\route_0506\latest_generation_output.json`
10. `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
11. `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
12. `C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py`

source inventory を作る:

```text
C:\tetie\notecode\logs\route_0506_category_ab_test_after_self_perspective_guard_20260510\source_inventory.json
C:\tetie\notecode\logs\route_0506_category_ab_test_after_self_perspective_guard_20260510\source_inventory.md
```

inventory では、各 UI カテゴリについて以下を記録する。

- category_id
- ui_label
- article_type
- semantic_article_key
- route_0506_genre_id
- source_artifact_path
- source_documents_count
- source_hash
- source_status: `usable | usable_after_contract_remap | missing | ambiguous`
- reason

現時点の事前把握:

```text
category_01_explanatory_article:
  likely usable:
    C:\tetie\notecode\logs\route_0506_same_source_three_variant_preflight_20260510\market_explanation\input_contract.json
    C:\tetie\notecode\logs\case003_generation_only_article_type_length_validation_20260504-201012\source_snapshot.json
  注意:
    2系統ある。Lee Japan 不動産ソースと case003 確認手順ソースを混ぜない。

category_02_daily_story:
  direct source artifact not confirmed.
  見つからなければ missing として生成しない。

category_03_company_service_intro:
  usable:
    C:\tetie\notecode\logs\route_0506_self_perspective_then_category_ab_test_20260510\category_03_company_service_intro\input_contract.json
    C:\tetie\notecode\logs\latest_generation_output.json

category_04_announcement:
  direct source artifact not confirmed.
  `_announcement_source_contract` の空 slot は source として扱わない。
  見つからなければ missing として生成しない。

category_05_case_study:
  direct case_study source artifact not confirmed.
  company/comparison source 内に `case.html` があっても、case_study として使えるかは source-fit で確認する。
  見つからなければ missing として生成しない。

category_06_industry_analysis:
  direct industry_analysis source artifact not confirmed.
  market_explanation / explanatory source の流用は `usable_after_contract_remap` とし、無理に生成しない。

category_07_comparative_review:
  likely usable:
    C:\tetie\notecode\logs\route_0506_same_source_three_variant_preflight_20260510\comparison_guide\input_contract.json
```

## Phase 1: Recording Contract Narrow Fix

目的:

- 実 API send count と artifact 記録のズレをなくす。
- `fail-open` などの紛らわしい表現を artifact / report から排除する。

許可:

- narrow product code fix は可。
- 対象は usage ledger / validation summary / report wording に限定する。
- stage output guard の挙動変更はしない。必要がある場合は別 owner にする。

禁止:

- prompt tuning
- persona sprawl
- repair loop 追加
- QA threshold relaxation
- repair_acceptance relaxation
- Route 0506 品質改善をこの phase に混ぜること

検証:

```powershell
py -3 -m py_compile note\route_0506_usage_ledger.py note\route_0506_structured_blog_result_adapter.py note\route_0506_structured_blog_adapter.py note\route_0506_stage_output_guard.py
py -3 -m pytest -q note\tests\test_route_0506_structured_blog_adapter.py note\tests\test_route_0506_ui_bridge.py note\tests\test_route_0506_saved_source_cli_validation.py
```

## Phase 2: Category AB Test

Phase 0 で `usable` または明確に妥当な `usable_after_contract_remap` になったカテゴリだけ実行する。

各カテゴリで以下を守る。

- A = Route A current mainline generation。
- B = Route 0506 shadow generation。
- A/B は同一 source_documents / same source hash。
- Route A fallback は使わない。
- URL refetch はしない。
- old rejected routes は使わない。
- raw full `source_documents` pass を「修正」として扱わない。ただし、過去ログ artifact に保存された source_documents を同一 source として使うのは可。
- model は `gpt-5.4-mini`。
- reasoning effort は `high`。
- 各カテゴリ A/B 1本ずつを基本とする。
- 失敗・blocked の retry は最大 1 回まで。retry する場合は理由と差分を artifact に残す。

API send budget:

```text
max_api_send = usable_categories * 2 + Phase1 validation if needed
```

API send count は実送信数だけを記録する。

## Output Placement

ユーザー比較用本文だけを配置する。

```text
C:\tetie\notecode\docs\新しいフォルダー\route_0506_category_ab_20260510\<category_id>\A_route_a_article.md
C:\tetie\notecode\docs\新しいフォルダー\route_0506_category_ab_20260510\<category_id>\B_route_0506_article.md
```

このフォルダには本文比較に不要な JSON / trace / logs を置かない。

詳細 artifact は以下へ保存する。

```text
C:\tetie\notecode\logs\route_0506_category_ab_test_after_self_perspective_guard_20260510\<category_id>\
```

カテゴリごとに保存する artifact:

- `input_contract.json`
- `source_snapshot.json`
- `source_hash_check.json`
- `route_a_latest_generation_output.json`
- `route_a_latest_generation_output.md`
- `route_a_quality_report.json`
- `route_0506_latest_generation_output.json`
- `route_0506_latest_generation_output.md`
- `route_0506_quality_report.json`
- `ab_compare_summary.json`
- `manual_japanese_naturalness_review.md`

全体 artifact:

- `source_inventory.json`
- `source_inventory.md`
- `recording_contract_fix_summary.md`
- `api_send_ledger_reconciliation.json`
- `category_ab_manifest.json`
- `category_ab_summary.json`
- `decision.md`

## Quality Review Criteria

文字数だけで勝敗を決めない。

カテゴリごとに見る:

- source-grounding
- category intent
- 日本語自然さ
- AI ぽさの少なさ
- self-perspective / viewpoint consistency
- third-party viewpoint leakage
- wrapper / review leakage
- 会社・サービス紹介では自己視点が自然か
- お知らせは `C:\tetie\notecode\0506` の設計どおり簡潔でよい
- explanatory / comparative は無理に 5 section fullness を要求しない
- max sentence length / sentence_too_long
- QA pass / score / issues

## Hard Boundaries

- Route 0506 remains shadow-only.
- この window で Route A replacement / adoption を最終決定しない。
- URL refetch false。
- Route A fallback false。
- old rejected routes false。
- threshold_relaxed false。
- repair_acceptance_relaxed false。
- prompt_bloat none を維持。
- module_bloat none を維持。必要な narrow fix だけ。
- source がないカテゴリを無理に生成しない。
- source が複数候補ある場合は、混ぜずに 1 source family を選び、hash を保存する。

## Closeout Decision

最後に以下のいずれかで closeout する。

```text
decision:
  ready_for_user_category_ab_review
  ready_for_route_0506_adoption_discussion
  needs_source_collection_for_missing_categories
  needs_recording_contract_owner
  needs_category_specific_owner
  continue_shadow
  blocked
  reject
```

## Required Final Report

```text
decision:
artifact_root:
user_comparison_folder:
local_reference_path: C:\tetie\notecode\0506
product_code_changed:
changed_files:
api_send_count:
model: gpt-5.4-mini
reasoning_effort: high
source_inventory_completed:
usable_categories:
missing_source_categories:
ambiguous_source_categories:
route_a_generated_categories:
route_0506_generated_categories:
same_source_hash_confirmed_categories:
recording_contract_fixed:
fail_open_wording_removed:
tests:
manual_japanese_naturalness_note:
codex_ab_quality_judgment:
next_one_owner:
route_a_regenerated: true/false per category
url_refetched: false
route_a_fallback_used: false
old_routes_reopened: false
raw_full_source_documents_passed_as_fix: false
threshold_relaxed: false
repair_acceptance_relaxed: false
prompt_bloat: none | found
module_bloat: none | found
AGENTS_update_needed:
WORKLOG_update_needed:
```

## Notes For The Work Window

- `Route A regenerated` は今回だけ user 明示許可により、同一 source AB の A 側生成として許可される。
- ただし Route A を fallback として使うこと、Route 0506 の失敗を Route A で埋めることは禁止。
- source が見つからないカテゴリがあれば、生成せず `missing_source_categories` に入れて報告する。
- 以前の `api_send_count` と ledger のズレは、AB の前に解消または明確化する。
- 「fail-open」は以後使わず、実挙動に合わせて「bad editor output rejected / previous article preserved」と記録する。
