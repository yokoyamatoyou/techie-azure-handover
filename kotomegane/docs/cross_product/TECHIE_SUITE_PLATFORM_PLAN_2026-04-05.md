# TECHIE Suite Platform Plan 2026-04-05

## Purpose

この文書は、`コトメイク`、`コトミガキ`、`コトメガネ` を `TECHIE` の同一 SaaS 群として扱う前提で、今後の Azure 移行と共通基盤の再利用方針を整理するための運用文書です。

`C:\tetie\kotomegane\Saa S基盤設計.docx` は準備済みの元資料として扱い、この markdown を日常運用の参照先にします。

## Current Position

- `コトメガネ` は現在 `LLMO Prompt Loop PoC` としてローカル運用中
- UI / デザインは `コトメイク` / `コトミガキ` と同一 SaaS 群へ寄せる方針
- Azure 側の標準構成はすでに別 SaaS で成立しており、今後の量産に流用する前提がある
- 料金プランは現時点では未確定

## Suite Definition

3製品は、別アプリではなく `TECHIE` の同一プロダクト群として扱う。

- `コトメイク`
  - 制作 / 生成寄りの主サービス
- `コトミガキ`
  - 改善 / 編集寄りの主サービス
- `コトメガネ`
  - AI 可視性 / 回答露出分析サービス

共通化したいもの:

- ブランドシェル
- デザイン文法
- 認証方針
- Azure 上の基本構成
- DNS パターン
- 決済連携パターン

分離したいもの:

- SaaS ごとの Stripe キー
- SaaS ごとの Entra アプリ登録
- SaaS ごとのフロント / API 実体
- SaaS ごとの価格設計

## Azure Reuse Policy

`Saa S基盤設計.docx` から引き継ぐ current decision は次です。

### Reusable

- App Service を使う `フロント + API` の 2 層構成
- App Service Plan の共通利用方針
- `app.xxx.jp` / `api.xxx.jp` の DNS パターン
- Stripe Webhook の設計パターン
- Entra External ID を使う認証フローの骨格

### Must Be Isolated Per SaaS

- Stripe API key
- Stripe Webhook の接続先実体
- Entra のアプリ登録
- SaaS ごとの App Service
- SaaS ごとの設定値と環境変数

## Standard SaaS Template

今後の標準テンプレは次を基本にする。

1. LP
   - `xxx.jp`
2. Frontend
   - `app.xxx.jp`
3. API
   - `api.xxx.jp`
4. Auth
   - Entra の別アプリ登録
5. Billing
   - Stripe を SaaS ごとに分離

## Documentation Rule

- `Saa S基盤設計.docx` は参考元として残す
- 運用上の更新は markdown 側を先に直す
- Azure 移行や 3 製品共通化の current decision はこの文書に集約する
- 料金プランが未確定の間は、価格表や plan 名を source of truth にしない

## Pricing Status

現時点の扱い:

- 料金プランは検討中
- `billing_rules.py` や `plan_catalog.py` の current value は PoC / 実装都合の内部ルールとして扱う
- 対外説明用の正式料金としては扱わない

料金プラン確定後に別文書へ切り出す対象:

- プラン名
- 各製品の提供範囲
- クレジット / 実行回数 / batch 条件
- 契約単位

## Immediate Next Documentation Targets

1. `コトメイク` / `コトミガキ` / `コトメガネ` の共通ナビと共通認証前提を別紙で整理する
2. Azure 移行時の `dev / staging / prod` 分離方針を追記する
3. 料金プラン確定後に `TECHIE_SUITE_PRICING_PLAN_*.md` を新設する
