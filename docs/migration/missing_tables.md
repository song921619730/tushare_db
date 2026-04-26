# Missing Tables Report — 2026-04-26

## Summary

| Metric | Value |
|--------|-------|
| PG logical tables | 141 |
| CH tables (tushare db) | 144 |
| PG has but CH missing | 56 |
| CH has but PG missing | 59 |
| PG tables with data | ~60 |
| PG tables with 0 rows | ~30 |

## PG has but CH missing (56 tables)

Only non-zero data tables listed below:

| Table | PG Rows | Notes |
|-------|---------|-------|
| tushare_stock_weekly | 1,538,761 | Partitioned by year (2019-2027) |
| tushare_index_weight | 551,558 | Index constituents |
| tushare_anns_d | ? | Announcements |
| tushare_bo_daily | ? | Block order |
| tushare_cctv_news | ? | CCTV news |
| tushare_cyq_chips | ? | Chip distribution |
| tushare_dc_member | ? | DC index members |
| tushare_etf_iopv | ? | ETF IOPV |
| tushare_etf_mins | ? | ETF minute data |
| tushare_fina_audit | ? | Financial audit |
| tushare_fut_mins | ? | Futures minute |
| tushare_hk_* | various | HK stock data |
| tushare_index_daily | ? | Index daily |
| tushare_index_mins | ? | Index minute |
| tushare_index_monthly | 0 | Monthly index (empty) |
| tushare_irm_qa_sh/sz | ? | IRM Q&A |
| tushare_major_news | ? | Major news |
| tushare_news | ? | News |
| tushare_npr | ? | NPR data |
| tushare_opt_mins | ? | Options minute |
| tushare_pledge_detail | ? | Pledge detail |
| tushare_research_report | ? | Research reports |
| tushare_rt_* | ? | Real-time data |
| tushare_stock_mins | ? | Stock minute data |
| tushare_stock_monthly | ? | Stock monthly |
| tushare_us_* | various | US stock data |
| tushare_fina_mainbz | 0 | Main business (empty) |
| tushare_top10_holders | 0 | Top 10 holders (empty) |
| tushare_stk_holdertrade | 0 | Holder trades (empty) |
| tushare_moneyflow_ths | 0 | Money flow THS (empty) |
| tushare_moneyflow_ind_ths | 0 | Money flow ind THS (empty) |
| tushare_moneyflow_cnt_ths | 0 | Money flow cnt THS (empty) |
| tushare_dc_hot | 0 | DC hot (empty) |
| tushare_fund_nav | 0 | Fund NAV (empty) |
| tushare_fund_portfolio | ? | Fund portfolio |
| tushare_fund_div | ? | Fund dividends |
| tushare_broker_recommend | ? | Broker recommendations |

## CH has but PG missing (59 tables)

These are CH-only tables from other sources (backtest, derived data, etc.):
tushare_bak_basic, tushare_bak_daily, tushare_bond_blk, tushare_bond_blk_detail,
tushare_bse_mapping, tushare_cb_factor_pro, tushare_cb_rate, tushare_ccass_hold,
tushare_ccass_hold_detail, tushare_ci_daily, tushare_ci_index_member, tushare_daily_info,
tushare_eco_cal, tushare_etf_index, tushare_etf_share_size, tushare_ft_limit,
tushare_fund_factor_pro, tushare_fund_sales_ratio, tushare_fund_sales_vol,
tushare_fut_weekly_detail, tushare_fut_wsr, tushare_ggt_daily, tushare_ggt_monthly,
tushare_ggt_top10, tushare_gz_index, tushare_hm_detail, tushare_hm_list,
tushare_hsgt_top10, tushare_idx_factor_pro, tushare_index_global, tushare_kpl_concept_cons,
tushare_kpl_list, tushare_limit_list_ths, tushare_namechange, tushare_new_share,
tushare_report_rc, tushare_sf_month, tushare_shibor_quote, tushare_slb_len, tushare_st,
tushare_stk_account_old, tushare_stk_auction_c, tushare_stk_auction_o, tushare_stk_managers,
tushare_stk_nineturn, tushare_stk_surv, tushare_stock_hsgt, tushare_stock_st,
tushare_sw_daily, tushare_sz_daily_info, tushare_teleplay_record, tushare_top10_floatholders,
tushare_us_tbr, tushare_us_tltr, tushare_us_trltr, tushare_us_trycr, tushare_us_tycr,
tushare_wz_index, tushare_yc_cb

## Partition Details

### tushare_stock_daily partitions (PG)
| Partition | Rows |
|-----------|------|
| _2019 | 6,000 |
| _2020 | 964,131 |
| _2021 | 1,085,445 |
| _2022 | 1,162,629 |
| _2023 | 1,233,828 |
| _2024 | 1,280,739 |
| _2025 | 1,310,141 |
| _2026 | 399,588 |
| _2027 | 0 |
| _default | 0 |
| **TOTAL** | **7,442,501** |

### tushare_adj_factor partitions (PG)
| Partition | Rows |
|-----------|------|
| _2019-2025 | 0 |
| _2026 | 11,515 |
| _default | 0 |
| **TOTAL** | **11,515** |

> Note: adj_factor in PG has only 11K rows vs 4.67M in CH. PG data is from a limited collection period.

## Decision

Proceed with migration for tables with non-zero PG data that CH either:
1. Doesn't have (new tables)
2. Has but with minimal data (e.g., stock_daily 27K vs PG 7.4M)

Tables where CH already has more data (e.g., adj_factor) should NOT overwrite — migration only adds rows, _version handles dedup.
