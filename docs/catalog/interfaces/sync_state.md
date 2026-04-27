# sync_state

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | _meta |
| 行数 | 364,853 |

## 字段列表 (9 个字段)

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (8个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `interface` | LowCardinality(String) |  |
| 2 | `scope_key` | String |  |
| 3 | `status` | Enum8('pending' = 0, 'running' = 1, 'done' = 2, 'partial' = 3, 'failed' = 4, 'biz_err' = 5) |  |
| 4 | `rows` | UInt64 |  |
| 5 | `last_success_at` | DateTime64(3, 'Asia/Shanghai') |  |
| 6 | `heartbeat_at` | DateTime64(3, 'Asia/Shanghai') |  |
| 7 | `attempts` | UInt8 |  |
| 8 | `last_error` | String |  |
