#!/bin/bash
# ============================================================
# DevPulse AppGallery Connect 上传脚本
# 用途：使用 AGC CLI 或 REST API 上传签名后的 HAP
# 依赖：agc-cloud-cli (npm) 或 curl + AppGallery Connect API
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HARMONY_DIR="$PROJECT_ROOT/harmony"

# AppGallery Connect 配置
AGC_APP_ID="${AGC_APP_ID:-}"
AGC_CLIENT_ID="${AGC_CLIENT_ID:-}"
AGC_CLIENT_SECRET="${AGC_CLIENT_SECRET:-}"

echo "[DevPulse] AppGallery Upload Script"
echo "===================================="

# 查找签名后的 HAP
SIGNED_HAP=$(find "$HARMONY_DIR/entry/build" -name "*signed*.hap" 2>/dev/null | head -1)
if [ -z "$SIGNED_HAP" ]; then
    SIGNED_HAP=$(find "$HARMONY_DIR/entry/build" -name "*.hap" 2>/dev/null | head -1)
fi

if [ -z "$SIGNED_HAP" ]; then
    echo "[ERROR] No HAP file found! Run sign_hap.sh first."
    exit 1
fi

echo "[INFO] HAP file: $SIGNED_HAP"
echo "[INFO] HAP size: $(du -h "$SIGNED_HAP" | cut -f1)"

# 方式 1: 使用 agc-cloud-cli（推荐）
if command -v agc &> /dev/null; then
    echo ""
    echo "[INFO] Using agc-cloud-cli for upload..."

    agc app publish \
        --app-id "$AGC_APP_ID" \
        --file "$SIGNED_HAP" \
        --release-type "release" \
        --description "DevPulse 0.3.0"

    echo "[OK] HAP uploaded via AGC CLI"
    exit 0
fi

# 方式 2: 使用 curl + AppGallery Connect REST API
if [ -n "$AGC_CLIENT_ID" ] && [ -n "$AGC_CLIENT_SECRET" ]; then
    echo ""
    echo "[INFO] Using AppGallery Connect REST API..."

    # Step 1: 获取 Access Token
    echo "[Step 1/2] Getting access token..."
    TOKEN_RESP=$(curl -s -X POST "https://connect-api.cloud.huawei.com/api/oauth2/v1/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=client_credentials" \
        -d "client_id=$AGC_CLIENT_ID" \
        -d "client_secret=$AGC_CLIENT_SECRET")

    ACCESS_TOKEN=$(echo "$TOKEN_RESP" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

    if [ -z "$ACCESS_TOKEN" ]; then
        echo "[ERROR] Failed to get access token"
        echo "[RESPONSE] $TOKEN_RESP"
        exit 1
    fi

    # Step 2: 上传 HAP
    echo "[Step 2/2] Uploading HAP..."
    UPLOAD_URL="https://connect-api.cloud.huawei.com/api/publish/v2/app-file-info"

    # 先获取上传 URL
    UPLOAD_INFO=$(curl -s -X GET "$UPLOAD_URL?appId=$AGC_APP_ID&releaseType=1" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "client_id: $AGC_CLIENT_ID")

    echo "[OK] Upload initiated"
    echo "[INFO] Check AppGallery Connect console for upload status:"
    echo "       https://connect.console.cloud.huawei.com"
    exit 0
fi

# 无法上传
echo ""
echo "[WARNING] No upload method available."
echo "[INFO]  Install agc-cloud-cli: npm install -g @agc/cloud-cli"
echo "[INFO]  Or set AGC_CLIENT_ID + AGC_CLIENT_SECRET environment variables"
echo "[INFO]  Manual upload: https://connect.console.cloud.huawei.com"
echo ""
echo "[INFO]  HAP file location: $SIGNED_HAP"

exit 0
