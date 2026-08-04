# TECHIE Native Email Authentication implementation receipt — 2026-08-04

## Status

- Code: `LOCAL_IMPLEMENTED`
- Offline tests: `PASS`
- Local browser path: `PASS_WITH_SYNTHETIC_BROKER`
- Entra External ID application native-auth configuration: `APPLIED_AND_READ_BACK`
- Live Email OTP: `NOT_VALIDATED`
- Production deploy: `NOT_PERFORMED`
- Production DB / Stripe writes: `NONE`
- API route connection audit: `LOCAL_PASS`
- Deployment staging contract: `LOCAL_PASS / NOT_EXECUTED`
- Native Email account-link candidate: `LOCAL_IMPLEMENTED / LIVE_NOT_VALIDATED`
- Native Email account-link browser sequence: `PASS_WITH_SYNTHETIC_BROKER`
- Target-signup browser sequence: `PASS_WITH_SYNTHETIC_BROKER`
- Binding-conflict browser recovery: `LOCAL_PASS / LIVE_CLEANUP_NOT_VALIDATED`
- Identity-linking deployment activation contract: `LOCAL_PASS / NOT_EXECUTED`

This receipt does not authorize or claim a production rollout.

## User experience contract

The TECHIE method chooser contains no email input. When native Email OTP is
enabled and live-verified, selecting Email opens a TECHIE-owned page with:

1. exactly one email-address field;
2. one confirmation-code field on the next page; and
3. no Google or Microsoft provider choice inside either Email step.

Outlook, Hotmail, and Microsoft 365 addresses use this ordinary Email OTP
route. TECHIE does not present Microsoft SSO as a public provider.

## Security and ownership boundary

`shared/auth/native_email.py` is a narrow broker for Entra External ID native
authentication. It:

- never chooses, creates, or merges a TECHIE business `tenant_id`;
- never reads or writes `customer_account`, Stripe Customer, subscription, or
  payment data;
- never uses email equality, Stripe metadata, the workforce directory, or the
  External ID directory tenant as a business-tenant selector;
- never returns the Entra continuation token to browser JavaScript;
- seals continuation state, intent, and the submitted email inside a
  five-minute AES-GCM envelope;
- requests no `offline_access` scope and returns no refresh token;
- validates the returned ID token with the existing External ID validator
  before releasing it to the Hub;
- accepts requests only from an explicit Hub-origin allowlist; and
- applies an additional per-instance hashed abuse limit without retaining the
  email address in its limiter keys.

The unauthenticated start and verify endpoints are explicitly limited to the
`/api/auth/native-email` middleware prefix because no bearer token exists
before Email OTP completes. This does not bypass the broker's exact Hub-Origin
allowlist, encrypted short-lived flow state, or abuse limit. Success and error
responses carrying flow or token material include `Cache-Control: no-store`
and `Pragma: no-cache`.

The source-to-runtime route is covered by a contract test: Hub requests use
`API_BASE_URL`; the production API Web App uses the `kotomake` image; that
image starts `note.note_writer_app`; and that application mounts the native
Email router. This closes the earlier local gap where authentication
middleware would have returned 401 before the router was reached.

Canonical principal, business tenant, and billing resolution remain the
responsibility of the existing token validator and identity resolver on the
first authenticated API request. Auto-provision and binding-claim trust remain
off unless their separate rollout gates are approved.

## Native Email account-link candidate

The local Hub candidate can use Native Email as either side of the existing
two-authentication link ceremony. It first reauthenticates the already bound
source method, creates a short-lived server-side link intent, then requires a
separate login to an existing Email identity or an explicit new Email signup
before calling `link-complete` with the target token. It never treats matching
email text as proof of account ownership or as a merge key.

The source bearer token is not copied into session storage. After successful
binding, the newly verified target method becomes the current browser session.
If completion fails, the candidate clears the locally stored target token,
blocks fallback to a cached MSAL account, and requires a fresh login. Both the
Hub entry point and the link create/complete API fail closed unless
`IDENTITY_LINKING_ENABLED=true`; the checked-in public setting and backend
environment default remain off.

The deployment candidate renders and supplies that flag only when the explicit
identity-linking switch is present together with resolver `enforce`, verified
schema, separately confirmed binding hardening, and separately confirmed
existing-customer bootstrap. The initial rollout contract also refuses
auto-provision and binding-claim trust. Bicep independently derives an
effective false value unless the same conditions hold. These switches are not
proof that their live gates passed; they may be used only with the separately
approved immutable receipts. Both entrypoints also require distinct protected
64-character receipt SHA-256 values; the values are not rendered into Hub
configuration, runtime settings, outputs, or logs.

The link-intent API and repository accept only `email` and `google`. The
historical backend value `microsoft` remains readable as an identity
coordinate, but it cannot create a new link intent. A pending historical
Microsoft intent is cancelled as a provider mismatch before any binding,
tenant, customer-account, or Stripe mutation.

This is local source and contract-test evidence only. A target `signup` can
create an Entra External ID user before the binding transaction completes. If
the later binding is rejected or conflicts, that External ID user can remain
unbound and needs an approved operator reconciliation/removal procedure. The
candidate does not create a business tenant, customer account, or Stripe
Customer, and automatic provisioning remains off. The full live link
sequence, live OTP, live DB transaction, conflict recovery, and invariant
proof are all `NOT_VALIDATED`.

Native Email routing is evaluated before the MSAL browser-library requirement.
This keeps the TECHIE-owned Email flow usable if the unrelated delegated or
federated library cannot load; Google and delegated fallback still require
MSAL. A focused contract test protects this branch order.

## Fail-closed flags

Backend readiness requires all of:

- `EMAIL_NATIVE_AUTH_ENABLED=true`
- a valid `ENTRA_NATIVE_TENANT_SUBDOMAIN`
- `ENTRA_CLIENT_ID`
- an explicit Hub origin
- `EMAIL_NATIVE_AUTH_SESSION_KEY` containing a base64url-encoded 32-byte key

Public Hub availability separately requires both:

- `EMAIL_NATIVE_AUTH_ENABLED=true`
- `EMAIL_NATIVE_AUTH_LIVE_VERIFIED=true`

The existing delegated Email screen is an operator-controlled emergency route
through `EMAIL_DELEGATED_AUTH_FALLBACK_ENABLED`. It is false by default and is
never entered automatically. If enabled during an incident, the UI explicitly
warns that the Entra provider selection can be shown again.

Google remains independently closed until both `GOOGLE_AUTH_ENABLED` and
`GOOGLE_AUTH_DIRECT_ROUTE_VERIFIED` are true for the exact production
app/user-flow pair.

Deployment is deliberately two-stage. `-EnableNativeEmailBroker` prepares the
server broker while the Hub method remains hidden. Publishing the Hub method
also requires both `-PublishNativeEmail` and the separate
`-ConfirmNativeEmailLiveVerified` confirmation. Partial combinations fail
before Azure CLI execution. The session key must be supplied through the
protected process environment and decode to exactly 32 bytes. It is scoped to
the API/kotomake runtime rather than the Hub or unrelated service containers.
No deployment command has been run.

## Rollback

Before rollout, retain the currently active Hub and API revisions. A native
Email incident can be contained without touching identity or billing records:

1. set the public live-verification flag false so the native Email control is
   disabled;
2. keep or set `IDENTITY_LINKING_ENABLED=false` so no new link intent or
   completion request is accepted;
3. set the backend native-auth flag false and restart the API revision;
4. route traffic to the retained previous revision if the API itself is
   unhealthy; and
5. enable the delegated Email fallback only as a deliberate availability
   decision that accepts the documented combined-screen UX.

No rollback step changes identity bindings, `tenant_id`, customer accounts, or
Stripe mappings.

## Acceptance gates still open

1. Enable public-client/native-auth support for the exact External ID app.
2. Confirm the app is attached to the intended customer user flow.
3. Confirm Email OTP and required sign-up attributes. The broker currently
   submits only `displayName`; unexpected required attributes fail closed.
4. Configure the server-side envelope key and allowed Hub origin without
   exposing either value.
5. Run one approved canary sign-up and one approved existing-user sign-in.
6. Verify the returned token resolves through the existing resolver without
   business-tenant or Stripe mapping changes.
7. Verify rate limiting at the platform edge if the API scales beyond one
   instance.
8. Only after those checks set the public live-verification flag true.
9. Before any live link enablement, separately approve resolver enforcement,
    binding hardening, existing-customer bootstrap, live DB validation, and an
    operator procedure for an unbound target created by a failed signup/link.
10. Run approved live canaries for both an existing Email target and the
    explicit target-signup path, including binding-conflict recovery.
11. Prove after those canaries that the canonical principal is shared while
    business `tenant_id`, `customer_account`, Stripe Customer, subscriptions,
    contracts, credits, and ledgers are unchanged.

## Local evidence

- Native broker, middleware, deployment, and route-chain tests: `14 passed`
- Provider-policy contract: `PASS`
- Existing identity-resolver focused suite: `56 passed`
- Combined focused Python suite: `70 passed`
- PowerShell deployment entrypoint parsing: `PASS`; thirteen invalid deployment
  combinations stopped before Azure CLI execution (ten identity-linking and
  three Native Email combinations).
- Hub config template compiled with both closed and enabled boolean renderings;
  checked-in public config remains closed.
- Sensitive added-line scan and prohibited Microsoft runtime-hint scan: `PASS`.
- Browser: Login and sign-up each exposed exactly one email input; the Email
  step exposed zero Google buttons and no horizontal overflow.
- Browser synthetic sequence: method chooser -> single email -> single OTP ->
  authenticated home completed without contacting Entra, DB, or Stripe.
- Browser synthetic account-link sequence: existing Native Email login ->
  fixed/read-only source Email reauthentication -> one-time source OTP ->
  explicit existing-target choice -> one target Email field -> one target OTP
  -> link completion -> same contract-management screen completed. No Entra,
  DB, Stripe, or Google Cloud connection was made.
- Browser synthetic target-signup sequence: source reauthentication -> explicit
  new-target choice -> one display-name field plus exactly one Email field ->
  one target OTP -> link completion -> same contract-management screen
  completed.
- Browser synthetic binding-conflict sequence: target completion returned a
  conflict; the target token and link state were cleared, cached-account
  fallback remained blocked, the stale logout control was removed, and only a
  fresh-login action remained. No live External ID user was created or removed,
  so operator reconciliation of a real unbound signup remains `NOT_VALIDATED`.
