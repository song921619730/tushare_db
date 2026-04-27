# income

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | income |
| 表名 | `tushare_income` |
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
| 行数 | 123,800 |

## 字段列表 (87 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ann_date` | Date |  |
| 2 | `f_ann_date` | Date |  |
| 3 | `end_date` | Date |  |
| 4 | `update_flag` | String |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 估值指标 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `prfshare_payable_dvd` | Nullable(String) |  |
| 2 | `comshare_payable_dvd` | Nullable(String) |  |

### 股本/市值 (3个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_revenue` | Nullable(Decimal(18, 2)) |  |
| 2 | `total_cogs` | Nullable(Decimal(18, 2)) |  |
| 3 | `total_profit` | Nullable(Decimal(18, 2)) |  |

### 数值 (76个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `report_type` | String |  |
| 2 | `comp_type` | String |  |
| 3 | `end_type` | String |  |
| 4 | `basic_eps` | Nullable(Float64) |  |
| 5 | `diluted_eps` | Nullable(Float64) |  |
| 6 | `revenue` | Nullable(Float64) |  |
| 7 | `int_income` | Nullable(Decimal(18, 2)) |  |
| 8 | `prem_earned` | Nullable(Float64) |  |
| 9 | `comm_income` | Nullable(Decimal(18, 2)) |  |
| 10 | `n_commis_income` | Nullable(Decimal(18, 2)) |  |
| 11 | `n_oth_income` | Nullable(Decimal(18, 2)) |  |
| 12 | `n_oth_b_income` | Nullable(Decimal(18, 2)) |  |
| 13 | `prem_income` | Nullable(Decimal(18, 2)) |  |
| 14 | `out_prem` | Nullable(String) |  |
| 15 | `une_prem_reser` | Nullable(String) |  |
| 16 | `reins_income` | Nullable(Decimal(18, 2)) |  |
| 17 | `n_sec_tb_income` | Nullable(Decimal(18, 2)) |  |
| 18 | `n_sec_uw_income` | Nullable(Decimal(18, 2)) |  |
| 19 | `n_asset_mg_income` | Nullable(Decimal(18, 2)) |  |
| 20 | `oth_b_income` | Nullable(Decimal(18, 2)) |  |
| 21 | `prem_income_p` | Nullable(Decimal(18, 2)) |  |
| 22 | `fv_value_chg_gain` | Nullable(Float64) |  |
| 23 | `invest_income` | Nullable(Decimal(18, 2)) |  |
| 24 | `ass_invest_income` | Nullable(Decimal(18, 2)) |  |
| 25 | `forex_gain` | Nullable(Float64) |  |
| 26 | `oper_cost` | Nullable(Decimal(18, 2)) |  |
| 27 | `int_exp` | Nullable(Float64) |  |
| 28 | `comm_exp` | Nullable(Float64) |  |
| 29 | `biz_tax_surchg` | Nullable(Float64) |  |
| 30 | `sell_exp` | Nullable(String) |  |
| 31 | `admin_exp` | Nullable(Float64) |  |
| 32 | `fin_exp` | Nullable(String) |  |
| 33 | `assets_impair_loss` | Nullable(String) |  |
| 34 | `prem_refund` | Nullable(String) |  |
| 35 | `compens_payout` | Nullable(String) |  |
| 36 | `reser_insur_liab` | Nullable(String) |  |
| 37 | `div_payt` | Nullable(String) |  |
| 38 | `reins_exp` | Nullable(String) |  |
| 39 | `oper_exp` | Nullable(Float64) |  |
| 40 | `compens_payout_refu` | Nullable(String) |  |
| 41 | `insur_reser_refu` | Nullable(String) |  |
| 42 | `reins_cost_refund` | Nullable(String) |  |
| 43 | `other_bus_cost` | Nullable(Decimal(18, 2)) |  |
| 44 | `operate_profit` | Nullable(Decimal(18, 2)) |  |
| 45 | `non_oper_income` | Nullable(Decimal(18, 2)) |  |
| 46 | `non_oper_exp` | Nullable(Float64) |  |
| 47 | `nca_disploss` | Nullable(String) |  |
| 48 | `income_tax` | Nullable(Float64) |  |
| 49 | `n_income` | Nullable(Decimal(18, 2)) |  |
| 50 | `n_income_attr_p` | Nullable(Float64) |  |
| 51 | `minority_gain` | Nullable(String) |  |
| 52 | `oth_compr_income` | Nullable(Decimal(18, 2)) |  |
| 53 | `t_compr_income` | Nullable(Decimal(18, 2)) |  |
| 54 | `compr_inc_attr_p` | Nullable(Float64) |  |
| 55 | `compr_inc_attr_m_s` | Nullable(String) |  |
| 56 | `ebit` | Nullable(Float64) |  |
| 57 | `ebitda` | Nullable(Float64) |  |
| 58 | `insurance_exp` | Nullable(String) |  |
| 59 | `undist_profit` | Nullable(Decimal(18, 2)) |  |
| 60 | `distable_profit` | Nullable(Decimal(18, 2)) |  |
| 61 | `rd_exp` | Nullable(String) |  |
| 62 | `fin_exp_int_exp` | Nullable(String) |  |
| 63 | `fin_exp_int_inc` | Nullable(String) |  |
| 64 | `transfer_surplus_rese` | Nullable(String) |  |
| 65 | `transfer_housing_imprest` | Nullable(String) |  |
| 66 | `transfer_oth` | Nullable(String) |  |
| 67 | `adj_lossgain` | Nullable(String) |  |
| 68 | `withdra_legal_surplus` | Nullable(String) |  |
| 69 | `withdra_legal_pubfund` | Nullable(String) |  |
| 70 | `withdra_biz_devfund` | Nullable(String) |  |
| 71 | `withdra_rese_fund` | Nullable(String) |  |
| 72 | `withdra_oth_ersu` | Nullable(String) |  |
| 73 | `workers_welfare` | Nullable(String) |  |
| 74 | `distr_profit_shrhder` | Nullable(String) |  |
| 75 | `capit_comstock_div` | Nullable(String) |  |
| 76 | `continued_net_profit` | Nullable(Decimal(18, 2)) |  |
