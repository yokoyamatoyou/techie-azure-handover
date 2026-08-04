# TECHIE Native Authentication live app enablement receipt — 2026-08-04

## Scope and authorization

The user explicitly approved the Entra Native Authentication configuration.
This operation was limited to the already configured TECHIE customer External
ID directory and the application whose public client ID matches the Hub
configuration. No workforce-directory application was changed.

## Pre-write evidence

- Correct customer External ID directory: confirmed in the Entra admin center.
- Configured application: exact Hub client match, one SPA redirect, zero public
  client platforms before the change.
- Target customer user flow: associated with the configured application.
- Providers: Email One Time Passcode and Google.
- Collected attributes: Email Address and Display Name.
- Public client flow: disabled.
- Native Authentication: disabled.

No customer account was selected and no login or OTP challenge was started
during the pre-write inspection.

## Applied change

Only these two application authentication settings were enabled and saved:

1. allow public client flows;
2. enable Native Authentication.

Post-save readback returned both settings enabled, the Save control returned to
disabled, and the portal reported a successful update.

## Safe protocol preflight

After save, a sign-in `initiate` request used a random address under the
reserved `example.invalid` domain and advertised `oob redirect`. The endpoint
returned `user_not_found`, rather than `invalid_client`, establishing that the
exact application now accepts Native Authentication initiation.

The challenge endpoint was not called. Therefore no OTP was sent, no customer
value was used, and no user was created.

## Unchanged boundaries

- Hub production flags: unchanged and still fail closed.
- API deployment and environment: unchanged.
- Production DB: no connection or write in this operation.
- Stripe: no connection or write in this operation.
- Google Cloud: no write in this operation.
- Identity schema, bootstrap, resolver, auto-provision, and binding-claim trust:
  unchanged.
- Microsoft SSO: not enabled.

## Rollback

The direct Entra rollback is to reopen the same application Authentication
settings, disable Native Authentication and public client flows, then save and
read back both as disabled. The Hub remains closed independently, so this
rollback does not require tenant, customer, identity-binding, or Stripe changes.

## Remaining gate

Do not enable the public Hub Native Email flags until the broker is deployed
with its protected envelope key and allowed origin, then a controlled Email OTP
canary passes token validation and existing resolver invariants.

Google was rechecked separately against the canonical run-user-flow endpoint
and still failed before provider handoff with `AADSTS90023`. Native Email app
enablement does not change that independent Google gate.
