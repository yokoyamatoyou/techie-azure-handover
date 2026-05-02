# PHASE 05: Layout Guard

## Objective
Protect global article structure so supplemental content appears in natural positions and flow remains coherent.

## Inputs
- structured draft (title, sections, paragraphs)
- config keys:
  - `phase05_layout_guard_enabled`
  - `supplement_min_position_ratio`
  - `intro_max_length_ratio`
  - `section_coherence_min_score`

## Outputs
- `layout_validation_report`
- `supplement_position_alerts`
- `reorder_plan` (structure-preserving)

## Tasks (GPT-5 mini granularity)
1. Identify section roles (intro, core explanation, supplement, conclusion).
2. Detect supplemental blocks placed too early.
3. Enforce supplement position after `supplement_min_position_ratio`.
4. Validate heading continuity and transition quality.
5. Apply minimal reordering without deleting content.

## DoD
1. Intro does not absorb supplemental details excessively.
2. Supplemental blocks are placed from mid-section onward.
3. Final structure remains consistent and readable.

## Test View
1. Draft with early supplement -> alert and corrected ordering.
2. Already well-structured draft -> no forced changes.
3. Verify title and section headings remain intact.

## Rollback
Disable `phase05_layout_guard_enabled`.

## Failure Handling
1. Try one correction for section-role misclassification.
2. If unresolved, stop phase and report structure parse result.

