# Azure 引き継ぎ要約

本資料は、TECHIE の Azure 本番環境を保守・復旧・追加開発する担当者向けの要約です。

詳細なデプロイ手順は `DEPLOYMENT.md`、usage/credit API の詳細は `docs/stage3_azure_usage_spec.md`、Azure 構成の技術ガイドは `docs/azure_migration_engineer_guide.md` を参照してください。

## 対象サービス

- `techie-hub`: WIX から最初に遷移する Hub 画面です。
- `notecode`: コトメイク。ブログ・記事生成を担当します。
- `aio2-main`: コトミガキ。SEO/AIO 分析と改善レポートを担当します。
- `kotomegane`: コトメガネ。AI 検索・LLM 観測を担当します。
- `shared`: 認証、Stripe、usage/credit API などの共通処理です。
- `infra`: Azure Bicep と DB 初期化 SQL です。

## 本番 URL

- Hub / WIX 初回遷移先: `https://app.techie.jp`
- API / コトメイク custom domain: `https://api.techie.jp`
- Stripe webhook: `https://api.techie.jp/webhook/stripe`
- コトメイク Container App: `https://kotomake.ashymushroom-021a53c5.japanwest.azurecontainerapps.io`
- コトミガキ Container App: `https://kotomigaki.ashymushroom-021a53c5.japanwest.azurecontainerapps.io`
- コトメガネ Container App: `https://kotomegane.ashymushroom-021a53c5.japanwest.azurecontainerapps.io`

## Azure リソースの役割

- Azure Container Registry: 各サービスの Docker image を保存します。
- Azure Container Apps: コトメイク、コトミガキ、コトメガネなどの container 実行基盤です。
- App Service: `app.techie.jp`、`api.techie.jp` の custom domain 側 container を実行します。
- PostgreSQL Flexible Server: 契約、usage ledger、credit account、Stripe/Reseller 関連の永続データを保存します。
- Storage Account / Queues: Stripe webhook、payout、coupon などの非同期処理 queue を保持します。
- Application Insights / Log Analytics: 監視、ログ、障害調査に使用します。
- Bicep: `infra/main.bicep` と `infra/modules/` に Azure resource 定義を保持しています。

## 削除してはいけないもの

- PostgreSQL server と database
- Storage Account と queue
- Container Apps environment
- Container Apps 本体
- App Service 本体
- Azure Container Registry
- Application Insights / Log Analytics
- custom domain に紐づく App Service 設定

## 環境変数と secret

本番 secret は Git には含めていません。Azure App Settings / Container Apps environment variables、または安全な別経路で管理してください。

代表的な項目:

- `POSTGRES_ADMIN_PASSWORD`: PostgreSQL 管理者 password
- `DATABASE_URL`: アプリから PostgreSQL へ接続する connection string
- `OPENAI_API_KEY`: OpenAI API 呼び出し用
- `STRIPE_SECRET_KEY`: Stripe server-side API 用
- `STRIPE_PUBLISHABLE_KEY`: Stripe client/public key
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook signature 検証用
- `GEMINI_API_KEY`: Gemini runtime を有効にする場合のみ
- `ANTHROPIC_API_KEY`: Claude runtime を有効にする場合のみ

## データとバックアップ

- 主要 DB は Azure Database for PostgreSQL Flexible Server です。
- Storage Account には Stripe webhook queue、payout queue、coupon queue 等の非同期データが入ります。
- DB 復旧は PostgreSQL Flexible Server の backup / point-in-time restore を前提にしてください。
- Storage queue の失敗イベントは dead-letter queue または処理ログを確認してください。

## 運用メモ

- Stripe webhook は browser GET ではなく Stripe Dashboard から test event を送信して確認します。
- 署名なし POST が invalid signature になることは正常です。
- usage API は認証必須です。認証なしアクセスが認証エラーになることは正常です。
- 生成/分析/バッチ実行は credit 消費 trigger です。
- コトメガネの batch は job 作成時に credit を消費する設計です。

## 今後の推奨

現状は本番直接反映の構成です。今後は staging 環境を作成し、staging で UI、認証、Stripe、credit 消費、prompt injection 対策を確認してから production に反映する構成を推奨します。
