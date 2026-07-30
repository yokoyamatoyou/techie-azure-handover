# Route 0506 Codex CLI Next Start Prompt 2026-05-09

Use this in the next Codex CLI window after starting with sandbox/network access that allows the external OpenAI API call.

## Startup Assumption

- Workdir: `C:\tetie\notecode`
- Goal: test route_0506 with the original 0506 OpenAI path, not the local deterministic validation path.
- Environment has `OPENAI_API_KEY`.
- Model: `gpt-5.4-mini`
- Reasoning effort: `high`
- Source: Route A saved artifact only.

## Required Read First

1. `C:\tetie\notecode\AGENTS.md`
2. `C:\tetie\WORKLOG.md`
3. `C:\tetie\notecode\logs\route_0506_ui_1case_20260508-235226\pipeline_diagnosis.md`
4. `C:\tetie\notecode\logs\route_0506_ui_1case_openai_blocked_20260509\validation_summary.json`

## Constraints

- Route A is `C:\tetie\notecode\logs\latest_generation_output.json` saved artifact only.
- Do not regenerate Route A.
- Do not use Route A fallback.
- Do not refetch URLs.
- Do not revive old routes.
- Do not tune quality.
- Do not relax thresholds.
- Do not relax `repair_acceptance`.
- Run 1 case only.
- Do not print or write the API key.

## Command

```powershell
cd C:\tetie\notecode
$env:BLOGGEN_LLM_MODE = "openai"
$env:OPENAI_MODEL = "gpt-5.4-mini"
$env:OPENAI_REASONING_EFFORT = "high"

.\.venv\Scripts\python.exe .\tools\run_route_0506_ui_1case.py `
  --route-0506-client-mode openai `
  --output-root "C:\tetie\notecode\logs\route_0506_ui_1case_openai_manual_20260509" `
  --json
```

## Expected Checks

After execution, inspect:

- `C:\tetie\notecode\logs\route_0506_ui_1case_openai_manual_20260509\validation_summary.json`
- `C:\tetie\notecode\logs\route_0506_ui_1case_openai_manual_20260509\route_0506\latest_generation_output.json`
- `C:\tetie\notecode\logs\route_0506_ui_1case_openai_manual_20260509\route_0506\latest_generation_output.md`
- `C:\tetie\notecode\logs\route_0506_ui_1case_openai_manual_20260509\usage_ledger.jsonl`
- `C:\tetie\notecode\logs\route_0506_ui_1case_openai_manual_20260509\api_usage_ledger.jsonl`

Report these fields:

- artifact root
- route_0506_status
- client_mode
- api_send
- model
- reasoning_effort
- source_snapshot_hash
- window3_source_snapshot_hash
- source hash match
- Route A regenerated=false
- Route A fallback=false
- URL refetch=false
- security_gate_status
- mapping_collision_status
- usage ledger status
- title/body visibility
- manual Japanese blog naturalness note
- decision: `reject | continue_shadow | blocked`

## Compare Summary

If generation succeeds, create:

`C:\tetie\notecode\logs\route_0506_ui_1case_openai_manual_20260509\compare_summary.json`

Minimum required fields:

- `decision`
- `source_snapshot_hash_match`
- `route_a_changed=false`
- `route_a_regenerated=false`
- `route_a_fallback=false`
- `url_refetch=false`
- `api_send=true`
- `model=gpt-5.4-mini`
- `reasoning_effort=high`
- `security_gate`
- `usage_ledger`
- `manual_japanese_blog_naturalness_note`
- `guardrails`

If generation blocks, stop after confirming:

- blocked reason redacted
- source snapshot hash
- security gate
- mapping collision
- artifact completeness

