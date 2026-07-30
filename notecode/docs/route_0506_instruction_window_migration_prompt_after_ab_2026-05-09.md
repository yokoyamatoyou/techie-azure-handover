# Route 0506 Instruction Window Migration Prompt After AB 2026-05-09

あなたは `C:\tetie\notecode` の Route 0506 / Route A 比較を管理する新しい指示ウインドウです。実作業ウインドウではありません。状態確認、境界管理、次ウインドウ prompt 作成、完了報告の受け取りを担当してください。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. Current result report:
   - `C:\tetie\notecode\docs\route_0506_work_window_result_report_to_instruction_window_2026-05-09.md`
5. Latest AB / method / archive artifacts:
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\compare_summary.json`
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\manual_review.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\README.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\method_check_summary.json`
   - `C:\tetie\notecode\archive\non_0506_route_records_20260509\MANIFEST.json`
6. Prior closeout artifacts, only as needed:
   - `C:\tetie\notecode\logs\route_0506_visible_output_shape_guard_20260509\fix_attempt_01\code_diff_summary.md`
   - `C:\tetie\notecode\logs\route_0506_fullness_article_brief_20260509\diagnosis.md`
   - `C:\tetie\notecode\logs\route_0506_fullness_article_brief_20260509\stage_compare.json`
7. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`

## Current Status

- Route A current mainline: frozen / immutable
- Route 0506: shadow-only
- post-guard AB test decision: `reject`
- Route A replacement / adoption judgment: not made
- product code changed in latest report window: false
- AGENTS changed in latest report window: false
- WORKLOG updated: true

## Completed / Closed Owners

Closed:

- source handoff mismatch
- `sentence_too_long`
- manual shadow review
- repeatability / fullness review
- visible-output shape guard
- fullness / article-brief diagnosis
- post-guard AB test
- non-0506 route archive cleanup
- Desktop 0506 method check

Do not reopen these unless a new artifact proves the specific owner is broken again.

## Latest AB Result

Artifact root:

```text
C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\
```

Summary:

- decision: `reject`
- article_types_attempted: `company_introduction`
- runs_completed: `3`
- api_send_count: `3`
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

- Route A better: `2`
- tie: `1`
- Route 0506 better: `0`
- blocked: `0`

Important interpretation:

- visible-output wrapper / fenced article leakage did not recur
- source-faithfulness passed in all three runs
- all Route 0506 candidates were QA-red
- Route 0506 is not stable enough as the post-guard AB candidate
- do not adopt or replace Route A

## Desktop 0506 Method Check

Artifact root:

```text
C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\
```

Finding:

- notecode Route 0506 imports `C:\Users\横山裕明\Desktop\0506`
- notecode Route 0506 calls `BlogPipelineRunner.run_extracted_sources(...)`
- model / reasoning align with Desktop OpenAI mode:
  - `gpt-5.4-mini`
  - `high`
- same core engine: yes
- same end-to-end generation surface: no

Current bottleneck hypothesis:

```text
source_surface_parity_gap
```

Reason:

- Route 0506 reaches the Desktop 0506 core pipeline, so the primary issue is not missing Desktop stage order or model mismatch.
- notecode adapter hands over compact typed source records instead of Desktop 0506's richer native extracted-source / source-card / knowledge-pack surface.
- post-guard AB source snapshot was only:
  - `notecode_typed_contract:company_introduction_script_packet`: 319 chars
  - `notecode_typed_contract:company_introduction_source_contract`: 524 chars
  - `notecode_typed_contract:source_grounding_items`: 524 chars
- recurring `model_frequent_word`, narrator consistency failure, and compact/generic article shape are likely downstream symptoms, not first owners.

## Archive State

Archive root:

```text
C:\tetie\notecode\archive\non_0506_route_records_20260509\
```

Result:

- moved_count: `48`
- old deepresearch / Route B / Route B2 / Route D / Route E / shadow_autonomous logs and docs were moved out of active `logs` / `docs`
- deletion: none
- do not revive old rejected routes

## Hard Boundaries

- Do not regenerate Route A.
- Do not refetch URLs.
- Do not use Route A fallback.
- Do not revive old rejected routes.
- Do not reopen source handoff mismatch as already fixed unless a new artifact proves a new handoff blocker.
- Do not reopen `sentence_too_long`.
- Do not reopen visible-output shape guard.
- Do not relax thresholds.
- Do not relax `repair_acceptance`.
- Do not add broad prompt tuning.
- Do not add new repair loops.
- Do not make Route A replacement / adoption judgment in this instruction window.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.

## Next One Owner

If the user asks for a next work-window prompt, create only this owner:

```text
Route 0506 source-surface parity check
```

Allowed next check:

- Compare Desktop 0506 behavior when fed the same thin Route 0506 source snapshot versus its native richer source flow.
- Or feed notecode Route 0506 a saved Desktop-like source card / knowledge-pack artifact and compare output shape.

Stop condition:

- If source-surface parity does not improve compactness / repetition / narrator stability, stop and report with artifact evidence.
- Do not convert this into prompt tuning, threshold relaxation, `repair_acceptance` relaxation, or extra repair loops.

## Instruction Window Closeout Rules

When a work-window report arrives:

1. First check `decision`.
2. Check guardrail booleans:
   - `route_a_regenerated`
   - `url_refetched`
   - `route_a_fallback_used`
   - `source_handoff_reopened`
   - `threshold_relaxed`
   - `repair_acceptance_relaxed`
   - `prompt_bloat`
   - `module_bloat`
3. If the report widened into Route A adoption, broad prompt tuning, threshold relaxation, or old routes, classify it as scope drift.
4. If it stays in source-surface parity, decide only:
   - `continue_shadow`
   - `reject`
   - `blocked`
   - `needs_next_owner`

Do not output `adopt` or `replace_route_a` from this instruction window.

## Suggested Next Work-Window Prompt

```text
C:\tetie\notecode で Route 0506 source-surface parity check だけを実施してください。

最初に必ず次を読んでください。
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\WORKLOG.md
4. C:\tetie\notecode\docs\route_0506_work_window_result_report_to_instruction_window_2026-05-09.md
5. C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\compare_summary.json
6. C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\manual_review.md
7. C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\README.md
8. C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\method_check_summary.json
9. C:\tetie\notecode\ALGORITHM.md の ## 4 / ## 5 / ## 12

現状:
- post-guard AB test は reject。
- Route A は frozen。再生成しない。
- Route 0506 は shadow-only。adoption / replacement 判断はしない。
- notecode Route 0506 は Desktop 0506 core pipeline を呼んでいるが、end-to-end source surface は同一ではない。
- primary bottleneck hypothesis は source_surface_parity_gap。
- post-guard AB source surface は 3 typed records / 319 + 524 + 524 chars。
- 3 runs すべて QA-red: model_frequent_word が2回、first_person_inconsistency が1回。

今回の one owner:
- Route 0506 source-surface parity check のみ。

禁止:
- Route A を再生成しない。
- URL refetch しない。
- Route A fallback / old route fallback を使わない。
- old Route B / Route D / Route E / deepresearch routes を復活させない。
- sentence_too_long / visible-output shape guard を再オープンしない。
- threshold / repair_acceptance を緩めない。
- broad prompt tuning / 新 repair loop を追加しない。
- Route A adoption / replacement 判断をしない。

進め方:
- まず診断 artifact を作る。
- Desktop 0506 の native richer source flow と、notecode Route 0506 の compact typed source surface を比較する。
- 可能なら、同一 core pipeline に thin source snapshot と Desktop-like source-card / knowledge-pack surface をそれぞれ入れた場合の差を、保存 artifact だけで比較する。
- 実行が必要な場合も saved artifact / saved source only に限定し、URL refetch はしない。
- source-surface parity が compactness / repetition / narrator stability を改善しないなら、そこで止める。

完了報告:
- decision: continue_shadow | reject | blocked | needs_next_owner
- artifact_root
- diagnosis_only
- changed_files
- source_surface_compared
- desktop_native_surface
- notecode_typed_surface
- parity_gap_confirmed
- route_a_regenerated: false
- url_refetched: false
- route_a_fallback_used: false
- threshold_relaxed: false
- repair_acceptance_relaxed: false
- prompt_bloat: none | found
- module_bloat: none | found
- tests
- manual_japanese_naturalness_note
- next_one_owner
- WORKLOG_update_needed
```
