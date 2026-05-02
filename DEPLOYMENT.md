# TECHIE Production Deployment

This repository contains several historical deployment scripts, but only the scripts below should be used for the current production handover.

## Current Scripts

### Full current app refresh

Use this after UI/runtime changes for Kotomake, Kotomigaki, Kotomegane, or Techie Hub.

```powershell
.\deploy-azure0429-refresh-kyotokyotechie.ps1 -Environment prod
```

This builds and deploys:

- `techie-hub`
- `kotomake`
- `kotomigaki`
- `kotomegane`

It also updates the custom-domain App Service containers for:

- `https://app.techie.jp`
- `https://api.techie.jp`

### Platform / usage API deployment

Use this only when the Azure infrastructure, usage API, database schema, or shared runtime configuration changes.

```powershell
.\deploy-stage3-kyotokyotechie.ps1 -Environment prod
```

If the database schema has already been applied, use:

```powershell
.\deploy-stage3-kyotokyotechie.ps1 -Environment prod -SkipDatabaseInit
```

### Kotomegane-only deployment

Normally this is called automatically by the full refresh script. Use directly only when deploying Kotomegane alone.

```powershell
.\deploy-kotomegane-kyotokyotechie.ps1 -Environment prod
```

## Legacy Scripts

Older Phase 2 / V2 deployment scripts are stored under:

```text
docs/legacy-deploy-scripts/
```

They are retained for audit/history only and should not be used for the current production deployment unless an engineer intentionally needs to reproduce an older deployment path.

## Required Secrets

Set required secrets in the shell before deployment. Do not commit real secret values to Git.

```powershell
$env:POSTGRES_ADMIN_PASSWORD='<set securely>'
$env:OPENAI_API_KEY='<set securely>'
$env:STRIPE_SECRET_KEY='<set securely>'
$env:STRIPE_PUBLISHABLE_KEY='<set securely>'
$env:STRIPE_WEBHOOK_SECRET='<set securely>'
```

Optional provider keys are required only when enabling Gemini or Claude runtime paths:

```powershell
$env:GEMINI_API_KEY='<set securely>'
$env:ANTHROPIC_API_KEY='<set securely>'
```

## Production URLs

- Hub: `https://app.techie.jp`
- API / Kotomake custom domain: `https://api.techie.jp`
- Stripe webhook: `https://api.techie.jp/webhook/stripe`
- Kotomake Container App: `https://kotomake.ashymushroom-021a53c5.japanwest.azurecontainerapps.io`
- Kotomigaki Container App: `https://kotomigaki.ashymushroom-021a53c5.japanwest.azurecontainerapps.io`
- Kotomegane Container App: `https://kotomegane.ashymushroom-021a53c5.japanwest.azurecontainerapps.io`
