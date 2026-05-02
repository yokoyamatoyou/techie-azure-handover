# Persona / UI Writer Role / Quality Fail Handoff 2026-04-23

## Current Situation

- Workspace: `C:\tetie\notecode`
- User is moving to a separate window.
- Immediate issue: UI generation stopped by output quality guard.
- User concern:
  - UI has a writer-role selection.
  - This may collide with article-type persona.
  - Persona should be used more fully to increase natural freedom.
  - Avoid expanding symptomatic rules; WORKLOG contains repeated failures where patchy guards / prompt accretion made output worse.

## Latest Failure Confirmed In Logs

Primary files:

- `C:\tetie\notecode\logs\latest_ui_journey.json`
- `C:\tetie\notecode\logs\latest_generation_output.txt`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- `C:\tetie\notecode\logs\app.log`
- `C:\tetie\notecode\logs\generation_audit_log.jsonl`

Latest attempt:

- `attempt_id`: `gen-d74e4092`
- timestamp: `2026-04-23 12:22:54`
- `article_type`: `explanatory_article`
- `semantic_article_key`: `explanatory_article`
- UI route:
  - purpose: `explain`
  - target: `concept`
  - source mode: `grounded`
  - selected label: `解説・ノウハウ`
- source:
  - count: `1`
  - type: file
  - path: `C:\tetie\notecode\note\uploads\3c0e4fcb65d1415e94e52f7b36010548_AI______________.md`
  - fetched chars: `12000`
- title generated before block:
  - `AIっぽさはどこで生まれるか――エグゼクティブサマリーの読み方`
- fail:
  - `runtime_error_class`: `system`
  - `runtime_reason_code`: `SYS_QUALITY_WARNINGS_UNRESOLVED`
  - UI phase: `quality_output_guard`

Guard reasons:

- `fingerprint:bigram_mono_low`
- `fingerprint:vocab_repetition`
- `fingerprint:syntactic_complexity_low`
- `fingerprint:ending_repetition`
- `fingerprint:comma_overuse`
- `source_grounding:weak_reflection`

Relevant metrics:

- `body_chars`: `1597`
- `full_text_chars`: `1945`
- `proposition_informative_ratio`: `1.0`
- `contract_alignment_score`: `1.0`
- `must_cover_reflection_rate`: `1.0`
- `source_trace_coverage`: `0.3333`
- `source_grounding_item_count`: `6`
- `source_grounding_reflected_count`: `2`
- `source_grounding_reflection_ratio`: `0.3333`
- `flat_zone_count`: `5`
- `ending_bucket_max_run`: `10`
- `repair_trigger_score`: `0.62`
- `fingerprint_correction_applied`: `false`
- `repair_only_report.mode`: `off`
- `repair_only_report.applied`: `false`

Important observation:

- The latest output is not blocked for visible hidden instruction leakage.
- It is blocked because the generated text was too even / mechanically explanatory and did not reflect enough source-grounding anchors.
- The source itself is about AI-like writing. This creates a trap: generic explanatory persona can summarize the topic fluently while still becoming the same kind of flat, over-smoothed prose the source discusses.

## Recent Changes Already Made In Current Window

Changed files:

- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- `C:\tetie\WORKLOG.md`

Implemented:

- writer-facing source material separated from internal guard:
  - `SOURCE_DIGEST` / `EVIDENCE` no longer receive `source_limit`, guard-only text, bucket labels, source contract / validation / repair / persona terms.
- prompt-level thin phrase guard:
  - `効く`, `効いた`, `効いている`, `第一歩`, `価値を提供`, `最適なソリューション`.
- minimal post-normalize surface cleanup:
  - examples: `このやり方が効いたのは` -> `このやり方で差が出たのは`.
- 8 article types x 1 live generation checked.
  - accepted summary:
    - `C:\tetie\notecode\新しいフォルダー\新しいフォルダー (4)\one_each_after_style_guard_v2_20260423\accepted_summary.md`
    - `C:\tetie\notecode\新しいフォルダー\新しいフォルダー (4)\one_each_after_style_guard_v2_20260423\accepted_summary.json`

Tests run:

- `py -m pytest note/tests/test_simple_note_pipeline.py::test_normalize_draft_rewrites_empty_aiish_phrases note/tests/test_simple_note_pipeline.py::test_short_generation_prompt_adds_density_guidance_for_explanatory_article note/tests/test_simple_note_pipeline.py::test_generation_prompt_filters_guard_material_from_writer_evidence -q`
  - `3 passed`
- `py -m pytest note/tests/test_current_mainline_regressions.py::test_current_mainline_clean_mock_llm_result_passes_pure_output_guard note/tests/test_current_mainline_regressions.py::test_current_mainline_company_intro_uses_company_outline_headings -q`
  - `2 passed`

## Risk In Recent Changes

The thin phrase cleanup worked for the narrow 8-article validation, but it is a symptomatic guard. Do not expand this style of fix as the main path.

Reason:

- WORKLOG repeatedly records that prompt-only strengthening, formatter regex fixes, and surface-only patching can become counterproductive.
- The latest failure is broader:
  - weak source reflection
  - low syntactic variety
  - ending repetition
  - comma overuse
  - generic explanation style
- A larger blacklist or more after-the-fact rewriting would probably reduce freedom and worsen naturalness.

Recommended stance:

- Treat current surface cleanup as a temporary narrow guard.
- Do not add more phrase replacements unless a user-visible hard leak requires it.
- Prefer persona / source delivery / UI role semantics over patching symptoms.

## UI Writer Role And Persona Collision

Current conceptual split should be:

- Article-type persona:
  - decides what the article is trying to do.
  - controls lead angle, heading order, fact selection, paragraph emphasis, final paragraph.
- UI writer role:
  - should be a voice adapter, not another persona.
  - controls surface stance: first person, distance, register, pronoun policy, who is speaking.

Collision examples:

- UI selects `企業広報として語る`.
- Article persona expects neutral third-party company introduction.
- Result can mix:
  - `当社`
  - company name
  - `同社`
  - detached third-party language.

For this reason, avoid treating UI writer choice as a second persona. It should adapt the article-type persona, not override it.

Potential UI wording:

- replace or clarify `記事の書き手`
- candidates:
  - `語り口`
  - `文中の立場`
  - `誰の視点で書くか`

## Likely Root Cause Of Latest Error

The latest generation had:

- empty user prompt
- one long source file
- explanatory article route
- source fit passed
- source reflection low
- generated body short relative to source length
- no persona-level reason to choose concrete source anchors beyond headings / summary sections

This suggests that the current explanatory persona / source digest path likely compresses the source into a clean executive-summary structure, but does not force enough concrete source anchor selection in the body.

The weak point is not just quality thresholds. It is probably the writer's source-understanding action:

- It saw the source topic.
- It summarized the top sections.
- It did not sufficiently reuse source-specific anchors across sections.
- It produced a tidy article about the source instead of an article shaped by the source's own contrasts.

## Recommended Next Window Strategy

Do not start by lowering quality thresholds.

Do not start by adding more blacklist terms.

Do not start with broad prompt accretion.

Start by locating the writer-role / persona / source material route for this exact latest case:

- `explanatory_article`
- `source_count=1`
- long file source
- empty prompt
- UI writer role auto
- output guard reason includes `source_grounding:weak_reflection`

Preferred fix direction:

1. Make article-type persona the primary behavior controller.
2. Treat UI writer role as a voice adapter only.
3. For long source explanatory articles, add or improve a source-understanding step that selects enough concrete anchors before writing.
4. Increase freedom through persona behavior:
   - vary paragraph function,
   - use source-specific contrasts,
   - allow topic-appropriate subject omission,
   - keep Japanese rhythm natural,
   - avoid rigid section summaries.
5. Keep guard checks as validation, not as writing style generators.

Potential narrow hypothesis:

- `explanatory_article` with a long single source currently over-compresses into heading-level summary.
- If the generation persona receives a source anchor plan with 4-6 concrete source contrasts and is instructed through behavior rather than blacklist, source reflection rises and fingerprint warnings fall.

Possible owner files to inspect first:

- `C:\tetie\notecode\note\current_mainline_runner.py`
  - UI writer role / perspective / source fetch / input contract route.
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - source digest / writer prompt / style lines.
- `C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py`
  - distilled source digest and source anchor selection.
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - quality guard path, repair path, normalize, runtime source contracts.
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
  - prompt / source digest / style guard tests.
- `C:\tetie\notecode\note\tests\test_current_mainline_regressions.py`
  - current mainline generation behavior.

Relevant docs:

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\ALGORITHM.md`
  - `## 4. Single-Pass Generation`
  - `## 5. Repair Algorithm`
  - `## 12. Persona / Source Packet / Editing Persona Contract`
- `C:\tetie\WORKLOG.md`
  - especially 2026-04-23 source packet writer-facing guard record
  - and earlier failed hypotheses around prompt-only / formatter / surface patching.

## ALGORITHM Reminder

ALGORITHM.md has not yet been updated for this latest quality-fail issue.

If the next implementation changes the durable design, update ALGORITHM after validation, especially:

- `## 4. Single-Pass Generation`
- `## 12. Persona / Source Packet / Editing Persona Contract`

Likely ALGORITHM update content if validated:

- UI writer role is a voice adapter, not a competing persona.
- Article-type persona owns structure / source selection / emphasis.
- Long single-source explanatory articles require source-anchor selection before writing.
- Guard-only source stays out of writer evidence.
- Quality guard should detect failures, not become the main writing strategy.

## Suggested Test Case To Reproduce

Use latest upload:

- `C:\tetie\notecode\note\uploads\3c0e4fcb65d1415e94e52f7b36010548_AI______________.md`

Use same UI route:

- purpose: explain
- target: concept
- source mode: grounded
- article type: explanatory_article
- semantic key: explanatory_article
- length: adaptive
- tone: auto
- perspective: auto
- prompt: empty

Expected current failure:

- `SYS_QUALITY_WARNINGS_UNRESOLVED`
- `fingerprint:bigram_mono_low`
- `fingerprint:vocab_repetition`
- `fingerprint:syntactic_complexity_low`
- `fingerprint:ending_repetition`
- `fingerprint:comma_overuse`
- `source_grounding:weak_reflection`

Success condition:

- generation succeeds without lowering quality guard
- source reflection improves beyond the weak-reflection threshold
- no internal term leakage
- no added source-outside claims
- fingerprint warnings reduce without added surface blacklist
- Japanese reads less like a clean report summary and more like a source-aware explanatory note
