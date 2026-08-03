# TECHIE identity-binding hardening live gate

- Updated: 2026-08-04 JST
- Owner: one SOL agent only
- Status: `LOCAL TARGET PREFLIGHT + GUARDED RUNNER PASS / LIVE NOT RUN / APPLY NOT APPROVED`
- Migration: `infra/20260804_identity_binding_hardening.sql`
- Target preflight: `infra/20260804_identity_binding_hardening_target_preflight.js`
- Guarded runner: `infra/20260804_identity_binding_hardening_runner.js`
- Cloud Shell wrapper:
  `infra/identity-hardening-cloudshell/Invoke-IdentityBindingHardeningTargetPreflight.ps1`

## Purpose

This gate prevents the first live identity binding from being created while
the binding table still accepts empty directory/provider defaults. The SQL
changes only `public.external_identity_binding`: it removes the two unsafe
defaults and adds validated CHECK constraints for a non-empty normalized
directory and the exact providers `email`, `google`, and `microsoft`.

The SQL contains no business-data mutation and does not alter a tenant,
customer account, payment customer, contract, credit, subscription, billing,
payout, refund, or usage table.

## Independent database-target confirmation

The guarded runner now refuses every dry-run and apply unless the operator
provides the SHA-256 of the intended credential-free database target. The
canonical target contains only the lowercase host, explicit port, and database
name. Username, password, connection query, and TLS parameters are excluded.

The confirmation must not be derived only from the same `DATABASE_URL` that
will be used to connect. In the protected operator session:

1. obtain the expected host from the reviewed Azure PostgreSQL resource;
2. obtain the expected database name and port from the reviewed deployment
   contract;
3. obtain `DATABASE_URL` independently from the protected application runtime;
4. set those values only in the protected process environment;
5. run the offline target preflight;
6. use its confirmation hash only in that same protected session.

The preflight makes no network or database call. It reports only a pass/error
code and the non-secret confirmation SHA-256. Never put the raw inputs or the
actual confirmation hash in chat, Git, a screenshot, or a public artifact.

The commit-fixed Cloud Shell wrapper obtains the two sources without printing
them. Its Azure CLI allowlist contains only:

- `az account show`;
- `az webapp show`;
- `az webapp config appsettings list` with a query selecting only the named DB
  setting;
- `az postgres flexible-server show` selecting only resource ID and FQDN.

It pins the offline validation module hash, requires the exact workforce
subscription/tenant, rejects the customer External ID directory as the Azure
resource context, verifies exact App Service and PostgreSQL resource IDs, and
then compares the two target hashes in memory. It does not call the database,
create Cloud Shell storage, change Azure context, upload to Kudu, or run DDL.

Representative protected-session shape:

```text
node 20260804_identity_binding_hardening_target_preflight.js
```

Expected success shape:

```text
DATABASE_TARGET_PREFLIGHT_PASS confirm_database_target_sha256=<protected-sha256>
```

Any host, port, database-name, URL-protocol, or missing-source mismatch stops
before a DB client is created.

## Business-state pin

The runner also pins the aggregate state from the immutable successful live
identity-migration receipt. The repository stores only its SHA-256 digest, not
customer records or payment identifiers. Before `BEGIN`, inside the
transaction, after rollback, and after an approved commit, the aggregate
digest must remain exact. Any new customer, missing customer, payment-link
count change, or duplicate-state change stops the operation and requires a new
read-only review and separately approved rebaseline. It is never silently
accepted.

## Dry-run gate

The default command performs the DDL in a transaction, validates the hardened
state and pinned aggregates, then always rolls back and proves the original
state is restored.

Representative shape only:

```text
node 20260804_identity_binding_hardening_runner.js --confirm-database-target-sha256 <protected-sha256>
```

This live dry-run requires separate explicit approval. A passing target
preflight is not approval to connect to the DB. A passing dry-run is not
approval to apply.

The reviewed Kudu upload/execution path uses the separate apply-incapable
wrapper and exact flat-bundle contract in
`docs/identity_binding_hardening_kudu_dryrun_20260804.md`. The bundle accepts
only the protected target SHA-256, verifies directory/runtime/dependency/source
hashes, captures underlying output, and refuses every apply or extra argument.
Its corrected bundle contains a dedicated no-CLI/no-commit dry-run engine, not
the general apply-capable runner. Thirteen wrapper scenarios and seven engine
scenarios pass. It has not been uploaded or executed. The earlier `a92e41e`
ZIP is `HOLD / SUPERSEDED BEFORE LIVE USE` because it included the general
runner; it was never uploaded or executed and caused no live change.

## Apply gate

Apply additionally requires `--apply` and the exact committed migration SQL
SHA-256. It remains prohibited until a later, separate explicit approval.

Before any apply review, the empty-identity emergency rollback source and
runner must be commit-fixed, remote-hash verifiable, and locally passing. Its
separate contract is
`docs/identity_binding_hardening_emergency_rollback_20260804.md`. Preparing
that package does not authorize upload, rollback dry-run, or rollback apply.

```text
node 20260804_identity_binding_hardening_runner.js --confirm-database-target-sha256 <protected-sha256> --apply --confirm-sha256 <reviewed-migration-sha256>
```

The runner permits apply only while all four identity tables are empty, the
two constraints are absent, the two unsafe defaults are present, duplicates
are zero, the DB target matches, and the pinned aggregate digest matches.

## Safe output and stop conditions

Success output contains only booleans/status, zero identity rows, and commit
state. It does not print the database URL, host, database name, credentials,
business counts, customer values, payment identifiers, or tokens.

Stop on target mismatch, business digest mismatch, any identity row, existing
or partially present hardening, changed defaults, duplicates, SQL hash drift,
TLS verification change, timeout, unexpected argument, or a non-rollback dry
run result. A post-commit verification failure must remain visibly
`commit_state=committed`; it must never be reported as rolled back.

## Current local verification

- Guarded hardening runner: `8 passed`.
- Corrected Kudu dry-run wrapper/engine: `13 + 7 passed`; legacy `a92e41e`
  upload ZIP is superseded and prohibited.
- Empty-identity emergency rollback runner: `11 passed`; live use is
  `NOT_APPROVED`.
- Offline independent-target preflight: `6 passed`.
- Cloud Shell read-only wrapper/module: `9 scenarios passed`, three PowerShell
  files parsed, zero mutation/DB-connection commands, and zero sensitive output
  paths.
- Migration SQL SHA-256 remains pinned and unchanged.
- JavaScript syntax: passed.
- Live target values and live DB behavior remain `NOT_CHECKED` in this package.
