# SECURITY_GATE

Date: 2026-05-08 JST

## Security Decision Rule

The new 0506 UI route remains `blocked` or `hold` until unresolved critical/high issues are zero.

Do not claim 100% safety. Report only whether this package's defined gates are satisfied.

## Threat Model

Treat all user-provided and source-derived text as untrusted data.

Threats in scope:

- prompt injection from source text
- source-internal instructions that try to control tools, model behavior, route selection, or output disclosure
- secret leakage, including API key echo or exception leakage
- path traversal through source locators, filenames, URLs, or artifact names
- SSRF or unexpected URL refetch
- local file exposure through source locators
- artifact leak outside approved run roots
- schema bypass or fallback to unvalidated model output
- source-outside claims
- unsafe reuse of old materialized/deepresearch/Route D/Route E routes

## Hard Blocks

Block implementation completion if any of these remain unresolved:

- API key value is printed, stored, or included in artifacts.
- `.env` is created or modified.
- source locator is used to read arbitrary local files.
- source URL is refetched in saved-source or same-source compare windows.
- source text instructions are executed as commands or treated as system instructions.
- generated output uses facts outside `source_documents`.
- 0506 invalid schema output is accepted.
- Route A fallback is used as new route success.
- old materialized/deepresearch/Route D/Route E route is used as fallback.
- artifact path escapes approved root.
- critical/high security finding has no owner and no blocked status.

## Required Controls

Input controls:

- normalize `source_documents` into bounded source records
- cap source count and source text length
- reject empty or low-confidence source sets before generation
- treat `locator`, `url`, and `canonical_url` as labels only in saved-source route
- do not fetch network resources
- do not read local files from source metadata

Prompt controls:

- source text must be placed as data, not instructions
- system instructions must explicitly ignore source-internal commands
- prompt templates must remain outside Python large strings when possible
- do not add one-off prompt patches for naturalness tuning in this package

Schema controls:

- validate each 0506 JSON stage against schema
- fail closed on schema mismatch
- record redacted blocked reason
- keep the current `importance` max `5` mismatch as adapter/schema compatibility until fixed by that owner

Artifact controls:

- write only under approved run roots
- redact secrets from errors
- write one API call per usage ledger row
- include source snapshot hash
- keep Route A saved artifacts read-only

## Security Gate Artifact

Each validation run must write `security_gate.json` with:

```json
{
  "route_id": "route_0506_structured_blog_ui_v1",
  "decision": "pass | hold | blocked",
  "critical_unresolved": 0,
  "high_unresolved": 0,
  "medium_unresolved": 0,
  "checks": [],
  "blocked_reasons": [],
  "artifact_root": ""
}
```

`decision=pass` is allowed only when `critical_unresolved=0` and `high_unresolved=0`.

## Required Security Checks By Window

Window 1:

- manifest excludes `.env`, `.venv`, credentials, browser profiles, DBs unless explicitly approved
- archive target is inside `C:\tetie\notecode\archive\route_experiments_rejected_2026-05-08\`
- stop on destination collision

Window 2:

- adapter rejects local file locators
- adapter does not refetch URLs
- adapter redacts secret-like strings in errors
- adapter validates artifact root containment
- route ID cannot be confused with Route A

Window 3:

- saved-source CLI uses same source snapshot only
- OpenAI call requires explicit approval if external send is needed
- every API call writes `usage_ledger.jsonl`
- blocked schema output writes `blocked.json` and `security_gate.json`

Window 4:

- UI selection snapshot records `article_type`, `semantic_article_key`, and `ui_journey`
- UI result does not expose API key, local paths, or raw exception details
- button path cannot silently select Route A fallback

Window 5:

- same-source compare proves Route A saved artifact is not regenerated
- source snapshot hashes match
- compare summary separates Route A saved baseline from new route result

Window 6+:

- quality tuning may start only after mapping, security, and artifact gates pass
- prompt additions are not allowed as the first response to quality loss

## Hold Conditions

Use `hold` rather than `pass` when:

- external API approval is missing
- schema compatibility is unresolved
- route mapping collision is suspected
- artifact contract is incomplete
- any high/critical check has insufficient evidence

Use `blocked` when a hard block is observed.
