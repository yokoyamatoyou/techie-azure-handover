# Route 0506 openai article_brief target / claim volume parity 報告 2026-05-10

この文書は指示ウインドウへの報告用です。  
Route A current mainline は immutable のまま、Route 0506 は shadow-only のままです。

## 結論

- decision: `fixed_continue_shadow`
- owner: `route_0506_openai_article_brief_target_and_claim_volume_parity`
- artifact_root: `C:\tetie\notecode\logs\route_0506_openai_article_brief_target_and_claim_volume_parity_20260510\`
- accepted_attempt: `attempt_04`
- next_one_owner: `route_0506_draft_writer_target_length_adherence_if_full_3000_char_parity_is_required`

今回の owner では、OpenAI article_brief の `target_length_chars` と claim volume の parity gap は改善した。  
ただし visible body fullness は native 0506 reference 相当までは届いていないため、Route 0506 adoption / Route A replacement 判断には進まない。

## 実施範囲

- 対象: `company_service_intro` only
- 修正対象: adapter-side article_brief metadata normalization
- product code changed: `true`
- API send count: `4`
- attempts_used: `4`
- attempts_rolled_back: `[1, 2, 3]`
- accepted attempt: `attempt_04`

## 修正内容

変更ファイル:

- `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
- `C:\tetie\notecode\note\tests\test_route_0506_structured_blog_adapter.py`
- `C:\tetie\WORKLOG.md`

主な変更:

- thick `company_service_intro` の target / section floor を native reference 相当の `3000 / 5` へ寄せた。
- `source_thickness=medium` でも、5 sections / target >= 1800 / 10 claims 以上の claim-rich brief は fullness normalization 対象にした。
- 既存 schema field だけを使い、`style_rules` / section `discourse_rules` に fullness handoff metadata を追加した。
- attempt 03 で出た `connector_repetition` に対して、接続詞「また」に頼りすぎない最小 guard を `style_rules` に追加した。
- claim IDs は増減させず、existing OpenAI output の claim allocation を保存・正規化した。

## Attempts

### attempt_01

- hypothesis: thick company_service_intro floor を `3000 / 5` に戻す。
- result:
  - target: `3000`
  - section_count: `5`
  - assigned_claim_count: `16`
  - body_char_count: `1345`
  - QA: `pass=true / score=100`
- judgment: rollback
- reason: body length が previous reference `1478` より悪化。

### attempt_02

- hypothesis: target number だけでは弱いため、section-volume metadata を足す。
- result:
  - target: `2800`
  - section_count: `5`
  - assigned_claim_count: `18`
  - body_char_count: `1414`
  - QA: `pass=true / score=100`
- judgment: rollback
- reason: body length が previous reference `1478` より悪化。visible output 冒頭に editor-wrapper 風の読者不要文も混入。

### attempt_03

- hypothesis: medium / 5 sections / claim-rich brief も fullness normalization 対象にする。
- result:
  - target: `3000`
  - section_count: `5`
  - assigned_claim_count: `14`
  - body_char_count: `1967`
  - QA: `pass=false / score=92`
  - issue: `connector_repetition`
- judgment: rollback
- reason: body fullness は改善したが QA が悪化。

### attempt_04

- hypothesis: attempt 03 の fullness 改善を維持し、connector repetition だけを最小 guard で抑える。
- result:
  - target: `3000`
  - section_count: `5`
  - assigned_claim_count: `21`
  - max_claims_in_one_section: `7`
  - body_char_count: `1683`
  - QA: `pass=true / score=100 / issues=[]`
- judgment: accepted

## Accepted Result

前回 post-brief-parity validation:

- target: `1800`
- section_count: `5`
- assigned_claim_count: `11`
- body_char_count: `1478`
- QA: `pass=true / score=100 / issues=[]`

accepted attempt:

- target: `3000`
- section_count: `5`
- assigned_claim_count: `21`
- max_claims_in_one_section: `7`
- body_char_count: `1683`
- QA: `pass=true / score=100 / issues=[]`

判断:

- article_brief target parity: fixed
- section count parity: fixed
- claim volume parity: improved / fixed for this owner
- visible fullness: improved but incomplete
- adoption readiness: not decided

## Manual Japanese Naturalness Note

accepted attempt の本文は QA green で、日本語として読める。  
一人称は「私たち」で安定し、会社・サービス紹介としての焦点も維持している。  
source-grounding も保存済み source surface 内に収まっている。

ただし、target `3000` に対して final body は `1683 chars` であり、native 0506 reference 相当の fullness には届き切っていない。  
AB test に進めるかどうかは、visible body fullness をどこまで要求するかの判断が必要。

## Guardrails

- route_a_regenerated: `false`
- url_refetched: `false`
- route_a_fallback_used: `false`
- old_routes_reopened: `false`
- raw_full_source_documents_passed: `false`
- threshold_relaxed: `false`
- repair_acceptance_relaxed: `false`
- prompt_bloat: `none`
- module_bloat: `existing adapter remains large; no new module and no broad refactor in this owner`

## Verification

- `py -3 -m py_compile note\route_0506_structured_blog_adapter.py note\route_0506_ui_bridge.py note\route_0506_stage_output_guard.py note\route_0506_security_gate.py note\route_0506_usage_ledger.py`: pass
- `py -3 -m pytest note\tests\test_route_0506_structured_blog_adapter.py note\tests\test_route_0506_ui_bridge.py note\tests\test_route_0506_saved_source_cli_validation.py -q`: `51 passed`

## 次に切るべき作業ウインドウ

one owner:

```text
route_0506_draft_writer_target_length_adherence_if_full_3000_char_parity_is_required
```

目的:

- article_brief が `3000 / 5 / claim-rich` になっても final visible body が `1683 chars` に留まる理由を、draft_writer payload / draft_writer output / editor shortening のどこで起きるかに限定して精査する。
- 今回 fixed になった article_brief target / claim volume parity は reopen しない。

禁止:

- Route A adoption / replacement 判断
- Route A regeneration
- URL refetch
- Route A fallback
- old rejected routes reopen
- raw full `source_documents` pass
- prompt/persona broad tuning
- new repair loop
- QA threshold relaxation
- `repair_acceptance` relaxation

## AGENTS / WORKLOG

- AGENTS_update_needed: `false`
- WORKLOG_update_needed: `false`

