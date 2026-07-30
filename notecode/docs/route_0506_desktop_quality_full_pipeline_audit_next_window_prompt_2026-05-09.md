# Route 0506 Desktop Quality Full-Pipeline Audit Next Window Prompt 2026-05-09

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 / Desktop 0506 品質差分を徹底調査する診断ウインドウです。

目的は、`C:\Users\横山裕明\Desktop\0506` では同じ OpenAI 系モデル `gpt-5.4-mini` / reasoning `high` で安定した高品質に到達しているのに、notecode Route 0506 では QA-red が残る理由を、UI入力から最終QAまで全工程で特定することです。

このウインドウは調査専用です。実装修正、API生成、Route A replacement/adoption 判断は行いません。

## Required Read Order

### notecode / Route 0506

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. instruction / report / latest diagnosis:
   - `C:\tetie\notecode\docs\route_0506_instruction_window_migration_prompt_after_ab_2026-05-09.md`
   - `C:\tetie\notecode\docs\route_0506_work_window_result_report_to_instruction_window_2026-05-09.md`
   - `C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\diagnosis.md`
   - `C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\surface_compare.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_source_surface_adapter_design_20260509\design.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_source_surface_adapter_design_20260509\adapter_contract.json`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_source_surface_adapter_design_20260509\validation_plan.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_like_source_surface_adapter_design_20260509\decision_before_code.md`
5. AB / method artifacts:
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\compare_summary.json`
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\manual_review.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\README.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\method_check_summary.json`
6. notecode implementation surfaces:
   - `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
   - `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
   - `C:\tetie\notecode\tools\run_route_0506_saved_source_cli_validation.py`
   - `C:\tetie\notecode\note\note_writer_app.py`
   - any Route 0506 tests found under `C:\tetie\notecode\note\tests\`
7. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`

### Desktop 0506

8. `C:\Users\横山裕明\Desktop\0506\AGENTS.md`
9. `C:\Users\横山裕明\Desktop\0506\README.md`
10. `C:\Users\横山裕明\Desktop\0506\PROGRESS.md`
11. `C:\Users\横山裕明\Desktop\0506\WORKLOG.md`
12. Desktop algorithm / spec:
    - `C:\Users\横山裕明\Desktop\0506\docs\CURRENT_ALGORITHM.md`
    - `C:\Users\横山裕明\Desktop\0506\docs\PIPELINE_SPEC.md`
    - `C:\Users\横山裕明\Desktop\0506\docs\JAPANESE_STYLE_POLICY.md`
    - `C:\Users\横山裕明\Desktop\0506\docs\ARTICLE_GENRE_POLICY.md`
    - `C:\Users\横山裕明\Desktop\0506\docs\CONFIG_AND_PERSONA_POLICY.md`
13. Desktop code surfaces:
    - `C:\Users\横山裕明\Desktop\0506\app\services\pipeline_runner.py`
    - `C:\Users\横山裕明\Desktop\0506\app\services\llm_client.py`
    - `C:\Users\横山裕明\Desktop\0506\app\services\local_llm_client.py`
    - `C:\Users\横山裕明\Desktop\0506\app\services\source_acquisition.py`
    - `C:\Users\横山裕明\Desktop\0506\app\services\source_preprocessor.py`
    - `C:\Users\横山裕明\Desktop\0506\app\services\local_source_card_builder.py`
    - `C:\Users\横山裕明\Desktop\0506\app\services\local_draft_renderer.py`
    - `C:\Users\横山裕明\Desktop\0506\app\services\opening_editor.py`
    - `C:\Users\横山裕明\Desktop\0506\app\services\global_consistency_editor.py`
    - `C:\Users\横山裕明\Desktop\0506\app\services\style_postprocessor.py`
    - `C:\Users\横山裕明\Desktop\0506\app\services\structural_editor.py`
    - `C:\Users\横山裕明\Desktop\0506\app\ui\main.py`
    - `C:\Users\横山裕明\Desktop\0506\app\config\`
    - `C:\Users\横山裕明\Desktop\0506\app\personas\`
    - `C:\Users\横山裕明\Desktop\0506\app\prompts\`
14. Desktop high-quality artifacts:
    - `C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_human_tone_trials\human_tone_trial_05_closing_and_ending_tone\`
    - `C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_persona_timing_trials\persona_timing_trial_05_global_then_late_best_candidate\`
    - `C:\Users\横山裕明\Desktop\0506\artifacts\quality_review_package_pdf_1371322\`
    - `C:\Users\横山裕明\Desktop\0506\artifacts\GPT5.4mini\`

## Current Known Facts

- Desktop 0506 can produce QA-green outputs using the same intended model family:
  - model: `gpt-5.4-mini`
  - reasoning: `high`
- Desktop final examples include:
  - Kyoto Kogyo company/service intro: QA pass, score 100, no issues
  - PDF explainer final: QA pass, score 100, no issues
- notecode Route 0506 post-guard AB test:
  - decision: `reject`
  - 3 runs completed
  - all 3 Route 0506 candidates QA-red
  - run_01 / run_02: `model_frequent_word`
  - run_03: `first_person_inconsistency`
  - Route 0506 better: 0
- Route 0506 reaches Desktop 0506 core runner:
  - `BlogPipelineRunner.run_extracted_sources(...)`
- Confirmed likely gap so far:
  - Desktop native source surface is richer
  - notecode Route 0506 compresses saved input into 3 manual typed records
- But do not assume source surface is the only gap. This audit must check all layers.

## One Owner

Full-pipeline quality gap audit only.

This is a broad read-only diagnosis owner. It may inspect many layers, but it must not fix them in the same window.

## Audit Layers

For each layer below, compare Desktop 0506 success path against notecode Route 0506 path. Use file paths and artifact evidence.

1. UI / user input mapping
   - article type / genre mapping
   - narrator / first-person selection
   - target reader / article goal / source mode
   - whether notecode UI loses Desktop-required controls or defaults
2. Route dispatch and runtime mode
   - how notecode selects Route 0506
   - model name / reasoning effort / OpenAI mode
   - environment variables and defaults
3. Source acquisition and saved-source boundary
   - Desktop URL/PDF/manual source handling
   - notecode saved input contract handling
   - whether source identity, titles, locators, canonical URLs, and source order survive
4. Source preprocessing / source packets
   - packet object shape
   - chunks, spans, source locations, char counts, confidence, can_proceed
   - raw-source drift prevention
5. Source-card extraction
   - fact count
   - fact importance/confidence
   - source_span traceability
   - quote / source location preservation
6. Knowledge-pack integration
   - confirmed claims
   - deduping
   - do_not_infer / unsupported claim guard
   - source-card to claim mapping
7. Article brief
   - genre/persona
   - narrator
   - target length
   - section count
   - source thickness
   - claim allocation
   - heading and section purpose
8. Prompt handoff
   - system/developer/user prompt template shape
   - whether Desktop sends richer structured data to stages
   - whether notecode flattens or renames fields before Desktop runner
   - whether hidden internal labels leak or distort the stage
9. Persona / style profile / editor profile
   - Desktop persona registry and style profile use
   - notecode Route 0506 persona mapping
   - first-person consistency rules
   - company/service intro persona vs market explanation persona boundaries
10. Editor stage timing
    - Desktop: draft -> opening_editor -> global_consistency_editor -> style_editor -> structural_editor -> quality_checker
    - notecode Route 0506 actual stage order and artifact outputs
    - whether opening/global consistency stages fire with the same inputs
11. Quality checker / targeted rewriter
    - QA thresholds
    - `model_frequent_word`
    - first-person inconsistency
    - visible-output shape guard
    - targeted rewrite trigger and stop behavior
12. Artifact logging and observability
    - whether both sides expose comparable stage artifacts
    - missing logs that block diagnosis

## Required Output Artifacts

Create:

```text
C:\tetie\notecode\logs\route_0506_desktop_quality_full_pipeline_audit_20260509\
```

Required files:

```text
audit.md
layer_compare.json
gap_matrix.md
evidence_index.json
next_owner_recommendation.md
decision.md
```

`layer_compare.json` must include one object per audit layer:

```json
{
  "layer": "source_packets",
  "desktop_evidence": [],
  "notecode_route_0506_evidence": [],
  "same_or_different": "same | different | unknown",
  "gap_severity": "critical | major | minor | none | unknown",
  "quality_relevance": "proven | probable | possible | unlikely | unknown",
  "recommended_owner": "single owner name or none",
  "do_not_mix_with": []
}
```

`gap_matrix.md` must classify findings into:

- critical parity gaps
- major probable gaps
- minor differences
- not a gap
- unknown / needs instrumentation

`next_owner_recommendation.md` must recommend exactly one first next owner, plus parked later owners.

## Hard Boundaries

- Do not change product code.
- Do not run OpenAI API generation.
- Do not regenerate Route A.
- Do not refetch URLs.
- Do not use Route A fallback.
- Do not revive old rejected routes.
- Do not restore old Route B / Route D / Route E / deepresearch routes.
- Do not relax thresholds.
- Do not relax `repair_acceptance`.
- Do not add broad prompt tuning.
- Do not add new repair loops.
- Do not make Route A replacement / adoption judgment.
- Do not decide adoption based on Desktop quality alone.
- Do not claim source parity from hash equality alone.
- Do not collapse all findings into “prompt issue” unless artifact evidence proves prompt handoff is the first owner.

## What To Be Strict About

Desktop 0506 quality proves that the model family can produce stable output. Therefore, do not stop at “LLM variability” as the explanation.

You must check whether notecode Route 0506 differs in:

- source surface
- prompt shape
- persona mapping
- stage order
- UI-to-contract mapping
- article brief target length / section count
- source-card / knowledge-pack density
- editor stage inputs
- QA / rewrite trigger conditions
- artifact logging

If source surface remains the first owner, prove why it dominates the other gaps.

If prompt/persona/UI mapping is a stronger first owner, say so and park source-surface implementation.

## Tests

No product code changes:

- validate all JSON output artifacts with `ConvertFrom-Json`
- no pytest required

Optional read-only checks:

- run Desktop test suite only if needed to confirm current health:
  - `C:\Users\横山裕明\Desktop\0506\.venv\Scripts\python.exe -m pytest -q`
- do not run notecode generation or Desktop generation

## Decision Rules

Use `needs_next_owner` if:

- the audit identifies a concrete first owner to implement or instrument next

Use `continue_shadow` if:

- Route 0506 remains useful as shadow but the first owner is still not narrow enough

Use `blocked` if:

- required artifacts are missing or unreadable
- the gap cannot be diagnosed without a forbidden API run / URL refetch

Use `reject` if:

- the audit proves Route 0506 cannot reach Desktop-like quality without broad prompt tuning, threshold relaxation, old route revival, or unsupported source reconstruction

Do not output `adopt` or `replace_route_a`.

## Final Report Contract

Report in this exact shape:

```text
decision: needs_next_owner | continue_shadow | blocked | reject
artifact_root:
diagnosis_only: true
changed_files:
product_code_changed: false
api_send: false
desktop_quality_confirmed:
route_0506_quality_problem_confirmed:
layers_compared:
critical_parity_gaps:
major_probable_gaps:
not_gaps:
unknowns:
first_next_owner:
parked_later_owners:
route_a_regenerated: false
url_refetched: false
route_a_fallback_used: false
old_routes_reopened: false
threshold_relaxed: false
repair_acceptance_relaxed: false
prompt_bloat: none | found
module_bloat: none | found
tests:
manual_japanese_naturalness_note:
WORKLOG_update_needed: true | false
```

If `WORKLOG_update_needed=true`, update only the Route 0506 current state / next owner pointer in `C:\tetie\WORKLOG.md`. Do not rewrite unrelated history.
