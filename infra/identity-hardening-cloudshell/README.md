# TECHIE identity-binding Cloud Shell target preflight

- Owner: one SOL agent only
- Status: `LOCAL PASS / AZURE NOT CALLED / DB NOT CONNECTED`

This package confirms that the protected App Service `DATABASE_URL` points to
the exact reviewed Azure PostgreSQL resource before a separately approved
hardening dry-run. It also proves that Azure resource reads occur in the
workforce/resource directory, not the TECHIE customer External ID directory.

Files:

- `IdentityBindingHardeningTargetPreflight.psm1`: validation and hashing core;
- `Invoke-IdentityBindingHardeningTargetPreflight.ps1`: guarded Azure CLI
  reader and safe output;
- `Test-IdentityBindingHardeningTargetPreflight.ps1`: synthetic failure and
  source-contract tests.

The wrapper allows only `account show`, `webapp show`, App Service app-setting
list, and PostgreSQL Flexible Server show. It does not create Cloud Shell
storage, set account context, upload a file to Kudu, connect to PostgreSQL, run
SQL, or change Azure/Entra/Google/Stripe/API/deployment state.

Run tests locally:

```text
powershell -NoProfile -ExecutionPolicy Bypass -File .\Test-IdentityBindingHardeningTargetPreflight.ps1
```

Do not run the live wrapper without separate explicit approval. Its parameters
must be supplied only in the protected Cloud Shell session and must never be
copied into chat, Git, screenshots, or public receipts. If Cloud Shell requests
storage creation, stop without creating it.
