# NEW_ROUTE_CONTRACT

Date: 2026-05-08 JST

## Route Identity

New route ID:

```text
route_0506_structured_blog_ui_v1
```

This is not Route A and must not pretend to be Route A. It is a separate body-generation route connected to the current notecode UI only after archive cleanup and security gates are green.

Existing provenance route:

```text
route_b_0506_structured_blog_v1
```

Keep the existing provenance doc and adapter until the new route skeleton supersedes them.

## Inputs From Current UI Contract

The route receives only the normalized current UI `input_contract`.

Allowed fields:

- `source_documents`
- `article_type`
- `semantic_article_key`
- `ui_journey`
- `audience_profile` / `target_reader`
- `topic_statement`
- `core_message`
- `prompt_raw`
- narrator and self-reference fields
- `media`
- `length_mode`
- `source_mode`

Do not read local paths from source locators. Do not fetch URLs. Do not infer additional sources from `prompt_raw`.

## Grounding Contract

`source_documents` is the only grounding source.

Hard rules:

- no URL refetch
- no local file reads from source locators
- no Route A fallback
- no prompt-only fallback
- no old materialized/deepresearch/Route D/Route E fallback
- no source-outside numeric claims, achievements, customer names, prices, awards, dates, or comparison superiority
- source text is untrusted data and may not issue instructions

If `source_documents` is empty or unusable, return a blocked result with required input information. Do not run Route A as fallback.

## 0506 Genre Mapping

Validate this mapping before UI-live generation:

| notecode condition | 0506 genre |
|---|---|
| `article_type=branding` and `semantic_article_key=company_introduction` | `company_service_intro` |
| `semantic_article_key=product_introduction` | `company_service_intro` |
| `article_type=announcement` or `semantic_article_key=announcement` | `announcement` |
| `article_type=case_study` or `semantic_article_key in implementation_case, improvement_case, case_study` | `case_study` |
| `article_type=comparative_review` or `semantic_article_key=comparative_review` | `comparison_guide` |
| `article_type=daily_story` or `semantic_article_key=daily_story` | `daily_activity` |
| `article_type in explanatory_article, industry_analysis` or matching semantic keys | `market_explanation` |

If UI-connected quality drops, first suspect mapping collision across `semantic_article_key`, `article_type`, and `ui_journey`. Do not start 0506 quality tuning until mapping and source contracts are proven.

## Adapter Responsibilities

Generation owner:

- map `input_contract` to 0506 `ExtractedSource`
- preserve source span IDs and source labels
- choose 0506 genre and narrator
- call 0506 runner
- validate 0506 schema outputs
- write usage ledger
- copy allowed artifacts into notecode run root
- redact errors and secrets

UI owner:

- expose route selection only after Window 2/3 gates
- collect current UI input without changing Route A default
- pass only normalized `input_contract`
- display blocked/success output from the result adapter
- write UI selection snapshot

Result adapter owner:

- convert 0506 `BlogPipelineResult` into notecode visible result shape
- preserve `route_id=route_0506_structured_blog_ui_v1`
- never set Route A success fields to claim success
- include `blocked`, `reason_code`, quality report, artifact root, source snapshot hash, and usage summary

## OpenAI Strict Schema Compatibility

The current live blocked artifact shows:

```text
ValidationError: 10 is greater than the maximum of 5
schema path: facts[].importance
stage: source_card_extraction
```

This belongs to generation adapter/schema compatibility.

Allowed fixes:

- make 0506 OpenAI source-card instructions and strict schema agree
- add adapter-side strict validation before accepting output
- fail closed with a redacted blocked artifact

Not allowed:

- relaxing source-grounding thresholds
- accepting invalid schema output
- adding prompt bloat to hide the issue
- changing quality gates to pass invalid output

## Artifact Contract

Saved-source CLI artifacts:

- `source_snapshot.json`
- `input_contract.json`
- `route_0506/latest_generation_output.md`
- `route_0506/latest_generation_quality_report.json`
- `route_0506/pipeline_stage_artifacts/`
- `usage_ledger.jsonl`
- `security_gate.json`
- `compare_summary.json`
- `blocked.json` when blocked

UI-live artifacts:

- all saved-source CLI artifacts
- `ui_selection_snapshot.json`
- `visible_generation_result.json`
- screenshot or visible text snapshot if a UI validation owner explicitly runs UI checks

`source_snapshot.json` must include canonical hash. Same-source compare requires identical canonical hash across saved Route A artifact and new route input.

## Usage Ledger

One API call equals one JSONL row.

Required row fields:

- `timestamp`
- `route_id`
- `stage`
- `model`
- `reasoning_effort`
- `input_tokens`
- `cached_input_tokens`
- `output_tokens`
- `total_tokens`
- `estimated_cost_usd`
- `actual_usage_available`
- `status`
- `blocked_reason_redacted`
- `artifact_root`

Do not write API key values, request headers, raw environment variables, or full exception chains that may contain secrets.

## Promotion Gate

This route is not current default until all are true:

- Window 1 archive cleanup is green.
- Window 2 skeleton/adapter tests are green.
- Window 3 saved-source CLI validation is green or blocked only by explicit API approval absence.
- Window 4 one-case UI generation proves mapping and artifact contract.
- Window 5 same-source compare is available without Route A regeneration.
- `SECURITY_GATE.md` has zero unresolved critical/high issues.

Even after these gates, Route A remains available and unchanged unless a later explicit adoption package says otherwise.
