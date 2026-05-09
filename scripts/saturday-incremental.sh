#!/bin/bash
# saturday-incremental.sh — 每周六跑 saturday batch（基金分红、股东、质押等低频数据）
#
# 这些接口数据量大（如 fund_div 有 60000+ 单元），只在周六跑一次
#
# 用法：cron 调用
#   02 00 * * 6  /path/to/saturday-incremental.sh >> /var/log/tushare-saturday.log 2>&1

set -euo pipefail

COMPOSE_DIR="/mnt/f/AIcoding_space/VsCode/tushare_db"
LOG_PREFIX="[saturday-incremental]"
MAX_DURATION=28800  # 8 小时安全超时
ROUND_SLEEP=900     # 每轮间隔 15 分钟

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S CST') $LOG_PREFIX $*"
}

run_cmd() {
    docker compose run --rm --no-deps pipeline-mcp "$@" 2>&1
}

count_pending() {
    local status
    status=$(run_cmd tushare-db status 2>/dev/null || echo "")
    local failed running
    failed=$(echo "$status" | grep -oP 'failed:\s+\K\d+' || echo "0")
    running=$(echo "$status" | grep -oP 'running:\s+\K\d+' || echo "0")
    echo $((failed + running))
}

log "========== 开始周六增量更新 =========="

cd "$COMPOSE_DIR"
START_TIME=$(date +%s)
round=0

while true; do
    round=$((round + 1))

    ELAPSED=$(( $(date +%s) - START_TIME ))
    if [ "$ELAPSED" -ge "$MAX_DURATION" ]; then
        log "⚠️  已达到 ${MAX_DURATION}s 安全超时，停止"
        break
    fi

    log "--- 第 ${round} 轮 (已耗时 $((ELAPSED/60))min) ---"

    if [ "$round" -eq 1 ]; then
        # 第 1 轮：先 resume 遗留，再跑 saturday batch
        log "步骤 1/2: resume 遗留任务..."
        run_cmd tushare-db resume 2>&1 | tail -5

        log "步骤 2/2: 跑 saturday batch..."
        run_cmd tushare-db update --incremental --batch=saturday 2>&1 | tail -10
    else
        # 后续轮：只 resume 补漏
        log "运行 resume 补漏..."
        run_cmd tushare-db resume 2>&1 | tail -10
    fi

    PENDING=$(count_pending)
    log "当前 pending (failed+running): $PENDING"

    if [ "$PENDING" -eq 0 ]; then
        log "✅ 全部完成，共 ${round} 轮"
        break
    fi

    log "⚠️  仍有 $PENDING 个 pending，等待 ${ROUND_SLEEP}s 后继续..."
    sleep "$ROUND_SLEEP"
done

log "========== 周六增量更新完成 (共 ${round} 轮, 耗时 $(( $(date +%s) - START_TIME ))s) =========="

log "最终同步状态："
run_cmd tushare-db status 2>/dev/null | tail -5
