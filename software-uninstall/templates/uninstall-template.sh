#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Pre-flight Check: Detect if target is present
# If target is absent, exit 0 immediately for idempotency and efficiency.
# ==============================================================================

TARGET_NAME="<TARGET_NAME>"
TARGETS_FOUND=0

# 1. Process detection (strictly bounded regex to avoid substring collisions)
RUNNING_PIDS=$(pgrep -f "(^|/)${TARGET_NAME}($|[[:space:]])" 2>/dev/null | grep -v "^$$\$" || true)
if [[ -n "${RUNNING_PIDS}" ]]; then
    TARGETS_FOUND=1
fi

# 2. Binary / PATH locations
BINARIES=(
    "$(command -v "${TARGET_NAME}" 2>/dev/null || true)"
    "/opt/homebrew/bin/${TARGET_NAME}"
    "/usr/local/bin/${TARGET_NAME}"
)
for b in "${BINARIES[@]}"; do
    if [[ -n "$b" && -e "$b" ]]; then
        TARGETS_FOUND=1
        break
    fi
done

# Check NVM versions if applicable
for d in "$HOME/.nvm/versions/node"/*; do
    if [[ -d "$d" && -e "$d/bin/${TARGET_NAME}" ]]; then
        TARGETS_FOUND=1
        break
    fi
done

# 3. Config and Data Directories
DATA_PATHS=(
    "$HOME/.${TARGET_NAME}"
    "$HOME/Library/Application Support/${TARGET_NAME}"
    "$HOME/Library/Preferences/com.${TARGET_NAME}.plist"
    "$HOME/Library/Logs/${TARGET_NAME}"
)
for p in "${DATA_PATHS[@]}"; do
    if [[ -e "$p" ]]; then
        TARGETS_FOUND=1
        break
    fi
done

if [[ $TARGETS_FOUND -eq 0 ]]; then
    echo "[PRE-FLIGHT] 目标不存在：${TARGET_NAME} 已处于未安装/清理状态，无需处理。"
    exit 0
fi

echo "[PRE-FLIGHT] 发现 ${TARGET_NAME} 残留项，开始执行卸载流程..."

# ==============================================================================
# Phase 1: 终止运行进程
# ==============================================================================
if [[ -n "${RUNNING_PIDS}" ]]; then
    echo "[STEP 1] 终止运行中的进程: ${RUNNING_PIDS}"
    kill ${RUNNING_PIDS} 2>/dev/null || true
    sleep 1
    REMAIN_PIDS=$(pgrep -f "(^|/)${TARGET_NAME}($|[[:space:]])" 2>/dev/null | grep -v "^$$\$" || true)
    if [[ -n "${REMAIN_PIDS}" ]]; then
        kill -9 ${REMAIN_PIDS} 2>/dev/null || true
    fi
fi

# ==============================================================================
# Phase 2: 配置与凭证安全备份
# ==============================================================================
if [[ -d "$HOME/.${TARGET_NAME}" ]]; then
    BACKUP_TAR="/tmp/${TARGET_NAME}_backup_$(date +%Y%m%d%H%M%S).tar.gz"
    echo "[STEP 2] 备份 ~/.${TARGET_NAME} 至 ${BACKUP_TAR} ..."
    tar -czf "${BACKUP_TAR}" -C "$HOME" ".${TARGET_NAME}" 2>/dev/null || true
fi

# ==============================================================================
# Phase 3: 清理二进制与全局包
# ==============================================================================
echo "[STEP 3] 清理可执行文件与全局模块..."
for d in "$HOME/.nvm/versions/node"/*; do
    if [[ -d "$d" ]]; then
        rm -f "$d/bin/${TARGET_NAME}"
    fi
done
rm -f "/opt/homebrew/bin/${TARGET_NAME}" "/usr/local/bin/${TARGET_NAME}"

# ==============================================================================
# Phase 4: 清理配置、数据、日志目录
# ==============================================================================
echo "[STEP 4] 清理数据与日志目录..."
for p in "${DATA_PATHS[@]}"; do
    rm -rf "$p"
done

# ==============================================================================
# Phase 5: 校验
# ==============================================================================
hash -r 2>/dev/null || true
if ! command -v "${TARGET_NAME}" >/dev/null 2>&1; then
    echo "[SUCCESS] ${TARGET_NAME} 卸载清理完成。"
else
    echo "[WARNING] 仍能在 PATH 中检测到 ${TARGET_NAME}。"
    exit 1
fi
