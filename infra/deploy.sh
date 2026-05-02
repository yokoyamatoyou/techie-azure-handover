#!/bin/bash
# ============================================================
# TECHIE Azure SaaS — ACR ビルド & Container Apps デプロイ
#
# Usage:
#   ./deploy.sh [dev|staging|prod]
#
# 前提:
#   - az login 済み
#   - ACR, Container Apps Environment がデプロイ済み (main.bicep)
# ============================================================
set -euo pipefail

ENV="${1:-dev}"
RESOURCE_GROUP="rg-techie-${ENV}"
ACR_NAME="acrtechie${ENV}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo "  TECHIE Deploy — Environment: ${ENV}"
echo "============================================"

# ACR ログイン
echo "[1/5] Logging in to ACR..."
az acr login --name "$ACR_NAME"

ACR_SERVER="${ACR_NAME}.azurecr.io"
TAG="$(date +%Y%m%d-%H%M%S)"

# ビルド & プッシュ
echo "[2/5] Building and pushing images..."

echo "  → notecode (コトメイク)..."
az acr build \
    --registry "$ACR_NAME" \
    --image "notecode:${TAG}" \
    --image "notecode:latest" \
    --file "${PROJECT_ROOT}/notecode/Dockerfile" \
    "${PROJECT_ROOT}/notecode"

echo "  → aio2-main (コトミガキ)..."
az acr build \
    --registry "$ACR_NAME" \
    --image "aio2-main:${TAG}" \
    --image "aio2-main:latest" \
    --file "${PROJECT_ROOT}/aio2-main/Dockerfile" \
    "${PROJECT_ROOT}/aio2-main"

echo "  → doorknock (コトムスビ)..."
az acr build \
    --registry "$ACR_NAME" \
    --image "doorknock:${TAG}" \
    --image "doorknock:latest" \
    --file "${PROJECT_ROOT}/doorknock/Dockerfile" \
    "${PROJECT_ROOT}"

echo "  → techie-hub..."
az acr build \
    --registry "$ACR_NAME" \
    --image "techie-hub:${TAG}" \
    --image "techie-hub:latest" \
    --file "${PROJECT_ROOT}/techie-hub/Dockerfile" \
    "${PROJECT_ROOT}/techie-hub"

# コンテナアプリ更新
echo "[3/5] Updating Container Apps..."

for APP_NAME in "ca-kotomake-${ENV}" "ca-kotomigaki-${ENV}" "ca-kotomusubi-${ENV}" "ca-hub-${ENV}"; do
    case "$APP_NAME" in
        *kotomake*)  IMAGE="notecode:${TAG}" ;;
        *kotomigaki*) IMAGE="aio2-main:${TAG}" ;;
        *kotomusubi*) IMAGE="doorknock:${TAG}" ;;
        *hub*)       IMAGE="techie-hub:${TAG}" ;;
    esac

    echo "  → Updating ${APP_NAME} with ${IMAGE}..."
    az containerapp update \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --image "${ACR_SERVER}/${IMAGE}" \
        --output none || echo "  ⚠ Failed to update ${APP_NAME}"
done

# ヘルスチェック
echo "[4/5] Waiting for health checks..."
sleep 30

for APP_NAME in "ca-kotomake-${ENV}" "ca-kotomigaki-${ENV}" "ca-hub-${ENV}"; do
    FQDN=$(az containerapp show \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "properties.configuration.ingress.fqdn" \
        --output tsv 2>/dev/null || echo "unknown")
    
    if [ "$FQDN" != "unknown" ]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://${FQDN}/health" --max-time 10 || echo "000")
        if [ "$HTTP_CODE" = "200" ]; then
            echo "  ✓ ${APP_NAME}: https://${FQDN} — OK"
        else
            echo "  ✗ ${APP_NAME}: https://${FQDN} — HTTP ${HTTP_CODE}"
        fi
    else
        echo "  ⚠ ${APP_NAME}: FQDN not found"
    fi
done

echo "[5/5] Deploy complete!"
echo ""
echo "  Tag: ${TAG}"
echo "  Resource Group: ${RESOURCE_GROUP}"
echo ""
echo "============================================"
