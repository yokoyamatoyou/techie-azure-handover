# Route 0506 Archive Cleanup Plan 2026-05-12

scope: read-only cleanup planning only  
artifact_root: `C:\tetie\notecode\logs\route_0506_archive_cleanup_plan_readonly_20260512`  
product_code_changed: false  
archive_move_performed: false  
api_send_count: 0

## Current Route 0506 Contract

- Default UI body route: `route_0506_structured_blog_ui_v1`
- Deprecated legacy opt-out: explicit `NOTECODE_UI_BODY_ROUTE=route_a`
- Route A fallback: false
- Route A regeneration in this plan: false
- Route 0506 error/block handling: fail-closed blocked UI state, no automatic Route A fallback
- Source/security/quality blockers: fail-closed
- Category 05 / 07 handling: stop at confirmation/source gate when case-study or comparative source contract is not met
- Local stable reference: `C:\tetie\notecode\0506`

## Archive Policy

This plan does not move or delete files. It only classifies candidates for a future one-owner archive proposal.

Can be considered for future archive movement only after one-owner verification:

- Snapshot-style backup code under `C:\tetie\notecode\backups\...`
- Python files stored as handoff/snapshot material under `C:\tetie\notecode\docs\新しいフォルダー (5)\*.py`
- Rejected route / shadow-route snapshot material that is already outside active runtime paths
- Old generated artifacts that have a durable summary or manifest and are not current Route 0506 evidence

Must not be moved in the first archive pass:

- Current Route 0506 runtime
- Local 0506 stable reference
- Route A deprecated legacy opt-out runtime needed for explicit opt-out
- Focused tests and fixtures for current Route 0506 / Route A opt-out behavior
- Current source-of-truth docs, notices, handoff prompts, and recent Route 0506 evidence
- Anything whose only evidence is a static unreferenced scan

Deletion policy:

- Delete nothing without explicit user approval.
- Prefer archive move with a manifest over deletion.
- Future archive move must preserve enough path mapping to roll back.

## Classification Table

| Classification | Keep / Archive Handling | Examples / Notes |
|---|---|---|
| `active_runtime` | Do not archive. | `note\note_writer_app.py`, app entrypoints, current UI orchestration, post-success linkage. Large size is not enough to archive. |
| `route_0506_main_runtime` | Do not archive. | `note\route_0506_ui_bridge.py`, `note\route_0506_structured_blog_adapter.py`, `note\route_0506_stage_output_guard.py`, `note\route_0506_security_gate.py`, `note\route_0506_usage_ledger.py`. |
| `route_a_legacy_opt_out` | Do not archive in Route 0506 cleanup. Handle only under a separate Route A legacy owner. | `note\current_mainline_runner.py`, `note\newalgorithm_pipeline\`, `note\simple_note_pipeline\`. |
| `local_0506_reference` | Do not archive. | `C:\tetie\notecode\0506\`. Static scans can show false positives because this is a package/root reference. |
| `test_or_fixture` | Keep unless a future owner proves the runtime owner is removed or archived. | `note\tests\test_route_0506*.py`, local 0506 tests, fixtures used by current validation. |
| `docs_or_handoff` | Keep if current, recent, or a source-of-truth pointer. Archive only stale duplicated planning docs after manifest review. | `AGENTS.md`, `WORKLOG.md`, `ALGORITHM.md`, `docs\directory_map.md`, Route 0506 notices/prompts/evidence docs. |
| `archive_candidate` | Candidate only; verify in a future one-owner archive proposal. | `backups\...`, `docs\新しいフォルダー (5)\*.py`, rejected route snapshots already outside active runtime. |
| `delete_never_without_user_approval` | Never delete during automated cleanup. | All candidate files, generated evidence, backup snapshots, archived route records, and any source/customer input artifacts. |

## First Archive Candidates

These are candidates for the next verification owner, not approved moves.

### `C:\tetie\notecode\backups\...`

Reason to consider:

- Existing inventory shows many large Python snapshots under dated backup folders.
- The strongest candidates include old `input_contract.py`, `pipeline.py`, `section_generator.py`, `discourse_planner.py`, and historical tests.
- Current route contracts point to `note\...` and `0506\...`, not `backups\...`.

Why not move yet:

- Text references are numerous in some candidates, so static scan alone cannot prove no handoff dependency.
- A future owner must produce a move manifest, reference check, and focused import/test smoke before any actual movement.

### `C:\tetie\notecode\docs\新しいフォルダー (5)\*.py`

Observed files:

- `04_input_contract.py`
- `05_pipeline.py`
- `06_prompt_builder.py`
- `07_quality_guard.py`

Reason to consider:

- Python files live under a docs review folder rather than an active package.
- Existing inventory specifically called this folder a strong non-runtime cleanup candidate.
- `04_input_contract.py` appeared as unreferenced except for one text reference in the static inventory.

Why not move yet:

- The folder may be a user-facing or historical comparison package.
- The future owner must confirm whether these are review artifacts, current docs inputs, or still referenced by any handoff.

### Rejected Route / Snapshot Material

Reason to consider:

- Old rejected route records and shadow route snapshots are useful as history, but they should not stay mixed with active Route 0506 runtime surfaces.
- If the material already has a failure note or summary pointer, it may be better kept under `archive\...` or a dated logs archive.

Why not move yet:

- Failure history must remain discoverable.
- Do not collapse Route 0506 current evidence and rejected route records in the same move.

## Do-Not-Archive List

Minimum explicit keep list:

- `C:\tetie\notecode\note\route_0506_ui_bridge.py`
- `C:\tetie\notecode\note\route_0506_structured_blog_adapter.py`
- `C:\tetie\notecode\note\route_0506_stage_output_guard.py`
- `C:\tetie\notecode\note\route_0506_security_gate.py`
- `C:\tetie\notecode\note\route_0506_usage_ledger.py`
- `C:\tetie\notecode\0506\`
- `C:\tetie\notecode\note\tests\test_route_0506*.py`
- `C:\tetie\notecode\note\current_mainline_runner.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\`
- `C:\tetie\notecode\note\simple_note_pipeline\`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\WORKLOG.md`
- `C:\tetie\notecode\ALGORITHM.md`
- `C:\tetie\notecode\docs\directory_map.md`
- `C:\tetie\notecode\docs\route_a_legacy_opt_out_deprecation_notice_2026-05-12.md`
- `C:\tetie\notecode\logs\route_0506_main_route_replacement_20260511\`
- `C:\tetie\notecode\logs\module_deadcode_bloat_inventory_20260512\`

## Responsibility Split Recommendation

Recommendation: Route 0506 should be stabilized first. Archive cleanup should stop at this read-only plan until operational confidence and category-specific gates remain stable.

Reason:

- Route 0506 only became the default UI body route on 2026-05-11.
- Current source/security/quality gate behavior is more important than reducing repository volume.
- Archive movement has a broad blast radius when backup folders, rejected route artifacts, and legacy opt-out code are mixed.
- The right next cleanup owner is a verification owner, not a movement owner.

## Execution Phases

### Phase 0: No-Code Plan

- Create this plan.
- Do not edit product code.
- Do not move or delete files.
- Do not run generation, URL refetch, or API calls.

### Phase 1: Archive Candidate Verification

One owner verifies only one candidate family, recommended first:

```text
route_0506_archive_candidate_verification_backups_only
```

Required output:

- Candidate inventory
- Reference scan
- Import/text reference summary
- Keep/archive/blocked classification
- Proposed archive destination
- Move manifest draft
- Explicit rollback map

### Phase 2: One-Owner Archive Move Proposal

- Propose exactly one archive move set.
- Include source paths, destination paths, expected no-runtime-impact proof, and rollback command shape.
- Do not perform the move in the proposal owner.

### Phase 3: Optional Actual Archive Move After User Approval

- Only after explicit user approval.
- Move one candidate family at a time.
- Write a manifest before and after the move.
- Do not delete.
- Do not mix backups, docs snapshots, rejected routes, and Route A legacy paths in one move.

### Phase 4: Tests And Directory Map / WORKLOG Sync

After an approved move:

- Run import smoke.
- Run focused Route 0506 tests.
- Run Route A legacy opt-out smoke only if the move touches legacy-adjacent paths.
- Update `docs\directory_map.md` if path responsibilities changed.
- Update `WORKLOG.md` with only the move summary and manifest pointer.

## Validation / Rollback

Validation for this plan:

- no API
- no route generation
- no Route A regeneration
- no URL refetch
- static reference checks only
- existing inventory reused from `logs\module_deadcode_bloat_inventory_20260512`

Validation for future actual archive move:

- import smoke for current app modules
- focused `note\tests\test_route_0506*.py`
- Route 0506 bridge / structured adapter tests
- Route A opt-out smoke if any adjacent path is touched
- file-count and hash/manifest comparison before and after move

Rollback for future actual archive move:

- Use the move manifest as the source of truth.
- Restore every moved file from archive destination to original path.
- Re-run the same focused tests used after move.
- Do not attempt partial cleanup during rollback.

## Final Decision Contract

decision: needs_next_owner  
artifact_root: `C:\tetie\notecode\logs\route_0506_archive_cleanup_plan_readonly_20260512`  
product_code_changed: false  
api_send_count: 0  
archive_move_performed: false  
route_a_regenerated: false  
url_refetched: false  
route_a_fallback_used: false  
threshold_relaxed: false  
repair_acceptance_relaxed: false  
prompt_bloat: none  
module_bloat: found  
next_one_owner: `route_0506_archive_candidate_verification_backups_only`  
AGENTS_update_needed: no  
WORKLOG_update_needed: no
