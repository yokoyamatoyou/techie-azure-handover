# current_mainline_company_intro_source_grounding_weak_reflection_diagnosis_2026-04-27 PROGRESS

## Current Status

- Package status: diagnosis completed; implementation follow-up completed
- Date: `2026-04-27 JST`
- Mode: docs-only diagnosis + owner-local implementation follow-up
- Artifact: `C:\tetie\notecode\logs\article_type_self_perspective_quality_validation_record_continue_rerun_20260427-085139\`
- Follow-up artifact: `C:\tetie\notecode\logs\company_intro_source_grounding_observability_fix_20260427-100546\`
- Product code change: yes, owner-limited to `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`
- Test change: yes, focused cases in `C:\tetie\notecode\note\tests\test_newalgorithm_phase06_logging_compat.py`
- UI server started: yes, Kotomake restarted so runtime loaded changed observability code
- Pytest: completed; focused checks passed
- AGENTS update: not needed
- WORKLOG update: completed

## Implementation Follow-up 2026-04-27

Owner:

- `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`

Narrow change:

- Added company-introduction-only operational slot proxy evidence inside source grounding observability.
- Existing literal anchor matching remains first path.
- Proxy evidence is applied only when the source item maps to one of the required `company_introduction_operational_source_contract_v1` slots:
  - `current_business`
  - `customer_situation_or_entry_point`
  - `support_scope_boundary`
  - `operating_process_steps`
  - `pre_contact_decision`
- Threshold remains unchanged: `source_grounding:weak_reflection` still requires `source_grounding_item_count >= 2` and `source_grounding_reflection_ratio < 0.5` unless an existing auxiliary pass applies.
- No prompt / persona / source contract / quality_guard / output_guard / pipeline / note_writer_app / blog_image_auto changes.

Focused checks:

- `.\.venv\Scripts\python.exe -m py_compile note\newalgorithm_pipeline\quality_observability_mixin.py note\tests\test_newalgorithm_phase06_logging_compat.py` passed.
- `.\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase06_logging_compat.py -q` passed: `35 passed`.
- `.\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py -k "source_grounding or quality_observability" -q` passed: `2 passed, 74 deselected`.
- `.\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_regressions.py -k "source_grounding" -q` passed: `2 passed, 30 deselected`.

Artifact recompute:

| Attempt | Before ratio | After ratio | Before warning | After warning |
|---:|---:|---:|---|---|
| 1 | 0.2 | 1.0 | `source_grounding:weak_reflection` | none |
| 2 | 0.4 | 1.0 | `source_grounding:weak_reflection` | none |
| 3 | 0.4 | 1.0 | `source_grounding:weak_reflection` | none |

UI rerun:

| Attempt | Outcome | Source grounding | Image | Remaining repair |
|---:|---|---|---|---|
| 1 | `publishable_success` | `5/5`, ratio `1.0`, no weak reflection | success, 2 files | required, rejected |
| 2 | `publishable_success` | `5/5`, ratio `1.0`, no weak reflection | success, 2 files | required, rejected |
| 3 | `publishable_success` | `5/5`, ratio `1.0`, no weak reflection | success, 2 files | required, rejected |

Residual:

- Repair rejection remains present in all 3 attempts, but did not block publishable output in this rerun.
- Self-perspective remains a separate issue: bodies still mostly read as third-party explanatory voice.
- The first UI rerun used stale already-running Kotomake code and reproduced weak reflection; Kotomake was restarted and the fresh runtime rerun passed.

## Baseline

Record-and-continue rerun after harness fix:

| Article type | Outcome |
|---|---|
| `announcement` | 3/3 `publishable_success`, image 6/6 success |
| `comparative_review` | 3/3 `publishable_success`, image 6/6 success |
| `company_introduction` | 3/3 `review_required_draft` |

Company-introduction shared facts:

- `blocked_output_redacted=false` in all 3 attempts.
- Body is visible in all 3 attempts.
- `SYS_QUALITY_WARNINGS_UNRESOLVED` in all 3 attempts.
- `source_grounding:weak_reflection` in all 3 attempts.
- `repair_required=true` and `repair_rejected=true` in all 3 attempts.
- Product code hash status: `NO_PRODUCT_CODE_HASH_DIFF`.

## Attempt Comparison

| Attempt | Outcome | Item count | Reflected | Ratio | Groups matched / partial / missing | Metadata excluded | Contract validation | Repair |
|---|---|---:|---:|---:|---|---:|---|---|
| 1 | `review_required_draft` | 5 | 1 | 0.2 | 1 / 3 / 1 | 0 | required 5 slots all present, all `strong`, no trigger ids | required, rejected |
| 2 | `review_required_draft` | 5 | 2 | 0.4 | 2 / 3 / 0 | 0 | required 5 slots all present, all `strong`, no trigger ids | required, rejected |
| 3 | `review_required_draft` | 5 | 2 | 0.4 | 2 / 1 / 2 | 0 | required 5 slots all present, all `strong`, no trigger ids | required, rejected |

## Body / Source Reflection Notes

Visible bodies reflect the intended operational company-introduction slots:

- `current_business`: data input, entry, analysis, scanning, RPA support are explained in all attempts.
- `customer_situation_or_entry_point`: data usage purpose is unclear, collection/aggregation/analysis may be outsourced, and consultation can begin before details are fixed.
- `support_scope_boundary`: input, scanning, research, analysis, RPA support, operations support, and pre/post-processing appear in body text.
- `operating_process_steps`: inquiry, staff contact, meeting by in-person or Zoom, NDA if needed, estimate are described.
- `pre_contact_decision`: readers are told to separate purpose, data type, scope to outsource, and what decisions remain internal.

Runtime source contract validation agrees with the manual read:

- checked: true
- scope_match: true
- pattern: `company_introduction_operational_source_contract_v1`
- missing required slots: none
- unbacked required slots: none
- script packet statuses: all `strong`
- brochure-only / generic-company-copy / abstract-philosophy-only / wrong article type drift: false
- unsupported claim added: false
- source limit leakage: false

## Source Grounding Diagnostic Read

The source grounding denominator contains 5 groups:

- current business group includes company title, `1885年`, URL-like material, and catchcopy.
- entry point group combines service list, consultation problems, and data-input/scanning proposal text.
- support scope group combines input accuracy, security, nationwide support, customer seriousness, and pre/post-processing.
- process group combines inquiry, phone/email, staff contact, meeting mode, Zoom, NDA, and estimate text.
- pre-contact decision group combines questionnaire input, data usage, accurate questionnaire forms, input data, market research, Web research, and price-adjacent page content.

These groups are source-backed but too long and composite for literal anchor matching. The body often paraphrases them naturally, so group-level matching undercounts semantic reflection.

Suspicious observability points:

- `metadata_excluded_count=0` even though the first group contains title / URL / catchcopy-like material.
- `title_like_groups=0` even though the first group behaves like a title-like composite anchor.
- `source_grounding_group_auxiliary_pass=false` in all 3 attempts despite runtime company-introduction source contract validation being clean.

## Classification

Primary classification:

- `observability_anchor_mismatch`

Secondary classification:

- `source_packet_shape_issue`

Not primary:

- `true_source_grounding_failure`
- `company_intro_contract_alignment_issue`
- `repair_rejection_secondary`

Reason:

- The visible article reflects the company-introduction operational slots.
- Company-introduction source contract validation is clean.
- `contract_alignment` is not the blocker: alignment score is about `0.81`, must-cover reflection is `0.75`, source outside claim evidence was not observed.
- The source grounding metric is counting long composite anchors, not isolated reader-visible source facts.

## Repair Relationship

- `source_grounding:weak_reflection` is included in output guard hard-fail reasons and contributes to `SYS_QUALITY_WARNINGS_UNRESOLVED`.
- Repair ran in all 3 attempts.
- Repair candidates were complete tagged articles, but were rejected.
- The repair metadata shows trigger and source contract improvement, but source reflection / alignment / fingerprint acceptance did not clear.
- Repair rejection remains a separate secondary issue and should not be fixed before the source grounding observability blocker is isolated.

## First Blocker Decision

First blocker:

- source grounding observability / anchor grouping mismatch

Next owner:

- `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py`

Next narrow hypothesis:

- for `company_introduction`, source grounding anchor extraction/grouping overweights composite source excerpts and title/URL-like fragments; focused observability should measure atomic, reader-visible anchors without threshold relaxation or warning demotion.

## Hold Decision

`company_introduction` remains hold after this diagnosis.

Even if source grounding observability is fixed later, self-perspective consumption and repair rejection remain separate unresolved issues.
