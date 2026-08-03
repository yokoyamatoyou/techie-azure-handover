# TECHIE Kudu identity-binding hardening dry-run

- Owner: one SOL agent only
- Status: `LOCAL PREPARATION / NOT UPLOADED / DB NOT CONNECTED`
- Remote directory: `/home/LogFiles/techie-identity-hardening-audit`

This is an apply-incapable entrypoint for the separately approved live
identity-binding hardening transaction dry-run. It accepts exactly one
argument: the protected database-target confirmation SHA-256 produced by the
approved Cloud Shell target preflight.

The earlier `a92e41e` ZIP is `HOLD / SUPERSEDED BEFORE LIVE USE` because it
also included the general apply-capable runner. It was never uploaded or
executed. Do not reuse it. The corrected bundle below contains only the
dedicated no-commit engine.

The flat Kudu upload bundle contains:

- `20260804_identity_binding_hardening.sql`;
- `20260804_identity_binding_hardening_dryrun_engine.js`;
- `20260804_identity_binding_hardening_dryrun_only.js`;
- a non-secret exact-hash manifest.

The wrapper requires the exact isolated directory, Linux, a reviewed Node
major, `pg` 8.22.0, the pinned dry-run engine/SQL hashes, and the exact fixed
success output. The engine has no CLI, apply option, or commit branch.
Underlying output is captured in memory and is not emitted unless it exactly
matches the reviewed safe line.

The package does not install dependencies, display environment variables,
change application settings, deploy the app, or alter Azure/Entra/Google/
Stripe/API state. Do not upload or execute it without a new explicit approval.
Dry-run success never authorizes hardening apply.

Run local tests:

```text
node test_20260804_identity_binding_hardening_dryrun_engine.js
node test_20260804_identity_binding_hardening_dryrun_only.js
```
