# TECHIE Kudu identity-binding hardening dry-run

- Owner: one SOL agent only
- Status: `LOCAL PREPARATION / NOT UPLOADED / DB NOT CONNECTED`
- Remote directory: `/home/LogFiles/techie-identity-hardening-audit`

This is an apply-incapable entrypoint for the separately approved live
identity-binding hardening transaction dry-run. It accepts exactly one
argument: the protected database-target confirmation SHA-256 produced by the
approved Cloud Shell target preflight.

The flat Kudu upload bundle contains:

- `20260804_identity_binding_hardening.sql`;
- `20260804_identity_binding_hardening_runner.js`;
- `20260804_identity_binding_hardening_dryrun_only.js`;
- a non-secret exact-hash manifest.

The wrapper requires the exact isolated directory, Linux, a reviewed Node
major, `pg` 8.22.0, the pinned runner/SQL hashes, and the exact fixed success
output. It constructs the underlying runner arguments itself and never
forwards `--apply` or any other caller option. Underlying output is captured in
memory and is not emitted unless it exactly matches the reviewed safe line.

The package does not install dependencies, display environment variables,
change application settings, deploy the app, or alter Azure/Entra/Google/
Stripe/API state. Do not upload or execute it without a new explicit approval.
Dry-run success never authorizes hardening apply.

Run local tests:

```text
node test_20260804_identity_binding_hardening_dryrun_only.js
```
