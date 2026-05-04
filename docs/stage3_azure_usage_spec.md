# TECHIE Stage 3 Azure Usage / Credit 仕様

本資料は、TECHIE の Stage 3 で実装済みの usage/credit 管理仕様をまとめたものです。

## 対象範囲

現在の Azure/backend 側では以下を扱います。

- tenant に紐づく credit 残高管理
- service ごとの残 credit 取得
- idempotency key 付き credit 消費
- admin による credit 付与
- credit 不足時の制御
- コトメイク生成時の debit hook
- コトミガキ分析時の debit hook
- コトメガネ手動実行・batch・scheduled 実行向け debit logic

## Identity / Ownership model

- credit balance は `tenant_id` 単位で管理します。
- event には必要に応じて `subscription_contract_id` を metadata として持たせます。
- 操作ユーザーは `actor_user_id` として記録します。
- service ごとの残高は `service_key` で分離します。

## Service keys

- `kotomake`
- `kotomigaki`
- `kotomegane`

## Action keys

- `kotomake.generate`
- `kotomigaki.analyze`
- `kotomegane.manual`
- `kotomegane.batch`
- `kotomegane.scheduled`

## コトメガネ menu rule

固定 menu は以下です。

### OpenAI 単独観測

- 手動実行: `1` credit
- batch job 作成: `1` credit
- scheduled job 作成: `1` credit
- 想定 cadence: `72 hours`

### 3AI 横断観測

- 手動実行: `2` credits
- batch job 作成: `2` credits
- scheduled job 作成: `2` credits
- 想定 cadence: `48 hours`

現状の注意:

- menu model と credit rule は実装済みです。
- 現時点で runtime-ready な経路は OpenAI 単独観測です。
- 3AI 横断観測は code 上の model はありますが、Gemini / Claude key と client 側 final runtime/UI package の確定後に有効化してください。

## 既存 live app の標準消費単位

- コトメイク生成 click: `1`
- コトミガキ分析 click: `1`
- コトメガネ OpenAI 手動実行: `1`
- コトメガネ 3AI 手動実行: `2`

## API endpoints

Base URL:

- `https://api.techie.jp`

Endpoints:

- `GET /api/usage/summary?service_key=<service-key>`
- `POST /api/usage/consume`
- `POST /api/usage/grant`

## Request / Response

### `GET /api/usage/summary`

Query parameter:

- `service_key`

認証済み response 例:

```json
{
  "tenant_id": "uuid-or-tenant-key",
  "service_key": "kotomake",
  "included_credits": 15,
  "bonus_credits": 3,
  "used_credits": 4,
  "remaining_credits": 14,
  "updated_at": "2026-04-11T00:00:00Z"
}
```

### `POST /api/usage/consume`

Request body:

```json
{
  "service_key": "kotomake",
  "action_key": "kotomake.generate",
  "units": 1,
  "idempotency_key": "unique-click-or-job-id",
  "metadata": {
    "source": "ui"
  }
}
```

成功時は更新後の balance summary を返します。

credit 不足時:

- HTTP `402`
- `detail` に credit 不足理由を返します。

UI 側の推奨動作:

- credit 不足 message を表示します。
- `402` の場合は生成/分析を開始しません。

### `POST /api/usage/grant`

Request body:

```json
{
  "service_key": "kotomake",
  "units": 10,
  "reason": "admin.manual_grant",
  "idempotency_key": "grant-2026-04-11-001",
  "metadata": {
    "note": "campaign compensation"
  }
}
```

Authorization:

- `admin` または `platform_admin` が必要です。

## Trigger rule

### コトメイク

- Trigger: 記事生成 click
- Debit timing: 生成開始前
- credit 不足時: 処理を止め、不足 message を表示します。

### コトミガキ

- Trigger: 分析 click
- Debit timing: 分析開始前
- credit 不足時: 処理を止め、不足 message を表示します。

### コトメガネ手動実行

- Trigger: manual run click
- Debit timing: 手動実行開始前
- credit 不足時: 処理を止め、不足 message を表示します。

### コトメガネ batch

- Trigger: batch job submit / batch job 作成
- Debit timing: batch submit 時
- import、表示、report open では課金しません。
- batch job に紐づく idempotency key を使用します。
- debit 後に batch submit が失敗した場合は compensating grant / rollback を ledger に記録してください。

### コトメガネ scheduled

- Trigger: scheduler による scheduled batch job 作成
- Debit timing: 実行予定 slot の job 作成時
- 保存済みの `tenant_id` / `user_id` を使用します。
- `schedule_id + scheduled slot` に紐づく idempotency key を使用します。
- debit 後に submit が失敗した場合は compensating grant / rollback を記録してください。

## Idempotency rule

すべての debit/grant に `idempotency_key` を送ってください。

推奨 pattern:

- manual click: UI attempt ID
- analysis click: analysis attempt ID
- batch: batch job ID
- scheduled: `schedule_id + slot key`
- rollback: `<original-id>-rollback`

これにより retry、refresh、一時障害時の二重課金を防ぎます。

## Database tables

実装済み table:

- `service_usage_account`
- `usage_event_ledger`

用途:

- `service_usage_account`: tenant/service 単位の現在残高
- `usage_event_ledger`: debit / grant の immutable ledger

## 実装状態

実装済み:

- shared usage ledger backend
- usage API endpoints
- コトメイク debit hook
- コトミガキ debit hook
- コトメガネ manual / batch / scheduled debit logic

client 側で確認が必要な項目:

- final Kotomegane UI package/version
- final Kotomegane algorithm/runtime freeze
- Gemini / Claude を含む 3AI runtime の key と有効化範囲
- plan ごとの credit 付与数と menu 単価の最終確定
