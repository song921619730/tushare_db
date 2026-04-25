# Tushare Pro 10,000 积分权限可用数据清单

> 生成日期: 2026-04-24
> 权限等级: 10,000 积分

## 总览

- **可用接口**: 182 个
- **付费接口**: 45 个（需额外付费开通）
- **数据库表**: 对应 182 张表

## 可用接口详细清单（182 个）

### bonds -- 债券数据（15 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| cb_basic | tushare_cb_basic | P2 | full | normal | N/A |
| cb_daily | tushare_cb_daily | P2 | incremental | normal | 20200101 |
| cb_issue | tushare_cb_issue | P2 | incremental | normal | 20200101 |
| cb_call | tushare_cb_call | P3 | incremental | normal | 20200101 |
| cb_share | tushare_cb_share | P2 | incremental | normal | 20200101 |
| cb_rate | tushare_cb_rate | P3 | full | normal | 20200101 |
| cb_price_chg | tushare_cb_price_chg | P3 | incremental | normal | 20200101 |
| cb_factor_pro | tushare_cb_factor_pro | P2 | incremental | special | 20200101 |
| bond_blk | tushare_bond_blk | P3 | incremental | normal | 20200101 |
| bond_blk_detail | tushare_bond_blk_detail | P3 | incremental | normal | 20200101 |
| repo_daily | tushare_repo_daily | P2 | incremental | normal | 20200101 |
| yc_cb | tushare_yc_cb | P3 | incremental | normal | 20200101 |
| eco_cal | tushare_eco_cal | P3 | incremental | normal | 20200101 |
| bc_otcqt | tushare_bc_otcqt | P3 | incremental | normal | 20200101 |
| bc_bestotcqt | tushare_bc_bestotcqt | P3 | incremental | normal | 20200101 |

### etf -- ETF/基金数据（5 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| etf_basic | tushare_etf_basic | P1 | full | normal | N/A |
| etf_index | tushare_etf_index | P2 | full | normal | N/A |
| fund_daily | tushare_fund_daily | P1 | incremental | normal | 20200101 |
| fund_adj | tushare_fund_adj | P2 | incremental | normal | 20200101 |
| etf_share_size | tushare_etf_share_size | P2 | incremental | special | 20200101 |

### forex -- 外汇数据（2 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| fx_obasic | tushare_fx_obasic | P3 | full | normal | N/A |
| fx_daily | tushare_fx_daily | P3 | incremental | normal | 20200101 |

### fund -- 公募基金数据（8 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| fund_basic | tushare_fund_basic | P1 | full | normal | N/A |
| fund_nav | tushare_fund_nav | P1 | incremental | normal | 20200101 |
| fund_div | tushare_fund_div | P2 | incremental | normal | 20200101 |
| fund_portfolio | tushare_fund_portfolio | P2 | incremental | normal | 20200101 |
| fund_share | tushare_fund_share | P2 | incremental | normal | 20200101 |
| fund_company | tushare_fund_company | P2 | full | normal | N/A |
| fund_manager | tushare_fund_manager | P2 | incremental | normal | 20200101 |
| fund_factor_pro | tushare_fund_factor_pro | P2 | incremental | special | 20200101 |

### futures -- 期货数据（11 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| fut_basic | tushare_fut_basic | P2 | full | normal | N/A |
| fut_daily | tushare_fut_daily | P2 | incremental | normal | 20200101 |
| fut_holding | tushare_fut_holding | P2 | incremental | normal | 20200101 |
| fut_wsr | tushare_fut_wsr | P3 | incremental | normal | 20200101 |
| fut_settle | tushare_fut_settle | P3 | incremental | normal | 20200101 |
| fut_mapping | tushare_fut_mapping | P2 | incremental | normal | 20200101 |
| ft_limit | tushare_ft_limit | P2 | incremental | special | 20200101 |
| fut_weekly_detail | tushare_fut_weekly_detail | P3 | incremental | normal | 20200101 |
| fut_weekly_monthly | tushare_fut_weekly_monthly | P2 | incremental | normal | 20200101 |
| fut_index_daily | tushare_fut_index_daily | P2 | incremental | normal | 20200101 |
| fut_trade_cal | tushare_fut_trade_cal | P2 | full | normal | N/A |

### index -- 指数数据（15 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| index_basic | tushare_index_basic | P0 | full | normal | N/A |
| index_daily | tushare_index_daily | P0 | incremental | special | 20200101 |
| index_weekly | tushare_index_weekly | P1 | incremental | special | 20200101 |
| index_monthly | tushare_index_monthly | P1 | incremental | special | 20200101 |
| index_dailybasic | tushare_index_dailybasic | P1 | incremental | special | 20200101 |
| index_weight | tushare_index_weight | P1 | incremental | special | 20200101 |
| index_classify | tushare_index_classify | P1 | full | special | N/A |
| index_member_all | tushare_index_member_all | P2 | full | special | N/A |
| sw_daily | tushare_sw_daily | P2 | incremental | special | 20200101 |
| ci_daily | tushare_ci_daily | P2 | incremental | special | 20200101 |
| ci_index_member | tushare_ci_index_member | P2 | full | special | N/A |
| daily_info | tushare_daily_info | P2 | incremental | special | 20200101 |
| sz_daily_info | tushare_sz_daily_info | P2 | incremental | special | 20200101 |
| idx_factor_pro | tushare_idx_factor_pro | P2 | incremental | special | 20200101 |
| index_global | tushare_index_global | P2 | incremental | special | 20200101 |

### macro -- 宏观经济数据（18 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| cn_gdp | tushare_cn_gdp | P3 | incremental | normal | 20200101 |
| cn_cpi | tushare_cn_cpi | P3 | incremental | normal | 20200101 |
| cn_ppi | tushare_cn_ppi | P3 | incremental | normal | 20200101 |
| cn_pmi | tushare_cn_pmi | P3 | incremental | normal | 20200101 |
| cn_m | tushare_cn_m | P3 | incremental | normal | 20200101 |
| sf_month | tushare_sf_month | P3 | incremental | normal | 20200101 |
| shibor | tushare_shibor | P3 | incremental | normal | 20200101 |
| shibor_lpr | tushare_shibor_lpr | P3 | incremental | normal | 20200101 |
| shibor_quote | tushare_shibor_quote | P3 | incremental | normal | 20200101 |
| libor | tushare_libor | P3 | incremental | normal | 20200101 |
| hibor | tushare_hibor | P3 | incremental | normal | 20200101 |
| wz_index | tushare_wz_index | P3 | incremental | normal | 20200101 |
| gz_index | tushare_gz_index | P3 | incremental | normal | 20200101 |
| us_tycr | tushare_us_tycr | P3 | incremental | normal | 20200101 |
| us_tbr | tushare_us_tbr | P3 | incremental | normal | 20200101 |
| us_trycr | tushare_us_trycr | P3 | incremental | normal | 20200101 |
| us_tltr | tushare_us_tltr | P3 | incremental | normal | 20200101 |
| us_trltr | tushare_us_trltr | P3 | incremental | normal | 20200101 |

### options -- 期权数据（2 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| opt_basic | tushare_opt_basic | P2 | full | normal | N/A |
| opt_daily | tushare_opt_daily | P2 | incremental | normal | 20200101 |

### spot -- 现货数据（2 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| sge_basic | tushare_sge_basic | P3 | full | normal | N/A |
| sge_daily | tushare_sge_daily | P3 | incremental | normal | 20200101 |

### stock_basic -- 股票基础信息（13 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| stock_basic | tushare_stock_basic | P0 | full | normal | N/A |
| trade_cal | tushare_trade_cal | P0 | full | normal | N/A |
| stock_company | tushare_stock_company | P0 | full | normal | N/A |
| stk_managers | tushare_stk_managers | P1 | full | normal | 20200101 |
| stk_rewards | tushare_stk_rewards | P1 | full | normal | 20200101 |
| namechange | tushare_namechange | P2 | full | normal | 20200101 |
| new_share | tushare_new_share | P1 | incremental | normal | 20200101 |
| stk_premarket | tushare_stk_premarket | P2 | incremental | special | 20200101 |
| stock_st | tushare_stock_st | P2 | incremental | special | 20200101 |
| st | tushare_st | P2 | incremental | special | 20200101 |
| stock_hsgt | tushare_stock_hsgt | P1 | full | normal | N/A |
| bse_mapping | tushare_bse_mapping | P2 | full | normal | N/A |
| bak_basic | tushare_bak_basic | P3 | full | special | 20160101 |

### stock_daily -- 股票行情数据（14 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| daily | tushare_stock_daily | P0 | incremental | normal | 20200101 |
| weekly | tushare_stock_weekly | P0 | incremental | normal | 20200101 |
| monthly | tushare_stock_monthly | P1 | incremental | normal | 20200101 |
| adj_factor | tushare_adj_factor | P0 | incremental | normal | 20200101 |
| daily_basic | tushare_daily_basic | P0 | incremental | special | 20200101 |
| suspend_d | tushare_suspend_d | P1 | incremental | normal | 20200101 |
| stk_limit | tushare_stk_limit | P1 | incremental | special | 20200101 |
| ggt_daily | tushare_ggt_daily | P2 | incremental | special | 20200101 |
| ggt_top10 | tushare_ggt_top10 | P2 | incremental | special | 20200101 |
| hsgt_top10 | tushare_hsgt_top10 | P2 | incremental | special | 20200101 |
| bak_daily | tushare_bak_daily | P3 | incremental | special | 20200101 |
| stk_weekly_monthly | tushare_stk_weekly_monthly | P2 | incremental | special | 20200101 |
| stk_week_month_adj | tushare_stk_week_month_adj | P2 | incremental | special | 20200101 |
| ggt_monthly | tushare_ggt_monthly | P3 | incremental | special | 20200101 |

### stock_financial -- 财务数据（10 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| income | tushare_income | P0 | incremental | special | 20200101 |
| balancesheet | tushare_balancesheet | P0 | incremental | special | 20200101 |
| cashflow | tushare_cashflow | P0 | incremental | special | 20200101 |
| fina_indicator | tushare_fina_indicator | P0 | incremental | special | 20200101 |
| fina_audit | tushare_fina_audit | P1 | incremental | special | 20200101 |
| fina_mainbz | tushare_fina_mainbz | P1 | incremental | special | 20200101 |
| dividend | tushare_dividend | P1 | incremental | special | 20200101 |
| forecast | tushare_forecast | P2 | incremental | special | 20200101 |
| express | tushare_express | P2 | incremental | special | 20200101 |
| disclosure_date | tushare_disclosure_date | P2 | full | special | 20200101 |

### stock_limit_board -- 涨跌板/板块数据（22 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| limit_list_d | tushare_limit_list_d | P1 | incremental | special | 20200101 |
| limit_list_ths | tushare_limit_list_ths | P2 | incremental | special | 20231101 |
| limit_step | tushare_limit_step | P1 | incremental | special | 20200101 |
| limit_cpt_list | tushare_limit_cpt_list | P2 | incremental | special | 20200101 |
| top_list | tushare_top_list | P1 | incremental | special | 20200101 |
| top_inst | tushare_top_inst | P2 | incremental | special | 20200101 |
| ths_index | tushare_ths_index | P1 | full | special | N/A |
| ths_daily | tushare_ths_daily | P1 | incremental | special | 20200101 |
| ths_member | tushare_ths_member | P1 | full | special | N/A |
| ths_hot | tushare_ths_hot | P2 | incremental | special | 20200101 |
| dc_index | tushare_dc_index | P1 | full | special | N/A |
| dc_daily | tushare_dc_daily | P1 | incremental | special | 20200101 |
| dc_member | tushare_dc_member | P2 | full | special | N/A |
| dc_hot | tushare_dc_hot | P2 | incremental | special | 20200101 |
| hm_list | tushare_hm_list | P2 | full | special | N/A |
| hm_detail | tushare_hm_detail | P2 | incremental | special | 20220801 |
| kpl_list | tushare_kpl_list | P2 | incremental | special | 20200101 |
| kpl_concept_cons | tushare_kpl_concept_cons | P3 | full | special | N/A |
| tdx_index | tushare_tdx_index | P2 | full | special | N/A |
| tdx_member | tushare_tdx_member | P2 | full | special | N/A |
| tdx_daily | tushare_tdx_daily | P2 | incremental | special | 20200101 |
| stk_auction | tushare_stk_auction | P2 | incremental | special | 20200101 |

### stock_moneyflow -- 资金流向（8 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| moneyflow | tushare_moneyflow | P1 | incremental | special | 20200101 |
| moneyflow_hsgt | tushare_moneyflow_hsgt | P1 | incremental | special | 20200101 |
| moneyflow_ind_ths | tushare_moneyflow_ind_ths | P2 | incremental | special | 20200101 |
| moneyflow_ind_dc | tushare_moneyflow_ind_dc | P2 | incremental | special | 20200101 |
| moneyflow_mkt_dc | tushare_moneyflow_mkt_dc | P2 | incremental | special | 20200101 |
| moneyflow_ths | tushare_moneyflow_ths | P2 | incremental | special | 20200101 |
| moneyflow_dc | tushare_moneyflow_dc | P2 | incremental | special | 20230911 |
| moneyflow_cnt_ths | tushare_moneyflow_cnt_ths | P2 | incremental | special | 20200101 |

### stock_reference -- 融资融券/质押/大宗交易等参考数据（14 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| margin | tushare_margin | P1 | incremental | special | 20200101 |
| margin_detail | tushare_margin_detail | P1 | incremental | special | 20200101 |
| margin_secs | tushare_margin_secs | P2 | incremental | special | 20200101 |
| slb_len | tushare_slb_len | P2 | incremental | special | 20200101 |
| repurchase | tushare_repurchase | P2 | incremental | special | 20200101 |
| pledge_stat | tushare_pledge_stat | P2 | incremental | special | 20200101 |
| pledge_detail | tushare_pledge_detail | P2 | incremental | special | 20200101 |
| share_float | tushare_share_float | P2 | incremental | special | 20200101 |
| block_trade | tushare_block_trade | P1 | incremental | special | 20200101 |
| stk_holdernumber | tushare_stk_holdernumber | P2 | incremental | special | 20200101 |
| stk_holdertrade | tushare_stk_holdertrade | P2 | incremental | special | 20200101 |
| top10_holders | tushare_top10_holders | P2 | incremental | special | 20200101 |
| top10_floatholders | tushare_top10_floatholders | P2 | incremental | special | 20200101 |
| stk_account_old | tushare_stk_account_old | P3 | full | special | 20080101 |

### stock_special -- 特色数据（筹码、AH对比、持仓等）（13 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| hk_hold | tushare_hk_hold | P2 | incremental | special | 20200101 |
| ccass_hold | tushare_ccass_hold | P2 | incremental | special | 20200101 |
| ccass_hold_detail | tushare_ccass_hold_detail | P2 | incremental | special | 20200101 |
| stk_surv | tushare_stk_surv | P2 | incremental | special | 20200101 |
| stk_nineturn | tushare_stk_nineturn | P2 | incremental | special | 20230101 |
| cyq_perf | tushare_cyq_perf | P1 | incremental | special | 20200101 |
| cyq_chips | tushare_cyq_chips | P2 | incremental | special | 20200101 |
| stk_factor_pro | tushare_stk_factor_pro | P1 | incremental | special | 20200101 |
| report_rc | tushare_report_rc | P2 | incremental | special | 20200101 |
| broker_recommend | tushare_broker_recommend | P2 | incremental | special | 20200101 |
| stk_auction_o | tushare_stk_auction_o | P2 | incremental | special | 20200101 |
| stk_auction_c | tushare_stk_auction_c | P2 | incremental | special | 20200101 |
| stk_ah_comparison | tushare_stk_ah_comparison | P2 | incremental | special | 20200101 |

### tmt -- 文娱产业数据（8 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| bo_daily | tushare_bo_daily | P3 | incremental | normal | 20200101 |
| bo_weekly | tushare_bo_weekly | P3 | incremental | normal | 20200101 |
| bo_monthly | tushare_bo_monthly | P3 | incremental | normal | 20200101 |
| bo_cinema | tushare_bo_cinema | P3 | incremental | normal | 20200101 |
| film_record | tushare_film_record | P3 | incremental | normal | 20200101 |
| teleplay_record | tushare_teleplay_record | P3 | incremental | normal | 20200101 |
| tmt_twincome | tushare_tmt_twincome | P3 | incremental | normal | 20200101 |
| tmt_twincomedetail | tushare_tmt_twincomedetail | P3 | incremental | normal | 20200101 |

### wealth -- 财富销售数据（2 个接口）

| 接口名 | 数据库表 | 优先级 | 模式 | 频率 | 补库起始 |
|--------|----------|--------|------|------|----------|
| fund_sales_ratio | tushare_fund_sales_ratio | P3 | incremental | normal | 20200101 |
| fund_sales_vol | tushare_fund_sales_vol | P3 | incremental | normal | 20210101 |

## 付费接口（45 个，未开通）

### etf -- ETF/基金数据（2 个接口）

- **rt_etf_k** -> tushare_rt_etf_k
- **etf_iopv** -> tushare_etf_iopv

### futures -- 期货数据（2 个接口）

- **ft_mins** -> tushare_ft_mins
- **rt_fut_min** -> tushare_rt_fut_min

### hk -- 港股数据（11 个接口）

- **hk_mins** -> tushare_hk_mins
- **rt_hk_k** -> tushare_rt_hk_k
- **hk_basic** -> tushare_hk_basic
- **hk_daily** -> tushare_hk_daily
- **hk_daily_adj** -> tushare_hk_daily_adj
- **hk_adjfactor** -> tushare_hk_adjfactor
- **hk_income** -> tushare_hk_income
- **hk_balancesheet** -> tushare_hk_balancesheet
- **hk_cashflow** -> tushare_hk_cashflow
- **hk_fina_indicator** -> tushare_hk_fina_indicator
- **hk_tradecal** -> tushare_hk_tradecal

### index -- 指数数据（4 个接口）

- **idx_mins** -> tushare_index_mins
- **rt_idx_k** -> tushare_rt_idx_k
- **rt_idx_min** -> tushare_rt_idx_min
- **rt_sw_k** -> tushare_rt_sw_k

### news -- 新闻公告数据（8 个接口）

- **news** -> tushare_news
- **major_news** -> tushare_major_news
- **cctv_news** -> tushare_cctv_news
- **anns_d** -> tushare_anns_d
- **irm_qa_sh** -> tushare_irm_qa_sh
- **irm_qa_sz** -> tushare_irm_qa_sz
- **research_report** -> tushare_research_report
- **npr** -> tushare_npr

### options -- 期权数据（1 个接口）

- **opt_mins** -> tushare_opt_mins

### stock_daily -- 股票行情数据（4 个接口）

- **stk_mins** -> tushare_stock_mins
- **rt_min** -> tushare_rt_min
- **rt_k** -> tushare_rt_k
- **pro_bar** -> tushare_pro_bar

### stock_reference -- 融资融券/质押/大宗交易等参考数据（4 个接口）

- **slb_sec** -> tushare_slb_sec
- **slb_sec_detail** -> tushare_slb_sec_detail
- **slb_len_mm** -> tushare_slb_len_mm
- **stk_account** -> tushare_stk_account

### us -- 美股数据（9 个接口）

- **us_basic** -> tushare_us_basic
- **us_daily** -> tushare_us_daily
- **us_daily_adj** -> tushare_us_daily_adj
- **us_adjfactor** -> tushare_us_adjfactor
- **us_income** -> tushare_us_income
- **us_balancesheet** -> tushare_us_balancesheet
- **us_cashflow** -> tushare_us_cashflow
- **us_fina_indicator** -> tushare_us_fina_indicator
- **us_tradecal** -> tushare_us_tradecal

## 优先级说明

| 优先级 | 含义 | 更新频率 |
|--------|------|----------|
| P0 | 最高优先级 | 每个交易日必更 |
| P1 | 高优先级 | 交易日更新 |
| P2 | 中优先级 | 定期更新 |
| P3 | 低优先级 | 按需更新 |

## 频率限制说明

| 频率类型 | 每分钟调用次数 |
|----------|----------------|
| normal | 500 次/分钟 |
| special | 300 次/分钟 |

## 按优先级统计

### 优先级分布
- P0: 13 个接口
- P1: 34 个接口
- P2: 86 个接口
- P3: 49 个接口

### 频率类型分布
- normal: 84 个接口
- special: 98 个接口

### 同步模式分布
- full: 34 个接口
- incremental: 148 个接口

## 分类统计

| 分类 | 可用接口数 | 描述 |
|------|-----------|------|
| bonds | 15 | 债券数据 |
| etf | 5 | ETF/基金数据 |
| forex | 2 | 外汇数据 |
| fund | 8 | 公募基金数据 |
| futures | 11 | 期货数据 |
| index | 15 | 指数数据 |
| macro | 18 | 宏观经济数据 |
| options | 2 | 期权数据 |
| spot | 2 | 现货数据 |
| stock_basic | 13 | 股票基础信息 |
| stock_daily | 14 | 股票行情数据 |
| stock_financial | 10 | 财务数据 |
| stock_limit_board | 22 | 涨跌板/板块数据 |
| stock_moneyflow | 8 | 资金流向 |
| stock_reference | 14 | 融资融券/质押/大宗交易等参考数据 |
| stock_special | 13 | 特色数据（筹码、AH对比、持仓等） |
| tmt | 8 | 文娱产业数据 |
| wealth | 2 | 财富销售数据 |
