# TECHIE canonical identity resolver rollout

- Updated: 2026-08-04 JST
- Current owner: one SOL agent only
- Status: `LIVE DB SCHEMA + READ-ONLY SHADOW PROBE PASS / CLOUD SHELL HARDENING TARGET PREFLIGHT LIVE PASS+DB NOT CONNECTED / BINDING DIRECTORY+PROVIDER GUARD LOCAL PASS / DB BINDING HARDENING NOT APPLIED / ISOLATED JOB + FOUNDATION/JOB PREFLIGHT LOCAL PASS / EXISTING-CUSTOMER BOOTSTRAP+ROLLBACK LOCAL PASS+LIVE APPLY HOLD / LIVE JOB NOT DEPLOYED / PRODUCTION NOT CUT OVER`
- Repository branch: `agent/clarify-techie-login-options`
- Baseline commit: `705839b50414b4691574eeff29364a5b47d6462b`

This document is the current source of truth for the 2026-08-03 TECHIE
Microsoft/Google/email identity-linking slice. Older audit files remain valid
as historical evidence for the state at their capture time, but their
`IMPLEMENTATION HOLD` wording does not describe the current local branch.

The canonical directory/identifier/Stripe boundary and current-versus-target
state are defined in
`docs/identity_tenant_stripe_architecture_20260804.md`. The user-observed live
login state is Email-only. Google and Microsoft production provider/UI state
was not revalidated in this docs-only pass. The three-option Hub source is a
repository candidate, not deployment evidence.

## Non-negotiable ownership boundaries

- The TECHIE Entra External ID directory is the customer authentication
  authority.
- The workforce Azure directory owns the subscription and production
  resources. It is not a customer identity store.
- `tenants.tenant_id` remains the stable business, RLS, usage, and billing key.
- `customer_account.tenant_id` remains the application-to-Stripe anchor.
- Existing Stripe Customer, subscription, credit, and ledger identifiers are
  not rewritten by this migration.
- Stripe is authoritative for billing objects, not for customer
  authentication or business-tenant selection. Identity resolution must reach
  Stripe only through the stable business `tenant_id` and
  `customer_account.stripe_customer_id`.
- Existing Stripe metadata and customer-management behavior are not extended
  by the identity resolver; canonical principal data remains in TECHIE's DB.
- Google Cloud owns only the Google federation credential/configuration.
- Email equality never proves account ownership and never selects a tenant.
- `tenants.stripe_id` must not be used as an identity-link key. The current
  inspected billing path uses `customer_account.stripe_customer_id`; the older
  field requires a separate compatibility audit.

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

An active binding is accepted only when its saved External ID directory and
saved provider (`email`, `google`, or `microsoft`) both match the newly verified
token evidence. Shadow mode reports directory/provider drift only as a status
without exposing canonical coordinates. Enforce and link completion fail
closed; link completion cancels the intent and writes an identity-only audit
row. These checks never select or update a business tenant, customer account,
Stripe Customer, subscription, contract, credit, or ledger record.

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

- Focused identity tests: `49 passed` with pytest cache writes disabled because
  this managed workspace denies pytest's final cache-directory creation.
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
- The production `techie-api` Web App is Linux on Basic B1. Its App Service
  plan currently contains two apps and zero deployment slots. Basic does not
  support a staging slot, so no in-place shadow deployment or plan change was
  attempted.
- Kudu boolean-only checks confirmed the expected Entra authentication mode
  and sign-up/sign-in policy, present Entra tenant/client, database, and Stripe
  configuration, effective legacy resolver behavior, auto-provision off, and
  Entra business-binding claim trust off. No setting value was printed.
- The live Key Vault currently lists zero available secrets. This conflicts
  with the repository IaC, which defines a `database-url` secret and managed
  identity references. Do not treat the IaC declaration as proof that live
  Key Vault secret wiring exists, and do not copy the Web App connection string
  into a new resource without a separately approved secret-bootstrap plan.
- Read-only live shadow probe commit:
  `bde7bf87849b031add4ff87656369198ff3cf658`.
- Read-only shadow probe SHA-256:
  `B100C59407E46768510088FEA05FF18AEA3188C5006970CDB53E2A6B5D8DA0E3`.
- The remote hash matched before execution. `SHADOW_PROBE_PASS` then verified a
  repeatable-read, read-only transaction; unchanged `26`/`26`/`26` business
  aggregates; four empty identity tables; zero business/Stripe duplicates;
  zero duplicate or orphan identity rows; a zero-match synthetic identity;
  and one internal legacy-candidate lookup without emitting its coordinate.
- Shadow-probe dynamic tests: `4 passed`. Existing migration-runner dynamic
  tests: `3 passed`.
- A normal pytest invocation reached all 49 test bodies and 100% but stalled in
  pytest `cacheprovider` while attempting a denied temporary-directory write.
  A faulthandler trace identified that exact framework teardown path. Repeating
  the same suite with plugin autoload and only `cacheprovider` disabled exited
  cleanly: `49 passed in 0.88s`.
- The added coverage proves that email, Google, and Microsoft bindings return
  the same saved business tenant without mutation; a stored workforce-directory
  or provider mismatch fails before mutation; and reauthenticated linking
  touches only identity binding/intent/audit tables while leaving
  `customer_account`, Stripe data, `tenants`, and `canonical_principal`
  unchanged.
- The current PostgreSQL client warned that a future connection-string major
  version may change `sslmode=require` semantics. The successful run used the
  current certificate-verifying behavior; a later connection-setting change
  must preserve explicit `verify-full` semantics without exposing the URL.
- A deployment-hold package now exists at
  `infra/identity-shadow-job/` for an isolated Container Apps manual job. It
  contains a digest-required Docker build, a lockfile-pinned PostgreSQL client,
  a separate managed-identity/RBAC foundation, a version-pinned Key Vault
  reference, and the manual job Bicep resource. It does not contain a secret
  value or a live parameter file.
- The dedicated user-assigned identity is limited to `AcrPull` on the existing
  ACR and `Key Vault Secrets User` on the individual `database-url` secret,
  not the whole vault, resource group, or subscription. The job has no ingress,
  one replica, zero retries, a five-minute timeout, and a manual-only trigger.
- Isolated-job contract test: `1 passed`. Existing shadow-probe tests: `4
  passed`. Existing migration-runner tests: `3 passed`. The dependency lock is
  internally consistent and npm reported zero known vulnerabilities.
- Both Bicep templates compiled successfully with the Microsoft-signed Bicep
  CLI v0.45.15 after its SHA-256 matched the published binary hash. Compiled
  ARM inspection confirmed the exact ACR and individual-secret role scopes,
  manual-only trigger, one replica, zero retries, five-minute timeout,
  digest-based image reference, secure secret-version parameter, Key Vault
  reference without a secret `value`, and no ingress or Stripe configuration.
- Docker build, ACR push, Azure what-if, Key Vault secret bootstrap,
  identity/RBAC creation, job creation, and job start remain `NOT_CHECKED` or
  `NOT_STARTED`. Neither `az` nor `docker` is installed in the local command
  environment. These remain explicit live approval gates and are not implied
  by the successful local Bicep compile.
- The isolated-job package now also includes a secret-free Azure context and
  foundation what-if preflight. Its pure validator passed nine synthetic
  scenarios plus parser, mutation-command, and sensitive-literal checks. The
  live wrapper accepts the expected subscription, workforce resource tenant,
  and External ID tenant only as runtime parameters; verifies the two tenant
  roles are distinct; suppresses raw CLI output; and emits only aggregate
  booleans/counts. Foundation what-if passes only for exactly one dedicated
  identity create, one role assignment at the exact ACR scope, and one role
  assignment at the exact individual-secret scope. `Modify`, `Delete`,
  `Deploy`, `Ignore`, `Unsupported`, duplicate, unexpected, broad-vault, and
  malformed results all fail closed. No live Azure context check or what-if
  was run by this local validation.
- The same wrapper now has a later `JobWhatIf` gate. Before the Job what-if it
  verifies the reviewed Bicep hashes, exact workforce subscription/directory,
  existing environment/ACR/Key Vault/dedicated identity, absent Job, and
  exactly two direct role assignments for that identity: `AcrPull` on the ACR
  and Key Vault Secrets User on the individual database-secret scope. It reads
  only Key Vault secret-version identifiers and enabled attributes, never the
  secret value. Runtime input rejects mutable/uppercase image digests,
  unreviewed repositories, non-Consumption profiles, and malformed versions.
  The Job what-if passes only for one exact Job `Create`. Nineteen synthetic
  runtime/RBAC/what-if scenarios plus parser, mutation/value-read-command, and
  sensitive-literal checks passed locally. No live Job what-if was run.
- A separate existing-customer bootstrap runner and exact-key manifest schema
  are locally prepared under `infra/` and documented in
  `docs/existing_customer_identity_bootstrap_20260804.md`. The protected live
  manifest is not stored in Git and has not been created. It accepts only an
  explicitly approved immutable External ID issuer/OID coordinate, existing
  business tenant UUID, customer-account/Stripe anchor hashes, and approval
  and identity-evidence receipt hashes. Email is not an input or selection
  key. Default execution is SERIALIZABLE dry-run plus rollback; apply requires
  the exact manifest hash and operation count. A separate local dispute-only
  rollback runner preserves history, requires its own non-reused approval
  receipt hash, and changes only identity status/audit rows. Bootstrap and
  rollback each have 21 guarded scenarios passing locally. Both CLI runners
  reject manifests inside the source tree. Live DB execution and
  existing-customer linkage remain prohibited and `HOLD`; the local package is
  neither a live dry-run receipt nor apply authorization.

Only the additive, empty identity schema has been applied. No application
setting, API image, Entra production flow, Google Cloud setting, Stripe object,
customer linkage, deployment, or PR merge has been changed in this rollout
status. Git commit/push is evidence publication only and does not satisfy any
deployment, identity, or payment gate.

Current source inspection also identified a pre-existing billing stop gate:
`record_billing_from_invoice` can create a random business tenant when an
`invoice.paid` event has an unknown Stripe Customer and no invoice-line
`tenant_id`. This slice does not change that API/Stripe behavior. Before any
Google or Microsoft production cutover, a separately approved billing change
must make the unknown-customer path fail closed or quarantine it for explicit
reconciliation. Email or unverified Stripe metadata must never select or mint
a tenant. See the canonical architecture document for the full invariant.

The application now rejects an empty or changed binding directory and any
unknown or changed provider before creating or accepting a binding. Equivalent
database CHECK constraints for non-empty `directory_tenant_id` and the three
allowed `identity_provider` values are locally prepared but still
`NOT_APPLIED`. The additive migration is
`infra/20260804_identity_binding_hardening.sql`; its guarded runner refuses
unknown arguments, defaults to rollback, requires the exact reviewed SHA-256
for apply, requires all four identity tables to remain empty, and verifies
unchanged business/Stripe aggregates before and after the transaction. The
migration touches only `external_identity_binding`, drops its two unsafe
defaults, adds and validates the two binding CHECK constraints, and contains no
data mutation. The current runner additionally requires an independently
derived credential-free database-target SHA-256 and the exact aggregate-state
digest from the immutable live migration receipt before `BEGIN`. Its success
output no longer prints the aggregate counts. The offline independent-target
preflight makes no network/DB call and rejects any host, port, database-name,
or URL-protocol mismatch. Guarded hardening-runner tests: `8 passed`; target
preflight tests: `6 passed`. The exact protected-session procedure is in
`docs/identity_binding_hardening_live_gate_20260804.md`. A hash-pinned Cloud
Shell wrapper is also locally prepared with only four exact read-only Azure CLI
commands. It now requires a separately reviewed SHA-256 of the complete
subscription/two-directory/resource/database expectation tuple plus an exact
read-only operation phrase before Azure CLI use. Thirteen synthetic
context/resource/target scenarios pass, and no Azure write or database
connection command is present. Expected identifiers remain protected-session
inputs rather than Git values.

A separate Kudu transaction dry-run bundle is locally prepared under
`infra/identity-hardening-kudu-dryrun/`. Its wrapper is apply-incapable, accepts
only the protected target confirmation SHA-256, pins the isolated directory,
Linux/Node/`pg` runtime and dedicated-engine/SQL hashes, captures underlying
output, and accepts only `dry-run` plus `committed=false`. The dedicated engine
has no CLI, apply option, or commit branch. Thirteen wrapper scenarios, seven
engine scenarios, and exact manifest/source checks pass. It is `NOT_UPLOADED`
and `NOT_EXECUTED`; the exact gate is
`docs/identity_binding_hardening_kudu_dryrun_20260804.md`.

The earlier `a92e41e` ZIP is `HOLD / SUPERSEDED BEFORE LIVE USE`: its wrapper
was dry-run-only, but the bundle also contained the general apply-capable
runner. It was never uploaded or executed and caused no live change. Its
historical snapshot/receipt must not be deleted or treated as an approved
upload. Only the corrected dedicated-engine bundle may proceed to a future
separately approved upload review.

An empty-identity emergency schema rollback is also locally prepared as
`infra/20260804_identity_binding_hardening_emergency_rollback.sql` plus its
guarded runner and documented in
`docs/identity_binding_hardening_emergency_rollback_20260804.md`. It restores
only the two pre-hardening defaults and removes only the two hardening CHECK
constraints. The runner requires the exact DB target, pinned business state,
four empty identity tables, hardened pre-state, exact rollback SQL, a separate
emergency approval receipt, and the hardening-apply receipt. Eleven scenarios
pass, including a post-commit failure that remains visibly
`commit_state=committed`. It is not uploaded and no live rollback dry-run or
apply is approved.

A separate persistent-apply candidate is locally prepared under
`infra/identity-hardening-kudu-apply/` and documented in
`docs/identity_binding_hardening_kudu_apply_20260804.md`. The general runner is
not an approved direct live apply entrypoint and is not included in the apply
bundle. The apply-only wrapper pins the no-CLI apply engine, hardening SQL, and
emergency-recovery manifest and requires independent target,
corrected dry-run package, successful dry-run receipt, change-approval,
production-legacy runtime-state, maintenance-window, recovery-manifest, and
exact-operation confirmations before DB connection. It forwards no receipt
hash and preserves `not_committed`, `committed`, and `unknown` outcomes.
Fifteen wrapper scenarios, eight engine scenarios, and exact apply/recovery
manifest checks pass. Only the
non-executable recovery manifest is a future normal-apply input; emergency
rollback SQL/runner remain offline and require a separate emergency gate. It is not
packaged, uploaded, executed, or approved for live apply.

Hardening migration SHA-256:
`4E4D677AF23BF6781262F185FCC5C99338C112455294984CCAF2B1E59C310E53`.
Do not create the first live binding or enable enforce until this separate
migration is re-reviewed, independently target-confirmed, remote-hash verified,
dry-run, explicitly approved, and applied. The current target preflight and
runner changes have not been uploaded to Kudu or executed against any database.

The separately approved Cloud Shell target preflight passed on 2026-08-04 with
all resource/directory/target/context matches true, Azure write false, and
database connection false. Its protected inputs and confirmation hashes are
not stored in Git or this document. The protected-session receipt is
`C:\tmp\techie-live-audit-20260803\LIVE_IDENTITY_BINDING_CLOUDSHELL_TARGET_PREFLIGHT_RECEIPT_20260804.md`.

The immutable local execution receipt is
`C:\tmp\techie-live-audit-20260803\LIVE_IDENTITY_MIGRATION_RECEIPT_20260804.md`.
It records only the reviewed hashes, aggregate counts, commit result, unchanged
boundaries, and residual warning.

The immutable API-shadow preflight receipt is
`C:\tmp\techie-live-audit-20260803\LIVE_API_SHADOW_PREFLIGHT_RECEIPT_20260804.md`.
It records the Azure role separation, Basic/no-slot constraint, boolean-only
setting gates, read-only probe result, and the next deployment decision gate.

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
4. **Preflight completed and local manual-job package prepared 2026-08-04;
   live write not started:** the production Web App is on Basic B1 with no
   deployment slot. Do not deploy in place or add an app to the same plan.
   The recommended no-ingress manual-job option is now reviewable under
   `infra/identity-shadow-job/`, but it remains on deployment hold. Obtain
   explicit approval before the image push, the single-secret Key Vault
   bootstrap, the managed identity/two narrowly scoped role assignments, the
   job resource, and a separate approval before its first execution. The paid
   Standard-or-higher App Service tier and staging-slot option remains an
   alternative requiring its own approval. Any isolated runtime must keep
   resolver `shadow`, auto-provision `0`, and Entra binding claims trust `0`.
   Before any foundation write, use the reviewed local preflight first in
   `ContextOnly` mode and then, after the separately approved individual secret
   exists, in `FoundationWhatIf` mode. Store no live parameter file. Stop if
   the aggregate-only result is anything other than the exact three-create
   allowlist; what-if approval does not authorize foundation deployment.
   After an approved foundation exists and the immutable image digest and
   enabled secret version are separately available, use `JobWhatIf`. Stop on
   any extra/broad/conditional RBAC assignment or any result other than one
   exact Job create. A passing Job what-if does not authorize Job creation or
   execution.
5. Revalidate the actual live provider/UI state first. The current user report
   is Email-only; the repository's Google and Microsoft controls are not live
   proof. Preserve verified Email traffic on its current authorization tenant
   while `shadow_*` comparison evidence is collected. If a live Google path is
   independently confirmed, verify it separately. Verify the isolated
   Microsoft pilot token's directory/provider claims separately.
6. While all identity tables are still empty, remotely verify and dry-run the
   hash-pinned binding-hardening migration. Apply it only under a separate
   explicit DB approval, then confirm two validated constraints, zero unsafe
   defaults, zero identity rows, and unchanged business/Stripe aggregates.
7. Before global enforce, approve and execute a bounded non-customer instance
   or maintenance window that is not serving normal customer traffic. Use it
   to bootstrap a pilot binding and verify email, Google, Microsoft, and the
   explicit two-authentication link ceremony.
8. Bootstrap existing customers only from immutable verified Entra
   coordinates. Verify each business tenant and Stripe Customer remains
   unchanged; email equality is not a bootstrap key. Use the protected
   manifest contract and runner only after the binding-hardening apply,
   immutable provider evidence, explicit mapping approval, exact remote hash
   verification, default transaction-rollback dry-run, maintenance window, the
   commit-fixed dispute-only rollback runner, its separate approval gate, and
   a protected-batch rollback dry-run. The current local package does not
   authorize live manifest creation, upload, dry-run, or apply.
9. Move normal traffic to `enforce` only after existing-customer coverage and
   rollback evidence are complete, with auto-provision still `0`.
10. Only after all prior gates pass, separately approve and enable each missing
    Google or Microsoft production provider/UI path. Provider enablement must
    not change the business tenant or Stripe anchor.
11. Consider auto-provision separately after collision and rollback
    validation.

## Rollback and stop conditions

- Before enforce, return the resolver to `legacy`; no schema deletion is
  required.
- Disable each newly enabled Google or Microsoft provider/UI independently;
  preserve the verified Email path and any separately verified pre-existing
  provider path.
- Disable or dispute identity bindings; do not delete historical bindings or
  audit rows.
- Stop on directory ambiguity, provider ambiguity, an unknown-Stripe-customer
  event that would create/select a tenant, customer/Stripe count drift, any
  duplicate link, secret/PII exposure, or a migration hash mismatch.

The live database migration is complete and must not be rerun. The read-only
API-shadow probe is also complete. The current owner remains at the
isolated-runtime decision gate because the production Basic plan has no slots.
The recommended manual-job path is prepared locally but not deployed. The
running application remains on legacy behavior until a separately approved
isolated runtime is deployed with resolver `shadow`, auto-provision `0`, and
Entra binding-claim trust `0`. Any push must target the user-owned fork branch;
PR merge and every remaining live gate remain separate and prohibited at this
stage.
