# Generation UI UX Gate Fix 2026-04-23

## Objective

User-test gate fix for the generation UI. The current UI mixes source-backed generation, omakase/web-source collection, prompt-only daily story, pre-generation confirmation, and stale confirmation states. This package narrows those transitions without changing runtime grounding rules or quality guard thresholds.

## Scope

- UI source mode and 1-line topic visibility in `note/note_writer_app.py`.
- Generation CTA/gate state when source, omakase inventory, or confirmation is incomplete.
- Confirmation invalidation copy in `note/current_mainline_ui_confirm_adapter.py`.
- Focused tests for UI helper state, confirmation copy, and required reader defaults.

## Non-Goals

- Do not lower guard thresholds.
- Do not add blacklist or cleanup layers.
- Do not expand prompts.
- Do not change the runtime mainline:
  `current_mainline_runner -> newalgorithm_pipeline -> simple_note_pipeline`.
- Do not treat past blog body text as factual source for the current article.

## Phases

1. Source mode / 1-line topic visibility
   - Hide 1-line topic in source-backed mode.
   - Expose prompt-only UI only for `daily_story` when past-blog unlock is satisfied.
   - Keep runtime `prompt_only` contract intact for compatibility.
2. Missing-input and stale-confirmation behavior
   - Prioritize source/omakase missing actions before generic confirmation prompts.
   - Replace "reconfirm waiting" wording with an actionable next step.
   - Preserve entered values when validation blocks progression.
3. Wizard compression
   - Keep the confirmation panel hidden until required inputs are committed.
   - Leave completed steps as compact summaries where existing UI state already supports it.
4. Verification
   - Update focused UI state tests.
   - Run py_compile for touched modules.
   - Run source mode / gate / confirm adapter tests and relevant runtime gate checks.

## Acceptance Checks

- Source-backed mode does not show the 1-line topic input.
- Source-backed mode with no sources points to source input before pre-generation confirmation.
- Prompt-only UI is not available without past-blog unlock.
- Omakase with insufficient past blogs cannot start from only a 1-line topic.
- Reader default passes required input gate.
- Confirmation invalidation does not end with "reconfirm waiting" copy.
- "Confirmed" state does not present as generatable when the active mode is missing sources.
