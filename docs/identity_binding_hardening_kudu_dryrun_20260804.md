# TECHIE Kudu identity-binding hardening dry-run gate

- Updated: 2026-08-04 JST
- Owner: one SOL agent only
- Status: `LOCAL DRY-RUN-ONLY PACKAGE PASS / NOT UPLOADED / DB NOT CONNECTED`
- Remote directory: `/home/LogFiles/techie-identity-hardening-audit`
- Live apply capability in this bundle: `false`

## Purpose and order

This package is the only reviewed Kudu entrypoint for the first live
identity-binding hardening transaction dry-run. It must not be used until the
separately approved Cloud Shell target preflight passes in the protected
operator session. Its target confirmation SHA-256 must remain in that session
and is never stored in Git, chat, screenshots, the bundle, or a public receipt.

Required order:

1. keep production resolver `legacy`, auto-provision `0`, and Entra binding
   claim trust `0`;
2. establish a maintenance window with no customer/account/payment write;
3. run the separately approved Cloud Shell read-only target preflight;
4. obtain separate approval for Kudu upload and live transaction dry-run;
5. upload only the four reviewed flat-bundle entries to the exact isolated
   directory;
6. verify every remote SHA-256 before Node execution;
7. run the dry-run-only wrapper with the protected target confirmation;
8. stop and preserve only the fixed safe result.

No step above authorizes hardening apply, existing-customer linking, API
cutover, Microsoft production enablement, or a Stripe/Entra change.

## Flat upload bundle

The upload bundle contains exactly:

- `20260804_identity_binding_hardening.sql`;
- `20260804_identity_binding_hardening_runner.js`;
- `20260804_identity_binding_hardening_dryrun_only.js`;
- `kudu_hardening_dryrun_manifest.json`.

The manifest contains exact bytes and SHA-256 for the three executable inputs,
the exact isolated directory, the reviewed `pg` version, and
`apply_capability=false`. It contains no runtime value.

Do not upload the repository, `.env`, application settings, database dump,
customer export, payment value, token, secret, source tests, or audit receipts.
Do not use ZipDeploy or restart the app.

## Remote prerequisites

Before execution, confirm without printing environment values:

- current directory is exactly
  `/home/LogFiles/techie-identity-hardening-audit`;
- the three executable files match the manifest SHA-256 and byte counts;
- Linux runtime and reviewed Node major are present;
- existing runtime `pg` is exactly `8.22.0`;
- no dependency installation is required;
- the protected `DATABASE_URL` exists but is never displayed;
- the target confirmation came from the immediately preceding approved Cloud
  Shell preflight.

Stop rather than install, substitute, edit, rename, or regenerate a dependency
or source file remotely.

## Apply-incapable execution

The wrapper accepts exactly one option:

```text
node 20260804_identity_binding_hardening_dryrun_only.js --confirm-database-target-sha256 <protected-sha256>
```

Any missing, duplicate, extra, unknown, malformed, or apply argument is
rejected before DB connection. The wrapper constructs the underlying runner
arguments itself and never forwards caller arguments. The constructed
arguments contain no `--apply`.

It also verifies the runner and SQL hashes, captures all underlying output in
memory, requires the exact reviewed success line, and rejects any result whose
mode is not `dry-run` or whose `committed` state is not `false`.

Accept only exit code `0` and exactly:

```text
KUDU_HARDENING_DRY_RUN_PASS target_confirmed=true business_state_confirmed=true identity_rows=0 commit_state=not_committed apply_capability=false
```

No database URL, host, database name, aggregate count, customer value, payment
identifier, or token may appear. Any other output is a stop condition.

## Rollback and post-run boundary

The underlying runner performs the hardening DDL inside one transaction,
checks the target/business-state/empty-identity invariants, rolls back, and
verifies the original defaults and absent constraints are restored. A dry-run
success therefore leaves the hardening unapplied.

After success, do not run the general runner directly and do not add an apply
flag. Preserve the fixed status and remote hashes as an immutable non-secret
receipt. Hardening apply remains a later, separate approval and must use a
separate apply package/review rather than modifying this bundle.

## Current local evidence

- Dry-run-only wrapper scenarios: `13 passed`.
- Apply/extra arguments rejected before connection.
- Wrong directory, OS, Node major, `pg` version, runner hash, or SQL hash
  rejected before connection.
- Unexpected commit or output rejected.
- Manifest/source hash and byte equality passed.
- Live upload, runtime dependency state, DB transaction, and rollback remain
  `NOT_CHECKED`.
