#!/bin/bash
# daily-incremental.sh — 每日 T-1 增量更新，持续补漏直到当日全部完成
#
# 逻辑：
#   1. 先 resume 所有遗留 failed/partial
#   2. 分批次跑 update：A → B → C → D（跳过 saturday/reference）
#   3. 每批完成后 resume 补漏，持续循环直到无 pending
#   4. 每轮间隔 15 分钟，让限流窗口重置
#
# 用法：cron 调用
#   30 19 * * 1-5  /path/to/daily-incremental.sh >> /var/log/tushare-daily.log 2>&1

set -euo pipefail

COMPOSE_DIR="/mnt/f/AIcoding_space/VsCode/tushare_db"
LOG_PREFIX="[daily-incremental]"
MAX_DURATION=14400  # 4 小时安全超时（秒），19:30 开始最晚到 23:30
ROUND_SLEEP=900     # 每轮间隔 15 分钟，让限流窗口充分重置

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S CST') $LOG_PREFIX $*"
}

run_cmd() {
    docker compose run --rm --no-deps pipeline-mcp "$@" 2>&1
}

count_pending() {
    # 返回 failed + running 总数
    local status
    status=$(run_cmd tushare-db status 2>/dev/null || echo "")
    local failed running
    failed=$(echo "$status" | grep -oP 'failed:\s+\K\d+' || echo "0")
    running=$(echo "$status" | grep -oP 'running:\s+\K\d+' || echo "0")
    echo $((failed + running))
}

log "========== 开始每日增量更新 =========="

cd "$COMPOSE_DIR"
START_TIME=$(date +%s)
round=0

while true; do
    round=$((round + 1))

    # 安全超时检查
    ELAPSED=$(( $(date +%s) - START_TIME ))
    if [ "$ELAPSED" -ge "$MAX_DURATION" ]; then
        log "⚠️  已达到 ${MAX_DURATION}s 安全超时，停止补漏"
        log "⚠️  当日未完成的任务将在下次运行时继续"
        break
    fi

    log "--- 第 ${round} 轮 (已耗时 $((ELAPSED/60))min) ---"

    if [ "$round" -eq 1 ]; then
        # 第 1 轮：先 resume 遗留失败
        log "步骤 1/2: resume 遗留任务..."
        run_cmd tushare-db resume 2>&1 | tail -5

        # 分批次跑增量更新（A→B→C→D），跳过 saturday/reference
        log "步骤 2/2: 分批次增量更新 T-1..."
        for batch in A B C D; do
            log "  → Batch ${batch}..."
            run_cmd tushare-db update --incremental --batch="$batch" 2>&1 | tail -5

            # 批次间短暂等待
            sleep 30
        done
    else
        # 后续轮：只 resume 补漏
        log "运行 resume 补漏..."
        run_cmd tushare-db resume 2>&1 | tail -10
    fi

    # 检查剩余 pending 数
    PENDING=$(count_pending)
    log "当前 pending (failed+running): $PENDING"

    if [ "$PENDING" -eq 0 ]; then
        log "✅ 全部完成，共 ${round} 轮"
        break
    fi

    log "⚠️  仍有 $PENDING 个 pending，等待 ${ROUND_SLEEP}s 后继续..."
    sleep "$ROUND_SLEEP"
done

log "========== 每日增量更新完成 (共 ${round} 轮, 耗时 $(( $(date +%s) - START_TIME ))s) =========="

# 最终状态
log "最终同步状态："
run_cmd tushare-db status 2>/dev/null | tail -5
