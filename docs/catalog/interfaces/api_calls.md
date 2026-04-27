# api_calls

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | _meta |
| 行数 | 0 |

## 字段列表 (8 个字段)

### 比率/率 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `duration_ms` | UInt32 |  |

### 数值 (7个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `run_id` | UUID |  |
| 2 | `interface` | LowCardinality(String) |  |
| 3 | `params_hash` | UInt64 |  |
| 4 | `started_at` | DateTime64(3, 'Asia/Shanghai') |  |
| 5 | `status` | UInt16 |  |
| 6 | `rows` | UInt32 |  |
| 7 | `error_msg` | String |  |
