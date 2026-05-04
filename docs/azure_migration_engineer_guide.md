# Azure 移行・保守エンジニア向けガイド

本資料は、TECHIE Azure 環境を保守・復旧・追加開発するエンジニア向けの技術ガイドです。

## 1. 目的

この package は、TECHIE の本番 Azure 環境に関する以下を引き継ぐためのものです。

- アプリケーション source code
- Docker / Container Apps / App Service の deploy script
- Azure Bicep infrastructure
- PostgreSQL schema
- Stripe / usage / reseller 関連の共通 backend
- 運用・障害対応のための補足資料

## 2. サービス構成

| サービス | フォルダ | 役割 | 主な port |
|---|---|---|---|
| TECHIE Hub | `techie-hub` | WIX からの最初の遷移先。各 service への入口です。 | `8090` |
| コトメイク | `notecode` | ブログ・記事生成。OpenAI / image generation を使用します。 | `8080` |
| コトミガキ | `aio2-main` | SEO/AIO 分析、改善レポート、PDF 出力を行います。 | `8081` |
| コトメガネ | `kotomegane` | LLM 観測、手動実行、batch/scheduled 実行を行います。 | `8083` |
| 共通処理 | `shared` | auth、Stripe、usage/credit、repository を含みます。 | service 内で import |
| Azure infra | `infra` | Bicep、PostgreSQL init SQL を含みます。 | - |

## 3. 本番 URL

- WIX first redirect / Hub: `https://app.techie.jp`
- API / コトメイク custom domain: `https://api.techie.jp`
- Stripe webhook: `https://api.techie.jp/webhook/stripe`
- コトメイク Container App: `https://kotomake.ashymushroom-021a53c5.japanwest.azurecontainerapps.io`
- コトミガキ Container App: `https://kotomigaki.ashymushroom-021a53c5.japanwest.azurecontainerapps.io`
- コトメガネ Container App: `https://kotomegane.ashymushroom-021a53c5.japanwest.azurecontainerapps.io`

## 4. Azure resource 概要

| Resource | 用途 |
|---|---|
| Resource Group `TECHIE` | 本番 resource group です。 |
| Azure Container Registry | 各アプリの Docker image を保存します。 |
| Container Apps Environment | `kotomake`, `kotomigaki`, `kotomegane` 等を実行します。 |
| Azure App Service | custom domain `app.techie.jp`, `api.techie.jp` 側の container を実行します。 |
| PostgreSQL Flexible Server | tenant、contract、usage ledger、Stripe/Reseller 関連データを保存します。 |
| Storage Account / Queues | webhook、payout、coupon などの非同期処理 queue を保持します。 |
| Application Insights / Log Analytics | runtime log、監視、障害調査に使用します。 |
| Bicep files | `infra/main.bicep` と `infra/modules/` が resource 定義です。 |

## 5. デプロイ手順

通常のアプリ refresh は以下です。

```powershell
.\deploy-azure0429-refresh-kyotokyotechie.ps1 -Environment prod
```

この script は以下を実行します。

1. ACR credential を取得
2. `kotomake` image を build
3. `kotomigaki` image を build
4. `techie-hub` image を build
5. Container Apps / App Service の image を更新
6. コトメガネ deploy script を呼び出し
7. production URL と revision を表示

Azure 基盤、DB schema、usage API、shared config を変更する場合は以下です。

```powershell
.\deploy-stage3-kyotokyotechie.ps1 -Environment prod
```

DB schema 適用済みの場合:

```powershell
.\deploy-stage3-kyotokyotechie.ps1 -Environment prod -SkipDatabaseInit
```

コトメガネのみ更新する場合:

```powershell
.\deploy-kotomegane-kyotokyotechie.ps1 -Environment prod
```

## 6. 必要な runtime / framework

- Python: 3.11 系 container を主に使用
- NiceGUI: 各 UI service で使用
- Docker: ACR build / Container Apps deploy で使用
- Azure CLI: deploy script 実行に必要
- Bicep: Azure infrastructure deploy に必要
- PostgreSQL: Azure Database for PostgreSQL Flexible Server

各 service の Python dependency は以下を確認してください。

- `notecode/requirements.txt`
- `aio2-main/requirements.txt`
- `kotomegane/requirements.txt`
- `doorknock/requirements.txt`

## 7. 環境変数

本番 secret は Git に含めません。Azure App Settings / Container Apps environment variables で管理します。

主な項目:

- `DATABASE_URL`: PostgreSQL connection string
- `POSTGRES_ADMIN_PASSWORD`: DB admin password
- `OPENAI_API_KEY`: OpenAI API key
- `STRIPE_SECRET_KEY`: Stripe secret key
- `STRIPE_PUBLISHABLE_KEY`: Stripe publishable key
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook signature secret
- `STRIPE_WEBHOOK_URL`: `https://api.techie.jp/webhook/stripe`
- `HUB_BASE_URL`: `https://app.techie.jp`
- `SERVICE_BASE_URL` / `API_BASE_URL`: `https://api.techie.jp`
- `ENTRA_EXTERNAL_ID_*`: Entra External ID 連携用
- `GEMINI_API_KEY`: Gemini を使用する場合のみ
- `ANTHROPIC_API_KEY`: Claude を使用する場合のみ

## 8. Database

DB 初期化 SQL:

```text
infra/init.sql
```

主な table:

- `service_usage_account`
- `usage_event_ledger`
- `subscription_contract`
- `customer_account`
- `reseller_master`
- `customer_reseller_assignment`
- `billing_event_ledger`
- `webhook_event_log`
- `reseller_payout_ledger`
- `coupon_request`

DB 復旧は Azure PostgreSQL Flexible Server の backup / point-in-time restore を前提とします。

## 9. Stripe / billing

Stripe webhook endpoint:

```text
https://api.techie.jp/webhook/stripe
```

注意:

- browser GET は正しい webhook test ではありません。
- Stripe Dashboard から test event を送信して確認します。
- 署名なし POST が invalid signature になる場合、signature validation は有効です。
- webhook event は idempotent に処理する必要があります。

## 10. Usage / credit

usage API:

- `GET /api/usage/summary?service_key=<service-key>`
- `POST /api/usage/consume`
- `POST /api/usage/grant`

service key:

- `kotomake`
- `kotomigaki`
- `kotomegane`

credit 消費 trigger:

- コトメイク: 生成 click
- コトミガキ: 分析 click
- コトメガネ: manual run / batch job submit / scheduled job 作成

詳細は `docs/stage3_azure_usage_spec.md` を参照してください。

## 11. ログ確認

Azure 側:

- Container Apps logs
- App Service logs
- Application Insights
- Log Analytics
- Storage Queue / dead-letter queue

アプリ側:

- `logs/`
- service runtime stdout/stderr
- usage ledger / webhook ledger

## 12. 障害対応の基本順序

1. 対象 URL が疎通するか確認します。
2. Container App / App Service の latest revision と running status を確認します。
3. Application Insights / Container Apps logs で exception を確認します。
4. `DATABASE_URL`、OpenAI、Stripe 等の environment variable が設定されているか確認します。
5. DB schema が最新か `infra/init.sql` と照合します。
6. Stripe webhook の場合は Stripe Dashboard 側の delivery log と signature error を確認します。
7. credit 関連の場合は `service_usage_account` と `usage_event_ledger` を確認します。

## 13. 削除禁止 resource

以下は本番稼働に必要なため、削除しないでください。

- PostgreSQL Flexible Server
- Storage Account / Queues
- Azure Container Registry
- Container Apps Environment
- `kotomake`, `kotomigaki`, `kotomegane`, `techie-hub`
- App Service custom domain 側 resource
- Application Insights / Log Analytics

## 14. 今後の推奨構成

現状は本番直接反映の構成です。今後は以下を推奨します。

- staging resource group を作成
- staging DB / staging app / staging Stripe webhook を分離
- GitHub Actions または Azure DevOps で CI/CD 化
- staging で UI、Stripe、認証、credit 消費、prompt injection test を実施
- production へ promote する運用に変更
