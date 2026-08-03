# TECHIE Kudu identity-binding hardening apply gate

- Owner: one SOL agent only
- Status: `LOCAL PREPARATION / NOT PACKAGED / NOT UPLOADED / DB NOT CONNECTED`
- Remote directory: `/home/LogFiles/techie-identity-hardening-apply`
- Live authorization embedded in files: `false`

This directory prepares a separate, commit-reviewable entrypoint for the
persistent identity-binding hardening apply. It does not authorize any live
operation. The corrected transaction dry-run must first be separately
approved, uploaded, hash-verified, executed, and recorded as successful.

The future flat upload bundle is defined by
`kudu_hardening_apply_manifest.json`. It contains the migration, no-CLI apply
engine, commit-fixed non-executable emergency recovery manifest, and the
receipt-gated wrapper. The general CLI runner and emergency rollback SQL/runner
remain offline in the commit-fixed repository and are not part of the normal
apply upload. Do
not upload the repository, tests, receipts, `.env`, app settings,
customer/payment export, token, secret, or database dump.

The wrapper requires all of these before DB connection:

- exact isolated Kudu directory, Linux, reviewed Node major, and `pg` 8.22.0;
- exact hashes for all migration and emergency-recovery inputs;
- the independently confirmed DB target SHA-256;
- the corrected dry-run package SHA-256;
- a successful dry-run receipt SHA-256;
- a separate change-approval receipt SHA-256;
- a read-only production legacy/runtime-state receipt SHA-256;
- a maintenance-window receipt SHA-256;
- the commit-fixed emergency recovery manifest SHA-256;
- the exact operation phrase.

Every independent hash must be valid and non-reused. The wrapper does not
forward or print receipt hashes. It invokes the pinned no-CLI engine with only
the DB target and hash-verified migration bytes.

A failure after a confirmed underlying commit remains
`commit_state=committed`. An unexpected exception during the engine call is
`commit_state=unknown`, never falsely reported as rolled back.

Run local tests:

```text
node test_20260804_identity_binding_hardening_apply_only.js
```

Do not package, upload, execute, or apply without a new explicit approval.
