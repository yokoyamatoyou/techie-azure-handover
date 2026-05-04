# TECHIE 本番デプロイ手順

本リポジトリには過去のデプロイスクリプトも一部残していますが、現在の本番引き継ぎで使用するスクリプトは以下のみです。

## 現行スクリプト

### 現在のアプリ一式を更新する場合

コトメイク、コトミガキ、コトメガネ、TECHIE Hub の UI や runtime を更新した後は、以下を実行します。

```powershell
.\deploy-azure0429-refresh-kyotokyotechie.ps1 -Environment prod
```

このスクリプトは以下をビルド・デプロイします。

- `techie-hub`
- `kotomake`
- `kotomigaki`
- `kotomegane`

また、以下の custom domain 側 App Service container も更新します。

- `https://app.techie.jp`
- `https://api.techie.jp`

### Azure 基盤 / usage API を更新する場合

Azure インフラ、usage API、DB スキーマ、共通 runtime 設定を変更する場合のみ使用します。

```powershell
.\deploy-stage3-kyotokyotechie.ps1 -Environment prod
```

DB スキーマをすでに適用済みの場合は以下を使用します。

```powershell
.\deploy-stage3-kyotokyotechie.ps1 -Environment prod -SkipDatabaseInit
```

### コトメガネのみデプロイする場合

通常は上記の full refresh script から自動的に呼び出されます。コトメガネだけを個別更新する場合のみ直接使用します。

```powershell
.\deploy-kotomegane-kyotokyotechie.ps1 -Environment prod
```

## Legacy scripts

Phase 2 / V2 時点の古いスクリプトは以下に保管しています。

```text
docs/legacy-deploy-scripts/
```

これらは監査・履歴確認用です。現在の本番デプロイでは使用しないでください。

## 必要な secret

デプロイ前に shell の環境変数として設定してください。実際の secret 値は Git に commit しないでください。

```powershell
$env:POSTGRES_ADMIN_PASSWORD='<set securely>'
$env:OPENAI_API_KEY='<set securely>'
$env:STRIPE_SECRET_KEY='<set securely>'
$env:STRIPE_PUBLISHABLE_KEY='<set securely>'
$env:STRIPE_WEBHOOK_SECRET='<set securely>'
```

Gemini / Claude の runtime path を有効化する場合のみ、以下も必要です。

```powershell
$env:GEMINI_API_KEY='<set securely>'
$env:ANTHROPIC_API_KEY='<set securely>'
```

## 本番 URL

- Hub: `https://app.techie.jp`
- API / コトメイク custom domain: `https://api.techie.jp`
- Stripe webhook: `https://api.techie.jp/webhook/stripe`
- コトメイク Container App: `https://kotomake.ashymushroom-021a53c5.japanwest.azurecontainerapps.io`
- コトミガキ Container App: `https://kotomigaki.ashymushroom-021a53c5.japanwest.azurecontainerapps.io`
- コトメガネ Container App: `https://kotomegane.ashymushroom-021a53c5.japanwest.azurecontainerapps.io`
