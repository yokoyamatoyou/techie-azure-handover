# Route 0506 Desktop Log Compare And Fix Next Window Prompt

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 完成前監査・修正ウインドウです。

`C:\Users\横山裕明\Desktop\0506` を current reference implementation として扱い、notecode 側 Route 0506 のログ・stage artifacts・実装差分を比較してください。Route 0506 はまだ完成扱いにしません。品質低下の原因を「source handoff / source packet / article brief / editor stages / QA rewrite」の段階に分けて特定し、小分けに修正します。

## Objective

Desktop 0506 と notecode Route 0506 のログ比較から、notecode 側で品質低下している原因を特定して修正する。

最優先仮説:

- notecode bridge が Route A / notecode 側の `source contract` や `source_grounding_items` を Route 0506 向け source packet へ変換せず、`input_contract.source_documents` の raw URL本文をそのまま渡している。
- その結果、Desktop 0506 の自然な会社紹介ではなく、不動産売却ガイド全体に寄った broad output になっている。

この仮説は必ずログで検証してから修正してください。違う原因が見つかった場合は、証拠を残して次の narrow owner に切り替えます。

## Required Read Order

1. `C:\tetie\notecode\AGENTS.md`
2. `C:\tetie\WORKLOG.md`
   - 2026-05-09 の Route 0506 latest blocked cause / AB test execution を読む
3. `C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\compare_summary.json`
4. `C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\manual_review.md`
5. `C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\inventory.json`
6. `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
7. `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
8. `C:\tetie\notecode\note\route_0506_ui_bridge.py`
9. `C:\tetie\notecode\tools\run_route_0506_saved_source_cli_validation.py`
10. `C:\Users\横山裕明\Desktop\0506\AGENTS.md`
11. `C:\Users\横山裕明\Desktop\0506\docs\CURRENT_ALGORITHM.md`
12. `C:\Users\横山裕明\Desktop\0506\docs\PIPELINE_SPEC.md`
13. `C:\Users\横山裕明\Desktop\0506\WORKLOG.md`
14. `C:\Users\横山裕明\Desktop\0506\PROGRESS.md`
15. `C:\Users\横山裕明\Desktop\0506\artifacts\GPT5.4mini\`
16. `C:\Users\横山裕明\Desktop\0506\artifacts\runs\`

## Hard Rules

- Desktop 0506 は参照正本。まずログから比較する。
- Route A は再生成しない。
- URL refetch しない。
- local file locator / external file ingestion を有効化しない。
- Route A fallback / old route fallback を Route 0506 成功として数えない。
- threshold relaxation、repair_acceptance 変更、prompt accretion、追加 repair loop で解決しない。
- `1 issue = 1 narrow hypothesis = 1 owner scope` を維持する。
- 修正は notecode 側 bridge / adapter / compatibility boundary を優先する。Desktop 0506 本体は、明示的に必要と証明できるまで変更しない。
- 5 回連続で同じ修正系の blocked / error / quality regression が解消しなければ停止し、blocked artifact と WORKLOG 記録を残す。

## Evidence To Compare

### notecode Route 0506 artifacts

Root:

```text
C:\tetie\notecode\logs\route_0506_route_a_ab_test_20260509\
```

Inspect each completed company-introduction run:

```text
company_introduction_run_01\
company_introduction_run_02\
company_introduction_run_03\
```

For each run, inspect:

```text
input_contract.json
source_snapshot.json
validation_summary.json
route_0506\latest_generation_output.md
route_0506\latest_generation_quality_report.json
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\source_packets.json
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\source_cards.json
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\article_knowledge_pack.json
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\article_brief.json
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\draft.md
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\opening_edited_draft.md
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\global_consistency_edited_draft.md
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\edited_draft.md
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\structural_edited_draft.md
route_0506\pipeline_stage_artifacts\route_0506_ui_1case\editor_pass_report.json
```

Known notecode symptoms to verify:

- source hash matched saved Route A:
  - `ca2055f4b02a73c3ad94dce625cc85be3df06d848ba7aea9321e6d1bae33c1bb`
- source documents count: `5`
- source text chars around:
  - `3531, 5135, 4010, 2100, 4857`
- source card fact counts observed:
  - run 1: `13,25,22,13,15`
  - run 2: `18,34,17,10,26`
  - run 3: `21,26,26,10,25`
- knowledge pack confirmed facts:
  - run 1: `31`
  - run 2: `30`
  - run 3: `25`
- article brief over-allocation symptoms:
  - run 1: `target_length=700`, `section_count=5`, claim allocation `3,3,7,4,14`
  - run 2: `target_length=800`, `section_count=5`, claim allocation `4,4,6,6,11`
  - run 3: `target_length=1500`, `section_count=5`, claim allocation `3,4,6,4,8`
- quality:
  - run 1: `sentence_too_long`, QA fail
  - run 2: `sentence_too_long`, QA fail
  - run 3: QA pass 100

### Desktop 0506 reference artifacts

Inspect docs first:

```text
C:\Users\横山裕明\Desktop\0506\docs\CURRENT_ALGORITHM.md
C:\Users\横山裕明\Desktop\0506\docs\PIPELINE_SPEC.md
C:\Users\横山裕明\Desktop\0506\WORKLOG.md
C:\Users\横山裕明\Desktop\0506\PROGRESS.md
```

Inspect OpenAI output references:

```text
C:\Users\横山裕明\Desktop\0506\artifacts\GPT5.4mini\company_intro_high_01.md
C:\Users\横山裕明\Desktop\0506\artifacts\GPT5.4mini\company_intro_high_02.md
C:\Users\横山裕明\Desktop\0506\artifacts\GPT5.4mini\company_intro_high_03.md
```

Inspect pipeline stage references:

```text
C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_quality_trials\kyotokogyo_trial_05_long_fact_splitting\
C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_persona_timing_trials\persona_timing_trial_05_global_then_late_best_candidate\
C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_human_tone_trials\human_tone_trial_05_closing_and_ending_tone\
```

Known Desktop reference facts to verify:

- Current algorithm pipeline:
  - extracted sources
  - generation source packets
  - source cards
  - article knowledge pack
  - article brief
  - draft writer
  - opening editor
  - global consistency editor
  - style editor
  - structural editor
  - Japanese quality checker
  - targeted rewriter only when QA requires rewrite
- OpenAI default:
  - `model=gpt-5.4-mini`
  - `reasoning_effort=high`
- successful Kyoto Kogyo reference used 4 source packets, each around `922,1328,1065,1024` chars
- successful reference source-card facts were constrained, typically `6` facts per source in the final local pipeline trial
- Desktop logs explicitly mention Trial 5 `long_fact_splitting` and persona timing Trial 5 as selected references

## Required Log-Diff Artifact

Before editing code, create:

```text
C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\desktop_vs_notecode_log_diff.md
C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\desktop_vs_notecode_stage_diff.json
```

The diff must compare:

- source input count
- source included chars
- source packet chunk count
- source card fact count
- confirmed fact count
- deduped themes
- article brief target length
- article brief section count
- claim allocation per section
- article_goal
- target_reader
- narrator
- style_edit_policy
- editor_pass_policy
- draft chars
- stage-by-stage text length and hash
- opening/global/style/structural editor changed flags
- final QA pass / score / issue types
- final visible topic drift

## Diagnosis Decision Tree

### H1: Source handoff mismatch

Evidence:

- notecode `input_contract` contains company-introduction specific fields:
  - `_company_introduction_source_contract`
  - `_company_introduction_script_packet`
  - `source_grounding_items`
- but `route_0506_structured_blog_adapter.py` only passes `input_contract.source_documents` into Desktop 0506 `ExtractedSource`.
- notecode source cards and knowledge pack become broad real-estate sale guidance, not company/service introduction.

If confirmed:

- Fix only the notecode source handoff boundary.
- Add a small helper in or near `route_0506_structured_blog_adapter.py` that builds Route 0506 source records from article-type-filtered contract data when available.
- For `company_introduction` / branding introduce only a narrow source-record construction path using:
  - `_company_introduction_script_packet`
  - `_company_introduction_source_contract.slots`
  - `source_grounding_items`
- Preserve raw `source_documents` fallback when no typed contract exists.
- Do not change Desktop 0506 prompts, QA thresholds, or Route A.

Acceptance for H1 fix:

- source packet count and included chars shrink to the company-introduction packet surface, not five full raw pages.
- source cards no longer extract broad unrelated buckets like full tax/document/divorce/rental guide unless explicitly in company-introduction source contract.
- article brief claim allocation does not overload one section with 10+ claims.
- final article stays company/service introduction, not broad real-estate selling guide.

### H2: Article brief over-allocation

Evidence:

- article brief assigns too many claims to one section despite filtered source.
- `target_length_chars` is inconsistent with claim count or source thickness.

If confirmed after H1 is fixed or disproven:

- Keep the owner narrow.
- Compare Desktop 0506 local deterministic behavior and OpenAI behavior.
- Prefer compatibility normalization of notecode input/brief boundary over prompt changes.
- Do not hard-code article text, headings, or quality phrases.

### H3: Editor stages fire but do not repair

Evidence:

- opening / structural reports show `changed=false`.
- QA issue remains `sentence_too_long`.
- `targeted_rewriter` receives empty `text` and empty `claim_ids`.

If confirmed after source handoff is corrected:

- Treat as a separate owner.
- Do not mix with source handoff fix.
- First improve observability: persist exact long sentence / span in QA artifact if Desktop 0506 already has a compatible way.
- Do not add a broad repair loop.

### H4: Stage-output guard hides valid edits

Evidence:

- editor API output is generated but guard falls back to previous article.
- fallback is not observable in artifacts.

If confirmed:

- Add explicit fallback markers to artifacts first.
- Do not change guard behavior before proving false fallback.

## Self-Fix Loop

For each failed attempt:

1. Increment `fix_attempt_count`.
2. Save:

```text
C:\tetie\notecode\logs\route_0506_desktop_log_compare_fix_20260509\fix_attempt_XX\
```

Required files:

- `hypothesis.md`
- `desktop_reference_evidence.md`
- `notecode_evidence.md`
- `code_diff_summary.md`
- `test_result.txt`
- `rerun_summary.json`

3. Patch only one owner.
4. Run focused tests.
5. Rerun the smallest company-introduction case.
6. Recompare stage artifacts.

Stop condition:

- Stop after 5 failed fix attempts.
- Do not start a sixth fix.
- Write `blocked.json`, `failure_note.md`, and update `C:\tetie\WORKLOG.md`.

## Required Checks After Any Code Fix

Run at minimum:

```powershell
.\.venv\Scripts\python.exe -m py_compile note\route_0506_structured_blog_adapter.py note\route_0506_stage_output_guard.py note\route_0506_ui_bridge.py tools\run_route_0506_saved_source_cli_validation.py note\tests\test_route_0506_structured_blog_adapter.py
.\.venv\Scripts\python.exe -m pytest -q note\tests\test_route_0506_structured_blog_adapter.py note\tests\test_route_0506_ui_bridge.py note\tests\test_route_0506_saved_source_cli_validation.py
```

Add or update focused tests only for the changed owner.

## Rerun Policy

First rerun locally if possible:

- no URL refetch
- saved source only
- Route A unchanged

Then run one OpenAI candidate only if:

- local/log-diff checks support the fix,
- `OPENAI_API_KEY` is already available,
- `BLOGGEN_LLM_MODE=openai`,
- `OPENAI_MODEL=gpt-5.4-mini`,
- `OPENAI_REASONING_EFFORT=high`.

Do not run a 3x matrix until the one-case source handoff artifact is demonstrably closer to Desktop 0506.

## Final Report Contract

Report in this exact shape:

```text
decision: fixed_continue_shadow | blocked | needs_next_owner
artifact_root:
desktop_reference_paths:
notecode_artifacts_compared:
primary_cause:
source_handoff_mismatch: true | false
article_brief_overallocation: true | false
editor_stage_issue: true | false
stage_guard_issue: true | false
fix_attempts:
files_changed:
route_a_regenerated: false
url_refetched: false
threshold_relaxed: false
prompt_bloat: none | found
module_bloat: none | found
tests:
rerun_result:
quality_result:
remaining_risk:
worklog_updated: true | false
next_one_owner:
```

If blocked, include:

- exact stop reason
- 5 attempt summaries
- smallest reproducible case
- why Desktop 0506 still indicates a notecode-side gap

