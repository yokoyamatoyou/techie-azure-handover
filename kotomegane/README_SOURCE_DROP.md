# コトメガネ本体ソース束 2026-05-25

## 目的

外部エンジニアから「本体ソース差し替え対象が含まれていない」と指摘があったため、ローカル `C:\tetie\kotomegane` から軽量な本体ソース束を抽出したものです。

## 含めたもの

- コトメガネ本体 Python ソース
- `ui`
- `analysis_core`
- `llmo_core`
- `runtime`
- `config`
- `assets`
- `tests`
- `requirements.txt`
- 起動 / 停止 / setup 用 PowerShell
- `.env.example`

## 含めていないもの

- `.env`
- `.venv`
- `data`
- `logs`
- `exports`
- `__pycache__`
- `*.pyc`

## 注意

このソース束は、現在のローカル作業元から抽出したものです。

Azure 本番で動いている image `techiereg2026.azurecr.io/kotomegane:20260508-140225` を作ったソースと同一かは未確認です。

外部エンジニア側で、既存 Azure image の元ソース / Dockerfile / build pipeline と突き合わせてください。

## 重要な差分

このローカルソースは、確認時点では SQLite 前提です。

- `storage.py` は `sqlite3` を使用
- `config.py` はローカル DB path を使用
- `DATABASE_URL` 利用は未確認
- `tenant_id` 保存 / 絞り込みは未確認
- Entra 認証 env の利用は未確認
- `SERVICE_LEDGER_MODE` の利用は未確認

そのため、Azure 本番の tenant 別保存・Stripe / Azure クレジット連携が既にある場合、このソースをそのまま差し替えるのではなく、既存 Azure 用ソースへ差分移植する方針を推奨します。

