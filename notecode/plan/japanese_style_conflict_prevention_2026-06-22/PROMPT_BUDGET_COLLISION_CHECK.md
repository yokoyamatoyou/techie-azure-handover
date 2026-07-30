# Prompt Budget Collision Check

Status: proposal / non-current

Current owner preserved: `draft_writer_depth_budget_contract_smoke_failure_diagnosis`

Owner executed in this document: `prompt_budget_collision_check`

Decision: prompt budget collision check completed as a read-only proposal artifact. No product code, prompt template, AGENTS, WORKLOG, or API-validation change is authorized by this document.

## Scope

This document checks current prompt templates for:

- physical and nonblank line counts,
- prompt-budget threshold risk,
- duplicated instruction surfaces,
- external-reference wording or full-manual contamination risk,
- future collision points if style-conflict contracts are ever rendered.

This slice does not edit prompts or rendered prompt code.

## Inputs Read

- `notecode/plan/japanese_style_conflict_prevention_2026-06-22/README.md`
- `notecode/plan/japanese_style_conflict_prevention_2026-06-22/INVENTORY.md`
- `notecode/plan/japanese_style_conflict_prevention_2026-06-22/RESEARCH_PLAN.md`
- `notecode/plan/japanese_style_conflict_prevention_2026-06-22/CONTRACT_DESIGN.md`
- `notecode/plan/japanese_style_conflict_prevention_2026-06-22/QA_CANDIDATE_AUDIT.md`
- `notecode/plan/japanese_style_conflict_prevention_2026-06-22/GENRE_APPLICABILITY_MATRIX.md`
- `notecode/0506/docs/CONFIG_AND_PERSONA_POLICY.md`
- `notecode/0506/app/prompts/draft_writer.md`
- `notecode/0506/app/prompts/style_editor.md`
- `notecode/0506/app/prompts/structural_editor.md`
- `notecode/0506/app/prompts/japanese_quality_checker.md`
- `notecode/0506/app/prompts/targeted_rewriter.md`

## Non-goals

- Do not implement product code.
- Do not change prompt templates.
- Do not change AGENTS.md or WORKLOG.md.
- Do not run API validation.
- Do not reopen Route A fallback, writer-only fallback, old repair loops, or raw full `source_documents` pass.
- Do not relax QA thresholds or repair acceptance.
- Do not paste external manuals, Gist text, or Web-source wording into prompts.
- Do not propose broad prompt tuning.
- Do not increase module bloat or prompt bloat.

## Current Boundary

The current Route B / 0506 owner remains:

```text
draft_writer_depth_budget_contract_smoke_failure_diagnosis
```

This read-only prompt budget check does not change DraftWriter, the depth-budget contract, source-shape detection, claim allocation, QA thresholds, repair acceptance, Route A fallback, writer-only fallback, raw source handoff, reader-meta filtering, style postprocessor behavior, or the H1 contract.

## Prompt Size Thresholds

From `CONFIG_AND_PERSONA_POLICY.md`:

- Prefer each prompt template under 120 lines.
- A prompt over 180 lines requires prompt-bloat review.
- Shared rules should live in config/persona/policy docs and be rendered selectively.
- Do not copy the same forbidden phrase list into every prompt.
- Do not add prompt text until the responsible owner is identified.

## Current Prompt Counts

Line count method:

- physical lines: PowerShell `Get-Content` line count, including blank lines;
- nonblank lines: same file after removing blank lines.

The existing `CONTRACT_DESIGN.md` count matches the nonblank line count.

| Prompt template | Physical lines | Nonblank lines | Bytes | Budget status |
|---|---:|---:|---:|---|
| `draft_writer.md` | 15 | 11 | 327 | under 120; no bloat |
| `japanese_quality_checker.md` | 8 | 6 | 276 | under 120; no bloat |
| `structural_editor.md` | 11 | 8 | 303 | under 120; no bloat |
| `style_editor.md` | 8 | 6 | 189 | under 120; no bloat |
| `targeted_rewriter.md` | 5 | 4 | 183 | under 120; no bloat |

Current prompt budget result:

```text
prompt_bloat: none
```

## External-reference Contamination Check

Read-only search found no prompt-template matches for:

- Gist or `japanese-tech-writing`,
- JTF / Google / Microsoft / GOV.UK / Nielsen / NIST / OpenAI source labels,
- proposal contract IDs such as `style_conflict_contract`, `floor_safe_local_only`, `source_claims_only`, `genre_weighted`, or `flagged_spans_only`,
- universal one-sentence, footnote, or technical-writing manual wording.

External-source wording risk:

```text
external_manual_text_in_prompts: false
```

## Duplicate Instruction Surfaces

Read-only search found these repeated safety boundaries:

| Instruction family | Prompt surfaces | Collision decision |
|---|---|---|
| Use only assigned claims / do not add unsupported facts | `draft_writer.md`, `style_editor.md`, `structural_editor.md`, `targeted_rewriter.md` | Allowed safety repetition. It protects source-grounding and should not be collapsed unless a future owner proves duplication causes prompt conflict. |
| Preserve names, dates, numbers, facts, claim IDs | `style_editor.md`, `structural_editor.md`, `targeted_rewriter.md` | Allowed safety repetition. It is stage-local and concise. |
| Narrator / viewpoint consistency | `draft_writer.md`, `style_editor.md`, `japanese_quality_checker.md`, `targeted_rewriter.md` | Allowed because viewpoint is a current source-of-truth contract. |
| Rhythm / connector / model-frequent detection | `japanese_quality_checker.md`, current stylometry policy | Allowed in QA only. Do not duplicate a full watchlist in prompts. |

Duplicate-rule risk:

```text
duplicate_rule_bloat: none
```

## Future Rendering Collision Risks

If a future owner ever renders this proposal's style-conflict contract, these are the safe limits.

| Future item | Safe rendering | Blocked rendering |
|---|---|---|
| Floor-safe redundancy | One compact ID or short bullet outside DraftWriter while current owner remains unresolved. | Any "shorten", "compress", or "remove redundancy" instruction in DraftWriter. |
| Source-grounded argument | One compact ID or short bullet that says logic must stay inside confirmed claims. | Any broad instruction to add causal links, reader objections, benefits, outcomes, or comparisons. |
| Genre-weighted strictness | Compact genre/profile flag. | A genre table copied into every prompt. |
| Rewriter locality | One compact ID or short bullet in targeted rewriter handoff. | Whole-article style rewrite instruction. |
| QA candidates | Existing issue types or one local issue family after audit. | Broad LLM review loop, second forbidden-word list, AI-detector gate, or threshold relaxation. |

## Stage-specific Prompt Budget Decision

| Stage | Current budget state | Style-conflict placement decision |
|---|---|---|
| DraftWriter | Very small template, but current owner is depth-budget smoke failure diagnosis. | Do not add proposal style rules here. DraftWriter placement remains blocked until current docs select a new owner. |
| Style editor | Very small template. | Future local style IDs may fit, but only after owner proof and floor-safe review. No edit now. |
| Structural editor | Very small template and best future fit for paragraph role and heading support fit. | Future compact rule IDs may fit, but no prompt edit now. |
| Japanese quality checker | Very small template. | Future deterministic issue IDs may fit if schema/tests select them. No duplicate watchlist. |
| Targeted rewriter | Very small template. | Future `flagged_spans_only` style locality language may fit, but current prompt already covers this boundary. No edit now. |

## Collision Decision

No prompt-budget collision blocks the proposal from moving to docs-only handoff.

Current prompt templates are far below the 120-line preferred limit and contain no external manual text. The main risk is future prompt bloat if a later owner pastes genre tables, external writing rules, or broad style manuals into prompts. That risk is preventable by keeping long rationale in proposal docs and rendering only compact IDs after a current owner explicitly selects prompt work.

## Recommended Next Owner

Recommended next owner inside this non-current proposal package:

```text
non_current_proposal_handoff
```

Reason: the read-only prompt budget check found no blocking prompt collision. The remaining safe work is to close or hand off this non-current proposal package without promoting it to current Route B / 0506 source of truth.

Recommended current Route B / 0506 owner remains:

```text
draft_writer_depth_budget_contract_smoke_failure_diagnosis
```

## Validation Summary

- Status included: yes, proposal / non-current.
- Current owner preserved: yes, `draft_writer_depth_budget_contract_smoke_failure_diagnosis`.
- Owner executed included: yes, `prompt_budget_collision_check`.
- Prompt templates read-only checked: yes.
- Physical and nonblank line counts included: yes.
- Duplicate instruction surfaces checked: yes.
- External-reference contamination checked: yes.
- Product code changed: false.
- Prompt template changed: false.
- AGENTS changed: false.
- WORKLOG changed: false.
- API validation used: false.
- Route A fallback used: false.
- Writer-only fallback used: false.
- Raw full `source_documents` passed: false.
- QA threshold relaxed: false.
- Repair acceptance relaxed: false.
- Prompt bloat: none.
- Module bloat: none.
