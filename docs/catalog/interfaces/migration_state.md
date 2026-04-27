# migration_state

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | _meta |
| 行数 | 55 |

## 字段列表 (11 个字段)

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 比率/率 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `duration_sec` | UInt32 |  |

### 数值 (9个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `pg_table` | String |  |
| 2 | `ch_table` | String |  |
| 3 | `ch_database` | String |  |
| 4 | `status` | Enum8('pending' = 0, 'running' = 1, 'done' = 2, 'failed' = 3) |  |
| 5 | `rows_migrated` | UInt64 |  |
| 6 | `pg_row_count` | UInt64 |  |
| 7 | `started_at` | DateTime64(3, 'Asia/Shanghai') |  |
| 8 | `finished_at` | Nullable(DateTime64(3, 'Asia/Shanghai')) |  |
| 9 | `error_msg` | String |  |
