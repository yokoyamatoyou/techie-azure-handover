# TECHIE login direction 1 design QA

- Verified: 2026-08-04 JST
- Route/state: local `/login` and `/signup`, signed out
- Browser viewport: 1280 x 720 CSS px
- Product decision: Email OTP plus Google; Microsoft SSO is not offered

## Result

`passed` for the local repository candidate.

- Login and signup each show exactly two enabled choices: Email and Google.
- No Microsoft authentication or account-link control is present.
- Email copy explicitly covers Outlook, Hotmail, and Microsoft 365 addresses
  and says that a confirmation code is sent to the address.
- Google copy explicitly says that it proceeds to Google account selection.
- Signup provider controls carry `mode=signup`; signup does not auto-start the
  combined Entra page before the customer chooses a method.
- The selected direction uses the existing TECHIE orange, cream, surface,
  border, deep-brown, muted, and information tokens.
- Both inspected routes had no horizontal overflow at 1280 x 720.
- Native buttons and focus-visible styling remain in place.

## Contract evidence

- `infra/test_auth_provider_policy.js`: `auth provider policy contract: PASS`
- `shared/auth/test_identity_resolver.py`: `52 passed`
- Identity infrastructure Node contracts: `118 passed` plus the provider
  policy contract PASS
- Microsoft-like configuration values are ignored by the public provider
  policy; `authRequest('microsoft', ...)` returns `null`.
- Backend compatibility tests may still use the provider coordinate
  `microsoft` to prove that dormant/historical bindings cannot rewrite the
  canonical business tenant or existing customer anchor. This does not expose
  Microsoft SSO.

## Boundaries

This is local UI and source evidence only. It does not prove production
deployment, completed Google registration, identity hardening, customer
bootstrap, resolver cutover, or Stripe continuity in production. No live
provider, customer, DB, API, Stripe, or deployment state was changed.

## Follow-up polish

- P3: add provider logos only after approved source assets are added to the
  TECHIE design system; do not approximate brand marks.
