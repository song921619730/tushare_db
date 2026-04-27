# disclosure_date

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | disclosure_date |
| 表名 | `tushare_disclosure_date` |
| 优先级 | P2 |
| 模式 | full |
| 频率分桶 | special |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | toYYYYMM(end_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 6,000 |

## 字段列表 (6 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ann_date` | String |  |
| 2 | `end_date` | Date |  |
| 3 | `pre_date` | String |  |
| 4 | `actual_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |
