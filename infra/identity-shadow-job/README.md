# TECHIE identity shadow job (deployment hold)

This package prepares an isolated Azure Container Apps **manual job** for the
read-only `20260804_identity_shadow_probe.js`. It is not a production API
deployment and does not enable Microsoft, create users, link customers, change
Stripe objects, or change the resolver mode of any running TECHIE application.

Current state: **LOCAL PREPARATION ONLY / NOT DEPLOYED / NOT STARTED**.

## Local validation evidence

- `foundation.bicep` and `job.bicep` both compiled successfully with the
  Microsoft-signed Bicep CLI v0.45.15. The downloaded compiler SHA-256 matched
  its published value before execution.
- Compiled ARM inspection confirmed exactly one dedicated identity, two role
  assignments, one manual Job, individual-secret Key Vault scope, ACR scope,
  no secret `value`, no ingress, one replica, zero retries, and the expected
  timeout and resolver safety settings.
- Docker build, ACR push, Azure what-if, and all live resources remain
  `NOT_CHECKED` or `NOT_STARTED` and require their own approvals.
- `Invoke-IdentityShadowFoundationPreflight.ps1` is a secret-free, read-only
  context, foundation what-if, and manual Job what-if gate. It compares the current Azure CLI
  subscription/workforce tenant to caller-supplied expected GUIDs without
  printing them. Its what-if parser permits exactly three `Create` changes:
  the dedicated identity, `AcrPull` at the exact ACR scope, and Key Vault
  Secrets User at the exact individual-secret scope. Every other change type,
  resource, duplicate, broad vault scope, or directory ambiguity fails closed.
- The `JobWhatIf` action is valid only after the reviewed foundation exists.
  It requires the dedicated identity to have exactly two direct role
  assignments across the subscription: `AcrPull` at the exact ACR and Key
  Vault Secrets User at the exact individual-secret scope. Extra, inherited,
  conditional, delegated, broad, or wrong-role assignments fail closed.
- `JobWhatIf` also requires a lowercase immutable image manifest digest, the
  `Consumption` workload profile, and an exact enabled 32-character Key Vault
  secret version. It uses `secret list-versions`, whose response contains
  identifiers and attributes but no secret values; it does not use `secret
  show`. The what-if result must contain exactly one `Microsoft.App/jobs`
  `Create` and no other change.
- Both Bicep files must match their reviewed SHA-256 before any Azure command
  is allowed. The reviewed Job template itself fixes manual trigger, no
  ingress, one replica, zero retries, five-minute timeout, resolver `shadow`,
  auto-provision `0`, and Entra binding-claim trust `0`.
- The preflight never stores a live parameter file or prints raw Azure CLI
  output, resource IDs, tenant/subscription IDs, secret URIs, or values. The
  `ContextOnly` action may safely report that the secret is absent. The
  `FoundationWhatIf` action requires the separately approved secret version to
  exist but still performs no Azure write.
- Local synthetic validation is run with
  `powershell -NoProfile -File .\Test-IdentityShadowFoundationPreflight.ps1`.
  It covers valid and invalid what-if shapes, exact role scopes, directory
  separation, PowerShell parsing, mutation-command absence, and secret-literal
  scanning without contacting Azure.
- The manual Job extension is validated with
  `powershell -NoProfile -File .\Test-IdentityShadowJobPreflight.ps1`. It adds
  19 runtime, RBAC, and Job what-if scenarios and confirms that no secret-value
  read or Azure mutation command is present.

## Safety contract

- The job uses `Manual` trigger, one replica, zero retries, and a five-minute
  timeout. Resource creation does not start an execution.
- The image is selected by an immutable ACR manifest digest. Mutable tags are
  rejected by the operator preflight.
- The Docker build has no default base image. The operator must supply a base
  image reference pinned by digest.
- `DATABASE_URL` is a version-pinned Key Vault reference. The value is never a
  Bicep parameter, deployment output, image layer, source file, or command-line
  argument.
- A dedicated user-assigned managed identity receives only `AcrPull` on the
  existing ACR and `Key Vault Secrets User` on the individual existing
  `database-url` secret, not on the entire Key Vault.
- `foundation.bicep` and `job.bicep` are deliberately separate. After the
  separately approved versioned `database-url` secret exists, deploy the
  foundation and stop until both narrowly scoped role assignments are visible.
- The job has no ingress configuration and cannot receive customer traffic.
- The probe itself opens a PostgreSQL repeatable-read, read-only transaction,
  verifies aggregate invariants, rolls back, and never emits a coordinate,
  email, token, secret, customer identifier, or Stripe identifier.

## Required explicit approvals

No command in the live sequence is currently approved merely because these
files exist. Record a separate approval and snapshot before each write gate:

1. Build and push the dedicated image to ACR.
2. Bootstrap exactly one version of `database-url` in the existing Key Vault
   without displaying or logging its value.
3. Create the dedicated managed identity and two scoped role assignments.
4. Create the manual job.
5. Start exactly one execution.
6. Delete the manual job and, after evidence capture, remove both temporary
   role assignments and the temporary identity.

Creating or starting this job does not authorize Entra, Google Cloud, Stripe,
existing-customer linkage, production settings, API deployment, or PR merge.

## Build contract

Build context is `infra`, not the repository root. Before a live build, record
the source commit, Dockerfile SHA-256, probe SHA-256, lockfile SHA-256, and the
chosen base-image digest. A representative command is shown below with only
placeholders; do not replace them until the image gate is approved.

```powershell
docker build --pull=false `
  --build-arg NODE_BASE_IMAGE_REPOSITORY='node:22-bookworm-slim' `
  --build-arg NODE_BASE_IMAGE_DIGEST='sha256:<64-lowercase-hex>' `
  --file .\identity-shadow-job\Dockerfile `
  --tag '<acr>.azurecr.io/techie-identity-shadow:<reviewed-tag>' `
  .
```

After push, obtain the registry manifest digest and pass only the
`sha256:...` digest to `job.bicep`. Never deploy by tag.

## Staged Bicep sequence

Run all commands from an authenticated Azure Cloud Shell or a controlled
operator environment. First confirm `az account show` matches the workforce
resource-owner tenant and the intended subscription. The TECHIE External ID
customer directory is not the deployment directory.

1. After separate secret-bootstrap approval, create one version of the
   `database-url` secret without printing its value. Capture only the secret
   name, enabled state, and version fingerprint/identifier in a protected
   receipt; never the value.
2. Run `az deployment group what-if` for `foundation.bicep` and save the
   redacted change list. Expected additions are one user-assigned identity and
   two role assignments scoped respectively to the existing ACR and the
   individual existing `database-url` secret.
   Prefer the reviewed `Invoke-IdentityShadowFoundationPreflight.ps1` with
   `-Action FoundationWhatIf`; supply all real IDs and names only in the
   protected operator session. Its output is aggregate-only and it stops
   unless the current CLI context is the workforce resource tenant rather than
   the TECHIE External ID tenant.
3. Only after explicit approval, deploy the foundation.
4. Confirm the exact role assignment scopes. Wait for RBAC propagation.
5. Run `az deployment group what-if` for `job.bicep`. Expected addition is one
   `Microsoft.App/jobs` resource. No application, Web App, Container App,
   Entra, Google, Stripe, database row, or network ingress may change.
   Use the same reviewed wrapper with `-Action JobWhatIf`; pass an immutable
   manifest digest and exact secret version only in the protected operator
   session. Continue only when the aggregate result reports the reviewed two
   direct role assignments, enabled secret version, immutable digest, and
   exactly one Job create.
6. Only after explicit approval, deploy `job.bicep`. Creation must leave the
   execution list empty.
7. Only after a final start approval, run exactly one
   `az containerapp job start` and inspect aggregate-only logs.

The exact parameter values belong in the protected operator session and its
redacted receipt, not in this repository or chat.

## Stop conditions

Stop before deployment or execution on any tenant/subscription ambiguity,
unexpected what-if change, mutable image reference, missing image digest,
missing or broad role assignment, missing/disabled secret version, secret
output, non-empty identity tables before the approved bootstrap phase,
customer/Stripe aggregate drift, duplicate binding, or orphan identity row.

## Rollback order

1. Stop a running execution if necessary.
2. Delete only the dedicated manual job.
3. Preserve aggregate-only logs and the redacted execution receipt.
4. Remove the temporary Key Vault secret version only under a separate
   destructive approval; otherwise disable it and retain rollback evidence.
5. Delete both dedicated role assignments explicitly, then delete the
   dedicated managed identity only after the job is gone. Independently verify
   that no orphaned or broader role assignment remains.

Do not delete the four additive identity tables. Returning production behavior
to `legacy` requires no schema deletion, and the running production API is not
changed by this package.
