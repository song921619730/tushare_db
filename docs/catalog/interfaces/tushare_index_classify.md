# index_classify

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | index_classify |
| 表名 | `tushare_index_classify` |
| 优先级 | P1 |
| 模式 | full |
| 频率分桶 | special |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | toYYYYMM(trade_date) |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 1 |

## 字段列表 (8 个字段)

### 标识 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `index_code` | String |  |
| 2 | `industry_code` | String |  |
| 3 | `parent_code` | String |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `industry_name` | String |  |
| 2 | `level` | String |  |
| 3 | `is_pub` | String |  |
| 4 | `src` | String |  |
