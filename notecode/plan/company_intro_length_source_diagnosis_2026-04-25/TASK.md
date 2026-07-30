# company_intro_length_source_diagnosis_2026-04-25 TASK

## Global Rules

- First action is diagnosis / measurement.
- Runtime behavior remains unchanged unless Phase 5 finds one strong, narrow cause.
- `single-pass + optional single repair 1回` remains the baseline.
- `1 issue = 1 narrow hypothesis = 1 owner scope`.
- Green phases continue without waiting for user confirmation.
- Same error may be retried up to 3 times in one phase. Stop after the third same error and report phase, command, error excerpt, attempted fixes, blocked responsibility, rollback candidate, and residual risk.

## Phase Map

| Phase | Scope | Owner files | Behavior change | Exit |
|---|---|---|---|---|
| 0 | read / package / baseline | plan package only | no | required docs/logs read, package created, baseline tests recorded |
| 1 | instrumentation audit design | plan notes / code inspection only | no | metric source map written; unavailable fields have fallback estimation rules |
| 2 | diagnosis runner | plan package runner and logs | no runtime change | runner writes raw result, metrics, excerpt, and error files |
| 3 | 15-run diagnosis | generated logs | no runtime change | Kyoto Kogyo 15 runs completed or fail-closed rows recorded; optional extra company if available |
| 4 | classification | generated metrics/report | no | target / compression / realization / repair rejection cause classified |
| 5 | narrow fix only if evidence is strong | one owner scope TBD | yes, only if justified | one focused fix plus owner-local regression, or explicit no-fix decision |
| 6 | closeout / record | plan docs, logs, optional WORKLOG | no unless Phase 5 used | final judgment and next decision recorded |

## Phase 0 Required Checks

```text
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
```

## Phase 1 Metric Source Map

- Prefer existing result / pipeline_check / diagnostics fields.
- If `target_chars` or `length_mode` is unavailable, record `not available`; do not infer zero.
- If `source facts reflected count` is not available, estimate only from explicit source slot coverage and mark the method.
- If repair candidate summaries are present, compare candidate body chars / section lengths / slot coverage against final artifact.
- Runner-side estimates are allowed for section distribution, final paragraph chars, title chars, and lead chars.

## Phase 2 Runner Requirements

- Save logs under:

```text
C:\tetie\notecode\logs\company_intro_length_source_diagnosis_YYYYMMDD-HHMMSS\
```

- Save per run:
  - raw result JSON
  - metrics JSON
  - visible text excerpt
  - error JSON/TXT if generation fails
- Save aggregate:
  - metrics JSONL
  - metrics JSON
  - summary Markdown
  - classification Markdown/JSON after Phase 4
- Console output must be ASCII-safe to avoid Windows console encoding failures.
- Do not change runtime code to expose metrics.

## Phase 3 Run Scope

- Required:
  - Kyoto Kogyo source-rich company introduction: 15 runs
- Optional:
  - one additional source-rich company introduction profile from existing fixture/logs: 5 runs
- If no suitable additional company profile is found, proceed with Kyoto Kogyo only.

## Phase 4 Classification Rules

- `target_low_suspected`
  - `target_chars` is around 1200 and `body_chars` follows it.
- `realization_shallow_suspected`
  - `target_chars` is 1600-2000+ but `body_chars` stays around 900-1200, or source packet has usable material but sections stay shallow.
- `compression_loss_suspected`
  - `source_total_chars` is enough but `source_packet_chars`, grounding item count, must-cover count, or slot text lengths are too small.
- `repair_rejection_suspected`
  - repair candidate materially improves explanation depth but is rejected.
- `source_thin`
  - source itself does not provide enough concrete expansion material.
- `fail_closed_ok`
  - failure is a correct hard guard and no thin visible article is returned.

## Phase 5 Fix Candidates

Select at most one if evidence is strong:

1. Keep slightly more required-slot explanation material in company introduction source packet.
2. Adjust company_introduction `target_chars` / length-mode estimation.
3. Add one source-backed explanation expansion step to company_intro section realization.
4. Fix only the repair acceptance connection if it rejects an explanation-improving candidate.

Forbidden:

- Broad length increase across article types.
- Quality threshold relaxation.
- Repair count increase.
- Prompt accretion.
- Source-outside claim permission.
