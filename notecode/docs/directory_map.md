# notecode Directory Map

Last updated: 2026-06-04

This document maps the current `C:\tetie\notecode` responsibility layout. It is a navigation and responsibility map, not a full file inventory. The filesystem remains the source of truth for exact file lists.

## Top Level

```text
C:\tetie\notecode\
|-- AGENTS.md
|-- ALGORITHM.md
|-- README.md
|-- WORKLOG.md
|-- docs\
|-- logs\
|-- note\
|-- 0506\
|-- plan\
|-- archive\
|-- backups\ (empty shell; snapshot files archived under archive\route_0506_archive_move_backups_only_20260512\)
|-- newalgorithm\
|-- human_resonance\
|-- human_resonance2\
```

## Responsibility Map

| Path | Responsibility | Current handling |
|---|---|---|
| `AGENTS.md` | notecode work entrypoint and Route 0506 work rules | Keep concise; link out to detailed docs and artifacts. |
| `ALGORITHM.md` | notecode algorithm source of truth | Keep current route contracts and Route A legacy caveats here. |
| `WORKLOG.md` | notecode-specific change and responsibility-split log | Use for module split decisions and local handoff details. |
| `docs\directory_map.md` | this responsibility map | Update when module ownership changes. |
| `docs\` | durable handoff docs, prompts, notices, failure summaries | Avoid dumping generated artifacts here unless user-facing review requires it. |
| `logs\` | run artifacts, validation evidence, inventories | Keep detailed evidence here; do not duplicate full detail into WORKLOG. |
| `note\` | current notecode app/runtime integration | Main target for responsibility split work. |
| `note\note_writer_app.py` | NiceGUI page shell, shared state/widgets, hidden legacy compatibility handles, and owner wiring | Confirmed bloat; writer-only card/click handler, manual legal UI, source input add/remove/upload state helpers, generated-image panel shell, app logging setup, app runner setup, client-scope timer/token registry/detached mutation handling, current-mainline compat wrappers, writer-role compatibility callables/import cleanup, writer-role status/select widget refresh, writer-role interaction state transitions, custom genre metadata constants, generation progress labels/display-state, output-shape display text, main-page section helpers, generation step indicator/progress refresh, required-input wizard/status explicit-widget refresh, journey-direction wizard explicit-widget refresh, journey-confirmation CTA explicit-widget refresh, interview followup/status explicit-widget refresh, core-message/profile-control explicit-widget refresh, source-mode choice-card/status refresh, journey/semantic label helpers, journey confirmation state helpers, interview-question rendering / pure workflow/signature helpers, required-input wizard pure helpers, generation gate helpers, fetch-failure helpers, announcement inline error text, and thin interview contract mapper wrappers have been split. Previous-source inventory restore for fresh clients is default-off and only opt-in via `NOTECODE_RESTORE_PREVIOUS_SOURCES_ON_NEW_CLIENT`. The unbound hidden `run_generation()` body, its unreferenced downstream helper island, legacy generated-image progress/timer compatibility island, def-only current-mainline / Route 0506 stubs, unreferenced ambiguity confirmation dialog island, unreferenced self-reference/explanatory-focus helper island, def-only client generation-token wrappers, a def-only current-mainline complete-plan UI wrapper, def-only scroll-to-result helper, def-only current-mainline question render wrapper, def-only journey-stage/manual-legal wrappers, def-only generation-phase UI wrapper, and unreferenced current-mainline/output-guard dead definitions have been removed. The old hidden `generate_button` NiceGUI object is replaced by a no-op compatibility target. |
| `note\note_writer_app_current_mainline_compat.py` | Lazy current-mainline runner/profile/runtime/UI adapter compatibility wrappers | Keep wrapper-only and lazy. Do not eager import Route A, Route 0506, `newalgorithm_pipeline`, or `simple_note_pipeline`; do not add writer-only, image, SNS / LinkedIn, source input, or manual legal behavior here. |
| `note\note_writer_app_generation_progress.py` | Pure generation progress display text, stage label, display-state, and percent helpers | Keep limited to progress text, display percent, display-state assembly, stage label, and stage percent projection helpers. Route 0506 labels/percent must stay injected through a callable. Do not add timer, pipeline, Route A / Route 0506 eager imports, writer-only, image, SNS / LinkedIn, source input, or manual legal behavior here. |
| `note\note_writer_app_generation_delay_display.py` | Pure generation-delay notice display text helper and slow-source thresholds | Keep limited to `_build_generation_delay_notice(...)` and its display thresholds. Do not add source collection, generation timing, writer-only, image, SNS / LinkedIn, source input, manual legal, or route behavior here. |
| `note\note_writer_app_journey_semantic_labels.py` | Pure journey compare-axis/goal/target and semantic article label mappings/helpers | Keep limited to label mapping, fallback projection, journey purpose/target labels, and target option/selection projection. Do not add UI state, source-mode gating, writer-only generation, image, SNS / LinkedIn, manual legal, or legacy route behavior here. |
| `note\note_writer_app_article_source_mode.py` | Pure article type catalog and source-mode option/helper text/input-surface helpers | Keep limited to fixed article type labels, prompt catalog projection, source-mode labels, prompt-only gating, and returned dict/text contracts. Do not add NiceGUI widget mutation, source add/remove/upload/fetch/review behavior, writer-only generation, image, SNS / LinkedIn, manual legal, or legacy route behavior here. |
| `note\note_writer_app_main_page_sections.py` | Main-page section rendering helpers and explicit-widget refresh helpers | Keep limited to page section construction, generation step/progress indicator mutation, required-input wizard/status widget mutation, writer-role status/select widget mutation, journey-direction wizard widget mutation, journey-confirmation CTA widget mutation, interview followup/status widget mutation, core-message/profile-control widget mutation, and source-mode choice-card/status widget mutation with explicit widget/value arguments. Do not add app-wide state/page context bundles, source fetching, API calls, writer-only generation, image, SNS / LinkedIn, manual legal, or legacy route behavior here. |
| `note\note_writer_app_subviews.py` | Small subview renderers, dialog builders, custom-genre metadata constants/dialog action wiring, privacy blur view shell, and display helper functions | Keep callbacks injected from the app. Do not add generation, API calls, source fetching, image generation, SNS / LinkedIn, manual legal automation, or legacy route behavior here. |
| `note\note_writer_app_logging.py` | App JSON logging formatter, benign NiceGUI error filter, and rotating log setup | Keep limited to logging setup. Do not add UI rendering, source fetching, API calls, writer-only generation, image, SNS / LinkedIn, manual legal, or legacy route behavior here. |
| `note\note_writer_app_runner.py` | NiceGUI startup port/headless/run helper for note_writer_app | Keep limited to startup parameter assembly and port probing. Do not add page rendering, generation, source fetching, API calls, image, SNS / LinkedIn, manual legal, or legacy route behavior here. |
| `note\note_writer_app_client_scope.py` | Client-scope timer and generation-token registry for note_writer_app | Keep limited to client key normalization, timer deactivation, active client tracking, attached-generation token checks, and detached-client mutation handling with injected logging/release callbacks. Do not add page rendering, generation payloads, source fetching, API calls, image, SNS / LinkedIn, manual legal, or legacy route behavior here. |
| `note\note_writer_core_message_helpers.py` | Pure core-message placeholder/helper text and required-input visibility predicate helpers | Keep limited to `_build_core_message_placeholder`, `_build_core_message_helper_text`, and `_requires_core_message_input`. Do not add NiceGUI widgets, source-session/generate-gate/wizard/audience/self-reference text, writer-only generation, image, SNS / LinkedIn, manual legal, source input, or legacy route behavior here. |
| `note\note_writer_interview_question_renderer.py` | Interview question card/select/input rendering helper | Keep limited to rendering already-filtered question items into an injected NiceGUI container with injected answer-change callback. Do not pass whole app state, fetch sources, notify, run LLM/API work, or add writer-only, image, SNS / LinkedIn, manual legal, source input, or legacy route behavior here. |
| `note\note_writer_interview_question_workflow.py` | UI-free interview question workflow projections, generation-prep interview state, context signatures, selection payload, and request kwargs builders | Keep pure. Own reason labels, missing-required field projection, question-policy kwargs, confirm-preview kwargs, interview context signature hashing, generation-request input normalization, generation-selection projection, interview-state reset/counting, and UI question-item filtering only. Do not import NiceGUI, `ArticleFetcher`, `run.io_bound`, LLM/API clients, writer-only, image, SNS / LinkedIn, manual legal, source input, or legacy route modules. |
| `note\note_writer_journey_confirmation_helpers.py` | Pure journey confirmation CTA state, confirm-button text, signature readiness, and source-session acceptance confirmation plan helpers | Keep UI-free. Do not import NiceGUI, mutate widgets, fetch sources, call APIs, or add writer-only, image, SNS / LinkedIn, manual legal, source input, or legacy route behavior here. |
| `note\note_writer_required_input_wizard.py` | Pure required-input wizard projections, defaults, helper text, typing-reset decisions, and writer-role interaction state transitions | Keep UI-free. Do not import NiceGUI, mutate widgets, fetch sources, call APIs, or add writer-only, image, SNS / LinkedIn, manual legal, source input, or legacy route behavior here. |
| `note\note_writer_generate_gate_helpers.py` | Pure source-mode, omakase, and generate-gate surface projection helpers | Keep UI-free and preserve lazy omakase preflight compatibility. Do not add NiceGUI mutation, API sends, image, SNS / LinkedIn, manual legal, source input mutation, or legacy route eager imports here. |
| `note\note_writer_fetch_failure_helpers.py` | Pure fetch failure classification, formatting, 403 URL extraction, source notice projection, and fetch-summary projection | Keep `ui.notify`, source mutation, fetch/IO, writer-only generation, image, SNS / LinkedIn, manual legal, and legacy route behavior out of this module. |
| `note\note_writer_announcement_inline_error.py` | Pure announcement inline validation error text helper | Keep limited to date/target/change wording checks and returned inline message text. Do not add UI mutation, writer-only generation, image, SNS / LinkedIn, manual legal, source input, or legacy route behavior here. |
| `note\note_writer_quality_report_helpers.py` | Pure quality/fingerprint report projection helpers | Keep limited to report flattening and display-safe metric projection. Do not import NiceGUI, output guard modules, LLM/API clients, writer-only, image, SNS / LinkedIn, manual legal, source input, or legacy route modules. |
| `note\note_writer_role_handoff_helpers.py` | Pure writer-role option/default and article handoff default helpers | Keep UI-free. Custom genre resolution must remain injected via a callable from `note_writer_app.py`; do not import `genre_manager`, NiceGUI, LLM clients, image generation, SNS / LinkedIn, source input, manual legal, or legacy route modules here. |
| `note\note_writer_detail_profile_constants.py` | Pure detail writing-profile option label dictionaries | Keep limited to detail/profile option labels such as branding subtype/focus, pattern select, tone profile, content goal, writing focus, length mode, and self-reference policy labels. Do not add UI widgets, event binding, selected-value resolution, writer-only generation, image, SNS / LinkedIn, source input, manual legal, or legacy route behavior here. |
| `note\note_writer_app_output_shape_display.py` | Pure article-type output-shape display text helper | Keep limited to `_describe_note_output_shape(...)`. Do not add UI mutation, writer-only generation, image, SNS / LinkedIn, source input, manual legal, or legacy route behavior here. |
| `note\note_writer_app_ui_compat.py` | Tiny no-op UI compatibility targets for removed hidden legacy controls | Keep small; do not add visible UI rendering or legacy generation behavior here. |
| `note\note_writer_app_writer_only_ui.py` | Visible normal UI generation card, Route B click handler glue, article/SNS result mapping glue, and injected fail-open post-success image handoff | Keep small; do not add Route A behavior here. Image generation must remain injectable for stubbed tests. |
| `note\route_b_generation_service.py` | Normal UI Route B service boundary: strict source intake, Route B adapter call, route flags, latest output / quality report projection, and SNS fallback text from generated article | Keep thin. Do not add Route A fallback, writer-only fallback, broad prompt tuning, or rejected routes here. |
| `note\note_writer_app_generated_image_panel.py` | Generated-image auto panel shell, generated image refreshable container factory, and image touch selector construction | Keep display-shell only. Preserve `render_generated_images_subview(...)`, image state ownership, writer-only image handoff, and image algorithm ownership outside this module. |
| `note\note_writer_app_source_input_helpers.py` | Source input state/action helpers for add/remove/upload/recent-PDF recovery wiring | Keep UI rendering, privacy blur, and writer-only generation out of this module. Preserve `SourceItem` shape and inject app callbacks/dependencies. |
| `note\note_writer_app_manual_legal_ui.py` | Manual legal NiceGUI expansion, result display, and local button handlers | Keep `run_legal_postcheck` injected so legal postcheck remains lazy. Do not change hidden auto postcheck behavior here. |
| `note\note_writer_app_manual_legal_helpers.py` | Pure manual legal request/result/apply payload helpers | Keep UI-free and preserve existing helper behavior. |
| `note\writer_only_service.py` | End-to-end writer-only route orchestration for source intake, brief, writer, smoke evaluator, and artifact writing | Keep body generation on writer-only only. Do not restore Route 0506 / Route A, repair, or quality pipeline behavior here. |
| `note\writer_only_source_bundle.py` | Writer-only source policy routing and source bundle creation for http/https URLs and uploaded local documents | Keep URL policy strict for http/https. Uploaded `.pdf`, `.docx`, `.txt`, and `.md` paths are allowed only under `note\uploads`; arbitrary local paths and unsupported extensions remain fail-closed. |
| `note\writer_only_image_handoff.py` | Pure writer-only success-result to post-success image-context handoff helper | Keep small; resolve title/lead/body/article_type and compact source claims only. Do not call image generation or load legacy body routes. |
| `note\route_0506_ui_bridge.py` | Route 0506 UI invocation, blocked/progress view helpers, validation artifact projection | Keep Route 0506 UI bridge behavior stable while splitting. |
| `note\route_0506_structured_blog_adapter.py` | notecode-to-local-0506 adapter, source records, preflight, OpenAI compatibility, quality shims | Split only by proven owner; source/preflight and OpenAI compatibility are likely boundaries. |
| `note\route_0506_stage_output_guard.py` | Route 0506 stage output safety guard | Keep fail-closed. |
| `note\route_0506_security_gate.py` | Route 0506 source/security gate | Keep arbitrary local file rejection fail-closed. |
| `note\route_0506_usage_ledger.py` | Route 0506 usage ledger rows | Keep observability local and small. |
| `note\simple_note_pipeline\` | deprecated legacy Route A opt-out pipeline | Do not treat as current default; touch only as a separate Route A legacy owner. |
| `note\newalgorithm_pipeline\` | Route A compatibility path | Frozen/deprecated except explicit Route A opt-out maintenance. |
| `note\tests\` | focused and regression tests | Add tests only for touched owner boundaries. |
| `0506\` | local stable Route 0506 reference | Prefer this over Desktop 0506. Do not edit casually while stabilizing notecode adapter. |
| `plan\` | planning packages and historical/current initiatives | Keep as reference packages; do not make them runtime owners. |
| `archive\` | archived records and rejected route history | Reference only unless the user explicitly asks for archive maintenance. Includes `archive\route_0506_archive_move_docs_new_folder_5_20260512\新しいフォルダー (5)\` for the seven-file historical docs snapshot moved on 2026-05-12. |
| `backups\` | former old snapshot code location | Snapshot files were moved under `archive\route_0506_archive_move_backups_only_20260512\backups\` in the backups-only archive owner. Empty directories may remain; do not delete without a separate owner. |
| `newalgorithm\` | older design/mapping records | Reference only unless a current owner proves it is active. |

## Current Main Routes

Current visible writer-only UI body generation:

```text
C:\tetie\notecode\note\note_writer_app.py
-> C:\tetie\notecode\note\note_writer_app_writer_only_ui.py
-> C:\tetie\notecode\note\writer_only_service.py
-> C:\tetie\notecode\note\writer_only_source_bundle.py
```

Writer-only post-success image handoff context:

```text
C:\tetie\notecode\note\writer_only_service.py result/artifacts
-> C:\tetie\notecode\note\writer_only_image_handoff.py
-> C:\tetie\notecode\note\note_writer_app_writer_only_ui.py injected image generator
-> C:\tetie\notecode\note\blog_image_auto.py
```

This handoff starts only after writer-only success and is fail-open; image failure does not invalidate article or SNS / LinkedIn output.

Deprecated legacy Route A opt-out:

```text
C:\tetie\notecode\note\current_mainline_runner.py
-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
```

## Current Split Candidates

1. `note\note_writer_app.py`
   - Completed first owner: `writer_only_ui_handler_extraction`
   - Completed followup owner: `manual_legal_ui_extraction`
   - Completed cleanup owner: `current_mainline_downstream_dead_helper_removal_after_hidden_run_generation`
   - Completed followup owner: `source_input_add_remove_upload_state_helper_extraction_after_inventory`
   - Completed followup owner: `generated_image_auto_panel_shell_extraction`
   - Completed followup owner: `generated_image_legacy_progress_timer_removal_after_inventory`
   - Completed cleanup owner: `def_only_current_mainline_and_route0506_stub_removal_after_inventory`
   - Completed followup owner: `current_mainline_compat_wrapper_module_extraction_after_def_stub_removal`
   - Completed followup owner: `generation_progress_display_helper_extraction_after_compat_extraction`
   - Completed followup owner: `note_output_shape_display_helper_extraction_and_followup_inventory`
   - Completed followup owner: `generation_delay_notice_display_helper_extraction_and_journey_semantic_inventory`
   - Completed followup owner: `journey_semantic_label_helper_group_extraction_and_article_source_role_inventory`
   - Completed followup owner: `article_source_mode_pure_helper_extraction_and_writer_role_handoff_inventory`
   - Completed followup owner: `core_message_ui_text_helper_extraction_only`
   - Completed self-driving guarded owner: `note_writer_app_shrink_to_around_1000_self_driving_guarded`
   - Remaining candidates: still-referenced UI closure islands, especially `main_page()`, `load_interview_questions`, `_refresh_journey_confirm_preview`, source-mode status, and generation progress polling groups. Handle with inventory-first owners if they would otherwise require a large widget/state context bundle.
   - Do not restore Route 0506 / Route A, change fallback behavior, generation logic, legal checks, or image generation during split work.

2. `note\route_0506_structured_blog_adapter.py`
   - Candidate boundaries: source extraction/preflight, local 0506 module loading, OpenAI structured-output compatibility, quality boundary shims.
   - Split only after `note_writer_app.py` branch inventory or a separate proven owner.

3. `note\simple_note_pipeline\pipeline.py`
   - Large, but Route A is deprecated legacy opt-out.
   - Defer unless the owner is explicitly Route A legacy maintenance or archival reduction.

4. `note\simple_note_pipeline\prompt_builder.py`
   - Large prompt contract owner for Route A legacy.
   - Do not conflate with Route 0506 prompt bloat; local 0506 prompt files are currently small.

## Update Rules

- Update this file when a module is split, moved, archived, or newly assigned a durable responsibility.
- Keep this file as a map, not a changelog. Put change history in `WORKLOG.md`.
- If a candidate is only suspected dead code, record it as a candidate until import/text references and runtime/test impact are checked.
