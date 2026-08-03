# TECHIE canonical identity resolver rollout

- Updated: 2026-08-04 JST
- Current owner: one SOL agent only
- Status: `LIVE DB SCHEMA APPLIED / API SHADOW NOT DEPLOYED / PRODUCTION NOT CUT OVER`
- Repository branch: `agent/clarify-techie-login-options`
- Baseline commit: `705839b50414b4691574eeff29364a5b47d6462b`

This document is the current source of truth for the 2026-08-03 TECHIE
Microsoft/Google/email identity-linking slice. Older audit files remain valid
as historical evidence for the state at their capture time, but their
`IMPLEMENTATION HOLD` wording does not describe the current local branch.

## Non-negotiable ownership boundaries

- The TECHIE Entra External ID directory is the customer authentication
  authority.
- The workforce Azure directory owns the subscription and production
  resources. It is not a customer identity store.
- `tenants.tenant_id` remains the stable business, RLS, usage, and billing key.
- `customer_account.tenant_id` remains the application-to-Stripe anchor.
- Existing Stripe Customer, subscription, credit, and ledger identifiers are
  not rewritten by this migration.
- Existing Stripe metadata and customer-management behavior are not extended
  by the identity resolver; canonical principal data remains in TECHIE's DB.
- Google Cloud owns only the Google federation credential/configuration.
- Email equality never proves account ownership and never selects a tenant.

## Local implementation

The branch adds four append-only identity tables:

1. `canonical_principal`: application principal to stable business tenant.
2. `external_identity_binding`: verified Entra issuer plus immutable `oid` or
   `sub` to canonical principal.
3. `identity_link_intent`: ten-minute, SHA-256 digest-only, single-use
   dual-authentication intent.
4. `identity_link_audit_log`: non-secret result and provider metadata.

The binding table stores only a SHA-256 email fingerprint for collision
guarding. It does not duplicate the email address. The fingerprint may block
unsafe automatic provisioning, but it cannot select a principal or tenant.
Same-email races are serialized in the database before the collision check.

The resolver modes are:

- `legacy` (default): current production behavior; no canonical read/write.
- `shadow`: compare an existing binding, or a verified `oid` exactly matching a
  legacy business tenant, with the current authorization tenant. It emits only
  binding/legacy match-or-mismatch status evidence. It never returns the
  compared coordinates, uses email as a candidate, replaces the current
  tenant/principal, creates a binding, or rejects an unbound identity.
- `enforce`: require an active binding, a guarded legacy bootstrap, or an
  explicitly enabled new-account provision.

Safety defaults remain:

- `AUTH_IDENTITY_AUTO_PROVISION=0`
- `AUTH_TRUST_ENTRA_BINDING_CLAIMS=0`
- no Microsoft `domain_hint=login.live.com`

With Entra custom-attribute trust disabled, `extension_tenantId` and
`extension_principalId` cannot enter canonical resolution. A verified Entra
object ID is the only default legacy bootstrap coordinate. Provider mismatch,
directory mismatch, ambiguous mapping, an already-linked identity, and a
resolver outage fail closed.

An unknown provider cannot create or bootstrap a binding. Automatic
provisioning additionally requires a non-empty ASCII email collision key; a
missing or non-ASCII address requires the explicit two-authentication link
ceremony instead of guessing a new tenant.

Provider evidence is accepted only as an exact known value, an exact trusted
provider hostname, or the Microsoft consumer tenant ID in the expected
Microsoft issuer path. Similar-looking values such as a hostname that merely
contains `google` or `login.live.com` remain `unknown` and fail closed.

## Account-link ceremony

1. Authenticate with an already bound login method.
2. Reauthenticate that source identity with `prompt=login` and create a
   digest-only link intent.
3. Authenticate the additional email, Google, or Microsoft identity.
4. Verify directory, issuer, audience, immutable subject, recent token issue
time, requested provider, intent expiry, and cross-principal uniqueness.
5. Add the second identity to the same canonical principal and business
   tenant. Do not mutate the Stripe linkage.

The source principal and source binding must still be active at completion.
The source identity cannot be linked to itself. A completed state is
idempotent only for the exact second issuer/type/subject coordinate that used
it; replay by another identity fails closed.

The link-completion route verifies the second Entra token without requiring it
to be pre-bound. All other protected routes continue through canonical
resolution.

## Deployment entrypoint guards

Both PowerShell deployment entrypoints now default the resolver to `legacy`
and reject `shadow` or `enforce` unless the operator explicitly confirms that
the additive identity schema was hash-verified and applied. They also reject
auto-provision or trusted Entra binding claims outside `enforce`, and require
the External ID directory tenant ID for every non-legacy deployment.

The Bicep entrypoint applies the same fail-safe posture to all three container
apps. Its effective resolver mode remains `legacy` unless both the schema
confirmation flag and External ID tenant ID are present. Auto-provision and
trusted binding claims remain disabled unless the effective mode is
`enforce`. These changes only guard future deployments; they do not change any
currently running app setting or Azure resource.

## Validation and live state

- Focused identity tests: `39 passed`.
- Guarded migration-runner dynamic tests: `3 passed`.
- Python in-memory syntax validation: `9` files passed.
- PowerShell parser validation: both deployment scripts passed with zero
  parser errors.
- Bicep deployment contract: static regression passed. A real Bicep compile is
  `NOT_CHECKED` because neither `bicep` nor `az` is installed in this command
  environment.
- Hub inline script syntax: passed.
- `git diff --check`: passed; only existing line-ending warnings remain.
- Migration SHA-256:
  `29D71CBE7F53739858BD499D009CF9527782F3E67D21F745D8FB73DAF074DBCB`
- Guarded runner SHA-256:
  `CCB52A8EC66D0312DA77C89D93003365D7A7C95A0BB7FCBA23D059F1AA83EF37`
- Read-only live aggregate preflight: `26` business tenants, `26` customer
  accounts, `26` Stripe links, zero duplicate tenant-account links, zero
  duplicate Stripe links, and zero identity tables before the migration.
- Remote SQL and runner hashes matched the reviewed commit exactly before any
  database execution.
- Transaction dry-run: `DRY_RUN_PASS`; rollback verification returned zero
  identity tables and unchanged business aggregates.
- One-time additive apply: `APPLY_PASS`; post-commit verification returned four
  empty identity tables, unchanged `26`/`26`/`26` business aggregates, and zero
  duplicate tenant-account or Stripe links.
- No customer fields, emails, tokens, secrets, or Stripe identifiers were
  emitted by the preflight, dry-run, apply, or receipt.
- Azure reports seven completed automatic backups. On-demand backup is not
  supported by the server's current burstable compute tier.
- The current PostgreSQL client warned that a future connection-string major
  version may change `sslmode=require` semantics. The successful run used the
  current certificate-verifying behavior; a later connection-setting change
  must preserve explicit `verify-full` semantics without exposing the URL.

Only the additive, empty identity schema has been applied. No application
setting, API image, Entra production flow, Google Cloud setting, Stripe object,
customer linkage, deployment, or PR merge has been changed in this rollout
status. Git commit/push is evidence publication only and does not satisfy any
deployment, identity, or payment gate.

The immutable local execution receipt is
`C:\tmp\techie-live-audit-20260803\LIVE_IDENTITY_MIGRATION_RECEIPT_20260804.md`.
It records only the reviewed hashes, aggregate counts, commit result, unchanged
boundaries, and residual warning.

A versioned local changed-file snapshot is available under
`C:\tmp\techie-live-audit-20260803`. The external snapshot manifest records
the current archive SHA-256 and preserves prior versions. It contains only the
22 scoped source files plus its immutable content manifest and no repository
metadata, environment values, token, credential, customer export, database
dump, or Stripe value.

## Existing token-transport security gate

The Hub currently keeps a duplicate access token in browser `localStorage` and
passes `access_token` in the URL query when handing off to a service. The
service middleware immediately removes the query parameter and converts the
token to an HttpOnly cookie, but transient URL, history, logging, or referrer
exposure remains possible. This behavior predates the identity resolver and is
not expanded by this slice.

Do not claim the authentication transport is hardened until a separate owner
replaces this handoff and verifies every service route. That remediation must
have its own plan, rollback, and cross-service browser regression; it is not a
reason to rewrite tenant, Stripe, or identity-link semantics in this rollout.

## Required live sequence

1. **Completed 2026-08-04:** place the exact hashed migration in the isolated
   Kudu audit directory.
2. **Completed 2026-08-04:** place
   `infra/20260803_identity_binding_runner.js` beside it and run the
   runner without flags. It verifies the migration hash, executes inside a
   transaction, verifies four empty tables and unchanged business aggregates,
   rolls back, then verifies zero identity tables.
3. **Completed 2026-08-04:** apply the same hash additively and verify four
   empty identity tables and unchanged pre-change aggregates. Apply mode used
   both `--apply` and the exact `--confirm-sha256` value; the DB URL was never
   logged. The runner kept TLS certificate verification enabled.
4. Deploy code with resolver `shadow`, auto-provision `0`, and Entra binding
   claims trust `0`.
5. Verify email and Google traffic remains on its current authorization
   tenant while `shadow_*` comparison evidence is collected. Verify the
   isolated Microsoft pilot token's directory/provider claims separately.
6. Before global enforce, approve and execute a bounded non-customer instance
   or maintenance window that is not serving normal customer traffic. Use it
   to bootstrap a pilot binding and verify email, Google, Microsoft, and the
   explicit two-authentication link ceremony.
7. Bootstrap existing customers only from immutable verified Entra
   coordinates. Verify each business tenant and Stripe Customer remains
   unchanged; email equality is not a bootstrap key.
8. Move normal traffic to `enforce` only after existing-customer coverage and
   rollback evidence are complete, with auto-provision still `0`.
9. Only after all prior gates pass, associate Microsoft with the production
   flow and enable the TECHIE Microsoft UI.
10. Consider auto-provision separately after collision and rollback
    validation.

## Rollback and stop conditions

- Before enforce, return the resolver to `legacy`; no schema deletion is
  required.
- Disable the Microsoft production provider/UI independently; keep email and
  Google available.
- Disable or dispute identity bindings; do not delete historical bindings or
  audit rows.
- Stop on directory ambiguity, provider ambiguity, customer/Stripe count
  drift, any duplicate link, secret/PII exposure, or a migration hash mismatch.

The live database migration is complete and must not be rerun. The current
owner is now at the API-shadow gate: first confirm the live settings and a
bounded slot/canary capability read-only, then deploy only with resolver
`shadow`, auto-provision `0`, and Entra binding-claim trust `0`. The running
application remains on legacy behavior until that separate deployment gate is
verified. Any push must target the user-owned fork branch; PR merge and every
remaining live gate remain separate and prohibited at this stage.
