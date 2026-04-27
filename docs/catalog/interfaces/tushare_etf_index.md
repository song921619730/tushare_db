# etf_index

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | etf_index |
| 表名 | `tushare_etf_index` |
| 优先级 | P2 |
| 模式 | full |
| 频率分桶 | normal |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | toYYYYMM(trade_date) |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 0 |

## 字段列表 (9 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `pub_date` | Date |  |
| 2 | `base_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (5个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `indx_name` | String |  |
| 2 | `indx_csname` | String |  |
| 3 | `pub_party_name` | String |  |
| 4 | `bp` | Float64 |  |
| 5 | `adj_circle` | String |  |
