# Route 0506 stage parity audit 報告 2026-05-10

この文書は指示ウインドウへの報告用です。  
Route A current mainline は immutable のまま、Route 0506 は shadow-only のままです。

## 結論

- decision: `needs_next_owner`
- owner: `route_0506_native_vs_notecode_same_source_stage_parity_audit`
- first_divergence: `article_brief`
- next_one_owner: `route_0506_article_brief_payload_parity_fix`

今回の audit では、company_service_intro 1 case に限定して、`C:\tetie\notecode\0506` native direct と notecode Route 0506 adapter を同一 saved source 条件で比較した。

source input / source packet 本文は実質同一だった。  
最初の品質劣化につながる route-handling 差分は、adapter 側の `article_brief` normalization / postprocess である。

## Artifact

- artifact_root:
  - `C:\tetie\notecode\logs\route_0506_native_vs_notecode_same_source_stage_parity_audit_20260510\`
- key files:
  - `decision.md`
  - `first_divergence.md`
  - `source_input_compare.json`
  - `source_packets_compare.json`
  - `article_brief_compare.json`
  - `stage_length_compare.json`
  - `final_quality_compare.json`
  - `absolute_reference_scan.txt`

## 実施範囲

- 比較対象: `company_service_intro` only
- native_0506_direct:
  - `C:\tetie\notecode\0506` の `BlogPipelineRunner.run_extracted_sources(...)` を直接実行
  - URL refetch なし
  - saved Route A source_documents 由来の同一 selected source records を使用
- notecode_route_0506_adapter:
  - `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py` 経由で実行
  - 直近 same-source validation の company_service_intro input_contract を使用

## API 実行

- api_send_count: `3`
- native_0506_api_send_count: `2`
- notecode_route_0506_api_send_count: `1`
- model: `gpt-5.4-mini`
- reasoning_effort: `high`

補足:

- 初回 native run で audit harness の `target_reader / article_goal` が adapter と完全一致していなかったため、native direct のみ 1 回取り直した。
- 比較判断に使う最終条件は、native direct と adapter の `target_reader` を同一にした run。
- fallback 生成、Route A fallback、URL refetch はしていない。

## Stage Findings

### source input

- source_snapshot_same: `true`
- raw_full_source_documents_passed: `false`
- selected_source_count: `5`
- selected_total_chars: `2072`
- source titles / locators / source types / span IDs / content hashes: same

判断:

- 今回の compact 化は source selected text の違いでは説明しない。

### source packets

- source_packets_same: `content_same_metadata_diff`
- native / adapter とも:
  - count: `5`
  - chunk_text_chars: `2072`

差分:

- `retrieved_at`
- `extraction_method`
  - native: `native_direct_saved_source_no_refetch`
  - adapter: `notecode_company_intro_saved_source_surface_v1`

判断:

- source_id / title / chunk text / source locations は同一。
- metadata 差は記録するが、compact output の first owner にはしない。

### article brief

first confirmed route-handling gap:

| field | native_0506_direct | notecode_route_0506_adapter |
| --- | --- | --- |
| target_length_chars | `3000` | `1800` |
| section_count | `5` | `3` |
| section_actual_count | `5` | `3` |
| assigned_claim_count | `15` | `13` |
| max_claims_in_one_section | `5` | `8` |

native headings:

- 東大阪市で不動産売買・売却を考える方へ
- 初めての売却で気になる流れ
- 仲介売却・買取・買取保証の違い
- 他社で難しかった物件も相談できます
- 一括査定代行とリフォーム提案

adapter headings:

- 東大阪市で初めて売却を考える方へ
- 売却相談から査定書提出までの流れ
- 仲介売却で進める場合

判断:

- adapter 側で native 0506 の fuller planning が `1800 / 3 sections` に縮む。
- compact output は `draft_writer` 前に始まっている。
- 次 owner は draft prompt ではなく `article_brief` payload parity。

## Final Quality

- native direct final:
  - QA red
  - issue: `sentence_too_long`
  - final chars: compact after rewrite
- adapter final:
  - QA red
  - issue: `first_person_inconsistency`
  - final chars: compact

manual note:

- native direct final も採用品質ではない。
- ただし native の article_brief planning は adapter より明確に fuller。
- 今回は adoption 判断ではなく、差分発生 stage の特定が目的。

## Desktop Reference Scan

- desktop_absolute_reference_required: `false`
- desktop_reference_runtime_dependency_found: `false`

scan hits:

- `README.md` の一般語 `Users`
- PDF trial summary artifact 内の旧 `C:\Users\横山裕明\Desktop\0506` provenance

判断:

- runtime / docs / tests の Desktop absolute dependency ではない。
- artifact provenance として扱う。

## Guardrails

- product_code_changed: `false`
- route_a_regenerated: `false`
- url_refetched: `false`
- route_a_fallback_used: `false`
- old_routes_reopened: `false`
- threshold_relaxed: `false`
- repair_acceptance_relaxed: `false`
- prompt_bloat: `none`
- module_bloat: `none`

Changed files:

- `C:\tetie\notecode\logs\route_0506_native_vs_notecode_same_source_stage_parity_audit_20260510\run_stage_parity_audit.py`
- this report file

Validation:

- `py_compile` passed for artifact script
- product tests not run because product code was not changed

## 次に切るべき作業ウインドウ

one owner:

- `route_0506_article_brief_payload_parity_fix`

目的:

- notecode adapter が native 0506 の `article_brief` planning をどこで `3000 / 5 sections` から `1800 / 3 sections` へ縮めているかを 1 owner で修正する。
- source input / source packet は reopen しない。

禁止:

- Route A adoption / replacement 判断
- Route A regeneration
- URL refetch
- raw full source_documents pass を成功扱いにすること
- prompt tuning
- persona 追加
- repair loop 追加
- QA threshold relaxation
- repair_acceptance relaxation

## AGENTS / WORKLOG

- AGENTS_update_needed: `False`
- WORKLOG_update_needed: `False`

