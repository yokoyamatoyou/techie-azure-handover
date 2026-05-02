# TECHIE Azure Handover

This repository is the production handover package for the TECHIE Azure environment.

It contains the application source code, Azure infrastructure files, database initialization SQL, deployment scripts, and operational notes required for maintenance, recovery, and future development.

## Services Included

| Folder | Service | Purpose |
|---|---|---|
| `techie-hub` | TECHIE Hub | Main service entry page and navigation hub. |
| `notecode` | Kotomake | Blog/article generation service. |
| `aio2-main` | Kotomigaki | Website SEO/AIO analysis and improvement report service. |
| `kotomegane` | Kotomegane | AI search / LLM observation service with manual and batch execution paths. |
| `shared` | Shared backend modules | Authentication, Stripe billing, usage/credit APIs, and shared repositories. |
| `infra` | Azure infrastructure | Bicep templates and PostgreSQL initialization SQL. |
| `docs` | Handover documents | Deployment, Azure, usage, and maintenance notes. |

## Production URLs

| Item | URL |
|---|---|
| WIX first redirect / Hub | `https://app.techie.jp` |
| API / Kotomake custom domain | `https://api.techie.jp` |
| Stripe webhook | `https://api.techie.jp/webhook/stripe` |
| Kotomake Container App | `https://kotomake.ashymushroom-021a53c5.japanwest.azurecontainerapps.io` |
| Kotomigaki Container App | `https://kotomigaki.ashymushroom-021a53c5.japanwest.azurecontainerapps.io` |
| Kotomegane Container App | `https://kotomegane.ashymushroom-021a53c5.japanwest.azurecontainerapps.io` |

## Start Here

Read these files first:

1. `DEPLOYMENT.md` - current production deployment commands and required secrets.
2. `docs/azure_handoff_summary.md` - Azure handover summary and operational context.
3. `docs/stage3_azure_usage_spec.md` - usage/credit API details.
4. `docs/azure_migration_engineer_guide.md` - broader Azure migration and maintenance guide.
5. `infra/init.sql` - PostgreSQL schema initialization.
6. `infra/main.bicep` - Azure infrastructure definition.

## Current Deployment Command

For the normal production app refresh, run:

```powershell
.\deploy-azure0429-refresh-kyotokyotechie.ps1 -Environment prod
```

This builds and deploys:

- `techie-hub`
- `kotomake`
- `kotomigaki`
- `kotomegane`

For platform, database schema, shared runtime configuration, or usage API changes, run:

```powershell
.\deploy-stage3-kyotokyotechie.ps1 -Environment prod
```

If the database schema was already applied, use:

```powershell
.\deploy-stage3-kyotokyotechie.ps1 -Environment prod -SkipDatabaseInit
```

## Required Secrets

Real secrets are not committed to this repository.

Set required values through Azure App Settings / Container Apps environment variables, or provide them securely outside Git.

Common required values:

```powershell
$env:POSTGRES_ADMIN_PASSWORD='<set securely>'
$env:OPENAI_API_KEY='<set securely>'
$env:STRIPE_SECRET_KEY='<set securely>'
$env:STRIPE_PUBLISHABLE_KEY='<set securely>'
$env:STRIPE_WEBHOOK_SECRET='<set securely>'
```

Optional provider keys are required only when enabling Gemini or Claude paths in Kotomegane:

```powershell
$env:GEMINI_API_KEY='<set securely>'
$env:ANTHROPIC_API_KEY='<set securely>'
```

## What Is Not Included

The repository intentionally excludes:

- `.env` files and real secrets
- local virtual environments
- logs and generated files
- local database snapshots
- downloaded client handoff ZIPs
- heavy debug/vendor folders
- archived old source folders

Older deployment scripts are retained only for history under:

```text
docs/legacy-deploy-scripts/
```

Do not use legacy deployment scripts for current production deployment unless intentionally reproducing an older deployment path.

## Testing Notes

Stripe webhook testing must be done from the Stripe Dashboard using real test events. A browser GET request is not valid. A POST without a Stripe signature should return an invalid-signature response, which means signature validation is active.

The usage API is authentication-protected. Requests without an auth token should return an authentication error.

## Recommended Future Improvement

The current deployment is production-first. For long-term maintenance, create a staging environment and test changes there before deploying to production.
