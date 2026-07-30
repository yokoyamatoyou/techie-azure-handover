# TASK

## Phase Map

| Phase | Gate |
|---|---|
| 0 package scaffold | README / TASK / PROGRESS / ROLLBACK / EXECUTION_PROMPT created |
| 1 source snapshot manifest | `source_snapshot_manifest.json` created from fixed artifacts only |
| 2 manifest wrapper | wrapper loads manifest and replaces base harness source inventory builder |
| 3 reconstruct-only validation | wrapper runs with `--reconstruct-only` and writes source inventory from manifest |
| 4 acceptance checks | no moving target dependency, Kyoto 4 URLs fixed, no generation artifacts |
| 5 closeout | PROGRESS and WORKLOG updated |

## Owner Scope

One issue, one owner scope:

- Owner: validation package / harness artifact only
- Product runtime owner: none

## Required Checks

```powershell
C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile C:\tetie\notecode\plan\current_mainline_full_flow_source_snapshot_fix_2026-04-26\run_full_flow_regression_from_manifest.py
C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\plan\current_mainline_full_flow_source_snapshot_fix_2026-04-26\run_full_flow_regression_from_manifest.py --reconstruct-only
```

Acceptance checks:

- `source_snapshot_manifest.json` does not reference `C:\tetie\notecode\logs\latest_generation_output.json`.
- Every active record has `moving_target=false`.
- Company record has exactly 4 Kyoto URL source documents.
- Reconstructed `source_inventory.json` comes from manifest records.
- No UI server is started.
- No article/image generation artifacts are produced.
- Product code hashes remain unchanged.
