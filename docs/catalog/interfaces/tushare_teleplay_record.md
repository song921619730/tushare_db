# teleplay_record

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | teleplay_record |
| 表名 | `tushare_teleplay_record` |
| 优先级 | P3 |
| 模式 | incremental |
| 频率分桶 | normal |
| 批次 | D |
| 采集策略 | date_loop |
| 日期字段 | trade_date |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 1 |

## 字段列表 (14 个字段)

### 日期 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `report_date` | String |  |
| 2 | `shooting_date` | String |  |

### 技术指标 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `remarks` | String |  |
| 2 | `_version` | UInt64 |  |

### 数值 (10个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `name` | LowCardinality(String) |  |
| 2 | `classify` | String |  |
| 3 | `types` | String |  |
| 4 | `org` | String |  |
| 5 | `license_key` | String |  |
| 6 | `episodes` | String |  |
| 7 | `prod_cycle` | String |  |
| 8 | `content` | String |  |
| 9 | `pro_opi` | String |  |
| 10 | `dept_opi` | String |  |
