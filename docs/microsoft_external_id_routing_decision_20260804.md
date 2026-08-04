# TECHIE Microsoft External ID routing decision

- Date: 2026-08-04 JST
- Scope: read-only Microsoft documentation review, existing Pilot evidence,
  and the superseding Email-OTP product decision
- Live write status: none

## Original product concern

Selecting Microsoft in TECHIE must not send the customer to a combined page
whose email field and Microsoft action compete with each other. The selected
route must remain inside the TECHIE Entra External ID trust boundary and must
not select a business tenant or billing account from an email address,
directory ID, provider metadata, or Stripe metadata.

## Current evidence

The isolated personal-Microsoft-account Pilot succeeds only when the customer
first reaches the managed TECHIE page and selects its Microsoft custom OIDC
button. The two direct-route experiments are not usable:

- `login.live.com` bypassed the managed page but failed with `AADSTS50020`;
- `login.microsoftonline.com` did not bypass the managed page.

Neither value may be treated as a production route.

Microsoft's current External ID documentation distinguishes these cases:

1. Google has the built-in issuer-acceleration value `google`.
2. A custom OIDC provider normally accelerates with the domain portion of its
   issuer URI.
3. A custom OIDC federation to a specific Microsoft Entra organization uses
   that organization's primary domain, for example an `onmicrosoft.com`
   domain. Microsoft also documents an unavoidable domain-confirmation dialog.
4. One external-tenant application can be associated with only one user flow.
   A second Microsoft-only user flow therefore requires a second application;
   it is not a routing switch for the existing TECHIE application.

Primary sources:

- [Identity providers and issuer acceleration](https://learn.microsoft.com/en-us/entra/external-id/customers/concept-authentication-methods-customers)
- [Microsoft Entra organization OIDC federation](https://learn.microsoft.com/en-us/entra/external-id/customers/how-to-entra-id-federation-customers)
- [Custom OIDC federation](https://learn.microsoft.com/en-us/entra/external-id/customers/how-to-custom-oidc-federation-customers)
- [Application to user-flow association](https://learn.microsoft.com/en-us/entra/external-id/customers/how-to-user-flow-add-application)

## Superseding product decision

Microsoft SSO is not a TECHIE public registration or login method. The public
Hub presents only Email and Google. Outlook, Hotmail, Microsoft 365, and other
Microsoft-hosted addresses register and sign in through Email OTP. The Hub has
no Microsoft provider button and no Microsoft routing configuration.

The provider value `microsoft` remains valid only as a dormant/historical
identity coordinate in the backend schema and tests. It does not establish a
public provider, production availability, or permission to enable one. The
local candidate now enforces this boundary server-side: link-intent creation
accepts only Email and Google, the repository independently rejects Microsoft
link intents, and any pending historical Microsoft intent is cancelled as a
provider mismatch before an identity binding is inserted.

Any future Microsoft federation proposal is a new product and security slice.
It requires an explicit new approval, supported provider-specific routing,
fresh provider/user-flow/app evidence, canonical-account and Stripe continuity
proof, and new public UI work. It must not restore `domain_hint=login.live.com`.

## Historical routing assessment

### Personal Microsoft accounts

The current Pilot does not have a supported, proven provider-specific direct
route. Personal Microsoft registration and login therefore remain disabled in
the public Hub. Do not use a Microsoft authentication-service hostname as a
substitute for a verified issuer-acceleration domain.

### Organization-specific Microsoft accounts

A future, separately approved candidate could consider this narrower route
only when all of the following are true:

- the provider is a separately verified custom OIDC federation for one exact
  Microsoft Entra organization;
- the associated production user flow and application are independently
  verified;
- the issuer uses the domain-based form required for acceleration;
- its new configuration contract is independently reviewed;
- the account-link, canonical tenant, and Stripe continuity gates have passed.

The Hub rejects known Microsoft authentication-service hosts. This prevents a
repeat of the failed personal-account acceleration attempt. Enabling this
narrower route would support only the verified organization and must be
labelled as an organization account; it would not satisfy a general
"Microsoft account" promise.

## Rejected shortcuts

- Do not restore `login.live.com`.
- Do not accept `login.microsoftonline.com`, `login.microsoft.com`, or
  `microsoft.com` as an organization tenant domain.
- Do not associate the production application with the isolated Pilot flow.
- Do not add a second client ID merely to bypass the one-flow-per-application
  rule; that changes token audience and API validation and still does not prove
  a provider-specific personal-account route.
- Do not ask for an email address and infer an Entra organization, canonical
  principal, business tenant, or Stripe customer from the domain.

## Closed product decision

The product owner chose not to expose the ambiguous managed-page handoff and
not to offer Microsoft SSO. Microsoft-hosted email addresses are supported by
Email OTP; Google remains the only additional federated route.
