# TECHIE Kudu identity-binding hardening persistent apply gate

- Updated: 2026-08-04 JST
- Owner: one SOL agent only
- Status: `LOCAL APPLY GATE PASS / NOT PACKAGED / NOT UPLOADED / DB NOT CONNECTED / LIVE APPLY NOT APPROVED`
- Remote directory: `/home/LogFiles/techie-identity-hardening-apply`
- Wrapper:
  `infra/identity-hardening-kudu-apply/20260804_identity_binding_hardening_apply_only.js`
- Manifest:
  `infra/identity-hardening-kudu-apply/kudu_hardening_apply_manifest.json`

## Purpose and authority boundary

This package is a separately reviewable candidate entrypoint for the one-time
persistent apply of the empty identity-binding invariant hardening. It does not
authorize packaging, Kudu upload, DB connection, or apply. A successful target
preflight or transaction dry-run is evidence only and is not apply approval.

The general hardening runner is not an approved direct live entrypoint and is
not included in this bundle. A future apply review must use the exact
commit-fixed apply wrapper, no-CLI apply engine, and flat manifest. Do not add
`--apply` to the dry-run command and do not invoke the general runner directly.

## Required prior evidence

All of the following must exist in the protected operator session before an
apply approval can be requested:

1. the separately approved Cloud Shell read-only target preflight passed for
   the workforce resource directory, exact App Service, and exact PostgreSQL
   resource;
2. the customer authentication directory remains the separate TECHIE Entra
   External ID directory;
3. the corrected apply-incapable dry-run ZIP has exact SHA-256
   `6A2658589D35D079CE2E826A7CEF958913CAA8C095B1CD07636238FF76E93727`;
4. that exact ZIP was separately approved, uploaded to the dry-run-only
   directory, remote-hash verified, executed successfully, and captured in an
   immutable protected dry-run receipt;
5. a fresh read-only runtime-state receipt proves production resolver
   `legacy`, auto-provision `0`, Entra binding-claim trust `0`, and no
   authentication/deployment drift;
6. a maintenance-window receipt proves customer/account/payment writes are
   paused for the bounded operation;
7. the commit-fixed emergency recovery manifest and both recovery source
   hashes are locally and remotely verifiable;
8. a separate change approval explicitly authorizes the persistent DB
   hardening apply.

No receipt may expose a database URL, host, database name, credential, token,
customer value, email, Stripe identifier, Client Secret, or protected
confirmation hash in Git, chat, screenshots, or public artifacts.

## Future flat bundle

If later approved for packaging, the flat ZIP must contain exactly the four
manifested inputs plus `kudu_hardening_apply_manifest.json`:

- hardening SQL;
- no-CLI apply engine;
- emergency recovery manifest;
- apply-only wrapper;
- apply manifest.

The emergency rollback SQL and runner remain offline at their commit-fixed
Git hashes. They must not be placed in the normal apply directory. The
non-executable recovery manifest proves the exact offline sources and their
separate emergency-approval boundary.

The package is intentionally apply-capable. It must never share the dry-run
directory and must not be prepared or uploaded merely because local tests pass.
Upload requires a later explicit approval and remote SHA-256 equality for
every entry before execution.

## Apply wrapper confirmations

The wrapper accepts exactly one value for each of these confirmations and no
other argument:

- independently confirmed DB target SHA-256;
- corrected dry-run package SHA-256;
- successful protected dry-run receipt SHA-256;
- separate change-approval receipt SHA-256;
- production-legacy runtime-state receipt SHA-256;
- maintenance-window receipt SHA-256;
- emergency recovery manifest SHA-256;
- exact operation phrase
  `APPLY_TECHIE_EMPTY_IDENTITY_BINDING_HARDENING_20260804`.

All independent hashes must be valid and distinct. The wrapper verifies the
migration, no-CLI apply engine, and recovery manifest hashes before DB
connection. The recovery manifest itself pins the offline emergency SQL/runner
and their source commit. The wrapper never prints or forwards receipt hashes.
It calls the engine with only the protected target hash and hash-verified
migration bytes.

Representative shape only; do not run now:

```text
node 20260804_identity_binding_hardening_apply_only.js --confirm-database-target-sha256 <protected-target-sha256> --confirm-dry-run-package-sha256 <reviewed-dry-run-package-sha256> --confirm-dry-run-receipt-sha256 <protected-dry-run-receipt-sha256> --confirm-change-approval-sha256 <protected-change-approval-receipt-sha256> --confirm-runtime-state-receipt-sha256 <protected-runtime-receipt-sha256> --confirm-maintenance-window-receipt-sha256 <protected-maintenance-receipt-sha256> --confirm-recovery-manifest-sha256 <reviewed-recovery-manifest-sha256> --confirm-operation APPLY_TECHIE_EMPTY_IDENTITY_BINDING_HARDENING_20260804
```

## Safe output and recovery routing

Accept only exit code `0` and exactly the fixed boolean/status success shape.
The wrapper suppresses underlying output and emits no hashes or runtime values.

Failure states are intentionally distinct:

- `commit_state=not_committed`: preserve the output and run read-only
  verification; do not retry without a fresh review;
- `commit_state=committed`: assume the schema change persists, stop writes,
  and inspect the exact schema/business state read-only before deciding
  anything;
- `commit_state=unknown`: treat it as possibly committed, stop writes, and
  resolve the schema state read-only before any retry or recovery.

Never launch emergency rollback automatically. Even after a committed or
unknown result, first verify whether the intended constraints/defaults are
already correct and business/Stripe state is unchanged. Persistent emergency
rollback is available only while all four identity tables remain empty,
production remains `legacy`, a rollback dry-run passes, and a new emergency
approval is issued under
`docs/identity_binding_hardening_emergency_rollback_20260804.md`.

## Current local evidence

- Apply-only wrapper scenarios: `15 passed`.
- Every required receipt/target/package hash was shape-checked and non-reused.
- Wrong directory, OS, Node, `pg`, source hash, recovery hash, package hash,
  operation phrase, or missing DB configuration stopped before runner use.
- Only the target and hash-verified SQL bytes reached the no-CLI engine.
- Receipt hashes and fixture DB values were absent from output.
- Apply-engine scenarios: `8 passed`, including transaction rollback and
  post-commit failure injection; no CLI or argument parser exists.
- Post-commit failures remained `commit_state=committed`; unexpected engine
  exceptions were `commit_state=unknown`.
- Apply and emergency manifests matched exact source bytes and hashes.
- Live packaging, upload, remote dependency/hash validation, DB connection,
  persistent apply, and emergency rollback remain `NOT_CHECKED / NOT_APPROVED`.
