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

Exact subscription, workforce directory, External ID directory, resource
names, database name/port, and setting name remain protected-session inputs;
their values are not stored in Git. Before Azure CLI is called, the wrapper
canonicalizes that complete tuple and requires its SHA-256 to equal a digest
computed from a separately reviewed protected target description. It also
requires the exact operation phrase
`READ_ONLY_TECHIE_IDENTITY_HARDENING_TARGET_PREFLIGHT_20260804`. Do not compute
the confirmation from casually retyped values in the same command line.

Run tests locally:

```text
powershell -NoProfile -ExecutionPolicy Bypass -File .\Test-IdentityBindingHardeningTargetPreflight.ps1
```

Do not run the live wrapper without separate explicit approval. Its parameters
must be supplied only in the protected Cloud Shell session and must never be
copied into chat, Git, screenshots, or public receipts. If Cloud Shell requests
storage creation, stop without creating it.

Current local tests: `13 scenarios passed`; three PowerShell files parsed,
mutation/DB-connection commands `0`, sensitive output paths `0`.
