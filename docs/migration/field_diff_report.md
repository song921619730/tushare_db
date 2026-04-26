# Field Diff Report

Generated: 2026-04-26T07:08:37.632637+00:00


## tushare_stock_basic

| both (10) | act_ent_type, act_name, area, cnspell, industry, list_date, market, name, symbol, ts_code |
| pg_only_drop (7) | curr_type, delist_date, enname, exchange, fullname, is_hs, list_status |
| ch_only_default (1) | _version |

## tushare_trade_cal

| both (4) | cal_date, exchange, is_open, pretrade_date |
| ch_only_default (1) | _version |

## tushare_stock_daily

| both (11) | amount, change, close, high, low, open, pct_chg, pre_close, trade_date, ts_code, vol |
| ch_only_default (1) | _version |

## tushare_stock_weekly

| both (0) |  |
| pg_only_drop (11) | amount, change, close, high, low, open, pct_chg, pre_close, trade_date, ts_code, vol |

## tushare_adj_factor

| both (3) | adj_factor, trade_date, ts_code |
| ch_only_default (1) | _version |

## tushare_daily_basic

| both (17) | circ_mv, dv_ratio, dv_ttm, float_share, free_share, pb, pe, pe_ttm, ps, ps_ttm, total_mv, total_share, trade_date, ts_code, turnover_rate, turnover_rate_f, volume_ratio |
| ch_only_default (2) | _version, close |

## tushare_stk_limit

| both (4) | down_limit, trade_date, ts_code, up_limit |
| pg_only_drop (9) | amp, fc_ratio, fd_amount, first_time, fl_ratio, last_time, open_times, pre_close, up_stat |
| ch_only_default (1) | _version |

## tushare_suspend_d

| both (4) | suspend_timing, suspend_type, trade_date, ts_code |
| pg_only_drop (1) | reason |
| ch_only_default (1) | _version |

## tushare_income

| both (18) | ann_date, basic_eps, comm_exp, comm_income, comp_type, diluted_eps, ebit, ebitda, end_date, f_ann_date, int_exp, int_income, n_commis_income, prem_earned, report_type, revenue, total_revenue, ts_code |
| pg_only_drop (27) | handling_chrg, handling_chrg_comm, incl_inc_invest_assoc, less_inc_tax, less_non_bus_exp, minus_ase_exp, minus_min_int_inc, moins_commis_chrg, n_int_income, n_oth_op_income, n_profit, n_profit_attr_p, op_cost, oper_profit, other_com_income, plus_admin_exp, plus_disp_gain_non_cur_asset, plus_finance_exp, plus_n_gain_chg_fv, plus_n_gain_fx_ents |
| ch_only_default (69) | _version, adj_lossgain, admin_exp, ass_invest_income, assets_impair_loss, biz_tax_surchg, capit_comstock_div, compens_payout, compens_payout_refu, compr_inc_attr_m_s, compr_inc_attr_p, comshare_payable_dvd, continued_net_profit, distable_profit, distr_profit_shrhder, div_payt, end_type, fin_exp, fin_exp_int_exp, fin_exp_int_inc |

## tushare_balancesheet

| both (27) | acct_payable, adv_receipts, ann_date, cap_rese, comp_type, defer_tax_liab, div_payable, end_date, f_ann_date, fa_avail_for_sale, fix_assets, htm_invest, int_payable, inventories, invest_real_estate, lt_borr, lt_eqt_invest, lt_payable, money_cap, notes_payable |
| pg_only_drop (22) | acct_recv, bonds_payable, construc_in_prog, defer_tax_asset, div_recv, int_recv, longdefer_exp, ncr_within_1y, ncr_within_1y_liab, notes_recv, oth_recv, prepay, sal_payable, spec_rese, tax_surcharges_pay, tot_cur_assets, tot_cur_liab, tot_hldr_eqy_exc_min_int, tot_hldr_eqy_inc_min_int, tot_liab |
| ch_only_default (126) | _version, acc_exp, acc_receivable, accounts_pay, accounts_receiv, accounts_receiv_bill, acting_trading_sec, acting_uw_sec, agency_bus_liab, amor_exp, bond_payable, cash_reser_cb, cb_borr, cip, cip_total, client_depos, client_prov, comm_payable, const_materials, contract_assets |

## tushare_cashflow

| both (12) | ann_date, comp_type, depr_fa_coga_dpba, end_date, f_ann_date, invest_loss, loss_disp_fiolta, loss_fv_chg, net_profit, proc_issue_bonds, report_type, ts_code |
| pg_only_drop (31) | amortia_exp, amortia_lt_deferred_exp, cash_equ_end_bal, cash_equ_init_bal, cash_paid_invest, cash_pay_acq_const_fiolta, cash_pay_beh_empl, cash_pay_dist_dpcp_int_exp, cash_pay_goods_services, cash_pay_oth_oper_act, cash_prepay_amt_borr, cash_recp_borr, cash_recp_cap_contri, cash_recp_disp_withdrwl_invest, cash_recp_oth_recp_oper_act, cash_recp_return_invest, cash_recp_sg_rs, fin_exp, im_net_cash_fnc_act, im_net_cash_inv_act |
| ch_only_default (86) | _version, amort_intang_assets, beg_bal_cash, beg_bal_cash_equ, c_cash_equ_beg_period, c_cash_equ_end_period, c_disp_withdrwl_invest, c_fr_oth_operate_a, c_fr_sale_sg, c_inf_fr_operate_a, c_paid_for_taxes, c_paid_goods_s, c_paid_invest, c_paid_to_for_empl, c_pay_acq_const_fiolta, c_pay_claims_orig_inco, c_pay_dist_dpcp_int_exp, c_prepay_amt_borr, c_recp_borrow, c_recp_cap_contrib |

## tushare_fina_indicator

| both (44) | ann_date, ar_turn, assets_turn, bps, ca_turn, capital_rese_ps, cash_ratio, cfps, current_ratio, dt_eps, dt_netprofit_yoy, ebit, ebitda, end_date, eps, eqt_yoy, extra_item, fa_turn, fcfe, fcff |
| pg_only_drop (3) | inc_net_profit_to_income, inc_rev_ps, inv_turn |
| ch_only_default (65) | _version, adminexp_of_gr, assets_to_eqt, assets_yoy, basic_eps_yoy, bps_yoy, ca_to_assets, cfps_yoy, cogs_of_sales, current_exint, currentdebt_to_debt, debt_to_assets, debt_to_eqt, diluted2_eps, dp_assets_to_eqt, dt_eps_yoy, ebit_of_gr, ebit_ps, ebt_yoy, eqt_to_debt |

## tushare_dividend

| both (12) | ann_date, cash_div, cash_div_tax, div_proc, end_date, ex_date, pay_date, record_date, stk_bo_rate, stk_co_rate, stk_div, ts_code |
| pg_only_drop (2) | base_date, base_share |
| ch_only_default (3) | _version, div_listdate, imp_ann_date |

## tushare_moneyflow

| both (20) | buy_elg_amount, buy_elg_vol, buy_lg_amount, buy_lg_vol, buy_md_amount, buy_md_vol, buy_sm_amount, buy_sm_vol, net_mf_amount, net_mf_vol, sell_elg_amount, sell_elg_vol, sell_lg_amount, sell_lg_vol, sell_md_amount, sell_md_vol, sell_sm_amount, sell_sm_vol, trade_date, ts_code |
| ch_only_default (1) | _version |

## tushare_moneyflow_hsgt

| both (6) | ggt_ss, ggt_sz, hgt, north_money, south_money, trade_date |
| pg_only_drop (1) | sggt |
| ch_only_default (2) | _version, sgt |

## tushare_top_list

| both (14) | amount, amount_rate, close, l_amount, l_buy, l_sell, name, net_amount, net_rate, pct_change, reason, trade_date, ts_code, turnover_rate |
| ch_only_default (2) | _version, float_values |

## tushare_margin

| both (8) | exchange_id, rqmcl, rqyl, rzche, rzmre, rzrqye, rzye, trade_date |
| pg_only_drop (4) | rqchl, rqmcl_yoy, rqyl_total, rzye_yoy |
| ch_only_default (2) | _version, rqye |

## tushare_block_trade

| both (7) | amount, buyer, price, seller, trade_date, ts_code, vol |
| ch_only_default (1) | _version |

## tushare_share_float

| both (7) | ann_date, float_date, float_ratio, float_share, holder_name, share_type, ts_code |
| ch_only_default (1) | _version |

## tushare_stk_holdernumber

| both (4) | ann_date, end_date, holder_num, ts_code |
| ch_only_default (1) | _version |

## tushare_pledge_stat

| both (5) | end_date, pledge_count, rest_pledge, ts_code, unrest_pledge |
| pg_only_drop (1) | total_pledged_ratio |
| ch_only_default (3) | _version, pledge_ratio, total_share |

## tushare_index_weight

| both (0) |  |
| pg_only_drop (4) | con_code, index_code, trade_date, weight |

## tushare_fina_mainbz

| both (0) |  |
| pg_only_drop (9) | bz_code, bz_cost, bz_item, bz_profit, bz_sales, curr_type, end_date, ts_code, update_flag |

## tushare_top10_holders

| both (6) | ann_date, end_date, hold_amount, hold_ratio, holder_name, ts_code |
| pg_only_drop (2) | hold_ratio_type, rank |
| ch_only_default (4) | _version, hold_change, hold_float_ratio, holder_type |

## tushare_stk_holdertrade

| both (11) | after_ratio, after_share, ann_date, avg_price, change_ratio, change_vol, holder_name, holder_type, in_de, total_share, ts_code |
| pg_only_drop (1) | holder_rank |
| ch_only_default (1) | _version |

## tushare_moneyflow_ths

| both (0) |  |
| pg_only_drop (10) | buy_elg_amount, buy_lg_amount, buy_md_amount, buy_sm_amount, net_mf_amount, sell_elg_amount, sell_lg_amount, sell_md_amount, sell_sm_amount, trade_date |

## tushare_moneyflow_ind_ths

| both (0) |  |
| pg_only_drop (11) | buy_elg_amount, buy_lg_amount, buy_md_amount, buy_sm_amount, net_mf_amount, sell_elg_amount, sell_lg_amount, sell_md_amount, sell_sm_amount, trade_date, ts_code |

## tushare_moneyflow_cnt_ths

| both (0) |  |
| pg_only_drop (4) | change_type, count, industry, trade_date |

## tushare_dc_hot

| both (0) |  |
| pg_only_drop (5) | hot_rank, hot_score, name, trade_date, ts_code |

## tushare_index_monthly

| both (0) |  |
| pg_only_drop (11) | amount, change, close, high, low, open, pct_chg, pre_close, trade_date, ts_code, vol |

## tushare_fund_nav

| both (0) |  |
| pg_only_drop (9) | accum_div, accum_nav, adj_nav, ann_date, cal_date, net_asset, total_netasset, ts_code, unit_nav |

## tushare_fund_portfolio

| both (0) |  |
| pg_only_drop (8) | ann_date, end_date, hold_mv, hold_ratio, hold_vol, name, symbol, ts_code |

## tushare_fund_div

| both (0) |  |
| pg_only_drop (8) | ann_date, cash_dvd_per_sh_after_tax, cash_dvd_per_sh_pre_tax, div_proc, div_year, end_date, net_ex_date, ts_code |

## tushare_index_daily

| both (0) |  |
| pg_only_drop (11) | amount, change, close, high, low, open, pct_chg, pre_close, trade_date, ts_code, vol |

## tushare_anns_d

| both (0) |  |
| pg_only_drop (6) | ann_date, content, id, title, ts_code, url |

## tushare_bo_daily

| both (0) |  |
| pg_only_drop (6) | bo, bo_avg, date, name, people, rank |

## tushare_cctv_news

| both (0) |  |
| pg_only_drop (4) | content, date, id, title |

## tushare_cyq_chips

| both (0) |  |
| pg_only_drop (5) | price, trade_date, ts_code, volume, volume_pct |

## tushare_dc_member

| both (0) |  |
| pg_only_drop (6) | code, id, in_date, name, out_date, ts_code |

## tushare_etf_iopv

| both (0) |  |
| pg_only_drop (3) | iopv, trade_time, ts_code |

## tushare_etf_mins

| both (0) |  |
| pg_only_drop (9) | amount, close, freq, high, low, open, trade_time, ts_code, vol |

## tushare_film_record

| both (0) |  |
| pg_only_drop (6) | bo_avg, bo_total, name, people, rank, release_date |

## tushare_fina_audit

| both (0) |  |
| pg_only_drop (7) | ann_date, audit_agency, audit_fees, audit_result, audit_sign, end_date, ts_code |

## tushare_fut_mins

| both (0) |  |
| pg_only_drop (9) | amount, close, freq, high, low, open, trade_time, ts_code, vol |

## tushare_index_mins

| both (0) |  |
| pg_only_drop (9) | amount, close, freq, high, low, open, trade_time, ts_code, vol |

## tushare_irm_qa_sh

| both (0) |  |
| pg_only_drop (6) | a_date, answer, id, q_date, question, ts_code |

## tushare_irm_qa_sz

| both (0) |  |
| pg_only_drop (6) | a_date, answer, id, q_date, question, ts_code |

## tushare_major_news

| both (0) |  |
| pg_only_drop (4) | content, datetime, id, title |

## tushare_news

| both (0) |  |
| pg_only_drop (5) | channels, content, datetime, id, title |

## tushare_npr

| both (0) |  |
| pg_only_drop (6) | category, content, id, pub_date, source, title |

## tushare_opt_mins

| both (0) |  |
| pg_only_drop (9) | amount, close, freq, high, low, open, trade_time, ts_code, vol |

## tushare_pledge_detail

| both (0) |  |
| pg_only_drop (11) | ann_date, end_date, holder_name, holding_amount, is_release, pledge_amount, pledged_amount, pledgor, release_date, start_date, ts_code |

## tushare_research_report

| both (0) |  |
| pg_only_drop (8) | author, content, id, org, pub_date, rating, title, ts_code |

## tushare_rt_etf_k

| both (0) |  |
| pg_only_drop (8) | amount, close, high, low, open, trade_time, ts_code, vol |

## tushare_rt_idx_k

| both (0) |  |
| pg_only_drop (8) | amount, close, high, low, open, trade_time, ts_code, vol |

## tushare_rt_min

| both (0) |  |
| pg_only_drop (8) | amount, close, high, low, open, trade_time, ts_code, vol |

## tushare_rt_sw_k

| both (0) |  |
| pg_only_drop (8) | amount, close, high, low, open, trade_time, ts_code, vol |

## tushare_stock_mins

| both (0) |  |
| pg_only_drop (9) | amount, close, freq, high, low, open, trade_time, ts_code, vol |

## tushare_stock_monthly

| both (0) |  |
| pg_only_drop (11) | amount, change, close, high, low, open, pct_chg, pre_close, trade_date, ts_code, vol |

## tushare_hk_basic

| both (0) |  |
| pg_only_drop (10) | cnspell, delist_date, enname, fullname, industry, list_date, list_status, market, name, ts_code |

## tushare_hk_daily

| both (0) |  |
| pg_only_drop (11) | amount, change, close, high, low, open, pct_chg, pre_close, trade_date, ts_code, vol |

## tushare_us_basic

| both (0) |  |
| pg_only_drop (8) | delist_date, exchange, fullname, industry, list_date, list_status, name, ts_code |

## tushare_us_daily

| both (0) |  |
| pg_only_drop (11) | amount, change, close, high, low, open, pct_chg, pre_close, trade_date, ts_code, vol |

## tushare_api_calls_log

| both (0) |  |
| pg_only_drop (9) | api_name, call_time, duration_ms, error_msg, id, params, points, row_count, status |

## tushare_sync_status

| both (0) |  |
| pg_only_drop (8) | api_name, config, error_message, last_data_date, last_sync, status, sync_mode, total_rows |

## tushare_broker_recommend

| both (0) |  |
| pg_only_drop (4) | broker, name, trade_date, ts_code |

## tushare_cb_issue

| both (3) | issue_price, issue_size, ts_code |
| pg_only_drop (6) | issue_date, list_date, maturity, name, rate, rating |
| ch_only_default (21) | _version, ann_date, issue_type, offl_size, onl_code, onl_date, onl_name, onl_pch_excess, onl_pch_num, onl_pch_vol, onl_size, plan_issue_size, res_ann_date, shd_ration_code, shd_ration_date, shd_ration_name, shd_ration_pay_date, shd_ration_price, shd_ration_ratio, shd_ration_record_date |