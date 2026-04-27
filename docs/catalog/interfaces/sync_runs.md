# sync_runs

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | _meta |
| 行数 | 0 |

## 字段列表 (11 个字段)

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `normalize_version` | UInt16 |  |

### 股本/市值 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `units_total` | UInt32 |  |

### 数值 (9个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `run_id` | UUID |  |
| 2 | `interface` | LowCardinality(String) |  |
| 3 | `batch` | LowCardinality(String) |  |
| 4 | `scope` | String |  |
| 5 | `started_at` | DateTime64(3, 'Asia/Shanghai') |  |
| 6 | `finished_at` | Nullable(DateTime64(3, 'Asia/Shanghai')) |  |
| 7 | `units_done` | UInt32 |  |
| 8 | `units_failed` | UInt32 |  |
| 9 | `status` | Enum8('running' = 1, 'done' = 2, 'partial' = 3, 'failed' = 4) |  |
