# Tushare Pro 官方调用频率与权限限制完整手册

> 生成日期: 2026-04-25
> 数据来源: [Tushare Pro 官方文档](https://tushare.pro/document/1?doc_id=290)
> 本工具权限: 10,000 积分

---

## 一、积分等级与调用频次对应表

| 积分等级 | 每分钟调用次数 | 每日/总调用限制 | 可用接口范围 |
|:--------:|:-------------:|:---------------:|:-------------|
| **120** (注册) | 50 次/分钟 | 8,000 次/天 | 仅股票非复权日线行情等少数接口 |
| **200** | ~100 次/分钟 | 未明确 | 部分基础数据 |
| **2000** | 200 次/分钟 | 100,000 次/个 API | 约 60% 的 API 可用（含财务、资金流等） |
| **5000** | 500 次/分钟 | 常规数据**无上限** | 约 90% 的 API 可用 |
| **10000** | 500 次/分钟 | 常规数据无上限；**特色数据 300 次/分钟** | 100% 全接口可用 |
| **15000+** | 500 次/分钟 | 特色数据权限进一步放宽 | 全接口 + 更高特色数据限额 |

### 关键说明

1. **积分是门槛，不消耗** — 调用 API 不会扣减积分，积分仅决定你能调用哪些接口以及频率
2. **积分有效期通常为一年** — 到期后可查询 [积分到期查询](https://tushare.pro/document/1?doc_id=307)
3. **部分特殊接口有独立的更高积分门槛** — 详见各接口文档

---

## 二、积分获取途径

| 途径 | 积分奖励 |
|------|:-------:|
| 注册新用户 | +100 |
| 完善个人信息 | +20 |
| 推荐有效用户注册 | +50/人 |
| 提交有效 Bug/建议 | 视情况奖励 |
| 社区贡献/代码贡献 | 视情况奖励 |
| 学生认证 | 免费获取一定积分 ([详情](https://tushare.pro/document/1?doc_id=360)) |
| 赞助 Tushare 社区 | 捐助金额越大，开放权限越多 |

---

## 三、本工具使用的频率限制（10,000 积分）

| 频率类型 | 每分钟调用次数 | 调用间隔 | 接口数量 | 说明 |
|:--------:|:-------------:|:--------:|:-------:|------|
| **normal** | 500 次/分钟 | 0.12 秒 | 84 个 | 标准接口（20 分档） |
| **special** | 300 次/分钟 | 0.20 秒 | 98 个 | 特色接口（200 分档 / 1 万积分档） |
| **超限等待** | — | 5 秒起 | — | 触发限流后等待，指数退避 (2x) |

**退避策略**:
- 触发限流: 等待 5 秒
- 指数退避: 2s → 4s → 8s，最大 60 秒
- 重试状态码: 429, 500, 502, 503, 504

---

## 四、可用接口清单（182 个，按频率类型分类）

### 4.1 normal 频率接口（500 次/分钟，共 84 个）

| 接口名 | 数据库表 | 分类 | 优先级 | 补库起始 |
|--------|----------|------|:------:|----------|
| adj_factor | tushare_adj_factor | stock_daily | P0 | 20200101 |
| bc_bestotcqt | tushare_bc_bestotcqt | bonds | P3 | 20200101 |
| bc_otcqt | tushare_bc_otcqt | bonds | P3 | 20200101 |
| bo_cinema | tushare_bo_cinema | tmt | P3 | 20200101 |
| bo_daily | tushare_bo_daily | tmt | P3 | 20200101 |
| bo_monthly | tushare_bo_monthly | tmt | P3 | 20200101 |
| bo_weekly | tushare_bo_weekly | tmt | P3 | 20200101 |
| bond_blk | tushare_bond_blk | bonds | P3 | 20200101 |
| bond_blk_detail | tushare_bond_blk_detail | bonds | P3 | 20200101 |
| bse_mapping | tushare_bse_mapping | stock_basic | P2 | N/A |
| cb_basic | tushare_cb_basic | bonds | P2 | N/A |
| cb_call | tushare_cb_call | bonds | P3 | 20200101 |
| cb_daily | tushare_cb_daily | bonds | P2 | 20200101 |
| cb_issue | tushare_cb_issue | bonds | P2 | 20200101 |
| cb_price_chg | tushare_cb_price_chg | bonds | P3 | 20200101 |
| cb_rate | tushare_cb_rate | bonds | P3 | 20200101 |
| cb_share | tushare_cb_share | bonds | P2 | 20200101 |
| cn_cpi | tushare_cn_cpi | macro | P3 | 20200101 |
| cn_gdp | tushare_cn_gdp | macro | P3 | 20200101 |
| cn_m | tushare_cn_m | macro | P3 | 20200101 |
| cn_pmi | tushare_cn_pmi | macro | P3 | 20200101 |
| cn_ppi | tushare_cn_ppi | macro | P3 | 20200101 |
| daily | tushare_stock_daily | stock_daily | P0 | 20200101 |
| eco_cal | tushare_eco_cal | bonds | P3 | 20200101 |
| etf_basic | tushare_etf_basic | etf | P1 | N/A |
| etf_index | tushare_etf_index | etf | P2 | N/A |
| fund_adj | tushare_fund_adj | etf | P2 | 20200101 |
| fund_basic | tushare_fund_basic | fund | P1 | N/A |
| fund_company | tushare_fund_company | fund | P2 | N/A |
| fund_daily | tushare_fund_daily | etf | P1 | 20200101 |
| fund_div | tushare_fund_div | fund | P2 | 20200101 |
| fund_manager | tushare_fund_manager | fund | P2 | 20200101 |
| fund_nav | tushare_fund_nav | fund | P1 | 20200101 |
| fund_portfolio | tushare_fund_portfolio | fund | P2 | 20200101 |
| fund_sales_ratio | tushare_fund_sales_ratio | wealth | P3 | 20200101 |
| fund_sales_vol | tushare_fund_sales_vol | wealth | P3 | 20210101 |
| fund_share | tushare_fund_share | fund | P2 | 20200101 |
| fut_basic | tushare_fut_basic | futures | P2 | N/A |
| fut_daily | tushare_fut_daily | futures | P2 | 20200101 |
| fut_holding | tushare_fut_holding | futures | P2 | 20200101 |
| fut_index_daily | tushare_fut_index_daily | futures | P2 | 20200101 |
| fut_mapping | tushare_fut_mapping | futures | P2 | 20200101 |
| fut_settle | tushare_fut_settle | futures | P3 | 20200101 |
| fut_trade_cal | tushare_fut_trade_cal | futures | P2 | N/A |
| fut_weekly_detail | tushare_fut_weekly_detail | futures | P3 | 20200101 |
| fut_weekly_monthly | tushare_fut_weekly_monthly | futures | P2 | 20200101 |
| fut_wsr | tushare_fut_wsr | futures | P3 | 20200101 |
| fx_daily | tushare_fx_daily | forex | P3 | 20200101 |
| fx_obasic | tushare_fx_obasic | forex | P3 | N/A |
| gz_index | tushare_gz_index | macro | P3 | 20200101 |
| hibor | tushare_hibor | macro | P3 | 20200101 |
| index_basic | tushare_index_basic | index | P0 | N/A |
| libor | tushare_libor | macro | P3 | 20200101 |
| monthly | tushare_stock_monthly | stock_daily | P1 | 20200101 |
| namechange | tushare_namechange | stock_basic | P2 | 20200101 |
| new_share | tushare_new_share | stock_basic | P1 | 20200101 |
| opt_basic | tushare_opt_basic | options | P2 | N/A |
| opt_daily | tushare_opt_daily | options | P2 | 20200101 |
| repo_daily | tushare_repo_daily | bonds | P2 | 20200101 |
| sf_month | tushare_sf_month | macro | P3 | 20200101 |
| sge_basic | tushare_sge_basic | spot | P3 | N/A |
| sge_daily | tushare_sge_daily | spot | P3 | 20200101 |
| shibor | tushare_shibor | macro | P3 | 20200101 |
| shibor_lpr | tushare_shibor_lpr | macro | P3 | 20200101 |
| shibor_quote | tushare_shibor_quote | macro | P3 | 20200101 |
| stk_managers | tushare_stk_managers | stock_basic | P1 | 20200101 |
| stk_rewards | tushare_stk_rewards | stock_basic | P1 | 20200101 |
| stock_basic | tushare_stock_basic | stock_basic | P0 | N/A |
| stock_company | tushare_stock_company | stock_basic | P0 | N/A |
| stock_hsgt | tushare_stock_hsgt | stock_basic | P1 | N/A |
| suspend_d | tushare_suspend_d | stock_daily | P1 | 20200101 |
| teleplay_record | tushare_teleplay_record | tmt | P3 | 20200101 |
| tmt_twincome | tushare_tmt_twincome | tmt | P3 | 20200101 |
| tmt_twincomedetail | tushare_tmt_twincomedetail | tmt | P3 | 20200101 |
| trade_cal | tushare_trade_cal | stock_basic | P0 | N/A |
| us_tbr | tushare_us_tbr | macro | P3 | 20200101 |
| us_tltr | tushare_us_tltr | macro | P3 | 20200101 |
| us_trltr | tushare_us_trltr | macro | P3 | 20200101 |
| us_trycr | tushare_us_trycr | macro | P3 | 20200101 |
| us_tycr | tushare_us_tycr | macro | P3 | 20200101 |
| weekly | tushare_stock_weekly | stock_daily | P0 | 20200101 |
| wz_index | tushare_wz_index | macro | P3 | 20200101 |
| yc_cb | tushare_yc_cb | bonds | P3 | 20200101 |

### 4.2 special 频率接口（300 次/分钟，共 98 个）

| 接口名 | 数据库表 | 分类 | 优先级 | 补库起始 |
|--------|----------|------|:------:|----------|
| bak_basic | tushare_bak_basic | stock_basic | P3 | 20160101 |
| bak_daily | tushare_bak_daily | stock_daily | P3 | 20200101 |
| balancesheet | tushare_balancesheet | stock_financial | P0 | 20200101 |
| block_trade | tushare_block_trade | stock_reference | P1 | 20200101 |
| broker_recommend | tushare_broker_recommend | stock_special | P2 | 20200101 |
| cashflow | tushare_cashflow | stock_financial | P0 | 20200101 |
| cb_factor_pro | tushare_cb_factor_pro | bonds | P2 | 20200101 |
| ccass_hold | tushare_ccass_hold | stock_special | P2 | 20200101 |
| ccass_hold_detail | tushare_ccass_hold_detail | stock_special | P2 | 20200101 |
| ci_daily | tushare_ci_daily | index | P2 | 20200101 |
| ci_index_member | tushare_ci_index_member | index | P2 | N/A |
| cyq_chips | tushare_cyq_chips | stock_special | P2 | 20200101 |
| cyq_perf | tushare_cyq_perf | stock_special | P1 | 20200101 |
| daily_basic | tushare_daily_basic | stock_daily | P0 | 20200101 |
| daily_info | tushare_daily_info | index | P2 | 20200101 |
| dc_daily | tushare_dc_daily | stock_limit_board | P1 | 20200101 |
| dc_hot | tushare_dc_hot | stock_limit_board | P2 | 20200101 |
| dc_index | tushare_dc_index | stock_limit_board | P1 | N/A |
| dc_member | tushare_dc_member | stock_limit_board | P2 | N/A |
| disclosure_date | tushare_disclosure_date | stock_financial | P2 | 20200101 |
| dividend | tushare_dividend | stock_financial | P1 | 20200101 |
| etf_share_size | tushare_etf_share_size | etf | P2 | 20200101 |
| express | tushare_express | stock_financial | P2 | 20200101 |
| fina_audit | tushare_fina_audit | stock_financial | P1 | 20200101 |
| fina_indicator | tushare_fina_indicator | stock_financial | P0 | 20200101 |
| fina_mainbz | tushare_fina_mainbz | stock_financial | P1 | 20200101 |
| forecast | tushare_forecast | stock_financial | P2 | 20200101 |
| ft_limit | tushare_ft_limit | futures | P2 | 20200101 |
| fund_factor_pro | tushare_fund_factor_pro | fund | P2 | 20200101 |
| ggt_daily | tushare_ggt_daily | stock_daily | P2 | 20200101 |
| ggt_monthly | tushare_ggt_monthly | stock_daily | P3 | 20200101 |
| ggt_top10 | tushare_ggt_top10 | stock_daily | P2 | 20200101 |
| hk_hold | tushare_hk_hold | stock_special | P2 | 20200101 |
| hm_detail | tushare_hm_detail | stock_limit_board | P2 | 20220801 |
| hm_list | tushare_hm_list | stock_limit_board | P2 | N/A |
| hsgt_top10 | tushare_hsgt_top10 | stock_daily | P2 | 20200101 |
| idx_factor_pro | tushare_idx_factor_pro | index | P2 | 20200101 |
| income | tushare_income | stock_financial | P0 | 20200101 |
| index_classify | tushare_index_classify | index | P1 | N/A |
| index_daily | tushare_index_daily | index | P0 | 20200101 |
| index_dailybasic | tushare_index_dailybasic | index | P1 | 20200101 |
| index_global | tushare_index_global | index | P2 | 20200101 |
| index_member_all | tushare_index_member_all | index | P2 | N/A |
| index_monthly | tushare_index_monthly | index | P1 | 20200101 |
| index_weekly | tushare_index_weekly | index | P1 | 20200101 |
| index_weight | tushare_index_weight | index | P1 | 20200101 |
| kpl_concept_cons | tushare_kpl_concept_cons | stock_limit_board | P3 | N/A |
| kpl_list | tushare_kpl_list | stock_limit_board | P2 | 20200101 |
| limit_cpt_list | tushare_limit_cpt_list | stock_limit_board | P2 | 20200101 |
| limit_list_d | tushare_limit_list_d | stock_limit_board | P1 | 20200101 |
| limit_list_ths | tushare_limit_list_ths | stock_limit_board | P2 | 20231101 |
| limit_step | tushare_limit_step | stock_limit_board | P1 | 20200101 |
| margin | tushare_margin | stock_reference | P1 | 20200101 |
| margin_detail | tushare_margin_detail | stock_reference | P1 | 20200101 |
| margin_secs | tushare_margin_secs | stock_reference | P2 | 20200101 |
| moneyflow | tushare_moneyflow | stock_moneyflow | P1 | 20200101 |
| moneyflow_cnt_ths | tushare_moneyflow_cnt_ths | stock_moneyflow | P2 | 20200101 |
| moneyflow_dc | tushare_moneyflow_dc | stock_moneyflow | P2 | 20230911 |
| moneyflow_hsgt | tushare_moneyflow_hsgt | stock_moneyflow | P1 | 20200101 |
| moneyflow_ind_dc | tushare_moneyflow_ind_dc | stock_moneyflow | P2 | 20200101 |
| moneyflow_ind_ths | tushare_moneyflow_ind_ths | stock_moneyflow | P2 | 20200101 |
| moneyflow_mkt_dc | tushare_moneyflow_mkt_dc | stock_moneyflow | P2 | 20200101 |
| moneyflow_ths | tushare_moneyflow_ths | stock_moneyflow | P2 | 20200101 |
| pledge_detail | tushare_pledge_detail | stock_reference | P2 | 20200101 |
| pledge_stat | tushare_pledge_stat | stock_reference | P2 | 20200101 |
| report_rc | tushare_report_rc | stock_special | P2 | 20200101 |
| repurchase | tushare_repurchase | stock_reference | P2 | 20200101 |
| share_float | tushare_share_float | stock_reference | P2 | 20200101 |
| slb_len | tushare_slb_len | stock_reference | P2 | 20200101 |
| st | tushare_st | stock_basic | P2 | 20200101 |
| stk_account_old | tushare_stk_account_old | stock_reference | P3 | 20080101 |
| stk_ah_comparison | tushare_stk_ah_comparison | stock_special | P2 | 20200101 |
| stk_auction | tushare_stk_auction | stock_limit_board | P2 | 20200101 |
| stk_auction_c | tushare_stk_auction_c | stock_special | P2 | 20200101 |
| stk_auction_o | tushare_stk_auction_o | stock_special | P2 | 20200101 |
| stk_factor_pro | tushare_stk_factor_pro | stock_special | P1 | 20200101 |
| stk_holdernumber | tushare_stk_holdernumber | stock_reference | P2 | 20200101 |
| stk_holdertrade | tushare_stk_holdertrade | stock_reference | P2 | 20200101 |
| stk_limit | tushare_stk_limit | stock_daily | P1 | 20200101 |
| stk_nineturn | tushare_stk_nineturn | stock_special | P2 | 20230101 |
| stk_premarket | tushare_stk_premarket | stock_basic | P2 | 20200101 |
| stk_surv | tushare_stk_surv | stock_special | P2 | 20200101 |
| stk_week_month_adj | tushare_stk_week_month_adj | stock_daily | P2 | 20200101 |
| stk_weekly_monthly | tushare_stk_weekly_monthly | stock_daily | P2 | 20200101 |
| stock_st | tushare_stock_st | stock_basic | P2 | 20200101 |
| sw_daily | tushare_sw_daily | index | P2 | 20200101 |
| sz_daily_info | tushare_sz_daily_info | index | P2 | 20200101 |
| tdx_daily | tushare_tdx_daily | stock_limit_board | P2 | 20200101 |
| tdx_index | tushare_tdx_index | stock_limit_board | P2 | N/A |
| tdx_member | tushare_tdx_member | stock_limit_board | P2 | N/A |
| ths_daily | tushare_ths_daily | stock_limit_board | P1 | 20200101 |
| ths_hot | tushare_ths_hot | stock_limit_board | P2 | 20200101 |
| ths_index | tushare_ths_index | stock_limit_board | P1 | N/A |
| ths_member | tushare_ths_member | stock_limit_board | P1 | N/A |
| top10_floatholders | tushare_top10_floatholders | stock_reference | P2 | 20200101 |
| top10_holders | tushare_top10_holders | stock_reference | P2 | 20200101 |
| top_inst | tushare_top_inst | stock_limit_board | P2 | 20200101 |
| top_list | tushare_top_list | stock_limit_board | P1 | 20200101 |

---

## 五、付费/未开通接口（45 个）

这些接口需要额外付费或更高积分才能开通：

### 5.1 分钟级行情（11 个）

| 接口名 | 数据库表 | 说明 |
|--------|----------|------|
| stk_mins | — | 股票分钟线 |
| idx_mins | — | 指数分钟线 |
| ft_mins | — | 期货分钟线 |
| opt_mins | — | 期权分钟线 |
| rt_min | — | 实时分钟线 |
| rt_k | — | 实时 K 线 |
| hk_mins | — | 港股分钟线 |

### 5.2 实时行情（8 个）

| 接口名 | 数据库表 | 说明 |
|--------|----------|------|
| rt_idx_k | — | 实时指数 K 线 |
| rt_idx_min | — | 实时指数分钟线 |
| rt_sw_k | — | 实时申万指数 K 线 |
| rt_etf_k | — | 实时 ETF K 线 |
| rt_fut_min | — | 实时期货分钟线 |
| rt_hk_k | — | 实时港股 K 线 |
| etf_iopv | — | ETF 实时净值 |

### 5.3 港股数据（8 个）

| 接口名 | 数据库表 | 说明 |
|--------|----------|------|
| hk_basic | — | 港股基础信息 |
| hk_daily | — | 港股日线 |
| hk_daily_adj | — | 港股日线复权 |
| hk_adjfactor | — | 港股复权因子 |
| hk_income | — | 港股利润表 |
| hk_balancesheet | — | 港股资产负债表 |
| hk_cashflow | — | 港股现金流量表 |
| hk_fina_indicator | — | 港股财务指标 |
| hk_tradecal | — | 港股交易日历 |

### 5.4 美股数据（8 个）

| 接口名 | 数据库表 | 说明 |
|--------|----------|------|
| us_basic | — | 美股基础信息 |
| us_daily | — | 美股日线 |
| us_daily_adj | — | 美股日线复权 |
| us_adjfactor | — | 美股复权因子 |
| us_income | — | 美股利润表 |
| us_balancesheet | — | 美股资产负债表 |
| us_cashflow | — | 美股现金流量表 |
| us_fina_indicator | — | 美股财务指标 |
| us_tradecal | — | 美股交易日历 |

### 5.5 新闻公告（7 个）

| 接口名 | 数据库表 | 说明 |
|--------|----------|------|
| news | — | 新闻快讯 |
| major_news | — | 重要新闻 |
| cctv_news | — | 央视新闻 |
| anns_d | — | 公司公告 |
| irm_qa_sh | — | 上证互动易 |
| irm_qa_sz | — | 深证互动易 |
| research_report | — | 研究报告 |
| npr | — | 券商晨会报告 |

### 5.6 融资融券（4 个）

| 接口名 | 数据库表 | 说明 |
|--------|----------|------|
| slb_sec | — | 融券标的 |
| slb_sec_detail | — | 融券明细 |
| slb_len_mm | — | 融资融券期限 |
| stk_account | — | 证券账户 |

### 5.7 其他（1 个）

| 接口名 | 数据库表 | 说明 |
|--------|----------|------|
| pro_bar | — | 通用行情接口（复合接口） |

---

## 六、分类统计汇总

| 分类 | normal 接口 | special 接口 | 合计 | 说明 |
|------|:-----------:|:-----------:|:----:|------|
| stock_basic | 10 | 3 | 13 | 股票基础信息 |
| stock_daily | 6 | 8 | 14 | 股票行情数据 |
| stock_financial | 0 | 10 | 10 | 财务数据 |
| stock_limit_board | 0 | 22 | 22 | 涨跌板/板块数据 |
| stock_moneyflow | 0 | 8 | 8 | 资金流向 |
| stock_reference | 0 | 14 | 14 | 融资融券/质押/大宗 |
| stock_special | 0 | 13 | 13 | 筹码/持仓/AH对比 |
| index | 1 | 14 | 15 | 指数数据 |
| etf | 3 | 2 | 5 | ETF/基金数据 |
| fund | 8 | 0 | 8 | 公募基金数据 |
| futures | 11 | 0 | 11 | 期货数据 |
| options | 2 | 0 | 2 | 期权数据 |
| bonds | 15 | 0 | 15 | 债券数据 |
| forex | 2 | 0 | 2 | 外汇数据 |
| spot | 2 | 0 | 2 | 现货数据 |
| macro | 18 | 0 | 18 | 宏观经济数据 |
| tmt | 8 | 0 | 8 | 文娱产业数据 |
| wealth | 2 | 0 | 2 | 财富销售数据 |
| **合计** | **84** | **98** | **182** | — |

---

## 七、优先级分布

| 优先级 | 数量 | 说明 | 调度时间 |
|:------:|:----:|------|----------|
| P0 | 13 | 最高优先级，每个交易日必更 | Batch A: 17:00 |
| P1 | 34 | 高优先级，交易日更新 | Batch A/B/C: 17:00-19:00 |
| P2 | 86 | 中优先级，定期更新 | Batch B/C/D: 18:00-19:45 |
| P3 | 49 | 低优先级，按需更新 | Batch D: 19:45 |

---

## 八、调度批次安排

| 批次 | 名称 | 时间 (CST) | 包含分类 |
|:----:|------|:----------:|----------|
| A | Daily Quotes | 17:00 | stock_daily, index, etf, futures, options, bonds |
| B | Money Flow & Reference | 18:00 | stock_moneyflow, stock_reference |
| C | Special & Limit Board | 19:00 | stock_limit_board, stock_special |
| D | Macro & Financial & Other | 19:45 | macro, stock_financial, tmt, wealth, forex, spot |

---

## 九、官方文档链接

| 文档 | 链接 |
|------|------|
| 积分与频次权限对应表 | [https://tushare.pro/document/1?doc_id=290](https://tushare.pro/document/1?doc_id=290) |
| 关于权限 | [https://tushare.pro/document/1?doc_id=108](https://tushare.pro/document/1?doc_id=108) |
| 平台积分 | [https://tushare.pro/document/1?doc_id=13](https://tushare.pro/document/1?doc_id=13) |
| 如何高效撸数据 | [https://tushare.pro/document/1?doc_id=230](https://tushare.pro/document/1?doc_id=230) |
| API 服务 | [https://tushare.pro/document/1?doc_id=11](https://tushare.pro/document/1?doc_id=11) |
| 积分到期查询 | [https://tushare.pro/document/1?doc_id=307](https://tushare.pro/document/1?doc_id=307) |
| 学生免费积分 | [https://tushare.pro/document/1?doc_id=360](https://tushare.pro/document/1?doc_id=360) |

Sources:
- [积分与频次权限对应表 - Tushare](https://tushare.pro/document/1?doc_id=290)
- [关于权限 - Tushare](https://tushare.pro/document/1?doc_id=108)
- [平台积分 - Tushare](https://tushare.pro/document/1?doc_id=13)
- [如何优雅高效的撸数据 - Tushare](https://tushare.pro/document/1?doc_id=230)
- [积分到期查询 - Tushare](https://tushare.pro/document/1?doc_id=307)
