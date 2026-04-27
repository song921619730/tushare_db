# cashflow

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | cashflow |
| 表名 | `tushare_cashflow` |
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
| 行数 | 123,676 |

## 字段列表 (98 个字段)

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
| 4 | `update_flag` | Nullable(String) |  |

### 技术指标 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `_version` | UInt64 |  |

### 估值指标 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `n_incr_clt_loan_adv` | Nullable(Float64) |  |
| 2 | `incl_dvd_profit_paid_sc_ms` | Nullable(String) |  |

### 数值 (90个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `comp_type` | Nullable(String) |  |
| 2 | `report_type` | Nullable(String) |  |
| 3 | `end_type` | Nullable(String) |  |
| 4 | `net_profit` | Nullable(Float64) |  |
| 5 | `finan_exp` | Nullable(String) |  |
| 6 | `c_fr_sale_sg` | Nullable(String) |  |
| 7 | `recp_tax_rends` | Nullable(String) |  |
| 8 | `n_depos_incr_fi` | Nullable(Float64) |  |
| 9 | `n_incr_loans_cb` | Nullable(String) |  |
| 10 | `n_inc_borr_oth_fi` | Nullable(String) |  |
| 11 | `prem_fr_orig_contr` | Nullable(String) |  |
| 12 | `n_incr_insured_dep` | Nullable(String) |  |
| 13 | `n_reinsur_prem` | Nullable(String) |  |
| 14 | `n_incr_disp_tfa` | Nullable(String) |  |
| 15 | `ifc_cash_incr` | Nullable(Float64) |  |
| 16 | `n_incr_disp_faas` | Nullable(String) |  |
| 17 | `n_incr_loans_oth_bank` | Nullable(Float64) |  |
| 18 | `n_cap_incr_repur` | Nullable(String) |  |
| 19 | `c_fr_oth_operate_a` | Nullable(Float64) |  |
| 20 | `c_inf_fr_operate_a` | Nullable(Float64) |  |
| 21 | `c_paid_goods_s` | Nullable(String) |  |
| 22 | `c_paid_to_for_empl` | Nullable(Float64) |  |
| 23 | `c_paid_for_taxes` | Nullable(Float64) |  |
| 24 | `n_incr_dep_cbob` | Nullable(String) |  |
| 25 | `c_pay_claims_orig_inco` | Nullable(String) |  |
| 26 | `pay_handling_chrg` | Nullable(Float64) |  |
| 27 | `pay_comm_insur_plcy` | Nullable(String) |  |
| 28 | `oth_cash_pay_oper_act` | Nullable(Float64) |  |
| 29 | `st_cash_out_act` | Nullable(Float64) |  |
| 30 | `n_cashflow_act` | Nullable(Float64) |  |
| 31 | `oth_recp_ral_inv_act` | Nullable(String) |  |
| 32 | `c_disp_withdrwl_invest` | Nullable(Float64) |  |
| 33 | `c_recp_return_invest` | Nullable(Float64) |  |
| 34 | `n_recp_disp_fiolta` | Nullable(Float64) |  |
| 35 | `n_recp_disp_sobu` | Nullable(String) |  |
| 36 | `stot_inflows_inv_act` | Nullable(Float64) |  |
| 37 | `c_pay_acq_const_fiolta` | Nullable(Float64) |  |
| 38 | `c_paid_invest` | Nullable(Float64) |  |
| 39 | `n_disp_subs_oth_biz` | Nullable(String) |  |
| 40 | `oth_pay_ral_inv_act` | Nullable(String) |  |
| 41 | `n_incr_pledge_loan` | Nullable(String) |  |
| 42 | `stot_out_inv_act` | Nullable(Float64) |  |
| 43 | `n_cashflow_inv_act` | Nullable(Float64) |  |
| 44 | `c_recp_borrow` | Nullable(String) |  |
| 45 | `proc_issue_bonds` | Nullable(Float64) |  |
| 46 | `oth_cash_recp_ral_fnc_act` | Nullable(String) |  |
| 47 | `stot_cash_in_fnc_act` | Nullable(Float64) |  |
| 48 | `free_cashflow` | Nullable(String) |  |
| 49 | `c_prepay_amt_borr` | Nullable(Float64) |  |
| 50 | `c_pay_dist_dpcp_int_exp` | Nullable(Float64) |  |
| 51 | `oth_cashpay_ral_fnc_act` | Nullable(String) |  |
| 52 | `stot_cashout_fnc_act` | Nullable(Float64) |  |
| 53 | `n_cash_flows_fnc_act` | Nullable(Float64) |  |
| 54 | `eff_fx_flu_cash` | Nullable(Float64) |  |
| 55 | `n_incr_cash_cash_equ` | Nullable(Float64) |  |
| 56 | `c_cash_equ_beg_period` | Nullable(Float64) |  |
| 57 | `c_cash_equ_end_period` | Nullable(Float64) |  |
| 58 | `c_recp_cap_contrib` | Nullable(String) |  |
| 59 | `incl_cash_rec_saims` | Nullable(String) |  |
| 60 | `uncon_invest_loss` | Nullable(String) |  |
| 61 | `prov_depr_assets` | Nullable(String) |  |
| 62 | `depr_fa_coga_dpba` | Nullable(Float64) |  |
| 63 | `amort_intang_assets` | Nullable(String) |  |
| 64 | `lt_amort_deferred_exp` | Nullable(String) |  |
| 65 | `decr_deferred_exp` | Nullable(String) |  |
| 66 | `incr_acc_exp` | Nullable(String) |  |
| 67 | `loss_disp_fiolta` | Nullable(Float64) |  |
| 68 | `loss_scr_fa` | Nullable(String) |  |
| 69 | `loss_fv_chg` | Nullable(Float64) |  |
| 70 | `invest_loss` | Nullable(Float64) |  |
| 71 | `decr_def_inc_tax_assets` | Nullable(String) |  |
| 72 | `incr_def_inc_tax_liab` | Nullable(String) |  |
| 73 | `decr_inventories` | Nullable(String) |  |
| 74 | `decr_oper_payable` | Nullable(String) |  |
| 75 | `incr_oper_payable` | Nullable(String) |  |
| 76 | `others` | Nullable(String) |  |
| 77 | `im_net_cashflow_oper_act` | Nullable(String) |  |
| 78 | `conv_debt_into_cap` | Nullable(String) |  |
| 79 | `conv_copbonds_due_within_1y` | Nullable(String) |  |
| 80 | `fa_fnc_leases` | Nullable(String) |  |
| 81 | `im_n_incr_cash_equ` | Nullable(String) |  |
| 82 | `net_dism_capital_add` | Nullable(Float64) |  |
| 83 | `net_cash_rece_sec` | Nullable(String) |  |
| 84 | `credit_impa_loss` | Nullable(String) |  |
| 85 | `use_right_asset_dep` | Nullable(String) |  |
| 86 | `oth_loss_asset` | Nullable(Float64) |  |
| 87 | `end_bal_cash` | Nullable(String) |  |
| 88 | `beg_bal_cash` | Nullable(String) |  |
| 89 | `end_bal_cash_equ` | Nullable(String) |  |
| 90 | `beg_bal_cash_equ` | Nullable(String) |  |
