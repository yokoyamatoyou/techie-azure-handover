# Persona Iterative Trial Separate-Window Prompt

## 目次
- role
- read order
- objective
- hard boundaries
- current implementation status
- source policy
- execution loop
- per-run checks
- logging
- image phase
- final report

## role
You are running the live separate-window validation for `persona_iterative_trial_2026-04-23`.

This is not a broad refactor window. Your main job is to run the current-mainline trial loop, gather suitable sources per blog type, use web search when local/source inputs are insufficient, review outputs strictly, keep only narrow improvements, and roll back worsening changes.

Prefer PLAN mode first if that mode is available in this window. If not, execute the same workflow in the default mode without waiting for extra user confirmation.

## read order
Read in this order before doing any live sweep work:

1. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
2. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
3. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
4. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
5. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`
   - `## 13. GPT Image 2 Image Generation Algorithm`
6. `C:\tetie\notecode\plan\persona_iterative_trial_2026-04-23\README.md`
7. `C:\tetie\notecode\plan\persona_iterative_trial_2026-04-23\TASK.md`
8. `C:\tetie\notecode\plan\persona_iterative_trial_2026-04-23\PROGRESS.md`
9. `C:\tetie\notecode\plan\persona_iterative_trial_2026-04-23\ROLLBACK.md`
10. `C:\tetie\notecode\新しいフォルダー\新しいフォルダー (5)\PERSONA_ITERATIVE_TRIAL_WINDOW_PROMPT_2026-04-23.md`

## objective
Run the live 7-type sweep on the current mainline only:

- `C:\tetie\notecode\note\note_writer_app.py`
- `-> C:\tetie\notecode\note\current_mainline_runner.py`
- `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

Your acceptance target is not "tests passed". Your acceptance target is:

- the article reads naturally for the intended article type
- the viewpoint and audience are visible to a strict reviewer
- source-backed types remain source-backed
- no internal persona/trial/source-contract leakage appears in visible output
- the per-type loop reaches stable success or is cleanly exhausted with evidence

Use UI simulation for acceptance. Pipeline-only runs may support diagnosis, but they do not count as final validation.

## hard boundaries
- Do not edit `C:\tetie\notecode\note\article_generator.py`.
- Do not edit `C:\tetie\notecode\note\article_style_persona_mixin.py`.
- Do not reopen legacy persona shims.
- Do not change the product UI default `一般読者`.
- In this initiative, any run that silently falls back to `一般読者` is a trial failure unless that audience was explicitly entered.
- Keep `single-pass + optional single repair 1回`.
- Do not expose `persona`, `editor`, `trial`, `source_contract`, `hidden`, or similar internal labels in visible prompt/output.
- Keep changes narrow: `1 phase = 1 narrow hypothesis = 1 owner scope`.
- If a change worsens results, roll it back and log the rollback reason.

## current implementation status
Assume the following implementation already exists and should be used as the starting baseline:

- hidden runtime fields:
  - `_persona_contract`
  - `_source_packet`
  - `_persona_trial`
- current-mainline prompt consumption for generation/editing/repair guards
- `pipeline_check.persona_trial` telemetry
- trial tooling and artifact initialization under:
  - `C:\tetie\notecode\tools\run_persona_iterative_trial.py`
  - `C:\tetie\notecode\新しいフォルダー\新しいフォルダー (5)\persona_iterative_trial_window_run`

Do not reopen already-solved implementation work without live evidence.
Only patch code when a concrete failure in the live loop points to a narrow owner-local fix.

Initialize or refresh artifacts first:

```powershell
py -3 C:\tetie\notecode\tools\run_persona_iterative_trial.py
```

## source policy
For each blog type, first use the best source set available for that type.

Priority order:

1. local or already-available source material that clearly matches the article type
2. source documents already used by the current fixture/harness
3. web search when the available source set is weak, mismatched, or missing

When using web search:

- prefer primary or official sources when possible
- use web search as evidence for the next narrow improvement or to build the source set
- log every search decision in `search_log.md`
- do not make runtime behavior depend on search evidence unless the resulting code/tests also support it

For each type, build a source set that is appropriate to the article form:

- `explanatory_article`: concrete operational memo, official docs, implementation notes, factual how/why source
- `daily_story`: prompt-led or diary-like source, but still keep explicit audience and visible return point
- `branding / company_introduction`: current business, entry-point friction, support boundary, operating steps, consultation/decision clue
- `announcement`: official notice with date/timing, target, change, impact, next action
- `case_study`: before, action, process, after, remaining issue, evidence
- `industry_analysis`: market/industry reports or primary data with explicit evaluation angle
- `comparative_review`: comparable options, axes, tradeoffs, fit conditions, next-step decision clue

## execution loop
Run the full 7-type sweep:

- `explanatory_article`
- `daily_story`
- `branding / company_introduction`
- `announcement`
- `case_study`
- `industry_analysis`
- `comparative_review`

For each type, keep the loop narrow:

1. Baseline run 1
2. Baseline run 2
3. Review both outputs strictly
4. Identify exactly one dominant failure
5. Apply exactly one narrow change
6. Rerun 1
7. Rerun 2
8. Review again
9. Keep or rollback

Per type rules:

- maximum `5` loops per type
- early stop on stable success
- rollback worsening changes
- do not stack multiple broad fixes in one loop

Stable success means:

- `2` consecutive accepted loops
- no meaningful regression across the last `4` generated articles

Exhausted means:

- `5` loops completed and stability is still not reached

When you need to execute the sweep artifact plan, use the driver as support tooling:

```powershell
py -3 C:\tetie\notecode\tools\run_persona_iterative_trial.py --execute --live
```

If you only need to refresh manifests/log scaffolding, do not add `--execute`.

## per-run checks
For every run, verify all of the following:

- audience is explicit
- `pipeline_check.persona_trial.resolved_audience` is correct
- `pipeline_check.persona_trial.default_audience_fallback_used` is `false`
- `pipeline_check.persona_trial.audience_valid_for_trial` is `true`
- persona family keys and late-return target are coherent with the article type
- visible output has no internal leakage
- source-backed article types do not drift outside source support
- repair/regeneration remains bounded and same-family
- no `SYS_PIPELINE_FAILURE`
- no unresolved quality failure that should block acceptance

Dominant failure labels should be chosen from evidence such as:

- `persona_not_fired`
- `audience_unclear`
- `default_audience_fallback`
- `source_packet_weak`
- `editing_not_firing`
- `regeneration_not_same_family`
- `company_intro_contract_unresolved`
- `generic_brochure_drift`
- `generic_blogger_drift`
- `late_return_missing`

If code changes become necessary, run the required checks from:

- `C:\tetie\notecode\plan\persona_iterative_trial_2026-04-23\TASK.md`

Minimum command set:

```powershell
py -3 -m py_compile <touched files>
py -3 -m pytest C:\tetie\notecode\note\tests\test_current_mainline_runner.py
py -3 -m pytest C:\tetie\notecode\note\tests\test_current_mainline_regressions.py
py -3 -m pytest C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py
py -3 -m pytest C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
py -3 -m pytest C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py
```

## logging
Write all live-trial evidence under:

- `C:\tetie\notecode\新しいフォルダー\新しいフォルダー (5)\persona_iterative_trial_window_run`

Required logs:

- `trial_plan.md`
- `change_log.md`
- `search_log.md`
- `rollback_log.md`
- `persona_matrix.md`
- `source_packet_notes.md`
- `case_manifest.json`
- per-type case directories with:
  - screenshots
  - generated outputs
  - quality reports
  - strict review notes
  - pass/fail decisions

For every narrow change, record:

- timestamp
- article type
- exact file(s) changed
- changed owner
- reason for the change
- expected benefit
- result after the next 2-run check
- keep or rollback decision

## image phase
Start image generation only after a type becomes stable.

For stable types only:

- use the existing GPT Image 2 flow
- align the image with the accepted article
- preserve comfortable text headroom when title-like text is used
- save prompt, revised prompt, image output, and validation screenshot

## final report
At the end of the window, answer with evidence:

1. Did the current hidden persona/source-packet path materially improve visible article quality?
2. Which article types reached stable success?
3. Which article types failed mainly because of source quality/coverage rather than persona routing?
4. Which narrow improvements helped most?
5. Which changes were rolled back because they worsened the result?
6. Did audience clarity improve in a way a strict reviewer could actually see?
