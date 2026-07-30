# TASK

## Phase Map

| Phase | Gate |
|---|---|
| 0 package scaffold | README / TASK / PROGRESS / ROLLBACK created |
| 1 artifact review | 6 `input_required_block` attempts identified from existing artifacts |
| 2 block classification | each blocked attempt assigned acceptance classification |
| 3 trial-scope decision | article types assigned `ready`, `ready_with_review_warning`, `hold`, or `source_needed` |
| 4 closeout | product-code hash unchanged, 18080 listener absent, WORKLOG updated |

## Owner Scope

- Owner: acceptance-review docs package only
- Runtime owner: none
- Product code owner: none

## Review Inputs

Use existing artifacts only:

- `post_run_acceptance_report.json`
- `image_validation_summary.json`
- per-attempt `attempt_summary.json`
- per-attempt `source_reconstructed_from_log.json`
- per-attempt `ui_visible_text.txt`

Do not rerun generation and do not start the UI server.

## Classification Criteria

| Classification | Criteria |
|---|---|
| `expected_input_block` | source shortage, route mismatch, empty body, legal/guarantee/unsafe warning, source outside claim, or internal-term leakage |
| `unexpected_runtime_block` | sufficient source, body exists, expected facts reflected, but output is still blocked |
| `review_required_draft_candidate` | body exists, no outside claim, no internal leakage, no `needs_input_items`, warning-only, but current UI/summary returns `input_required_block` |
| `source_caveat_block` | source is thin, synthetic, fixture-limited, or otherwise caveated; block is acceptable but not representative of production quality |
| `UI_harness_or_classification_issue` | UI visible message and summary classification diverge, or collector/fresh-snapshot mismatch is visible |

## Completion Gates

- 6 blocked attempts classified.
- User trial scope recorded by article type.
- First next-fix candidate recorded if needed.
- Product code hashes match prior snapshot.
- `18080` has no `LISTENING` entry.
- `C:\tetie\WORKLOG.md` updated.

## Required Checks

No pytest rerun is required for this docs-only package. Cite the previously completed checks from the source package:

- `137 passed`
- `36 passed`
- `264 passed`
- `35 passed`

Final verification commands:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath C:\tetie\notecode\note\current_mainline_runner.py,C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py,C:\tetie\notecode\note\simple_note_pipeline\pipeline.py,C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py,C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py,C:\tetie\notecode\note\note_writer_app.py,C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py
netstat -ano | Select-String ':18080.*LISTENING'
```
