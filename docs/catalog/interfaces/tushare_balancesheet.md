# balancesheet

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | balancesheet |
| 表名 | `tushare_balancesheet` |
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
| 行数 | 122,180 |

## 字段列表 (153 个字段)

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
| 1 | `adv_receipts` | Nullable(Float64) |  |
| 2 | `prem_receiv_adva` | String |  |

### 股本/市值 (16个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_share` | Nullable(Decimal(18, 4)) |  |
| 2 | `total_cur_assets` | Decimal(18, 2) |  |
| 3 | `total_nca` | Decimal(18, 2) |  |
| 4 | `total_assets` | Decimal(18, 2) |  |
| 5 | `total_cur_liab` | Decimal(18, 2) |  |
| 6 | `total_ncl` | Decimal(18, 2) |  |
| 7 | `total_liab` | Decimal(18, 2) |  |
| 8 | `treasury_share` | Decimal(18, 4) |  |
| 9 | `total_hldr_eqy_exc_min_int` | Decimal(18, 2) |  |
| 10 | `total_hldr_eqy_inc_min_int` | Float64 |  |
| 11 | `total_liab_hldr_eqy` | Float64 |  |
| 12 | `oth_rcv_total` | String |  |
| 13 | `fix_assets_total` | String |  |
| 14 | `cip_total` | String |  |
| 15 | `oth_pay_total` | String |  |
| 16 | `long_pay_total` | String |  |

### 数值 (129个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `report_type` | String |  |
| 2 | `comp_type` | String |  |
| 3 | `end_type` | String |  |
| 4 | `cap_rese` | Nullable(Float64) |  |
| 5 | `undistr_porfit` | Nullable(Float64) |  |
| 6 | `surplus_rese` | Nullable(Float64) |  |
| 7 | `special_rese` | String |  |
| 8 | `money_cap` | Nullable(Float64) |  |
| 9 | `trad_asset` | Nullable(Decimal(18, 2)) |  |
| 10 | `notes_receiv` | String |  |
| 11 | `accounts_receiv` | String |  |
| 12 | `oth_receiv` | String |  |
| 13 | `prepayment` | String |  |
| 14 | `div_receiv` | String |  |
| 15 | `int_receiv` | String |  |
| 16 | `inventories` | Nullable(Float64) |  |
| 17 | `amor_exp` | String |  |
| 18 | `nca_within_1y` | String |  |
| 19 | `sett_rsrv` | String |  |
| 20 | `loanto_oth_bank_fi` | Float64 |  |
| 21 | `premium_receiv` | String |  |
| 22 | `reinsur_receiv` | String |  |
| 23 | `reinsur_res_receiv` | String |  |
| 24 | `pur_resale_fa` | Float64 |  |
| 25 | `oth_cur_assets` | String |  |
| 26 | `fa_avail_for_sale` | Nullable(Float64) |  |
| 27 | `htm_invest` | Nullable(Float64) |  |
| 28 | `lt_eqt_invest` | Nullable(Float64) |  |
| 29 | `invest_real_estate` | Nullable(Float64) |  |
| 30 | `time_deposits` | String |  |
| 31 | `oth_assets` | Float64 |  |
| 32 | `lt_rec` | String |  |
| 33 | `fix_assets` | Nullable(Float64) |  |
| 34 | `cip` | String |  |
| 35 | `const_materials` | String |  |
| 36 | `fixed_assets_disp` | String |  |
| 37 | `produc_bio_assets` | String |  |
| 38 | `oil_and_gas_assets` | String |  |
| 39 | `intan_assets` | Float64 |  |
| 40 | `r_and_d` | String |  |
| 41 | `goodwill` | Float64 |  |
| 42 | `lt_amor_exp` | String |  |
| 43 | `defer_tax_assets` | Float64 |  |
| 44 | `decr_in_disbur` | Float64 |  |
| 45 | `oth_nca` | String |  |
| 46 | `cash_reser_cb` | Float64 |  |
| 47 | `depos_in_oth_bfi` | Float64 |  |
| 48 | `prec_metals` | Float64 |  |
| 49 | `deriv_assets` | Float64 |  |
| 50 | `rr_reins_une_prem` | String |  |
| 51 | `rr_reins_outstd_cla` | String |  |
| 52 | `rr_reins_lins_liab` | String |  |
| 53 | `rr_reins_lthins_liab` | String |  |
| 54 | `refund_depos` | String |  |
| 55 | `ph_pledge_loans` | String |  |
| 56 | `refund_cap_depos` | String |  |
| 57 | `indep_acct_assets` | String |  |
| 58 | `client_depos` | String |  |
| 59 | `client_prov` | String |  |
| 60 | `transac_seat_fee` | String |  |
| 61 | `invest_as_receiv` | String |  |
| 62 | `lt_borr` | Nullable(Float64) |  |
| 63 | `st_borr` | String |  |
| 64 | `cb_borr` | Float64 |  |
| 65 | `depos_ib_deposits` | String |  |
| 66 | `loan_oth_bank` | Float64 |  |
| 67 | `trading_fl` | Float64 |  |
| 68 | `notes_payable` | Nullable(Float64) |  |
| 69 | `acct_payable` | Nullable(Float64) |  |
| 70 | `sold_for_repur_fa` | Float64 |  |
| 71 | `comm_payable` | String |  |
| 72 | `payroll_payable` | Float64 |  |
| 73 | `taxes_payable` | Float64 |  |
| 74 | `int_payable` | Nullable(Float64) |  |
| 75 | `div_payable` | Nullable(Float64) |  |
| 76 | `oth_payable` | Nullable(Float64) |  |
| 77 | `acc_exp` | String |  |
| 78 | `deferred_inc` | String |  |
| 79 | `st_bonds_payable` | String |  |
| 80 | `payable_to_reinsurer` | String |  |
| 81 | `rsrv_insur_cont` | String |  |
| 82 | `acting_trading_sec` | String |  |
| 83 | `acting_uw_sec` | String |  |
| 84 | `non_cur_liab_due_1y` | String |  |
| 85 | `oth_cur_liab` | String |  |
| 86 | `bond_payable` | Float64 |  |
| 87 | `lt_payable` | Nullable(Float64) |  |
| 88 | `specific_payables` | String |  |
| 89 | `estimated_liab` | Float64 |  |
| 90 | `defer_tax_liab` | Nullable(Float64) |  |
| 91 | `defer_inc_non_cur_liab` | String |  |
| 92 | `oth_ncl` | String |  |
| 93 | `depos_oth_bfi` | Float64 |  |
| 94 | `deriv_liab` | Float64 |  |
| 95 | `depos` | Float64 |  |
| 96 | `agency_bus_liab` | String |  |
| 97 | `oth_liab` | Float64 |  |
| 98 | `depos_received` | String |  |
| 99 | `ph_invest` | String |  |
| 100 | `reser_une_prem` | String |  |
| 101 | `reser_outstd_claims` | String |  |
| 102 | `reser_lins_liab` | String |  |
| 103 | `reser_lthins_liab` | String |  |
| 104 | `indept_acc_liab` | String |  |
| 105 | `pledge_borr` | String |  |
| 106 | `indem_payable` | String |  |
| 107 | `policy_div_payable` | String |  |
| 108 | `ordin_risk_reser` | Float64 |  |
| 109 | `forex_differ` | String |  |
| 110 | `invest_loss_unconf` | String |  |
| 111 | `minority_int` | String |  |
| 112 | `lt_payroll_payable` | String |  |
| 113 | `oth_comp_income` | Decimal(18, 2) |  |
| 114 | `oth_eqt_tools` | Float64 |  |
| 115 | `oth_eqt_tools_p_shr` | Float64 |  |
| 116 | `lending_funds` | String |  |
| 117 | `acc_receivable` | String |  |
| 118 | `st_fin_payable` | String |  |
| 119 | `payables` | String |  |
| 120 | `hfs_assets` | String |  |
| 121 | `hfs_sales` | String |  |
| 122 | `cost_fin_assets` | String |  |
| 123 | `fair_value_fin_assets` | String |  |
| 124 | `contract_assets` | String |  |
| 125 | `contract_liab` | String |  |
| 126 | `accounts_receiv_bill` | String |  |
| 127 | `accounts_pay` | String |  |
| 128 | `debt_invest` | Float64 |  |
| 129 | `oth_debt_invest` | Float64 |  |
