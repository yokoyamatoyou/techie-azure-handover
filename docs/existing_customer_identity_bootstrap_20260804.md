# TECHIE existing-customer identity bootstrap

- Updated: 2026-08-04 JST
- Owner: one SOL agent only
- Status: `LOCAL BOOTSTRAP + DISPUTE-ONLY ROLLBACK PASS / LIVE MANIFEST NOT CREATED / DB NOT TOUCHED / APPLY HOLD`
- Current runner: `infra/20260804_existing_customer_identity_bootstrap_runner.js`
- Rollback runner: `infra/20260804_existing_customer_identity_bootstrap_rollback_runner.js`
- Manifest schema: `infra/existing_customer_identity_bootstrap_manifest.schema.json`
- Directory/tenant/Stripe boundary:
  `docs/identity_tenant_stripe_architecture_20260804.md`

## Purpose and boundary

This package prepares an explicit, bounded mapping from one already verified
TECHIE External ID `issuer + oid` coordinate to one existing stable business
`tenant_id`. It creates only additive canonical identity records. It never
selects a tenant by email and never changes the existing customer account,
Stripe Customer, contract, payment, payout, refund, usage, credit, or ledger
records.

The package is local preparation only. No live customer manifest has been
created and no DB, API, Entra, Google Cloud, Stripe, Azure resource, or
production setting has been read or changed by its tests.

Bootstrap creates the first canonical identity anchor for an existing
business tenant; adding a later Google, Microsoft, or Email login method uses
the separate two-authentication link ceremony. Both operations preserve the
same `canonical_principal`, business `tenant_id`, `customer_account`, and
existing Stripe Customer. Provider addition is never a second customer or a
new billing account.

## Why a separate bootstrap is required

The guarded runtime resolver can safely bootstrap a legacy customer only when
the verified Entra object ID is itself the existing business tenant UUID. A
Google, Microsoft, or replacement email identity can have a different Entra
object ID. Email equality cannot prove ownership and therefore cannot choose
the existing tenant. Any different provider must be linked through the
explicit dual-authentication ceremony or an approved immutable-coordinate
bootstrap manifest; it must not be guessed from email or Stripe metadata.

## Protected manifest contract

The live manifest belongs only in the protected operator session. Never add it
to Git, chat, PR artifacts, screenshots, general logs, or the public audit
folder. The committed JSON Schema contains structure only and no live values.

Each batch requires:

- one batch UUID;
- the SHA-256 of a separate explicit change-approval receipt;
- an exact expected operation count between 1 and 100;
- one unique entry per business tenant and immutable identity coordinate.

Each entry requires only:

- an opaque operation UUID;
- the existing business tenant UUID;
- SHA-256 digests of the expected customer-account UUID and existing Stripe
  Customer ID;
- the exact TECHIE External ID directory and issuer;
- `subject_type=oid` and the same verified UUID in `subject_value` and
  `entra_object_id`;
- the exact provider `email`, `google`, or `microsoft`;
- the SHA-256 of an immutable identity-evidence receipt.

No email address, name, billing address, raw customer-account ID, raw Stripe
ID, token, authorization code, PKCE value, cookie, password, client secret, or
database URL is a manifest field. Unknown fields fail closed.

## Mandatory prerequisites

1. Production remains on resolver `legacy`, auto-provision `0`, and Entra
   binding-claim trust `0` during the bootstrap maintenance window.
2. The two binding-hardening CHECK constraints are present and validated, and
   the unsafe directory/provider defaults are absent.
3. The exact External ID directory and issuer are independently verified in
   the protected operator session.
4. Every mapping has a separate immutable identity-evidence receipt and is
   covered by an explicit change-approval receipt. A digest without the
   underlying approved receipt is insufficient.
5. The customer-account and Stripe Customer hashes are produced and compared
   inside the protected environment without printing the raw values.
6. No normal customer traffic, Stripe webhook processing, contract update, or
   usage write is allowed during the bounded transaction.
7. The exact runner, schema, manifest, source commit, tests, and hashes are
   snapshotted before any remote upload.
8. The tested dispute-only rollback runner must be included in the same
   commit-fixed snapshot. Its separate rollback approval, protected-manifest
   hash confirmation, and rollback dry-run receipt must exist before apply.
   Local tests alone do not remove the live `HOLD`.

## Runner behavior

- Unknown or duplicate arguments fail before a DB connection.
- The manifest is limited to 1 MiB, has exact-key validation, and rejects
  duplicate operation IDs, tenants, and identity coordinates.
- CLI execution rejects a manifest stored anywhere inside the source tree.
  On non-Windows systems the protected manifest must also have no group/world
  permission bits (for example mode `0600`). `.gitignore` patterns are only a
  secondary guard and do not replace the outside-repository requirement.
- Default execution uses a SERIALIZABLE transaction and always rolls back.
- Apply requires the exact manifest SHA-256 and exact operation count on the
  command line after separate approval.
- TLS certificate verification remains enabled; `DATABASE_URL` is read only
  from the process environment and never printed.
- The target tenant and single customer account are row-locked and their
  customer-account/Stripe hashes must match the protected manifest.
- Target contract, billing, receipt, payout, payout-execution, refund, usage
  account, and usage event rows are locked for the transaction.
- Global business/Stripe/contract/ledger counts and duplicate checks must be
  unchanged before and after the identity inserts.
- Existing ambiguous principals, orphan identity rows, directory/provider
  drift, disabled bindings, or another tenant on the same identity coordinate
  fail closed.
- An exact existing binding is idempotent. A new mapping creates at most one
  canonical principal, one external identity binding, and one identity-only
  audit record.
- The binding stores no email fingerprint and uses
  `verified_existing_customer_bootstrap` as the link method.
- Audit details contain only batch/operation IDs, approval/evidence hashes, and
  provider; no customer, tenant, subject, Stripe, or email coordinate is copied
  into the JSON details.
- Output is aggregate-only: operation/insert/idempotent counts, invariant
  status, manifest hash, and fixed error code.

## Dispute-only rollback behavior

Rollback never deletes an identity row and never changes a business, Stripe,
contract, ledger, usage, credit, or payout row. It accepts the exact same
protected manifest and requires a distinct rollback-approval receipt hash that
cannot equal the manifest hash, original change-approval hash, or any identity
evidence hash.

For each operation it re-locks and re-verifies the customer-account and Stripe
anchors, business rows, original bootstrap binding, and the exact-key original
bootstrap audit. It changes the target binding from `active` to `disputed` and
records the fixed reason `approved_existing_customer_bootstrap_rollback`. A
principal created by that bootstrap is also disputed only when it has no other
active binding. A pre-existing principal, or a principal with another active
binding, remains active. Any related pending identity-link intent stops the
rollback; the runner neither completes nor cancels an authentication ceremony.
The rollback appends one identity-only audit record; repeat execution with the
exact same approval is idempotent.

Rollback also defaults to SERIALIZABLE dry-run plus transaction rollback. Its
apply mode requires the same exact manifest SHA-256 and operation count. A
rollback dry-run pass is evidence about the protected batch, not authorization
to run bootstrap apply or rollback apply.

## Dry-run and apply gates

Representative dry-run with placeholders only:

```text
node 20260804_existing_customer_identity_bootstrap_runner.js --manifest <protected-path>
```

The transaction must report `EXISTING_CUSTOMER_BOOTSTRAP_DRY_RUN_PASS` and the
post-rollback state must match the exact pre-transaction state. A dry-run pass
does not authorize apply.

Representative apply shape, only after a new explicit approval:

```text
node 20260804_existing_customer_identity_bootstrap_runner.js --manifest <protected-path> --apply --confirm-manifest-sha256 <reviewed-sha256> --confirm-operation-count <reviewed-count>
```

Do not place actual IDs, hashes, paths, or environment values in chat or this
document. Apply must remain stopped until the rollback package, remote hash
verification, dry-run receipt, maintenance window, and explicit apply approval
all exist.

Representative rollback dry-run shape, only with a separate reviewed rollback
approval receipt:

```text
node 20260804_existing_customer_identity_bootstrap_rollback_runner.js --manifest <protected-path> --rollback-approval-sha256 <reviewed-rollback-approval-sha256>
```

Representative rollback apply shape, only after a separate explicit rollback
apply approval:

```text
node 20260804_existing_customer_identity_bootstrap_rollback_runner.js --manifest <protected-path> --rollback-approval-sha256 <reviewed-rollback-approval-sha256> --apply --confirm-manifest-sha256 <reviewed-sha256> --confirm-operation-count <reviewed-count>
```

## Current local validation

- Runner JavaScript syntax: passed.
- Manifest Schema JSON parsing: passed.
- Bootstrap guarded dynamic/static scenarios: `21 passed`.
- Dispute-only rollback guarded dynamic/static scenarios: `21 passed`.
- Covered failure paths include unknown/extra fields, email-address field,
  wrong directory, issuer/OID mismatch, duplicate tenant, wrong account hash,
  wrong Stripe hash, absent hardening, ambiguous principal, provider drift,
  business/Stripe count drift, wrong manifest hash, and wrong operation count.
- Synthetic apply/idempotency proves only identity tables change and the
  existing target Stripe anchor remains byte-for-byte unchanged.
- Synthetic rollback proves no identity row is deleted, the bootstrap binding
  is disputed, an eligible batch-created principal is disputed, pre-existing
  or still-linked principals are preserved, and business/Stripe counts remain
  unchanged.
- Live customer data, DB behavior, and provider claims remain `NOT_CHECKED`.

## Stop conditions

Stop on any missing approval/evidence receipt, directory/issuer ambiguity,
manifest hash mismatch, customer/Stripe hash mismatch, duplicate mapping,
non-oid coordinate, email-derived mapping, hardening mismatch, business count
drift, identity ambiguity, raw value output, concurrent customer activity,
rollback approval reuse, audit-shape/provenance mismatch, or rollback dry-run
failure.
