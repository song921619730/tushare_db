# ths_member

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | ths_member |
| 表名 | `tushare_ths_member` |
| 优先级 | P1 |
| 模式 | full |
| 频率分桶 | special |
| 批次 | reference |
| 采集策略 | full_once |
| 排序键 | ts_code |
| 分区键 | tuple() |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 2 |

## 字段列表 (4 个字段)

### 标识 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |
| 2 | `con_code` | String |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 数值 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `con_name` | String |  |
