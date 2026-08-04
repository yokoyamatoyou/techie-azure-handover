# TECHIE provider and login UI read-only revalidation

## 2026-08-04 canonical Google route recheck

After Native Authentication was enabled for the exact Hub application, the
Entra user-flow run endpoint was compared with the Hub configuration. Host,
tenant path, client, and redirect target matched; the user-flow endpoint does
not carry a separate `p` parameter because the application association selects
the flow. Adding Microsoft's documented `domain_hint=google` to that canonical
endpoint still returned `AADSTS90023` before Google account selection.

Therefore Google direct routing remains `FAIL / PUBLICLY CLOSED`. The result
must not be worked around with an undocumented hint, `domain_hint=login.live.com`,
or a tenant/domain guess. No Google account was selected and no Google Cloud or
Entra provider setting was changed in this recheck.

- Observed: 2026-08-04 JST
- Owner: one SOL agent only
- Status: `READ-ONLY REVALIDATED / NO ACCOUNT SELECTED / NO LIVE WRITE`
- Applies to: TECHIE Entra External ID provider inventory, user-flow isolation,
  public login choices, and the local provider-specific UI gate

## Live read-only observations

- The workforce Azure directory remains the resource/subscription directory.
  It is not the customer directory and was not used as a business `tenant_id`.
- The TECHIE External ID directory remains the customer authentication
  directory.
- The External ID provider inventory visibly included Email OTP, Google, and
  the isolated Microsoft custom OIDC provider.
- The production user flow selected Email OTP and Google. The production app
  was associated with that production flow.
- The isolated Pilot user flow selected Email OTP and the Pilot Microsoft
  provider. Google was not selected there, and only the Pilot relying-party
  app was associated.
- The public TECHIE Hub showed Email as available, Google as test availability,
  and Microsoft as unavailable at the observed time.
- The public Google action reached the Google account chooser. Observation
  stopped before account selection, credential entry, consent, customer
  creation, or callback completion.
- Microsoft production provider association, direct routing, and a usable
  production Microsoft button were not established.

These observations prove visible provider/user-flow/UI state only. They do not
prove successful Google account registration, canonical binding,
business-tenant resolution, Stripe continuity, resolver cutover, or deployment
of the current repository candidate.

## Ambiguous managed-page evidence

The user-provided managed-page screenshot showed a primary email field above a
separate Google button. When a customer has already selected Google in TECHIE,
presenting that combined page again makes it unclear what
belongs in the upper field. The local candidate therefore uses a TECHIE-owned
method chooser before Entra and does not auto-start the combined page.

## Local candidate after revalidation

The later browser audit in `login_flow_combined_page_audit_20260804.md`
supersedes the Google-route assumption: the observed direct Google request
returned `AADSTS90023`. Google now also requires
`GOOGLE_AUTH_DIRECT_ROUTE_VERIFIED=true`, which defaults to false.

- Login and signup use the same grouped Email / Google chooser.
- Email explicitly includes Outlook, Hotmail, and Microsoft 365 addresses and
  explains that a one-time code is sent to the address.
- Google is selectable only when both `GOOGLE_AUTH_ENABLED=true` and
  `GOOGLE_AUTH_DIRECT_ROUTE_VERIFIED=true`; missing or false configuration
  fails closed. Its enabled route uses `domain_hint=google` only after the
  exact production app/user-flow pair is independently proven.
- Microsoft SSO is not presented or configurable in the public Hub. Personal
  and company Microsoft-hosted email addresses use Email OTP. The isolated
  Pilot remains historical evidence only; see
  `microsoft_external_id_routing_decision_20260804.md`. Server-side link-intent
  and completion rules also reject Microsoft as a newly linkable provider.
- Google uses the same provider gate when adding a login method from contract
  management. Native Email has a local two-authentication source/target link
  candidate, but both its public control and backend API remain fail-closed by
  default. Existing-target and explicit target-signup browser sequences pass
  against a synthetic local broker with one Email field per Email step and one
  code field per OTP step. Synthetic binding conflict clears the browser
  session and leaves only a fresh-login action. Live OTP, binding transaction,
  real External ID user reconciliation, and unchanged tenant/Stripe proof
  remain `NOT_VALIDATED`.
- No provider selection can derive or merge a business tenant from email,
  directory IDs, or Stripe data.

## Explicit no-change record

- Azure/Entra write: `false`
- Google Cloud write: `false`
- Stripe write: `false`
- DB/API connection or write: `false`
- Account selection, credential entry, consent, or customer creation: `false`
- Provider/user-flow/app association change: `false`
- Resolver setting change: `false`
- Production deployment or PR merge: `false`
- Origin push: `false`

## Remaining production gates

1. Separately approve and complete the identity-binding hardening live gate.
2. Bootstrap existing customers only from approved immutable External ID
   coordinates; do not use email or Stripe metadata.
3. Resolve the unknown-Stripe-Customer invoice behavior before a Google
   production cutover.
4. Revalidate canonical principal, stable business `tenant_id`, unchanged
   `customer_account`, and unchanged Stripe Customer/contract/ledger evidence
   before enabling any production provider.
