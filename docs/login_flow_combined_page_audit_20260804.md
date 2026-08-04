# TECHIE login flow combined-page audit

- Audited: 2026-08-04 JST
- Status: `FAIL / UI CLOSED / NO LIVE WRITE`

Update after explicit approval: a fail-closed Native Email OTP candidate is now
locally implemented. See `native_email_auth_implementation_20260804.md`.
Production remains closed until the exact External ID native-auth configuration
and live Email OTP path pass the listed gates.
- Screenshot set:
  `C:\Users\横山裕明\AppData\Local\Temp\techie-login-flow-audit-20260804`

## Scope and user goal

The customer must choose Email or Google once and must not be asked to choose
between the same methods again on a Microsoft-hosted intermediate page.

## Steps and health

1. **TECHIE method chooser — PASS.** The local candidate has no email input.
   It presents two grouped actions, Email and Google, and explains that
   Outlook, Hotmail, and Microsoft 365 addresses use Email OTP.
2. **Email selection — FAIL.** Browser-delegated Email reaches the combined
   Entra page containing both the email-address field and a Google button. The
   customer has already selected Email, so the second provider choice is
   redundant and confusing.
3. **Google selection — FAIL.** The local candidate sends
   `domain_hint=google`, but the observed app/user-flow pair returned
   `AADSTS90023` instead of reaching Google account selection. No account was
   selected and no customer or provider state was changed.

## Fail-closed response

The repository provider policy now requires both:

- `GOOGLE_AUTH_ENABLED=true`; and
- `GOOGLE_AUTH_DIRECT_ROUTE_VERIFIED=true`.

The second flag defaults to `false`. Google therefore remains unavailable
until the exact production app/user-flow association is revalidated and the
direct route reaches Google account selection without `AADSTS90023`.

## Email UX decision gate

Microsoft documents issuer acceleration for Google but does not document an
equivalent Email OTP `domain_hint`. The existing one-app/one-user-flow
browser-delegated design therefore cannot prove an Email-only managed page.

The clean target is:

- TECHIE-native Email OTP UI backed by Entra native authentication; and
- browser-delegated Google after its direct route is independently verified.

Because the native authentication API does not support browser CORS, TECHIE
must add a narrow server-side authentication-flow broker. This changes the
authentication security boundary and requires explicit architecture approval,
threat-model tests, rate limiting, continuation-token protection, and a
feature-flag rollback to the current Email browser flow before implementation
or deployment.

## Accessibility observations and limits

The TECHIE chooser has native buttons, visible labels, status text, and a
clear reading order. The duplicated provider choice on the Entra page is a
cognitive and task-flow problem independent of visual styling. Screenshots do
not prove keyboard, screen-reader, zoom, error-recovery, OTP resend, or focus
management behavior; those remain acceptance gates for any native flow.

No Entra, Google Cloud, Stripe, DB, API, customer, user-flow, or deployment
write was performed during this audit.
