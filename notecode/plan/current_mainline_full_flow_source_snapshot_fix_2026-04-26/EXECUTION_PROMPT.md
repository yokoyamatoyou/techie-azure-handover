# Execution Prompt

Continue `current_mainline_full_flow_source_snapshot_fix_2026-04-26`.

Rules:

- Product code change is forbidden.
- Prompt / threshold / repair / UI / output guard / image implementation changes are forbidden.
- Do not start UI server.
- Do not run article generation.
- Do not run image generation.
- Use `source_snapshot_manifest.json` as the only source input.
- Do not read `C:\tetie\notecode\logs\latest_generation_output.json` as a source origin.

Required validation:

```powershell
C:\tetie\notecode\.venv\Scripts\python.exe -m py_compile C:\tetie\notecode\plan\current_mainline_full_flow_source_snapshot_fix_2026-04-26\run_full_flow_regression_from_manifest.py
C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\plan\current_mainline_full_flow_source_snapshot_fix_2026-04-26\run_full_flow_regression_from_manifest.py --reconstruct-only
```

Stop after docs closeout. The next full-flow rerun is a separate package/window.
