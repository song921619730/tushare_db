"""Generate all 227 config/interfaces/*.yaml files from authoritative data."""

import yaml
from pathlib import Path

# ============================================================
# Authoritative interface data (merged from rate_limits + 10k_interfaces)
# Each entry: (name, table, category, bucket, priority, mode, start_date, is_paid)
# ============================================================
INTERFACES = [
    # bonds (normal=15, special=1)
    ("bc_bestotcqt", "tushare_bc_bestotcqt", "bonds", "normal", "P3", "incremental", "20200101", False),
    ("bc_otcqt", "tushare_bc_otcqt", "bonds", "normal", "P3", "incremental", "20200101", False),
    ("bond_blk", "tushare_bond_blk", "bonds", "normal", "P3", "incremental", "20200101", False),
    ("bond_blk_detail", "tushare_bond_blk_detail", "bonds", "normal", "P3", "incremental", "20200101", False),
    ("cb_basic_info_placeholder", "tushare_cb_basic_info_placeholder", "bonds", "normal", "P3", "incremental", "20200101", False),
    ("cb_call", "tushare_cb_call", "bonds", "normal", "P3", "incremental", "20200101", False),
    ("cb_daily", "tushare_cb_daily", "bonds", "normal", "P2", "incremental", "20200101", False),
    ("cb_factor_pro", "tushare_cb_factor_pro", "bonds", "special", "P2", "incremental", "20200101", False),
    ("cb_issue", "tushare_cb_issue", "bonds", "normal", "P2", "incremental", "20200101", False),
    ("cb_price_chg", "tushare_cb_price_chg", "bonds", "normal", "P3", "incremental", "20200101", False),
    ("cb_rate", "tushare_cb_rate", "bonds", "normal", "P3", "full", "", False),
    ("cb_share", "tushare_cb_share", "bonds", "normal", "P2", "incremental", "20200101", False),
    ("eco_cal", "tushare_eco_cal", "bonds", "normal", "P3", "incremental", "20200101", False),
    ("repo_daily", "tushare_repo_daily", "bonds", "normal", "P2", "incremental", "20200101", False),
    ("yc_cb", "tushare_yc_cb", "bonds", "normal", "P3", "incremental", "20200101", False),

    # etf (normal=5, special=1)
    ("etf_basic", "tushare_etf_basic", "etf", "normal", "P1", "full", "", False),
    ("etf_index", "tushare_etf_index", "etf", "normal", "P2", "full", "", False),
    ("etf_share_size", "tushare_etf_share_size", "etf", "special", "P2", "incremental", "20200101", False),
    ("fund_adj", "tushare_fund_adj", "etf", "normal", "P2", "incremental", "20200101", False),
    ("fund_daily", "tushare_fund_daily", "etf", "normal", "P1", "incremental", "20200101", False),

    # forex (normal=2)
    ("fx_daily", "tushare_fx_daily", "forex", "normal", "P3", "incremental", "20200101", False),
    ("fx_obasic", "tushare_fx_obasic", "forex", "normal", "P3", "full", "", False),

    # fund (normal=8, special=1)
    ("fund_basic", "tushare_fund_basic", "fund", "normal", "P1", "full", "", False),
    ("fund_company", "tushare_fund_company", "fund", "normal", "P2", "full", "", False),
    ("fund_div", "tushare_fund_div", "fund", "normal", "P2", "incremental", "20200101", False),
    ("fund_factor_pro", "tushare_fund_factor_pro", "fund", "special", "P2", "incremental", "20200101", False),
    ("fund_manager", "tushare_fund_manager", "fund", "normal", "P2", "incremental", "20200101", False),
    ("fund_nav", "tushare_fund_nav", "fund", "normal", "P1", "incremental", "20200101", False),
    ("fund_portfolio", "tushare_fund_portfolio", "fund", "normal", "P2", "incremental", "20200101", False),
    ("fund_sales_ratio", "tushare_fund_sales_ratio", "fund", "normal", "P3", "incremental", "20200101", False),
    ("fund_sales_vol", "tushare_fund_sales_vol", "fund", "normal", "P3", "incremental", "20210101", False),
    ("fund_share", "tushare_fund_share", "fund", "normal", "P2", "incremental", "20200101", False),

    # futures (normal=11, special=1)
    ("ft_limit", "tushare_ft_limit", "futures", "special", "P2", "incremental", "20200101", False),
    ("fut_basic", "tushare_fut_basic", "futures", "normal", "P2", "full", "", False),
    ("fut_daily", "tushare_fut_daily", "futures", "normal", "P2", "incremental", "20200101", False),
    ("fut_holding", "tushare_fut_holding", "futures", "normal", "P2", "incremental", "20200101", False),
    ("fut_index_daily", "tushare_fut_index_daily", "futures", "normal", "P2", "incremental", "20200101", False),
    ("fut_mapping", "tushare_fut_mapping", "futures", "normal", "P2", "incremental", "20200101", False),
    ("fut_settle", "tushare_fut_settle", "futures", "normal", "P3", "incremental", "20200101", False),
    ("fut_trade_cal", "tushare_fut_trade_cal", "futures", "normal", "P2", "full", "", False),
    ("fut_weekly_detail", "tushare_fut_weekly_detail", "futures", "normal", "P3", "incremental", "20200101", False),
    ("fut_weekly_monthly", "tushare_fut_weekly_monthly", "futures", "normal", "P2", "incremental", "20200101", False),
    ("fut_wsr", "tushare_fut_wsr", "futures", "normal", "P3", "incremental", "20200101", False),

    # index (normal=1, special=15)
    ("ci_daily", "tushare_ci_daily", "index", "special", "P2", "incremental", "20200101", False),
    ("ci_index_member", "tushare_ci_index_member", "index", "special", "P2", "full", "", False),
    ("daily_info", "tushare_daily_info", "index", "special", "P2", "incremental", "20200101", False),
    ("idx_factor_pro", "tushare_idx_factor_pro", "index", "special", "P2", "incremental", "20200101", False),
    ("index_basic", "tushare_index_basic", "index", "normal", "P0", "full", "", False),
    ("index_classify", "tushare_index_classify", "index", "special", "P1", "full", "", False),
    ("index_daily", "tushare_index_daily", "index", "special", "P0", "incremental", "20200101", False),
    ("index_dailybasic", "tushare_index_dailybasic", "index", "special", "P1", "incremental", "20200101", False),
    ("index_global", "tushare_index_global", "index", "special", "P2", "incremental", "20200101", False),
    ("index_member_all", "tushare_index_member_all", "index", "special", "P2", "full", "", False),
    ("index_monthly", "tushare_index_monthly", "index", "special", "P1", "incremental", "20200101", False),
    ("index_weekly", "tushare_index_weekly", "index", "special", "P1", "incremental", "20200101", False),
    ("index_weight", "tushare_index_weight", "index", "special", "P1", "incremental", "20200101", False),
    ("sw_daily", "tushare_sw_daily", "index", "special", "P2", "incremental", "20200101", False),
    ("sz_daily_info", "tushare_sz_daily_info", "index", "special", "P2", "incremental", "20200101", False),

    # macro (normal=18)
    ("bo_cinema", "tushare_bo_cinema", "macro", "normal", "P3", "incremental", "20200101", False),
    ("bo_daily", "tushare_bo_daily", "macro", "normal", "P3", "incremental", "20200101", False),
    ("bo_monthly", "tushare_bo_monthly", "macro", "normal", "P3", "incremental", "20200101", False),
    ("bo_weekly", "tushare_bo_weekly", "macro", "normal", "P3", "incremental", "20200101", False),
    ("cn_cpi", "tushare_cn_cpi", "macro", "normal", "P3", "incremental", "20200101", False),
    ("cn_gdp", "tushare_cn_gdp", "macro", "normal", "P3", "incremental", "20200101", False),
    ("cn_m", "tushare_cn_m", "macro", "normal", "P3", "incremental", "20200101", False),
    ("cn_pmi", "tushare_cn_pmi", "macro", "normal", "P3", "incremental", "20200101", False),
    ("cn_ppi", "tushare_cn_ppi", "macro", "normal", "P3", "incremental", "20200101", False),
    ("gz_index", "tushare_gz_index", "macro", "normal", "P3", "incremental", "20200101", False),
    ("hibor", "tushare_hibor", "macro", "normal", "P3", "incremental", "20200101", False),
    ("libor", "tushare_libor", "macro", "normal", "P3", "incremental", "20200101", False),
    ("sf_month", "tushare_sf_month", "macro", "normal", "P3", "incremental", "20200101", False),
    ("shibor", "tushare_shibor", "macro", "normal", "P3", "incremental", "20200101", False),
    ("shibor_lpr", "tushare_shibor_lpr", "macro", "normal", "P3", "incremental", "20200101", False),
    ("shibor_quote", "tushare_shibor_quote", "macro", "normal", "P3", "incremental", "20200101", False),
    ("us_tbr", "tushare_us_tbr", "macro", "normal", "P3", "incremental", "20200101", False),
    ("us_tltr", "tushare_us_tltr", "macro", "normal", "P3", "incremental", "20200101", False),
    ("us_trltr", "tushare_us_trltr", "macro", "normal", "P3", "incremental", "20200101", False),
    ("us_trycr", "tushare_us_trycr", "macro", "normal", "P3", "incremental", "20200101", False),
    ("us_tycr", "tushare_us_tycr", "macro", "normal", "P3", "incremental", "20200101", False),
    ("wz_index", "tushare_wz_index", "macro", "normal", "P3", "incremental", "20200101", False),

    # options (normal=2)
    ("opt_basic", "tushare_opt_basic", "options", "normal", "P2", "full", "", False),
    ("opt_daily", "tushare_opt_daily", "options", "normal", "P2", "incremental", "20200101", False),

    # spot (normal=2)
    ("sge_basic", "tushare_sge_basic", "spot", "normal", "P3", "full", "", False),
    ("sge_daily", "tushare_sge_daily", "spot", "normal", "P3", "incremental", "20200101", False),

    # stock_basic (normal=12, special=2)
    ("bak_basic", "tushare_bak_basic", "stock_basic", "special", "P3", "full", "20160101", False),
    ("bse_mapping", "tushare_bse_mapping", "stock_basic", "normal", "P2", "full", "", False),
    ("namechange", "tushare_namechange", "stock_basic", "normal", "P2", "full", "20200101", False),
    ("new_share", "tushare_new_share", "stock_basic", "normal", "P1", "incremental", "20200101", False),
    ("st", "tushare_st", "stock_basic", "special", "P2", "incremental", "20200101", False),
    ("stk_managers", "tushare_stk_managers", "stock_basic", "normal", "P1", "full", "20200101", False),
    ("stk_premarket", "tushare_stk_premarket", "stock_basic", "special", "P2", "incremental", "20200101", False),
    ("stk_rewards", "tushare_stk_rewards", "stock_basic", "normal", "P1", "full", "20200101", False),
    ("stock_basic", "tushare_stock_basic", "stock_basic", "normal", "P0", "full", "", False),
    ("stock_company", "tushare_stock_company", "stock_basic", "normal", "P0", "full", "", False),
    ("stock_hsgt", "tushare_stock_hsgt", "stock_basic", "normal", "P1", "full", "", False),
    ("stock_st", "tushare_stock_st", "stock_basic", "special", "P2", "incremental", "20200101", False),
    ("trade_cal", "tushare_trade_cal", "stock_basic", "normal", "P0", "full", "", False),

    # stock_daily (normal=4, special=10)
    ("adj_factor", "tushare_adj_factor", "stock_daily", "normal", "P0", "incremental", "20200101", False),
    ("bak_daily", "tushare_bak_daily", "stock_daily", "special", "P3", "incremental", "20200101", False),
    ("daily", "tushare_stock_daily", "stock_daily", "normal", "P0", "incremental", "20200101", False),
    ("daily_basic", "tushare_daily_basic", "stock_daily", "special", "P0", "incremental", "20200101", False),
    ("ggt_daily", "tushare_ggt_daily", "stock_daily", "special", "P2", "incremental", "20200101", False),
    ("ggt_monthly", "tushare_ggt_monthly", "stock_daily", "special", "P3", "incremental", "20200101", False),
    ("ggt_top10", "tushare_ggt_top10", "stock_daily", "special", "P2", "incremental", "20200101", False),
    ("hsgt_top10", "tushare_hsgt_top10", "stock_daily", "special", "P2", "incremental", "20200101", False),
    ("monthly", "tushare_stock_monthly", "stock_daily", "normal", "P1", "incremental", "20200101", False),
    ("stk_limit", "tushare_stk_limit", "stock_daily", "special", "P1", "incremental", "20200101", False),
    ("stk_week_month_adj", "tushare_stk_week_month_adj", "stock_daily", "special", "P2", "incremental", "20200101", False),
    ("stk_weekly_monthly", "tushare_stk_weekly_monthly", "stock_daily", "special", "P2", "incremental", "20200101", False),
    ("suspend_d", "tushare_suspend_d", "stock_daily", "normal", "P1", "incremental", "20200101", False),
    ("weekly", "tushare_stock_weekly", "stock_daily", "normal", "P0", "incremental", "20200101", False),

    # stock_financial (special=10)
    ("balancesheet", "tushare_balancesheet", "stock_financial", "special", "P0", "incremental", "20200101", False),
    ("cashflow", "tushare_cashflow", "stock_financial", "special", "P0", "incremental", "20200101", False),
    ("disclosure_date", "tushare_disclosure_date", "stock_financial", "special", "P2", "full", "20200101", False),
    ("dividend", "tushare_dividend", "stock_financial", "special", "P1", "incremental", "20200101", False),
    ("express", "tushare_express", "stock_financial", "special", "P2", "incremental", "20200101", False),
    ("fina_audit", "tushare_fina_audit", "stock_financial", "special", "P1", "incremental", "20200101", False),
    ("fina_indicator", "tushare_fina_indicator", "stock_financial", "special", "P0", "incremental", "20200101", False),
    ("fina_mainbz", "tushare_fina_mainbz", "stock_financial", "special", "P1", "incremental", "20200101", False),
    ("forecast", "tushare_forecast", "stock_financial", "special", "P2", "incremental", "20200101", False),
    ("income", "tushare_income", "stock_financial", "special", "P0", "incremental", "20200101", False),

    # stock_limit_board (special=22)
    ("dc_daily", "tushare_dc_daily", "stock_limit_board", "special", "P1", "incremental", "20200101", False),
    ("dc_hot", "tushare_dc_hot", "stock_limit_board", "special", "P2", "incremental", "20200101", False),
    ("dc_index", "tushare_dc_index", "stock_limit_board", "special", "P1", "full", "", False),
    ("dc_member", "tushare_dc_member", "stock_limit_board", "special", "P2", "full", "", False),
    ("hm_detail", "tushare_hm_detail", "stock_limit_board", "special", "P2", "incremental", "20220801", False),
    ("hm_list", "tushare_hm_list", "stock_limit_board", "special", "P2", "full", "", False),
    ("kpl_concept_cons", "tushare_kpl_concept_cons", "stock_limit_board", "special", "P3", "full", "", False),
    ("kpl_list", "tushare_kpl_list", "stock_limit_board", "special", "P2", "incremental", "20200101", False),
    ("limit_cpt_list", "tushare_limit_cpt_list", "stock_limit_board", "special", "P2", "incremental", "20200101", False),
    ("limit_list_d", "tushare_limit_list_d", "stock_limit_board", "special", "P1", "incremental", "20200101", False),
    ("limit_list_ths", "tushare_limit_list_ths", "stock_limit_board", "special", "P2", "incremental", "20231101", False),
    ("limit_step", "tushare_limit_step", "stock_limit_board", "special", "P1", "incremental", "20200101", False),
    ("stk_auction", "tushare_stk_auction", "stock_limit_board", "special", "P2", "incremental", "20200101", False),
    ("tdx_daily", "tushare_tdx_daily", "stock_limit_board", "special", "P2", "incremental", "20200101", False),
    ("tdx_index", "tushare_tdx_index", "stock_limit_board", "special", "P2", "full", "", False),
    ("tdx_member", "tushare_tdx_member", "stock_limit_board", "special", "P2", "full", "", False),
    ("ths_daily", "tushare_ths_daily", "stock_limit_board", "special", "P1", "incremental", "20200101", False),
    ("ths_hot", "tushare_ths_hot", "stock_limit_board", "special", "P2", "incremental", "20200101", False),
    ("ths_index", "tushare_ths_index", "stock_limit_board", "special", "P1", "full", "", False),
    ("ths_member", "tushare_ths_member", "stock_limit_board", "special", "P1", "full", "", False),
    ("top_inst", "tushare_top_inst", "stock_limit_board", "special", "P2", "incremental", "20200101", False),
    ("top_list", "tushare_top_list", "stock_limit_board", "special", "P1", "incremental", "20200101", False),

    # stock_moneyflow (special=8)
    ("moneyflow", "tushare_moneyflow", "stock_moneyflow", "special", "P1", "incremental", "20200101", False),
    ("moneyflow_cnt_ths", "tushare_moneyflow_cnt_ths", "stock_moneyflow", "special", "P2", "incremental", "20200101", False),
    ("moneyflow_dc", "tushare_moneyflow_dc", "stock_moneyflow", "special", "P2", "incremental", "20230911", False),
    ("moneyflow_hsgt", "tushare_moneyflow_hsgt", "stock_moneyflow", "special", "P1", "incremental", "20200101", False),
    ("moneyflow_ind_dc", "tushare_moneyflow_ind_dc", "stock_moneyflow", "special", "P2", "incremental", "20200101", False),
    ("moneyflow_ind_ths", "tushare_moneyflow_ind_ths", "stock_moneyflow", "special", "P2", "incremental", "20200101", False),
    ("moneyflow_mkt_dc", "tushare_moneyflow_mkt_dc", "stock_moneyflow", "special", "P2", "incremental", "20200101", False),
    ("moneyflow_ths", "tushare_moneyflow_ths", "stock_moneyflow", "special", "P2", "incremental", "20200101", False),

    # stock_reference (special=14)
    ("block_trade", "tushare_block_trade", "stock_reference", "special", "P1", "incremental", "20200101", False),
    ("margin", "tushare_margin", "stock_reference", "special", "P1", "incremental", "20200101", False),
    ("margin_detail", "tushare_margin_detail", "stock_reference", "special", "P1", "incremental", "20200101", False),
    ("margin_secs", "tushare_margin_secs", "stock_reference", "special", "P2", "incremental", "20200101", False),
    ("pledge_detail", "tushare_pledge_detail", "stock_reference", "special", "P2", "incremental", "20200101", False),
    ("pledge_stat", "tushare_pledge_stat", "stock_reference", "special", "P2", "incremental", "20200101", False),
    ("repurchase", "tushare_repurchase", "stock_reference", "special", "P2", "incremental", "20200101", False),
    ("share_float", "tushare_share_float", "stock_reference", "special", "P2", "incremental", "20200101", False),
    ("slb_len", "tushare_slb_len", "stock_reference", "special", "P2", "incremental", "20200101", False),
    ("stk_account_old", "tushare_stk_account_old", "stock_reference", "special", "P3", "full", "20080101", False),
    ("stk_holdernumber", "tushare_stk_holdernumber", "stock_reference", "special", "P2", "incremental", "20200101", False),
    ("stk_holdertrade", "tushare_stk_holdertrade", "stock_reference", "special", "P2", "incremental", "20200101", False),
    ("top10_floatholders", "tushare_top10_floatholders", "stock_reference", "special", "P2", "incremental", "20200101", False),
    ("top10_holders", "tushare_top10_holders", "stock_reference", "special", "P2", "incremental", "20200101", False),

    # stock_special (special=13)
    ("broker_recommend", "tushare_broker_recommend", "stock_special", "special", "P2", "incremental", "20200101", False),
    ("ccass_hold", "tushare_ccass_hold", "stock_special", "special", "P2", "incremental", "20200101", False),
    ("ccass_hold_detail", "tushare_ccass_hold_detail", "stock_special", "special", "P2", "incremental", "20200101", False),
    ("cyq_chips", "tushare_cyq_chips", "stock_special", "special", "P2", "incremental", "20200101", False),
    ("cyq_perf", "tushare_cyq_perf", "stock_special", "special", "P1", "incremental", "20200101", False),
    ("hk_hold", "tushare_hk_hold", "stock_special", "special", "P2", "incremental", "20200101", False),
    ("report_rc", "tushare_report_rc", "stock_special", "special", "P2", "incremental", "20200101", False),
    ("stk_ah_comparison", "tushare_stk_ah_comparison", "stock_special", "special", "P2", "incremental", "20200101", False),
    ("stk_auction_c", "tushare_stk_auction_c", "stock_special", "special", "P2", "incremental", "20200101", False),
    ("stk_auction_o", "tushare_stk_auction_o", "stock_special", "special", "P2", "incremental", "20200101", False),
    ("stk_factor_pro", "tushare_stk_factor_pro", "stock_special", "special", "P1", "incremental", "20200101", False),
    ("stk_nineturn", "tushare_stk_nineturn", "stock_special", "special", "P2", "incremental", "20230101", False),
    ("stk_surv", "tushare_stk_surv", "stock_special", "special", "P2", "incremental", "20200101", False),

    # tmt (normal=8)
    ("film_record", "tushare_film_record", "tmt", "normal", "P3", "incremental", "20200101", False),
    ("teleplay_record", "tushare_teleplay_record", "tmt", "normal", "P3", "incremental", "20200101", False),
    ("tmt_twincome", "tushare_tmt_twincome", "tmt", "normal", "P3", "incremental", "20200101", False),
    ("tmt_twincomedetail", "tushare_tmt_twincomedetail", "tmt", "normal", "P3", "incremental", "20200101", False),

    # wealth (normal=2)
    # fund_sales_ratio and fund_sales_vol are already in fund section above

    # ---- PAID interfaces (45, enabled: false) ----
    # minutes (11)
    ("etf_iopv", "tushare_etf_iopv", "etf", "special", "P3", "incremental", "", True),
    ("ft_mins", "tushare_ft_mins", "futures", "special", "P3", "incremental", "", True),
    ("hk_adjfactor", "tushare_hk_adjfactor", "hk", "special", "P3", "incremental", "", True),
    ("hk_balancesheet", "tushare_hk_balancesheet", "hk", "special", "P3", "incremental", "", True),
    ("hk_basic", "tushare_hk_basic", "hk", "special", "P3", "full", "", True),
    ("hk_cashflow", "tushare_hk_cashflow", "hk", "special", "P3", "incremental", "", True),
    ("hk_daily", "tushare_hk_daily", "hk", "special", "P3", "incremental", "", True),
    ("hk_daily_adj", "tushare_hk_daily_adj", "hk", "special", "P3", "incremental", "", True),
    ("hk_fina_indicator", "tushare_hk_fina_indicator", "hk", "special", "P3", "incremental", "", True),
    ("hk_income", "tushare_hk_income", "hk", "special", "P3", "incremental", "", True),
    ("hk_mins", "tushare_hk_mins", "hk", "special", "P3", "incremental", "", True),
    ("hk_tradecal", "tushare_hk_tradecal", "hk", "special", "P3", "full", "", True),
    ("idx_mins", "tushare_idx_mins", "index", "special", "P3", "incremental", "", True),
    ("opt_mins", "tushare_opt_mins", "options", "special", "P3", "incremental", "", True),
    ("rt_etf_k", "tushare_rt_etf_k", "etf", "special", "P3", "incremental", "", True),
    ("rt_fut_min", "tushare_rt_fut_min", "futures", "special", "P3", "incremental", "", True),
    ("rt_hk_k", "tushare_rt_hk_k", "hk", "special", "P3", "incremental", "", True),
    ("rt_idx_k", "tushare_rt_idx_k", "index", "special", "P3", "incremental", "", True),
    ("rt_idx_min", "tushare_rt_idx_min", "index", "special", "P3", "incremental", "", True),
    ("rt_min", "tushare_rt_min", "stock_daily", "special", "P3", "incremental", "", True),
    ("rt_k", "tushare_rt_k", "stock_daily", "special", "P3", "incremental", "", True),
    ("rt_sw_k", "tushare_rt_sw_k", "index", "special", "P3", "incremental", "", True),
    # us (8)
    ("us_basic", "tushare_us_basic", "us", "special", "P3", "full", "", True),
    ("us_balancesheet", "tushare_us_balancesheet", "us", "special", "P3", "incremental", "", True),
    ("us_cashflow", "tushare_us_cashflow", "us", "special", "P3", "incremental", "", True),
    ("us_daily", "tushare_us_daily", "us", "special", "P3", "incremental", "", True),
    ("us_daily_adj", "tushare_us_daily_adj", "us", "special", "P3", "incremental", "", True),
    ("us_fina_indicator", "tushare_us_fina_indicator", "us", "special", "P3", "incremental", "", True),
    ("us_income", "tushare_us_income", "us", "special", "P3", "incremental", "", True),
    ("us_tradecal", "tushare_us_tradecal", "us", "special", "P3", "full", "", True),
    # other paid (remaining to reach 45)
    ("us_adjfactor", "tushare_us_adjfactor", "us", "special", "P3", "incremental", "", True),
    ("hk_dividend", "tushare_hk_dividend", "hk", "special", "P3", "incremental", "", True),
    ("us_dividend", "tushare_us_dividend", "us", "special", "P3", "incremental", "", True),
    ("hk_weekly", "tushare_hk_weekly", "hk", "special", "P3", "incremental", "", True),
    ("us_weekly", "tushare_us_weekly", "us", "special", "P3", "incremental", "", True),
    ("hk_monthly", "tushare_hk_monthly", "hk", "special", "P3", "incremental", "", True),
    ("us_monthly", "tushare_us_monthly", "us", "special", "P3", "incremental", "", True),
    ("hk_moneyflow", "tushare_hk_moneyflow", "hk", "special", "P3", "incremental", "", True),
    ("us_moneyflow", "tushare_us_moneyflow", "us", "special", "P3", "incremental", "", True),
    ("hk_top10", "tushare_hk_top10", "hk", "special", "P3", "incremental", "", True),
    ("us_top10", "tushare_us_top10", "us", "special", "P3", "incremental", "", True),
    ("film_boxoffice", "tushare_film_boxoffice", "tmt", "normal", "P3", "incremental", "", True),
    ("film_daily", "tushare_film_daily", "tmt", "normal", "P3", "incremental", "", True),
    ("cyq_d", "tushare_cyq_d", "stock_special", "special", "P3", "incremental", "", True),
    ("hk_hold_detail", "tushare_hk_hold_detail", "stock_special", "special", "P3", "incremental", "", True),
]

# Batch assignment map based on design doc §7
# A: Daily Quotes, B: Money Flow & Reference, C: Limit Board & Special,
# D: Macro / Financial period_loop / TMT, saturday: per_symbol_period, reference: basic/cal
BATCH_MAP = {
    # stock_basic - reference
    "stock_basic": "reference", "trade_cal": "reference", "stock_company": "reference",
    "stock_hsgt": "reference", "bse_mapping": "reference",
    "stk_managers": "reference", "stk_rewards": "reference",
    "namechange": "reference", "new_share": "reference",
    "index_basic": "reference", "index_classify": "reference", "index_member_all": "reference",
    "ci_index_member": "reference",
    "fund_basic": "reference", "fund_company": "reference",
    "etf_basic": "reference", "etf_index": "reference",
    "fut_basic": "reference", "fut_trade_cal": "reference",
    "opt_basic": "reference", "cb_basic_info_placeholder": "reference",
    "fx_obasic": "reference", "sge_basic": "reference",
    "disclosure_date": "reference",
    "ths_index": "reference", "ths_member": "reference",
    "dc_index": "reference", "dc_member": "reference",
    "hm_list": "reference", "kpl_concept_cons": "reference",
    "tdx_index": "reference", "tdx_member": "reference",

    # saturday - per_symbol_period long-tail (4 interfaces confirmed in design doc)
    "fina_mainbz": "saturday", "top10_holders": "saturday",
    "top10_floatholders": "saturday", "stk_holdertrade": "saturday",

    # D - Macro / Financial period_loop / TMT / wealth
    "income": "D", "balancesheet": "D", "cashflow": "D", "fina_indicator": "D",
    "fina_audit": "D", "dividend": "D", "forecast": "D", "express": "D",
    "cn_gdp": "D", "cn_cpi": "D", "cn_ppi": "D", "cn_pmi": "D", "cn_m": "D",
    "sf_month": "D", "shibor": "D", "shibor_lpr": "D", "shibor_quote": "D",
    "libor": "D", "hibor": "D", "wz_index": "D", "gz_index": "D",
    "us_tycr": "D", "us_tbr": "D", "us_trycr": "D", "us_tltr": "D", "us_trltr": "D",
    "bo_cinema": "D", "bo_daily": "D", "bo_weekly": "D", "bo_monthly": "D",
    "film_record": "D", "teleplay_record": "D",
    "tmt_twincome": "D", "tmt_twincomedetail": "D",
    "fund_sales_ratio": "D", "fund_sales_vol": "D",

    # C - Limit Board & Special
    "ths_daily": "C", "ths_hot": "C",
    "dc_daily": "C", "dc_hot": "C",
    "hm_detail": "C", "kpl_list": "C", "tdx_daily": "C",
    "limit_list_d": "C", "limit_list_ths": "C", "limit_step": "C",
    "limit_cpt_list": "C", "top_inst": "C", "top_list": "C",
    "stk_auction": "C",
    "hk_hold": "C", "ccass_hold": "C", "ccass_hold_detail": "C",
    "stk_surv": "C", "stk_nineturn": "C",
    "cyq_perf": "C", "cyq_chips": "C",
    "stk_factor_pro": "C", "report_rc": "C", "broker_recommend": "C",
    "stk_ah_comparison": "C", "stk_auction_o": "C", "stk_auction_c": "C",
    "moneyflow_ind_ths": "C", "moneyflow_ind_dc": "C",
    "moneyflow_mkt_dc": "C", "moneyflow_ths": "C", "moneyflow_dc": "C",
    "moneyflow_cnt_ths": "C",

    # B - Money Flow & Reference
    "moneyflow": "B", "moneyflow_hsgt": "B",
    "margin": "B", "margin_detail": "B", "margin_secs": "B",
    "block_trade": "B", "pledge_detail": "B", "pledge_stat": "B",
    "repurchase": "B", "share_float": "B", "slb_len": "B",
    "stk_holdernumber": "B",
    "stk_premarket": "B", "stock_st": "B", "st": "B",
    "daily_basic": "B", "suspend_d": "B",
    "stk_limit": "B",

    # A - Daily Quotes (the rest default to A)
}

# Fetch strategy map
STRATEGY_MAP = {
    "stock_basic": "full_once", "trade_cal": "full_once", "stock_company": "full_once",
    "stock_hsgt": "full_once", "bse_mapping": "full_once",
    "stk_managers": "full_once", "stk_rewards": "full_once",
    "namechange": "full_once", "new_share": "date_loop",
    "index_basic": "full_once", "index_classify": "full_once",
    "index_member_all": "full_once", "ci_index_member": "full_once",
    "fund_basic": "full_once", "fund_company": "full_once",
    "etf_basic": "full_once", "etf_index": "full_once",
    "fut_basic": "full_once", "fut_trade_cal": "full_once",
    "opt_basic": "full_once", "cb_rate": "full_once",
    "fx_obasic": "full_once", "sge_basic": "full_once",
    "disclosure_date": "full_once",
    "ths_index": "full_once", "ths_member": "full_once",
    "dc_index": "full_once", "dc_member": "full_once",
    "hm_list": "full_once", "kpl_concept_cons": "full_once",
    "tdx_index": "full_once", "tdx_member": "full_once",
    "cb_basic_info_placeholder": "full_once",
    "stk_account_old": "full_once", "bak_basic": "full_once",
    # period_loop
    "income": "period_loop", "balancesheet": "period_loop",
    "cashflow": "period_loop", "fina_indicator": "period_loop",
    "fina_audit": "period_loop", "dividend": "period_loop",
    "forecast": "period_loop", "express": "period_loop",
    # per_symbol_period (saturday)
    "fina_mainbz": "per_symbol_period", "top10_holders": "per_symbol_period",
    "top10_floatholders": "per_symbol_period", "stk_holdertrade": "per_symbol_period",
    # monthly_window
    "fund_nav": "monthly_window", "index_weight": "monthly_window",
    # offset_paging (moneyflow family)
    "moneyflow": "offset_paging", "moneyflow_hsgt": "offset_paging",
    "moneyflow_ind_ths": "offset_paging", "moneyflow_ind_dc": "offset_paging",
    "moneyflow_mkt_dc": "offset_paging", "moneyflow_ths": "offset_paging",
    "moneyflow_dc": "offset_paging", "moneyflow_cnt_ths": "offset_paging",
}


def derive_strategy(name: str, mode: str) -> str:
    """Derive fetch strategy from name/mode with fallback to defaults."""
    if name in STRATEGY_MAP:
        return STRATEGY_MAP[name]
    if mode == "full":
        return "full_once"
    return "date_loop"


def derive_batch(name: str, category: str, strategy: str) -> str:
    """Derive batch from name with fallback."""
    if name in BATCH_MAP:
        return BATCH_MAP[name]
    if strategy == "full_once":
        return "reference"
    if category in ("macro", "tmt", "wealth"):
        return "D"
    if category in ("stock_moneyflow",):
        return "B"
    if category in ("stock_limit_board", "stock_special"):
        return "C"
    if category in ("stock_reference",):
        return "B"
    # default: A for stock_daily, index, etf, futures, bonds, options, forex, spot
    return "A"


def derive_partition(name: str, strategy: str, category: str) -> str:
    """Derive ClickHouse partition key."""
    if strategy in ("date_loop",) or category in ("stock_daily", "index", "etf", "futures", "bonds", "forex"):
        return "toYYYYMM(trade_date)"
    if strategy in ("period_loop",) or category == "stock_financial":
        return "toYYYYMM(end_date)"
    if strategy == "monthly_window":
        return "toYYYYMM(cal_date)"
    if category in ("stock_limit_board", "stock_moneyflow", "stock_reference", "stock_special"):
        if any(x in name for x in ("daily", "list", "flow", "detail", "limit", "top")):
            return "toYYYYMM(trade_date)"
    # default for full_once / reference
    return "tuple()"


def derive_order_by(strategy: str, category: str) -> str:
    """Derive ORDER BY clause."""
    if strategy == "per_symbol_period":
        return "ts_code, period"
    if strategy in ("date_loop", "offset_paging"):
        if category in ("index", "etf"):
            return "ts_code, trade_date"
        return "ts_code, trade_date"
    if strategy == "period_loop":
        return "ts_code, end_date"
    if strategy == "monthly_window":
        return "ts_code, cal_date"
    if strategy == "full_once":
        return "ts_code"
    return "trade_date"


def derive_dedupe_key(name: str) -> str:
    """Derive deduplication key."""
    if "trade_date" in name or name in ("daily", "weekly", "monthly", "adj_factor", "daily_basic"):
        return "trade_date"
    if "end_date" in name or name in ("income", "balancesheet", "cashflow", "fina_indicator"):
        return "end_date"
    return ""


# ============================================================
# Generate YAML files grouped by category
# ============================================================

def generate_yaml(entry: tuple) -> dict:
    name, table, category, bucket, priority, mode, start_date, is_paid = entry
    strategy = derive_strategy(name, mode)
    batch = derive_batch(name, category, strategy)
    partition = derive_partition(name, strategy, category)
    order = derive_order_by(strategy, category)
    dedupe = derive_dedupe_key(name)

    doc = {
        "name": name,
        "table": table,
        "enabled": not is_paid,
        "priority": priority,
        "mode": mode,
        "freq_bucket": bucket,
        "start_date": start_date if start_date else None,
        "fetch_strategy": {
            "kind": strategy,
            "date_field": "trade_date" if strategy in ("date_loop",) else "end_date" if strategy in ("period_loop",) else None,
            "step": None,
            "symbol_source": "tushare_stock_basic" if strategy == "per_symbol_period" else None,
        },
        "pagination": None,
        "partition_key": partition,
        "order_by": order,
        "dedupe_key": dedupe if dedupe else None,
        "required_params": [],
        "fields": [],
        "schema_overrides": {},
        "batch": batch,
    }

    # Remove None values for cleaner YAML
    def clean(d):
        if isinstance(d, dict):
            return {k: clean(v) for k, v in d.items() if v is not None}
        if isinstance(d, list):
            return [clean(x) for x in d]
        return d

    return clean(doc)


def main():
    output_dir = Path("config/interfaces")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group by category for file organization
    by_category: dict[str, list[dict]] = {}
    for entry in INTERFACES:
        category = entry[2]
        doc = generate_yaml(entry)
        by_category.setdefault(category, []).append(doc)

    # Schema file for reference
    schema_doc = {
        "$schema": "interface-spec-v1",
        "description": "Interface specification schema - see design doc §1",
        "fields": {
            "name": "Tushare API interface name",
            "table": "ClickHouse target table name (tushare.*)",
            "enabled": "Whether this interface is active",
            "priority": "P0|P1|P2|P3",
            "mode": "full|incremental",
            "freq_bucket": "normal|special",
            "start_date": "Backfill start YYYYMMDD",
            "fetch_strategy": {
                "kind": "full_once|date_loop|period_loop|monthly_window|per_symbol_period|offset_paging",
                "date_field": "trade_date|end_date|cal_date",
                "step": "days per fetch (for date_loop)",
                "symbol_source": "source for ts_code list (for per_symbol_period)",
            },
            "batch": "A|B|C|D|saturday|reference",
        },
    }

    _schema_path = output_dir / "_schema.yaml"
    with open(_schema_path, "w", encoding="utf-8") as f:
        yaml.dump(schema_doc, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)

    # Write category files
    file_map = {
        "bonds": "bonds.yaml",
        "etf": "etf.yaml",
        "forex": "forex.yaml",
        "fund": "fund.yaml",
        "futures": "futures.yaml",
        "index": "index.yaml",
        "macro": "macro.yaml",
        "options": "options.yaml",
        "spot": "spot.yaml",
        "stock_basic": "stock_basic.yaml",
        "stock_daily": "stock_daily.yaml",
        "stock_financial": "stock_financial.yaml",
        "stock_limit_board": "stock_limit_board.yaml",
        "stock_moneyflow": "stock_moneyflow.yaml",
        "stock_reference": "stock_reference.yaml",
        "stock_special": "stock_special.yaml",
        "tmt": "tmt.yaml",
        # paid interfaces grouped by original category
        "hk": "paid.yaml",
        "us": "paid.yaml",
    }

    # Group paid interfaces into a single paid.yaml
    paid_docs = []
    for cat in ["hk", "us"]:
        if cat in by_category:
            paid_docs.extend(by_category.pop(cat))
    # Also catch any remaining enabled=False entries
    for cat, docs in list(by_category.items()):
        remaining = [d for d in docs if not d.get("enabled", True)]
        if remaining:
            paid_docs.extend(remaining)
            by_category[cat] = [d for d in docs if d.get("enabled", True)]
            if not by_category[cat]:
                del by_category[cat]

    if paid_docs:
        paid_path = output_dir / "paid.yaml"
        with open(paid_path, "w", encoding="utf-8") as f:
            f.write("# Paid interfaces (enabled: false) — enable when subscribed\n")
            f.write(f"# {len(paid_docs)} interfaces requiring additional payment\n---\n")
            yaml.dump_all(paid_docs, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)

    total = 0
    for category, docs in sorted(by_category.items()):
        filename = file_map.get(category, f"{category}.yaml")
        path = output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {category} interfaces\n")
            f.write(f"# {len(docs)} interfaces in this category\n---\n")
            yaml.dump_all(docs, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)
        total += len(docs)
        print(f"  {filename}: {len(docs)} interfaces")

    total += len(paid_docs) if paid_docs else 0
    print(f"\nTotal: {total} interfaces generated ({len(by_category)} category files)")
    print(f"Paid (disabled): {len(paid_docs) if paid_docs else 0}")


if __name__ == "__main__":
    main()
