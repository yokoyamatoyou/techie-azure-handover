# Route 0506 作業ウインドウ結果報告 2026-05-09

この文書は指示用ウインドウへの報告用です。  
Route A current mainline は immutable のまま、Route 0506 は shadow-only のままです。

## 結論

- post-guard AB test decision: `reject`
- Route 0506 は Desktop 0506 の core pipeline を呼んでいるが、end-to-end の生成 surface は同一ではない
- 現時点の primary bottleneck hypothesis: `source_surface_parity_gap`
- 次に続ける場合の one owner: Route 0506 source-surface parity check のみ

## この作業ウインドウで実施したこと

1. post-guard AB test の結果を確認
2. 古い non-Route-0506 / non-Route-A 記録を archive
3. `C:\Users\横山裕明\Desktop\0506` と notecode Route 0506 の生成方法差分を確認
4. 結果を logs / WORKLOG に記録

## AB Test Result

Artifact root:

- `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\`

Summary:

- decision: `reject`
- article_types_attempted: `company_introduction`
- runs_completed: 3
- api_send_count: 3
- model: `gpt-5.4-mini`
- reasoning_effort: `high`
- source_snapshot_hash: `fd11521c0200f82a3ce77dcda89c4296d55f40f8bb03247e2df07d2ffab0ae80`
- Route A regenerated: false
- URL refetched: false
- Route A fallback used: false
- threshold relaxed: false
- repair_acceptance relaxed: false
- product code changed: false

Run results:

| run | body chars | quality | issue | judgement |
| --- | ---: | --- | --- | --- |
| run_01 | 1223 | fail / 92 | `model_frequent_word` | Route A better |
| run_02 | 1886 | fail / 92 | `model_frequent_word` | tie |
| run_03 | 1300 | fail / 92 | `first_person_inconsistency` | Route A better |

Winner distribution:

- Route A better: 2
- tie: 1
- Route 0506 better: 0
- blocked: 0

Manual note:

- visible-output wrapper / fenced article block leakage は再発していない
- source-faithfulness は 3 runs とも pass
- ただし全 candidate が QA-red
- recurring `model_frequent_word` と narrator consistency が残っており、Route A より安定しているとは言えない

## Archive Result

Archive root:

- `C:\tetie\notecode\archive\non_0506_route_records_20260509\`

Manifest:

- `C:\tetie\notecode\archive\non_0506_route_records_20260509\MANIFEST.json`

Result:

- moved_count: 48
- moved scope: old deepresearch / Route B / Route B2 / Route D / Route E / shadow_autonomous logs and docs
- remaining old non-0506 route records in active `logs` / `docs`: none found
- deletion: none

## Desktop 0506 Method Check

Artifact root:

- `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\`

Files:

- `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\README.md`
- `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\method_check_summary.json`

Finding:

- notecode Route 0506 imports `C:\Users\横山裕明\Desktop\0506`
- notecode Route 0506 calls `BlogPipelineRunner.run_extracted_sources(...)`
- Desktop 0506 runtime sequence:
  - extracted sources
  - source cards
  - article knowledge pack
  - article brief
  - draft writer
  - opening editor
  - global consistency editor
  - style editor
  - structural editor
  - Japanese quality checker
  - targeted rewriter
  - final quality check
- model / reasoning are aligned with Desktop OpenAI mode:
  - `gpt-5.4-mini`
  - `high`

Therefore:

- same core engine: yes
- same end-to-end generation surface: no

## Bottleneck Hypothesis

Primary:

- `source_surface_parity_gap`

Reason:

- Route 0506 reaches the Desktop 0506 pipeline, so the main issue is not model selection or missing Desktop stage order
- notecode adapter hands over compact typed source records instead of Desktop 0506's richer native extracted-source / source-card / knowledge-pack surface
- post-guard AB test source snapshot was only:
  - `notecode_typed_contract:company_introduction_script_packet`: 319 chars
  - `notecode_typed_contract:company_introduction_source_contract`: 524 chars
  - `notecode_typed_contract:source_grounding_items`: 524 chars
- Desktop 0506 good company-introduction artifacts under `C:\Users\横山裕明\Desktop\0506\artifacts\GPT5.4mini\` are around 2.5k to 3.0k bytes and appear to benefit from the richer source-card / knowledge-pack surface

Secondary symptoms:

- recurring `model_frequent_word`
- narrator consistency failure
- compact / generic article shape

Interpretation:

- These secondary issues are likely downstream symptoms of the thin source handoff
- Do not start with broad prompt tuning, extra repair loops, threshold relaxation, or repair_acceptance relaxation

## Current Status

- Route A: frozen / preserved
- Route 0506: shadow-only, not adopted
- post-guard AB test: `reject`
- Desktop 0506 parity: core engine same, generation surface not same
- archive cleanup: completed
- product code changed in this window: false
- AGENTS changed in this window: false
- WORKLOG updated: true

## Do Not Reopen

- Route A generation / replacement / adoption decision
- URL refetch
- Route A fallback
- `sentence_too_long`
- visible-output shape guard
- thresholds
- `repair_acceptance`
- broad prompt tuning
- new repair loop
- old Route B / Route D / Route E / deepresearch routes

## Recommended Next Work Window

One owner only:

- Route 0506 source-surface parity check

Allowed next check:

- Compare Desktop 0506 behavior when fed the same thin Route 0506 source snapshot versus its native richer source flow
- Or feed notecode Route 0506 a saved Desktop-like source card / knowledge-pack artifact and compare output shape

Stop condition:

- If source-surface parity does not improve compactness / repetition / narrator stability, stop and report with artifact evidence
- Do not convert this into prompt tuning or acceptance relaxation

## Report Pointers

- AB test summary:
  - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\compare_summary.json`
  - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\manual_review.md`
- method check:
  - `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\README.md`
  - `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\method_check_summary.json`
- archive:
  - `C:\tetie\notecode\archive\non_0506_route_records_20260509\MANIFEST.json`
- current handoff:
  - `C:\tetie\WORKLOG.md`
