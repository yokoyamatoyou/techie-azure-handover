# TECHIE identity / tenant / Stripe - SOL-only next-window handoff

- Prepared: 2026-08-04 JST
- Next owner: one SOL model only
- Orchestration, subagents, Luna, and Terra: prohibited by user instruction
- Status: `DOCS CLARIFIED / LIVE PROVIDER STATE NOT REVALIDATED / NO LIVE WRITE AUTHORIZED`
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
clear Email, Google, and Microsoft login choices. Multiple verified login
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

- User-observed production login is Email-only. Google/Microsoft production
  provider and UI state is `NOT_REVALIDATED` in this docs-only slice.
- The repository Hub candidate contains Email, Google, and Microsoft login
  cards and a two-authentication link flow. This is not deployment evidence.
- The additive identity schema and read-only probe evidence exist, but
  production resolver behavior remains `legacy`; automatic provisioning and
  binding-claim trust remain off.
- The identity-binding hardening target preflight passed without an Azure
  write or DB connection. The hardening migration itself is `NOT_APPLIED`.
- Existing-customer bootstrap and dispute-only rollback packages pass local
  tests, but no live manifest, live dry-run, or apply is authorized.
- Microsoft direct routing with `domain_hint=login.live.com` is `FAIL / HOLD`.
  Do not reintroduce it. The repository candidate does not send a Microsoft
  domain hint.
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
- Marked repository three-option UI as candidate source, not live evidence.
- Recorded a pre-existing billing/API risk as a production-cutover stop gate.

No Azure, Entra, Google Cloud, Stripe, DB, API, app setting, customer, provider,
deployment, or PR-merge state changed in this slice.

## 6. High-risk current-code finding

`shared/billing/repository.py::record_billing_from_invoice` can create a random
business tenant when an `invoice.paid` event has an unknown Stripe Customer and
no invoice-line `tenant_id`. The new identity docs do not change that existing
behavior.

Before Google or Microsoft production cutover, a separately approved
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

Report confirmed current state, source-only findings, live `NOT_REVALIDATED`
items, changes made, no-change boundaries, rollback availability, remaining
approvals, and AGENTS/WORKLOG update need separately.
