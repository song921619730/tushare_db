# Tushare DB Runbook

> 日常运维参考手册 — 如何启动、重启、排障、换 token、查日志。

## 快速启动

```powershell
# 1. 启动所有服务
docker compose up -d

# 2. 初始化（首次）
docker compose exec pipeline tushare-db init

# 3. Bootstrap（首次，需要 Tushare token）
docker compose exec pipeline tushare-db bootstrap

# 4. 启动调度器
docker compose exec pipeline tushare-db scheduler-run
```

## 服务状态检查

```powershell
# 查看所有容器状态
docker compose ps

# 查看 ClickHouse 健康
docker compose exec clickhouse clickhouse-client -q "SELECT status, count() FROM _meta.sync_state FINAL GROUP BY status"

# 查看最近运行记录
docker compose exec clickhouse clickhouse-client -q "SELECT interface, status, started_at FROM _meta.sync_runs ORDER BY started_at DESC LIMIT 5"

# 查看磁盘使用
docker compose exec clickhouse clickhouse-client -q "SELECT formatReadableSize(sum(bytes_on_disk)) FROM system.parts WHERE active AND database = 'tushare'"
```

## 重启服务

```powershell
# 重启 pipeline（含 scheduler + MCP server）
docker compose restart pipeline

# 重启 ClickHouse（不丢失数据，named volume 持久化）
docker compose restart clickhouse

# 完全重建（会丢失数据！）
docker compose down -v
docker compose up -d
docker compose exec pipeline tushare-db init
docker compose exec pipeline tushare-db bootstrap
```

## 更换 Tushare Token

1. 编辑 `.env` 文件，更新 `TUSHARE_TOKEN` 值
2. 重启 pipeline：`docker compose restart pipeline`
3. 调度器会自动使用新 token

```powershell
# 验证 token 是否生效
docker compose exec pipeline tushare-db probe --interface daily
```

## 查看日志

```powershell
# Pipeline 日志（结构化，含 run_id / interface / scope_key）
docker compose logs -f pipeline --tail=100

# ClickHouse 日志
docker compose logs -f clickhouse --tail=100

# 实时日志（容器内）
docker compose exec pipeline cat data/logs/app.log | tail -50
```

## 常用 CLI 命令

```powershell
# 全量回补
docker compose exec pipeline tushare-db backfill --all

# 按层回补（0=参考表, 1=日线核心, 2=日线次要, 3=财务, 4=P2, 5=其余）
docker compose exec pipeline tushare-db backfill --layer 0
docker compose exec pipeline tushare-db backfill --layer 1

# 按优先级回补
docker compose exec pipeline tushare-db backfill --priority P0

# 单接口回补
docker compose exec pipeline tushare-db backfill --interface daily --from 20240101 --to 20240331

# 查看状态
docker compose exec pipeline tushare-db status --interface daily
docker compose exec pipeline tushare-db status --interface daily --detail

# 续跑（崩溃后）
docker compose exec pipeline tushare-db resume --interface daily

# T-1 增量更新
docker compose exec pipeline tushare-db update --batch A --incremental

# 验证
docker compose exec pipeline tushare-db verify --gaps --checksums

# MCP server
docker compose exec pipeline tushare-db mcp-serve --transport stdio
docker compose exec pipeline tushare-db mcp-serve --transport sse --host 0.0.0.0 --port 7800
```

## 常见问题排查

### Tushare 一直返回 429

```sql
-- 检查 API 调用频率
SELECT toStartOfMinute(started_at) AS m, count() AS rpm
FROM _meta.api_calls
WHERE started_at > now() - INTERVAL 1 HOUR
GROUP BY m ORDER BY m DESC LIMIT 20;
```

- 正常值：≤475/min（normal bucket）或 ≤285/min（special bucket）
- 如果超限：检查 worker 数量是否过多（默认 8 normal + 4 special）
- 临时解决：等 1 分钟让 bucket 自然恢复

### ClickHouse OOM 崩溃

```sql
-- 检查 part 数量（>10000 说明 async_insert 可能没开）
SELECT count() FROM system.parts WHERE active AND database = 'tushare';
```

- 确认 `async_insert=1` 在 users.xml 的 pipeline 用户 profile 中
- 减少单次写入 batch size

### Scheduler 任务丢失

- MemoryJobStore 在进程重启时会丢失 job — 这是预期行为
- Job 在代码中定义，重启 `scheduler-run` 会自动重建
- 运行中的 backfill 不会丢失，因为进度在 `_meta.sync_state` 中

### Backfill 太慢

```powershell
# 检查当前运行中的单元
docker compose exec clickhouse clickhouse-client -q "SELECT interface, scope_key, heartbeat_at FROM _meta.sync_state FINAL WHERE status='running'"

# 检查 rate limiter 利用率（应接近 95%）
# 如果利用率低：可能是 HTTP/2 没开或 Tushare 侧限流
```

### 表不存在错误

```powershell
# 查看已创建的表
docker compose exec clickhouse clickhouse-client -q "SELECT name FROM system.tables WHERE database='tushare' ORDER BY name"

# 如果缺少表，重新 bootstrap
docker compose exec pipeline tushare-db bootstrap
```

### WSL2 内存占用过高

在 `%USERPROFILE%\.wslconfig` 中添加：

```ini
[wsl2]
memory=12GB
swap=4GB
```

然后 `wsl --shutdown` 重启。

## 访问端点

| 服务 | 地址 | 说明 |
|------|------|------|
| ClickHouse HTTP | `http://localhost:8123` | HTTP 接口 |
| MCP SSE | `http://localhost:7800` | MCP server SSE 传输 |
| Grafana | `http://localhost:3000` | 监控仪表盘 |
| Dashboard | `http://localhost:8080` | 前端 SPA（需手动启动） |

## 数据备份

```powershell
# 导出 _meta 表数据（用于迁移/恢复）
docker compose exec clickhouse clickhouse-client -q "SELECT * FROM _meta.sync_state FINAL FORMAT CSVWithNames" > sync_state_backup.csv
docker compose exec clickhouse clickhouse-client -q "SELECT * FROM _meta.sync_runs FORMAT CSVWithNames" > sync_runs_backup.csv

# 备份整个 ClickHouse 数据目录
docker compose exec clickhouse clickhouse-client -q "BACKUP DATABASE tushare TO Disk('backups', 'tushare_backup_$(date +%Y%m%d).zip')"
```

## 性能基准

| 操作 | 期望耗时 | 告警阈值 |
|------|----------|----------|
| 6 个月 daily 回补 | ≤24 min | >36 min |
| Batch A 单日增量 | ≤30 sec | >60 sec |
| `SELECT count() FROM tushare.daily` | <100 ms | >500 ms |
| MCP get_ohlcv 单股 1 年 | <500 ms | >2s |

## 数据保留

| 制品 | 保留期 | 清理方式 |
|------|--------|----------|
| `_meta.api_calls` | 90 天 | TTL 自动清理 |
| `_meta.sync_runs` | 365 天 | TTL 自动清理 |
| `_meta.sync_state` | 永久 | 手动清理（通常不需要） |
| `data/logs/app.log` | 50MB × 20 = 1GB | RotatingFileHandler 自动轮转 |
| `data/samples/*.json` | 永久 | 体积很小 |
