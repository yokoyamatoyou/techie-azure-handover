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
3. Only after explicit approval, deploy the foundation.
4. Confirm the exact role assignment scopes. Wait for RBAC propagation.
5. Run `az deployment group what-if` for `job.bicep`. Expected addition is one
   `Microsoft.App/jobs` resource. No application, Web App, Container App,
   Entra, Google, Stripe, database row, or network ingress may change.
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
