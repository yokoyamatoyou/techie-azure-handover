# TECHIE identity / tenant / Stripe - SOL-only next-window handoff

## 2026-08-04 Native Email approval update

The user explicitly approved the Entra Native Authentication architecture.
Local candidate code and its fail-closed feature gates are recorded in
`docs/native_email_auth_implementation_20260804.md`. This is not live Entra
deployment evidence. The exact External ID application has since had public
client flows and Native Authentication enabled and read back successfully; see
`docs/native_auth_live_app_enablement_receipt_20260804.md`. Email native auth
and Google remain publicly closed until their exact production paths are
independently verified.

- Prepared: 2026-08-04 JST
- Next owner: one SOL model only
- Orchestration, subagents, Luna, and Terra: prohibited by user instruction
- Status: `LOCAL UI GATED / READ-ONLY PROVIDER STATE REVALIDATED / NO LIVE WRITE AUTHORIZED`
- Repository: `C:\tmp\techie-azure-handover`
- Branch: `agent/clarify-techie-login-options`
- Push target: user-owned remote `fork` only
- Upstream `origin`: read-only for this task; never push

## 1. Required read order

Read every file completely before browser, cloud, DB, API, or deployment work:

1. `C:\Users\横山裕明\Documents\実行環境準備完了\tetie\AGENTS.md`
2. `C:\tmp\techie-azure-handover\docs\identity_tenant_stripe_architecture_20260804.md`
3. `C:\tmp\techie-azure-handover\docs\identity_resolver_rollout_20260803.md`
4. `C:\tmp\techie-azure-handover\docs\identity_binding_hardening_live_gate_20260804.md`
5. `C:\tmp\techie-azure-handover\docs\existing_customer_identity_bootstrap_20260804.md`
6. `C:\tmp\techie-azure-handover\docs\phase2_implementation_blueprint.md`
7. `C:\tmp\techie-live-audit-20260803\LIVE_IDENTITY_BINDING_CLOUDSHELL_TARGET_PREFLIGHT_RECEIPT_20260804.md`
8. `C:\tmp\techie-live-audit-20260803\MICROSOFT_LOGIN_READONLY_ASSESSMENT_20260803.md` as historical Pilot evidence only

The older
`C:\tmp\techie-live-audit-20260803\SOL_ONLY_NEXT_WINDOW_HANDOFF_20260803.md`
is superseded for current next-owner decisions. It remains historical evidence
and must not override this handoff or the canonical architecture document.

## 2. User objective

Keep TECHIE Entra External ID as the customer authentication authority and add
clear Email and Google login choices. Outlook, Hotmail, Microsoft 365, and
other Microsoft-hosted addresses use Email OTP; Microsoft SSO is not offered.
Multiple verified login
methods must resolve to the same canonical TECHIE principal, stable business
`tenant_id`, existing `customer_account`, and existing Stripe Customer.

The workforce Azure directory continues to own the subscription and resources;
it is not a customer directory. Google Cloud owns only the Google OAuth client
and federation configuration. Stripe owns billing objects; it does not own
authentication or choose a business tenant.

## 3. Immutable identifier chain

```text
External ID directory + issuer + provider + immutable oid/sub
  -> external_identity_binding
  -> canonical_principal.principal_id
  -> tenants.tenant_id
  -> customer_account.tenant_id
  -> customer_account.stripe_customer_id
  -> existing Stripe contract and ledger history
```

Email equality, billing email, Stripe metadata, Azure workforce tenant ID, and
External ID directory tenant ID never select or merge a business tenant.

## 4. Current evidence and non-evidence

- A 2026-08-04 read-only revalidation observed Email available, Google as test
  availability, and Microsoft unavailable in the public Hub. The Google action
  reached the Google account chooser without account selection. The production
  flow visibly selected Email OTP and Google; Microsoft remained isolated to
  its Pilot flow. See `identity_provider_ui_readonly_revalidation_20260804.md`.
- The repository Hub candidate now contains one grouped Email and Google
  chooser for signup and login, plus a two-authentication link flow. Microsoft
  SSO is absent from the public UI and runtime configuration. This is not
  deployment evidence.
- The additive identity schema and read-only probe evidence exist, but
  production resolver behavior remains `legacy`; automatic provisioning and
  binding-claim trust remain off.
- The identity-binding hardening target preflight passed without an Azure
  write or DB connection. The hardening migration itself is `NOT_APPLIED`.
- Existing-customer bootstrap and dispute-only rollback packages pass local
  tests, but no live manifest, live dry-run, or apply is authorized.
- Microsoft direct routing with `domain_hint=login.live.com` is `FAIL / HOLD`.
  Do not reintroduce it. The repository candidate rejects that value even when
  supplied through configuration.
- Git commit, push, local tests, and source screenshots never prove live
  Entra, Google, Stripe, DB, API, or deployment state.

## 5. Docs-only changes in this slice

- Added a canonical directory/identity/business-tenant/Stripe diagram and ID
  contract.
- Corrected the identity rollout so it no longer assumes Google is already a
  verified live production path.
- Clarified that Stripe is a billing authority, not an authentication or
  tenant-selection authority.
- Clarified that the inspected application anchor is
  `customer_account.tenant_id -> stripe_customer_id`; `tenants.stripe_id` is
  not an identity-link key and requires a separate compatibility audit.
- Marked the repository provider UI as candidate source, not live evidence;
  it now presents Email and Google only.
- Recorded a pre-existing billing/API risk as a production-cutover stop gate.

No Azure, Entra, Google Cloud, Stripe, DB, API, app setting, customer, provider,
deployment, or PR-merge state changed in this slice.

## 6. High-risk current-code finding

`shared/billing/repository.py::record_billing_from_invoice` can create a random
business tenant when an `invoice.paid` event has an unknown Stripe Customer and
no invoice-line `tenant_id`. The new identity docs do not change that existing
behavior.

Before Google production cutover, a separately approved
billing/API slice must make an unknown Stripe Customer fail closed or enter an
explicit reconciliation queue. It must never create/select a tenant from a
fallback UUID, email, or unverified Stripe metadata. Do not implement this
change without the user's separate approval for DB/API/Stripe integration
behavior.

## 7. Next safe action in the new window

1. Confirm this branch is clean at the documented handoff commit and the user
   fork contains that commit.
2. Read the canonical architecture and current rollout completely.
3. Report the exact next approval gate without performing it. The likely first
   live gate remains either a fresh read-only provider/UI-state revalidation or
   the separately approved binding-hardening DB dry-run; neither is authorized
   by this handoff.
4. Keep UI copy improvement as a separate local implementation slice. Replace
   internal architecture wording such as Wix/Azure Hub descriptions with
   customer-facing actions such as register, sign in, choose a plan, manage
   billing, and open services. No UI code was changed in this docs-only slice.

## 8. Separate approvals still required

- Any Entra provider, user-flow, app association, Pilot user, or production UI
  write.
- Any Google Cloud OAuth change.
- Any DB connection for hardening dry-run, hardening apply, identity bootstrap,
  identity linking, resolver migration, or rollback.
- Existing-customer mapping or use of any live customer identity.
- Billing webhook/API behavior change, Stripe metadata change, or Stripe object
  change.
- Resolver `shadow` or `enforce`, automatic provisioning, or trusted binding
  claims.
- API/container deployment, Azure resource change, production deployment, PR
  merge, or upstream push.

## 9. Stop conditions

Stop before any action that could expose a token, secret, customer value,
Stripe identifier, or raw protected hash; touch the wrong Azure directory;
select a tenant from email or Stripe metadata; create a second business tenant
for an existing customer; rewrite the Stripe anchor; reuse the failed Microsoft
domain hint; or cross an approval boundary without a specific new approval.

## 10. Required reporting

Report confirmed current state, source-only findings, limits of the latest
read-only live observation, changes made, no-change boundaries, rollback
availability, remaining approvals, and AGENTS/WORKLOG update need separately.

## 11. Post-handoff local continuation

The working tree after commit `fbef631a8fc031a90513e96ca1c4658f8e0bdc6c`
contains uncommitted local candidate changes. They:

- implement the user-selected grouped provider UI in existing TECHIE colors;
- stop automatic signup redirection before a provider is selected;
- require an explicit Google enable flag and keep Google explicitly routed;
- remove Microsoft SSO from the public chooser, account-link controls, and
  runtime configuration;
- state that Outlook, Hotmail, and Microsoft 365 addresses use Email OTP;
- keep the Microsoft Pilot as historical evidence only and prohibit restoring
  `domain_hint=login.live.com`;
- apply provider availability to account-link entry points;
- explain that safely linked methods return to the same contract/billing
  management while Stripe data is never used as login evidence;
- include the provider policy in the Hub container image;
- add local design QA evidence and focused regression coverage, including
  provider-specific login, signup, and account-link request contracts.

No commit, push, live provider setting, app association, DB/API behavior,
Stripe object, resolver mode, or deployment was changed by this continuation.

## 12. New-window local connection and deployment audit

The next-window SOL found and locally corrected two pre-deployment gaps:

- unauthenticated Native Email requests would previously have been rejected by
  `NiceGUIAuthMiddleware` before reaching the broker; only the exact
  `/api/auth/native-email` prefix is now public, while Origin, encrypted flow,
  token validation, no-store, and rate-limit controls remain enforced;
- the production Web App deployment entrypoint did not carry the broker
  settings, and the candidate Bicep circularly required live verification
  before the broker could start. The candidate now separates hidden broker
  deployment from a later, separately confirmed public Hub enablement and
  scopes the envelope key to API/kotomake runtimes.

Focused verification now reports `70 passed`, all 13 infra Node contract files
passing, both PowerShell deployment scripts parsing without errors, and
thirteen invalid deployment combinations stopping before Azure CLI execution
(ten identity-linking and three Native Email combinations). Added-line
sensitive-literal and prohibited Microsoft runtime-hint
scans pass. No Azure CLI or Bicep CLI is installed in the local command
environment, so a fresh real Bicep compile remains `NOT_RUN` in this window.

These are uncommitted local candidate changes only. No build, image push,
cloud setting, live API call, OTP, customer, DB, Stripe, Google Cloud, deploy,
commit, or push occurred.

Native Email account linking now has an uncommitted local candidate. It
reauthenticates the bound source, creates a short-lived server-side intent, and
then requires a separate target Email login or explicit signup. It does not
use email equality and does not retain the source bearer token in session
storage. The Hub control and both link API mutations fail closed unless the
separate identity-link flag is true; checked-in and backend defaults remain
off. The local contract suite covers source/target routing and the API
fail-closed gate. A synthetic local browser sequence now passes for existing
Native Email login, fixed source reauthentication, target Email login, link
completion, and return to the same contract-management screen. Every Email
screen contained one Email field and every OTP screen one code field; the
method chooser contained none. This contacted no Entra, DB, Stripe, or Google
Cloud system. The explicit target-signup path also completed against the
synthetic broker. A synthetic binding conflict cleared target token and link
state, blocked cached-account fallback, removed the stale logout control, and
left only a fresh-login action. Live OTP, live DB transaction, real External
ID user reconciliation, and unchanged tenant/customer/Stripe proof remain
`NOT_VALIDATED`.

The same audit found and fixed an unnecessary coupling where the Native Email
button checked MSAL library availability before entering the native route.
Native Email is now evaluated first; Google and delegated/federated routes
still require MSAL. Contract tests protect this ordering.

The public Microsoft prohibition is also enforced below the UI. The
link-intent API and repository accept only Email and Google. Dormant historical
Microsoft coordinates remain readable, but a Microsoft link intent cannot be
created and any pending historical one is cancelled as a provider mismatch
before binding, tenant, customer-account, or Stripe mutation.

The deployment candidate now renders and supplies identity linking only with
resolver `enforce`, schema verification, separate binding-hardening and
existing-customer-bootstrap confirmations, while auto-provision and binding-
claim trust remain off. Bicep independently computes an effective false value
when any condition is absent. Both entrypoints require separate protected
64-character SHA-256 values for the immutable hardening and bootstrap receipts;
the values are never rendered into Hub config, runtime settings, outputs, or
logs. All defaults remain false. These confirmations and hashes are downstream
guards only; they do not prove or authorize the live hardening, bootstrap,
resolver, DB, or deployment gates.

A target signup can create an External ID user before binding completion. If a
later binding conflicts or fails, the Entra user can remain unbound and needs
an approved operator reconciliation/removal procedure. Automatic provisioning
is off, so this candidate does not create a business tenant, customer account,
or Stripe Customer. Identity linking therefore remains a live `HOLD` even
though the local candidate is implemented.
