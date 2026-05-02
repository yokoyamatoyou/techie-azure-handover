# separate window execution prompt source log pattern rerun audit 2026-04-21

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md

今回の依頼種別:
- separate window execution prompt
- `SOURCE_LOG_PATTERN_RERUN_AUDIT`
- ログに残っている source URL / source_documents を元に、source handoff 修正後の横断確認を行う
- 各パターンは 1 回ずつだけ実行する
- 失敗した場合も同じケースを再試行して隠さず、原因分類を記録する

今回の目的:
- 今回修正した URL-only source handoff が company introduction だけでなく、非お知らせ系の記事タイプでも効いているか確認する
- 薄いソースを LLM が補強して長文化する経路が残っていないか確認する
- 本当にソースが足りない場合、または fetch できない場合に `INP_SOURCE_CONTEXT_INSUFFICIENT` 相当で止まるか確認する
- 「お知らせ」は短いソースでも自然なケースがあるため、source_substance の文字量 gate で不自然に止めない
- ログで拾えるソースを可能な限り拾い、会社紹介 / 商品紹介 / 説明記事 / 比較 / 事例 / お知らせ / 薄い placeholder のパターンを1回ずつ出す

今回の前提:
- 直前の修正で以下が入っている前提で確認する
  - `C:\tetie\notecode\note\current_mainline_runner.py`
    - `_resolve_current_mainline_contract_for_ui()` が resolve 前に `_hydrate_grounded_url_source_documents()` を呼ぶ
    - explicit topic があっても source context required の場合は不足を bypass しない
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
    - company introduction の source_substance gate
    - product / activity / recruit / case / comparative の route_source_substance gate
    - announcement は source_substance gate から除外
- 既存の成功経路は維持する
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

このウインドウで最初に読む証跡:
- C:\tetie\notecode\logs\latest_generation_output.json
- C:\tetie\notecode\logs\latest_generation_quality_report.json
- C:\tetie\notecode\logs\generation_audit_log.jsonl
- C:\tetie\notecode\logs\published_post_inventory.jsonl
- C:\tetie\notecode\logs\contract_root_audit_rerun_20260421.json
- C:\tetie\notecode\logs\attempt01_company_intro_replay.json
- C:\tetie\notecode\logs\attempt02_company_intro_replay.json
- C:\tetie\notecode\logs\attempt03_company_intro_replay.json
- C:\tetie\notecode\logs\attempt04_company_intro_replay.json
- C:\tetie\notecode\logs\attempt05_company_intro_replay.json
- C:\tetie\notecode\logs\attempt06_company_intro_replay.json
- C:\tetie\notecode\logs\codex_phase01_rerun_result_2026-04-07.json
- C:\tetie\notecode\logs\current_mainline_ui_all_genres_long_suite_latest.json
- C:\tetie\notecode\logs\current_mainline_ui_manual_long_probe_latest.json
- C:\tetie\notecode\logs\current_mainline_ui_manual_long_probe_alt_latest.json
- C:\tetie\notecode\logs\current_mainline_ui_manual_long_probe_ui_types_latest.json
- C:\tetie\notecode\logs\current_mainline_ui_long_matrix_latest.json
- C:\tetie\notecode\logs\current_mainline_ui_long_matrix_comparative_fragment_slice_20260320-234424.json
- C:\tetie\notecode\logs\prompt_only_probe_2026-04-03_same_source.json
- C:\tetie\notecode\logs\app.log

このウインドウで読むべきコード:
- primary:
  - C:\tetie\notecode\note\current_mainline_runner.py
  - C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - C:\tetie\notecode\note\tests\test_current_mainline_runner.py
  - C:\tetie\notecode\note\tests\test_newalgorithm_phase01_contract.py
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
- secondary if needed:
  - C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py
  - C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py

今回の禁止:
- output_guard.py の閾値変更
- strict_saas_mode の変更
- quality guard first
- repair prompt / acceptance の symptom patch first
- 薄いソースを LLM に補強させて長文化する方向の修正
- announcement を source_substance 文字量 gate に巻き込む修正
- article_type 固定ルーティング table の追加
- unrelated cleanup
- AGENTS / WORKLOG / plan docs 更新
- 同一ケースのリトライで結果を良く見せること

今回のテスト方針:
- ログから source URL / source_documents を拾い、可能な限り実ログ由来の payload で再現する
- URL が生きている場合は URL-only 入力で hydrate 経路を通す
- fixture URL や外部 fetch 不能 URL は、ログ内 source_documents を復元して contract / pipeline に渡す
- 1ケースにつき generation / contract resolve は1回だけ
- 失敗時も再試行せず、以下に分類する
  - fetch_failure
  - source_substance_insufficient
  - source_handoff_drop
  - output_quality_guard
  - route_selection_mismatch
  - expected_announcement_short_source
  - unrelated_runtime_error

ログ由来ソース候補:
- Kyoto company intro rich official source
  - logs:
    - `latest_generation_output.json`
    - `contract_root_audit_rerun_20260421.json`
    - `published_post_inventory.jsonl`
  - URLs:
    - https://www.kyotokogyo.co.jp/
    - https://www.kyotokogyo.co.jp/about/coprof/
    - https://www.kyotokogyo.co.jp/about/history/
    - https://www.kyotokogyo.co.jp/strength/
    - https://www.kyotokogyo.co.jp/service/input_scaning/
    - 必要なら https://www.kyotokogyo.co.jp/service/rpa/
- Yoshino company intro law-office source
  - logs:
    - `attempt01_company_intro_replay.json` through `attempt06_company_intro_replay.json`
  - URLs:
    - https://yoshinomore-law.jp/
    - https://yoshinomore-law.jp/company/
    - https://yoshinomore-law.jp/service/
    - https://yoshinomore-law.jp/arrangements/
- AINOW explanatory article source
  - logs:
    - `codex_phase01_rerun_result_2026-04-07.json`
  - URL:
    - https://ainow.ai/2026/04/06/277888/
- Kankeiren PDF explanatory source
  - logs:
    - `prompt_only_probe_2026-04-03_same_source.json`
    - `prompt_only_probe_2026-04-03_same_source_force_accept.json`
  - URL:
    - https://www.kankeiren.or.jp/material/260403release.pdf
- Fixture company / announcement / case / comparative sources
  - logs:
    - `current_mainline_ui_all_genres_long_suite_latest.json`
    - `current_mainline_ui_manual_long_probe_latest.json`
    - `current_mainline_ui_manual_long_probe_alt_latest.json`
    - `current_mainline_ui_manual_long_probe_ui_types_latest.json`
    - `current_mainline_ui_long_matrix_latest.json`
    - `current_mainline_ui_long_matrix_comparative_fragment_slice_20260320-234424.json`
  - URLs:
    - https://fixture.techie/branding/company-profile
    - https://fixture.techie/branding/support-policy
    - https://fixture.techie/branding/compliance-company-profile
    - https://fixture.techie/branding/compliance-support-policy
    - https://fixture.techie/announcement/sso-change
    - https://fixture.techie/announcement/sso-change-faq
    - https://fixture.techie/case-study/onboarding-funnel-audit
    - https://fixture.techie/case-study/onboarding-funnel-playbook
    - https://fixture.techie/case-study/monthly-report-handoff-audit
    - https://fixture.techie/case-study/monthly-report-handoff-playbook
    - https://fixture.techie/compare/knowledge-share-a
    - https://fixture.techie/compare/knowledge-share-b
    - https://fixture.techie/compare/knowledge-share-c
    - https://fixture.techie/compare/supportdesk-a
    - https://fixture.techie/compare/supportdesk-b
    - https://fixture.techie/compare/supportdesk-c
- Thin / placeholder regression source
  - logs:
    - `latest_generation_output.json`
    - `contract_root_audit_rerun_20260421.json`
  - symptom:
    - `source_documents` が `Compatibility Source 1..` になり、content が `自社の全体像を紹介する` 程度になる
  - expected:
    - 現行修正後は、URL-only から実本文 hydrate される
    - 実本文 fetch 不能や placeholder only の場合は、LLM 補強ではなく source insufficient で止める

実行ケース:
1. `company_intro_kyoto_url_only_rich`
   - route: `branding` / `company_introduction`
   - source_mode: `grounded`
   - source_inputs: Kyoto の URL 5件
   - expected:
     - `source_documents` が `Compatibility Source` ではない
     - `source_grounding_required = true`
     - `source_grounding_status = resolved`
     - `source_grounding_items >= 2`
     - `source_fit.status != block`
     - 1885年創業 / データ入力 / 強み / 沿革のいずれかが source facts に入る
2. `company_intro_yoshino_url_or_log_docs`
   - route: `branding` / `company_introduction`
   - source_inputs: Yoshino の URL 4件、fetch 不能なら replay JSON の source_documents
   - expected:
     - 2022年開所 / 月額5万円 / 予防法務 / 事業承継・世代交代のいずれかが source facts に入る
     - source_substance 不足で不当に止まらない
3. `product_intro_kyoto_service_url_only`
   - route: `branding` / `product_introduction`
   - source_inputs:
     - https://www.kyotokogyo.co.jp/service/input_scaning/
     - https://www.kyotokogyo.co.jp/service/rpa/
   - expected:
     - service / product facts が抽出される
     - `source_substance` が pass
     - company history だけで商品紹介を埋めない
4. `explanatory_ainow_single_article`
   - route: `explanatory_article`
   - source_inputs: AINOW URL 1件、fetch 不能なら log source_documents
   - expected:
     - 生成AI ROI / 5入力 / Dataiku 85% など source-backed facts が残る
     - source を薄い一般論に置き換えない
5. `explanatory_kankeiren_pdf`
   - route: `explanatory_article`
   - source_inputs: Kankeiren PDF URL 1件、PDF fetch/extract 不能なら log source_documents
   - expected:
     - PDF source の取得可否を明記
     - extract 不能なら fetch_failure または source_substance_insufficient として止める
     - LLM が PDF 内容を想像で補わない
6. `comparative_fixture_knowledge_share`
   - route: `comparative_review`
   - source_inputs or source_documents:
     - https://fixture.techie/compare/knowledge-share-a
     - https://fixture.techie/compare/knowledge-share-b
     - https://fixture.techie/compare/knowledge-share-c
   - comparison_axes:
     - 価格
     - 初期設定
     - 用途
   - expected:
     - 比較対象の差分 fact が2件以上ない場合は `source_substance` block
     - ある場合は差分が source-backed になる
7. `comparative_fixture_supportdesk`
   - route: `comparative_review`
   - source_inputs or source_documents:
     - https://fixture.techie/compare/supportdesk-a
     - https://fixture.techie/compare/supportdesk-b
     - https://fixture.techie/compare/supportdesk-c
   - comparison_axes:
     - 承認フロー
     - サポート密度
   - expected:
     - case 6 と同様。比較記事の薄いソースが warning だけで通らない
8. `case_study_fixture_onboarding`
   - route: `case_study` or `implementation_case`
   - source_inputs or source_documents:
     - https://fixture.techie/case-study/onboarding-funnel-audit
     - https://fixture.techie/case-study/onboarding-funnel-playbook
   - expected:
     - 導入前 / 進め方 / 変化 の fact が source-backed になる
     - 具体 fact 不足なら `source_substance` block
9. `case_study_fixture_monthly_report`
   - route: `case_study` or `improvement_case`
   - source_inputs or source_documents:
     - https://fixture.techie/case-study/monthly-report-handoff-audit
     - https://fixture.techie/case-study/monthly-report-handoff-playbook
   - expected:
     - 改善前後 / 引き継ぎ / レポート運用の fact が source-backed になる
10. `announcement_fixture_sso`
   - route: `announcement`
   - source_inputs or source_documents:
     - https://fixture.techie/announcement/sso-change
     - https://fixture.techie/announcement/sso-change-faq
   - expected:
     - 短いソースでも source_substance gate で止めない
     - 日時 / 対象 / 変更内容 / 行動 が不足する場合は announcement-specific の不足として扱う
     - 無理に本文を長くしない
11. `thin_placeholder_regression`
   - route: `branding` / `company_introduction`
   - source_documents:
     - title: `Compatibility Source 1`
       content: `自社の全体像を紹介する`
       locator: `compat://source/1`
   - expected:
     - `source_fit.status = block`
     - `source_fit.missing_buckets` に `source_substance`
     - `input_decision.reason_code = INP_SOURCE_CONTEXT_INSUFFICIENT`
     - LLM 補強で本文生成へ進めない

各ケースで記録する telemetry:
- case_id
- source origin log path
- route / semantic_article_key
- source_mode
- source_inputs count
- source_documents count
- source document locator list
- source document title list
- source document char counts
- `compatibility_bridge.grounded_source_fetch_hydrated`
- `compatibility_bridge.grounded_source_fetch_count`
- `compatibility_bridge.grounded_source_fetch_failures`
- `source_grounding_required`
- `source_grounding_status`
- `source_grounding_items count`
- `source_fit.status`
- `source_fit.missing_buckets`
- `source_fit.required_actions`
- `input_decision.action`
- `input_decision.reason_code`
- if generation executed:
  - attempt_id
  - runtime_reason_code
  - output_guard.blocked
  - output_guard reasons
  - source_trace_coverage
  - must_cover_reflection_rate
  - source_grounding_reflection_ratio
  - body chars
  - whether output stayed within source facts

実行時の注意:
- まず contract resolve / confirm preview 相当で source handoff を見る
- source insufficient で止まるのが expected のケースは generation まで進めない
- pass したケースだけ generation を1回行う
- generation が output_quality_guard で止まっても、source handoff が pass していれば別系統として分類する
- 文字数不足を理由に薄いソースを膨らませない
- announcement の短さは異常扱いしない
- fixture URL が外部 fetch できない場合、ログの source_documents を優先して再構成する
- ログから復元できない fixture は skip ではなく `source_reconstruction_failed` として記録する

成果物:
- C:\tetie\notecode\logs\source_log_pattern_rerun_audit_20260421.json
- C:\tetie\notecode\logs\source_log_pattern_rerun_audit_20260421.md

成果物 JSON の最低構造:
{
  "timestamp": "...",
  "case_results": [
    {
      "case_id": "...",
      "status": "pass|expected_block|unexpected_block|unexpected_pass|runtime_error|source_reconstruction_failed",
      "classification": "...",
      "source_origin_logs": [],
      "telemetry": {},
      "notes": []
    }
  ],
  "summary": {
    "total": 0,
    "pass": 0,
    "expected_block": 0,
    "unexpected_block": 0,
    "unexpected_pass": 0,
    "runtime_error": 0,
    "source_reconstruction_failed": 0
  }
}

事前チェック:
- C:\tetie\notecode\.venv\Scripts\python.exe が使えるならそれを使う
- 使えない場合は `py -3` を使う
- 最初に以下を実行して現行修正が壊れていないことを確認する
  - `py -3 -m pytest note\tests\test_current_mainline_runner.py -q`
  - `py -3 -m pytest note\tests\test_newalgorithm_phase01_contract.py note\tests\test_simple_note_pipeline.py -q`

必要に応じた focused checks:
- `py -3 -m pytest note\tests\test_current_mainline_runner.py -k "source or company_intro or product_intro" -q`
- `py -3 -m pytest note\tests\test_newalgorithm_phase01_contract.py -k "source_substance or announcement or comparative or product or company_intro" -q`

pass 条件:
- URL-only の company/product 系で、`Compatibility Source` への後退が起きない
- 非お知らせ系で薄い source が generation へ進まず source insufficient で止まる
- 比較記事で差分 source が薄い場合に warning だけで通らない
- case 系で具体 fact 不足が source_substance として検出される
- announcement は短い source を理由に source_substance block しない
- source handoff pass 後に output_quality_guard で止まる場合は、source 問題と別分類できる

stop conditions:
- source handoff の確認ではなく output_guard 閾値変更しか残らない
- 同じケースを再試行しないと判断できない
- ログ source 復元に失敗し、推測 payload しか作れない
- 修正が必要になり allowed scope を超える
- source insufficient を LLM 補強で回避する実装が必要になる

allowed touched files:
- 原則として成果物ログのみ
  - C:\tetie\notecode\logs\source_log_pattern_rerun_audit_20260421.json
  - C:\tetie\notecode\logs\source_log_pattern_rerun_audit_20260421.md
- 明確なバグが見つかり、最小修正が必要な場合のみ:
  - C:\tetie\notecode\note\current_mainline_runner.py
  - C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
  - C:\tetie\notecode\note\tests\test_current_mainline_runner.py
  - C:\tetie\notecode\note\tests\test_newalgorithm_phase01_contract.py

do-not-touch unless explicitly necessary:
- C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\plan\...
- C:\tetie\AGENTS.md
- C:\tetie\WORKLOG.md

最終報告フォーマット:
1. 読んだ正本 / 証跡 / コード
2. 抽出できたログ由来 source set
3. 実行した case_id 一覧
4. 各ケースの結果
   - pass / expected_block / unexpected_block / unexpected_pass / runtime_error
   - source handoff telemetry
   - source_substance 判定
   - generation まで進んだか
5. source handoff 修正が company introduction 以外にも効いたか
6. 薄いソースが LLM 補強で通る経路が残っているか
7. announcement が不自然に止まっていないか
8. 残るエラー要因
   - source 系
   - fetch 系
   - output quality 系
   - route selection 系
9. 追加修正が必要か
10. 成果物パス
```
