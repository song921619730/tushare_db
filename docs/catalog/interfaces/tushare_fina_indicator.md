# fina_indicator

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | fina_indicator |
| 表名 | `tushare_fina_indicator` |
| 优先级 | P0 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | D |
| 采集策略 | period_loop |
| 日期字段 | end_date |
| 排序键 | ts_code, end_date |
| 分区键 | toYYYYMM(end_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 118,565 |

## 字段列表 (109 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ann_date` | Date |  |
| 2 | `end_date` | Date |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 回报指标 (13个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `roe` | Nullable(Float64) |  |
| 2 | `roe_waa` | Nullable(Float64) |  |
| 3 | `roe_dt` | Nullable(Float64) |  |
| 4 | `roa` | Nullable(Float64) |  |
| 5 | `npta` | Nullable(Float64) |  |
| 6 | `roic` | Nullable(Float64) |  |
| 7 | `roe_yearly` | Nullable(Float64) |  |
| 8 | `roa2_yearly` | Nullable(String) |  |
| 9 | `roa_yearly` | Nullable(Float64) |  |
| 10 | `roa_dp` | Nullable(Float64) |  |
| 11 | `q_roe` | Nullable(Float64) |  |
| 12 | `q_dt_roe` | Nullable(Float64) |  |
| 13 | `q_npta` | Nullable(Float64) |  |

### 增长率/同比 (16个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `basic_eps_yoy` | Nullable(Float64) |  |
| 2 | `dt_eps_yoy` | Nullable(Float64) |  |
| 3 | `cfps_yoy` | Nullable(Float64) |  |
| 4 | `op_yoy` | Nullable(Float64) |  |
| 5 | `ebt_yoy` | Nullable(Float64) |  |
| 6 | `netprofit_yoy` | Nullable(Float64) |  |
| 7 | `dt_netprofit_yoy` | Nullable(Float64) |  |
| 8 | `ocf_yoy` | Nullable(Float64) |  |
| 9 | `roe_yoy` | Nullable(Float64) |  |
| 10 | `bps_yoy` | Nullable(Float64) |  |
| 11 | `assets_yoy` | Nullable(Float64) |  |
| 12 | `eqt_yoy` | Nullable(Float64) |  |
| 13 | `tr_yoy` | Nullable(Float64) |  |
| 14 | `or_yoy` | Nullable(Float64) |  |
| 15 | `q_sales_yoy` | Nullable(Float64) |  |
| 16 | `equity_yoy` | Nullable(Float64) |  |

### 股本/市值 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_revenue_ps` | Nullable(Float64) |  |
| 2 | `tbassets_to_totalassets` | Nullable(String) |  |

### 比率/率 (6个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `gross_margin` | Nullable(Float64) |  |
| 2 | `current_ratio` | Nullable(Float64) |  |
| 3 | `quick_ratio` | Nullable(Float64) |  |
| 4 | `cash_ratio` | Nullable(Float64) |  |
| 5 | `netprofit_margin` | Nullable(Float64) |  |
| 6 | `grossprofit_margin` | Nullable(Float64) |  |

### 数值 (68个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `eps` | Nullable(Float64) |  |
| 2 | `dt_eps` | Nullable(Float64) |  |
| 3 | `revenue_ps` | Nullable(Float64) |  |
| 4 | `capital_rese_ps` | Nullable(Float64) |  |
| 5 | `surplus_rese_ps` | Nullable(Float64) |  |
| 6 | `undist_profit_ps` | Nullable(Float64) |  |
| 7 | `extra_item` | Nullable(Float64) |  |
| 8 | `profit_dedt` | Nullable(Float64) |  |
| 9 | `ar_turn` | Nullable(Float64) |  |
| 10 | `ca_turn` | Nullable(Float64) |  |
| 11 | `fa_turn` | Nullable(Float64) |  |
| 12 | `assets_turn` | Nullable(Float64) |  |
| 13 | `op_income` | Nullable(Float64) |  |
| 14 | `ebit` | Nullable(Float64) |  |
| 15 | `ebitda` | Nullable(Float64) |  |
| 16 | `fcff` | Nullable(Float64) |  |
| 17 | `fcfe` | Nullable(Float64) |  |
| 18 | `current_exint` | Nullable(String) |  |
| 19 | `noncurrent_exint` | Nullable(String) |  |
| 20 | `interestdebt` | Nullable(Float64) |  |
| 21 | `netdebt` | Nullable(Float64) |  |
| 22 | `tangible_asset` | Nullable(Float64) |  |
| 23 | `working_capital` | Nullable(Float64) |  |
| 24 | `networking_capital` | Nullable(String) |  |
| 25 | `invest_capital` | Nullable(Float64) |  |
| 26 | `retained_earnings` | Nullable(Float64) |  |
| 27 | `diluted2_eps` | Nullable(Float64) |  |
| 28 | `bps` | Nullable(Float64) |  |
| 29 | `ocfps` | Nullable(Float64) |  |
| 30 | `retainedps` | Nullable(Float64) |  |
| 31 | `cfps` | Nullable(Float64) |  |
| 32 | `ebit_ps` | Nullable(String) |  |
| 33 | `fcff_ps` | Nullable(String) |  |
| 34 | `fcfe_ps` | Nullable(String) |  |
| 35 | `cogs_of_sales` | Nullable(String) |  |
| 36 | `expense_of_sales` | Nullable(String) |  |
| 37 | `profit_to_gr` | Nullable(Float64) |  |
| 38 | `saleexp_to_gr` | Nullable(String) |  |
| 39 | `adminexp_of_gr` | Nullable(Float64) |  |
| 40 | `finaexp_of_gr` | Nullable(String) |  |
| 41 | `impai_ttm` | Nullable(String) |  |
| 42 | `gc_of_gr` | Nullable(String) |  |
| 43 | `op_of_gr` | Nullable(Float64) |  |
| 44 | `ebit_of_gr` | Nullable(String) |  |
| 45 | `debt_to_assets` | Nullable(Float64) |  |
| 46 | `assets_to_eqt` | Nullable(Float64) |  |
| 47 | `dp_assets_to_eqt` | Nullable(Float64) |  |
| 48 | `ca_to_assets` | Nullable(String) |  |
| 49 | `nca_to_assets` | Nullable(String) |  |
| 50 | `int_to_talcap` | Nullable(String) |  |
| 51 | `eqt_to_talcapital` | Nullable(String) |  |
| 52 | `currentdebt_to_debt` | Nullable(String) |  |
| 53 | `longdeb_to_debt` | Nullable(String) |  |
| 54 | `ocf_to_shortdebt` | Nullable(String) |  |
| 55 | `debt_to_eqt` | Nullable(Float64) |  |
| 56 | `eqt_to_debt` | Nullable(Float64) |  |
| 57 | `eqt_to_interestdebt` | Nullable(String) |  |
| 58 | `tangibleasset_to_debt` | Nullable(String) |  |
| 59 | `tangasset_to_intdebt` | Nullable(String) |  |
| 60 | `tangibleasset_to_netdebt` | Nullable(String) |  |
| 61 | `ocf_to_debt` | Nullable(Float64) |  |
| 62 | `turn_days` | Nullable(String) |  |
| 63 | `fixed_assets` | Nullable(Float64) |  |
| 64 | `profit_to_op` | Nullable(Float64) |  |
| 65 | `q_saleexp_to_gr` | Nullable(String) |  |
| 66 | `q_gc_to_gr` | Nullable(String) |  |
| 67 | `q_ocf_to_sales` | Nullable(Float64) |  |
| 68 | `q_op_qoq` | Nullable(Float64) |  |
