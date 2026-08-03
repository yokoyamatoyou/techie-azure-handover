# TECHIE identity-binding hardening emergency rollback

- Updated: 2026-08-04 JST
- Owner: one SOL agent only
- Status: `LOCAL DRY-RUN/APPLY GUARDS PASS / NOT UPLOADED / DB NOT CONNECTED`
- SQL: `infra/20260804_identity_binding_hardening_emergency_rollback.sql`
- Runner: `infra/20260804_identity_binding_hardening_emergency_rollback_runner.js`

## Narrow purpose

This package reverses only the separate identity-binding invariant hardening:
it removes the two binding CHECK constraints and restores the two original
column defaults. It performs no row insert, update, delete, truncate, or table
drop and does not touch a tenant, customer account, Stripe Customer,
subscription, contract, credit, payment, payout, refund, usage, or ledger
table.

This is an emergency bridge back to the exact pre-hardening schema state. It
is not a general identity rollback. Never use it after any identity table has
a row, while resolver mode is `shadow` or `enforce`, while auto-provision or
Entra binding-claim trust is enabled, or as a way to resolve a customer
mapping dispute.

## Required external state

Before even a live rollback dry-run, a separately reviewed protected-session
receipt must prove all of the following without exposing values:

- production resolver mode is `legacy`;
- `AUTH_IDENTITY_AUTO_PROVISION=0`;
- `AUTH_TRUST_ENTRA_BINDING_CLAIMS=0`;
- no customer/account/payment write is in progress;
- the intended database target independently matches the Azure resource;
- the hardening apply receipt is immutable and identifies the applied state;
- all four identity tables are empty and business/Stripe aggregates remain at
  the pinned digest.

The DB runner independently enforces the target hash, pinned business digest,
empty identity tables, two present and validated hardening constraints, and
zero unsafe defaults. The protected app-setting/maintenance-window evidence is
an external gate and must not be inferred from DB checks.

## Default rollback dry-run

Without `--apply`, the runner applies the emergency SQL inside a SERIALIZABLE
transaction, verifies the exact pre-hardening schema, rolls back, and then
proves the hardened schema was restored.

Representative shape only:

```text
node 20260804_identity_binding_hardening_emergency_rollback_runner.js --confirm-database-target-sha256 <protected-target-sha256>
```

The only acceptable success shape is:

```text
HARDENING_EMERGENCY_ROLLBACK_DRY_RUN_PASS target_confirmed=true business_state_confirmed=true identity_rows=0 hardened_state_restored=true commit_state=not_committed
```

## Persistent emergency apply

Persistent rollback is prohibited without a new emergency approval after a
successful rollback dry-run. Apply requires all of these independent inputs:

- `--apply`;
- the exact emergency rollback SQL SHA-256;
- a separate emergency approval receipt SHA-256;
- the earlier hardening apply receipt SHA-256;
- the independently confirmed database-target SHA-256.

All receipt, SQL, target, and pinned-business hashes must be valid and distinct.
Representative shape only:

```text
node 20260804_identity_binding_hardening_emergency_rollback_runner.js --confirm-database-target-sha256 <protected-target-sha256> --apply --confirm-sha256 <reviewed-rollback-sql-sha256> --confirm-emergency-approval-sha256 <protected-approval-receipt-sha256> --confirm-hardening-apply-receipt-sha256 <protected-hardening-receipt-sha256>
```

A post-commit verification failure is reported with
`commit_state=committed`; it is never represented as rolled back. In that
case, stop all identity writes, keep production on `legacy`, preserve the
output, and perform read-only schema/business verification before any further
action.

## Current local evidence

- Emergency rollback runner scenarios: `11 passed`.
- Default execution restored the hardened state after transaction rollback.
- Apply required exact, non-reused target/SQL/approval/apply-receipt hashes.
- Non-empty identity state and business digest drift stopped before `BEGIN`.
- Post-commit verification failure retained `commit_state=committed`.
- Static SQL inspection found no row DML, table drop, or business/Stripe table
  alteration.
- Live upload, live rollback dry-run, and persistent emergency apply remain
  `NOT_CHECKED / NOT_APPROVED`.
