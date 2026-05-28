#!/bin/bash
# ============================================================
# DevPulse 鸿蒙 HAP 签名脚本
# 用途：使用 hvigor 构建 + hap-sign-tool 签名
# 依赖：DevEco Studio / hvigorw / Java 17+
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HARMONY_DIR="$PROJECT_ROOT/harmony"

echo "[DevPulse] HAP Sign & Package Script"
echo "===================================="

# 检查 DevEco Studio 环境
if [ -z "$DEVECO_SDK_HOME" ]; then
    echo "[WARNING] DEVECO_SDK_HOME not set, trying default path..."
    if [ -d "$HOME/Huawei/DevEcoStudio/sdk" ]; then
        export DEVECO_SDK_HOME="$HOME/Huawei/DevEcoStudio/sdk"
        echo "[INFO] Found DevEco SDK at $DEVECO_SDK_HOME"
    elif [ -d "C:/Users/$USER/AppData/Local/Huawei/DevEcoStudio/sdk" ]; then
        export DEVECO_SDK_HOME="C:/Users/$USER/AppData/Local/Huawei/DevEcoStudio/sdk"
    fi
fi

# Step 1: 构建 HAP
echo ""
echo "[Step 1/3] Building HAP..."
cd "$HARMONY_DIR"

if [ -f "./hvigorw" ]; then
    # macOS/Linux
    ./hvigorw assembleHap --mode module -p module=entry@default -p product=default --no-daemon
elif [ -f "./hvigorw.bat" ]; then
    # Windows (Git Bash)
    ./hvigorw.bat assembleHap --mode module -p module=entry@default -p product=default --no-daemon
else
    echo "[ERROR] hvigorw not found!"
    echo "[INFO] Please ensure DevEco Studio is installed and the project is configured."
    exit 1
fi

echo "[OK] HAP built successfully"

# Step 2: 签名 HAP
echo ""
echo "[Step 2/3] Signing HAP..."

HAP_PATH="$HARMONY_DIR/entry/build/default/outputs/default/entry-default-unsigned.hap"
SIGNED_HAP_PATH="$HARMONY_DIR/entry/build/default/outputs/default/entry-default-signed.hap"

if [ ! -f "$HAP_PATH" ]; then
    # 尝试查找默认路径
    HAP_FILE=$(find "$HARMONY_DIR/entry/build" -name "*.hap" -not -name "*signed*" | head -1)
    if [ -z "$HAP_FILE" ]; then
        echo "[ERROR] HAP file not found!"
        exit 1
    fi
    HAP_PATH="$HAP_FILE"
fi

# hap-sign-tool 路径
SIGN_TOOL="$DEVECO_SDK_HOME/hms/native/hap-sign-tool/hap-sign-tool.jar"
KEYSTORE_FILE="$HARMONY_DIR/keystore/devpulse.p12"
KEYSTORE_PASSWORD="${HAP_KEYSTORE_PASSWORD:-}"
SIGN_ALGORITHM="SHA256withECDSA"

if [ -f "$SIGN_TOOL" ] && [ -f "$KEYSTORE_FILE" ] && [ -n "$KEYSTORE_PASSWORD" ]; then
    java -jar "$SIGN_TOOL" sign-app \
        -mode localSign \
        -keyAlias "devpulse" \
        -signAlg "$SIGN_ALGORITHM" \
        -inFile "$HAP_PATH" \
        -outFile "$SIGNED_HAP_PATH" \
        -keystoreFile "$KEYSTORE_FILE" \
        -keystorePwd "$KEYSTORE_PASSWORD" \
        -keyPwd "$KEYSTORE_PASSWORD"

    echo "[OK] HAP signed: $SIGNED_HAP_PATH"
else
    echo "[WARNING] Signing tool or keystore not available, keeping unsigned HAP"
    echo "[INFO]  HAP location: $HAP_PATH"
    echo "[INFO]  Sign manually in DevEco Studio: Build > Generate Key and CSR"
fi

# Step 3: 验证
echo ""
echo "[Step 3/3] Verification..."
if [ -f "$SIGNED_HAP_PATH" ]; then
    HAP_SIZE=$(du -h "$SIGNED_HAP_PATH" | cut -f1)
    echo "[INFO] Signed HAP size: $HAP_SIZE"
    echo "[OK] Ready for AppGallery upload"
else
    echo "[INFO] Unsigned HAP ready for DevEco Studio signing"
fi

echo ""
echo "[DevPulse] HAP packaging complete"
echo "===================================="
