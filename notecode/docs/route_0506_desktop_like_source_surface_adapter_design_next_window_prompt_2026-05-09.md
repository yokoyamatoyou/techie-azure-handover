# Route 0506 Desktop-Like Source Surface Adapter Design Next Window Prompt 2026-05-09

このプロンプトを別 Codex 作業ウインドウに貼り付けて開始してください。

## Role

あなたは `C:\tetie\notecode` の Route 0506 Desktop-like source surface adapter design 実行ウインドウです。

今回の one owner は、confirmed `source_surface_parity_gap` を受けて、notecode Route 0506 が Desktop 0506 core pipeline へ渡す source surface をどう設計すればよいかを、saved artifacts のみで定義することです。

Route 0506 は shadow-only のままです。Route A replacement / adoption 判断は行いません。

## Required Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\WORKLOG.md`
4. source-surface parity 実行 prompt:
   - `C:\tetie\notecode\docs\route_0506_source_surface_parity_next_window_prompt_2026-05-09.md`
5. source-surface parity diagnosis artifacts:
   - `C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\diagnosis.md`
   - `C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\surface_compare.json`
   - `C:\tetie\notecode\logs\route_0506_source_surface_parity_20260509\decision_before_edit.md`
6. post-guard AB / method artifacts:
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\compare_summary.json`
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\manual_review.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\README.md`
   - `C:\tetie\notecode\logs\route_0506_desktop_method_check_20260509\method_check_summary.json`
7. Desktop 0506 reference artifacts:
   - `C:\Users\横山裕明\Desktop\0506\AGENTS.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\CURRENT_ALGORITHM.md`
   - `C:\Users\横山裕明\Desktop\0506\docs\PIPELINE_SPEC.md`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\runs\kyotokogyo_human_tone_trials\human_tone_trial_05_closing_and_ending_tone\`
   - `C:\Users\横山裕明\Desktop\0506\artifacts\GPT5.4mini\`
8. notecode Route 0506 owners / saved artifacts:
   - `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
   - `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
   - `C:\tetie\notecode\tools\run_route_0506_saved_source_cli_validation.py`
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\run_01\source_snapshot.json`
   - `C:\tetie\notecode\logs\route_0506_post_guard_ab_test_20260509\run_01\input_contract.json`
9. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`

## Current State

- Route A: frozen / immutable
- Route 0506: shadow-only
- post-guard AB test decision: `reject`
- source-surface parity diagnosis decision: `continue_shadow`
- product code changed in source-surface parity window: false
- API send in source-surface parity window: false
- confirmed bottleneck hypothesis: `source_surface_parity_gap`

Confirmed gap:

- Desktop native surface:
  - 4 URL source packets
  - 4339 chars
  - source-card 24 facts
  - knowledge 24 claims
  - source thickness `thick`
  - 3 brief sections
- notecode typed surface:
  - 3 manual typed records
  - 1367 chars
  - source-card 20 facts
  - knowledge 12 claims
  - source thickness `medium`
  - 5 brief sections

Interpretation:

- Desktop native flow preserves URL/page metadata and richer per-source text before source-card extraction.
- notecode Route 0506 compresses the saved contract into three typed manual records and loses source identity / density.
- The gap is plausible upstream cause for compactness / repetition / narrator instability.
- The diagnosis did not prove a safe adapter patch yet.

## One Owner

Route 0506 Desktop-like source surface adapter design only.

Design a narrow adapter contract that can preserve Desktop-like source identity / density from saved notecode artifacts without:

- URL refetch
- Route A generation
- Route A fallback
- old route revival
- restoring raw-source drift
- broad prompt tuning
- threshold relaxation
- `repair_acceptance` relaxation
- new repair loops

## Required Questions

Answer these before any implementation suggestion:

1. Which Desktop source packet / source-card / knowledge-pack fields are essential for preserving source identity and density?
2. Which of those fields can be reconstructed from notecode saved `input_contract.json` / `source_snapshot.json` without URL refetch?
3. Which fields must stay unavailable rather than invented?
4. What is the minimal adapter object shape for a Desktop-like saved-source handoff?
5. How does the adapter avoid the closed source handoff mismatch where raw broad source documents caused broad real-estate guide drift?
6. What deterministic validation can prove the adapter preserves source identity / density before any OpenAI run?
7. What would the next saved-source parity run compare, if this design is accepted?

## Hard Boundaries

- Do not regenerate Route A.
- Do not refetch URLs.
- Do not use Route A fallback.
- Do not revive old rejected routes.
- Do not restore old Route B / Route D / Route E / deepresearch routes from archive.
- Do not reopen source handoff mismatch as a fix target; use it only as a closed failure to avoid repeating.
- Do not reopen `sentence_too_long`.
- Do not reopen visible-output shape guard.
- Do not relax thresholds.
- Do not relax `repair_acceptance`.
- Do not add broad prompt tuning.
- Do not add new repair loops.
- Do not make Route A replacement / adoption judgment.
- Do not invent URL/page metadata that is not present in saved artifacts.
- Do not treat source hash equality alone as quality parity.
- Keep `1 issue = 1 narrow hypothesis = 1 owner scope`.

## Allowed Work

Allowed:

- read-only inspection of listed artifacts and code
- design of a minimal adapter contract
- deterministic prototype data shape written only under the artifact root
- validation scripts or notes under the artifact root only, if needed
- no product code changes by default

Not allowed in this window:

- product code patch
- OpenAI API call
- saved-source parity generation run
- URL fetch
- Route A generation

If you conclude a product-code patch or API run is necessary, stop with `needs_next_owner` and describe the next owner. Do not perform it in this window.

## Suggested Artifact Root

```text
C:\tetie\notecode\logs\route_0506_desktop_like_source_surface_adapter_design_20260509\
```

Required artifacts:

```text
design.md
adapter_contract.json
validation_plan.md
decision_before_code.md
```

`adapter_contract.json` should include:

- desktop_fields_required
- notecode_saved_fields_available
- unavailable_fields_do_not_invent
- proposed_source_record_shape
- source_identity_preservation_rules
- density_preservation_rules
- raw_source_drift_prevention_rules
- deterministic_validation_checks
- next_saved_source_parity_run_contract

## Decision Rules

Use `needs_next_owner` if:

- a safe adapter contract is defined and the next window should implement it or run a saved-source parity generation test

Use `continue_shadow` if:

- the design remains useful but no implementation/run should happen yet

Use `reject` if:

- Desktop-like parity cannot be approximated from saved artifacts without URL refetch, raw-source drift, or broad prompt tuning

Use `blocked` if:

- required artifacts are missing
- Desktop 0506 reference artifacts cannot be read
- notecode saved artifacts are insufficient to define a non-invented contract

Do not output `adopt` or `replace_route_a`.

## Tests

If no product code changes:

- validate any JSON artifact with `ConvertFrom-Json`
- no pytest required

Product code changes are not allowed in this window. If they become necessary, stop and report `needs_next_owner`.

## WORKLOG

If useful, update only the Route 0506 current state / next owner pointer in `C:\tetie\WORKLOG.md`.

Do not rewrite unrelated history.

## Final Report Contract

Report in this exact shape:

```text
decision: continue_shadow | needs_next_owner | reject | blocked
artifact_root:
diagnosis_only: true
changed_files:
adapter_design_only: true
product_code_changed: false
api_send: false
desktop_fields_required:
notecode_saved_fields_available:
unavailable_fields_do_not_invent:
adapter_contract_created: true | false
raw_source_drift_prevention:
deterministic_validation_checks:
next_saved_source_parity_run_contract:
route_a_regenerated: false
url_refetched: false
route_a_fallback_used: false
old_routes_reopened: false
source_handoff_reopened: false
sentence_too_long_reopened: false
visible_output_shape_guard_reopened: false
threshold_relaxed: false
repair_acceptance_relaxed: false
prompt_bloat: none | found
module_bloat: none | found
tests:
manual_japanese_naturalness_note:
next_one_owner:
WORKLOG_update_needed: true | false
```
