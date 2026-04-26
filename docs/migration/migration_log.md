# Migration Log — 2026-04-26

## Summary

| Metric | Value |
|--------|-------|
| PG source | PostgreSQL 16.13 (localhost:5432) |
| CH target | ClickHouse 24.8 (localhost:8123) |
| Tables migrated | 24 (all status=done) |
| Total rows | ~10,106,047 |
| Total sync_state records | 5,299 |
| Duration | ~15 minutes |

## Migrated Tables

### P0 (Core) — 8 tables

| Table | Rows | Duration | Notes |
|-------|------|----------|-------|
| tushare_stock_basic | 5,510 | <1s | |
| tushare_trade_cal | 13,162 | <1s | |
| tushare_stock_daily | 7,442,501 | 111s | Largest table, 8 year partitions |
| tushare_stock_weekly | 1,538,761 | 23s | Partitioned by year |
| tushare_adj_factor | 11,515 | <1s | PG has limited data vs CH 4.67M |
| tushare_daily_basic | 6,000 | <1s | PG partial data |
| tushare_stk_limit | 0 | | Empty |
| tushare_suspend_d | 0 | | Empty |

### P1 (Financials) — 5 tables

| Table | Rows | Duration | Notes |
|-------|------|----------|-------|
| tushare_income | 123,800 | 3s | 18 matching columns |
| tushare_balancesheet | 122,180 | 4.7s | 27 matching columns |
| tushare_cashflow | 123,676 | 2.6s | |
| tushare_fina_indicator | 118,565 | 7.2s | |
| tushare_dividend | 0 | | Empty in PG |

### P2 (Money Flow + Limit Board) — 8 tables

| Table | Rows | Duration | Notes |
|-------|------|----------|-------|
| tushare_moneyflow | 456,000 | 12.5s | |
| tushare_moneyflow_hsgt | 1,478 | 0.6s | |
| tushare_top_list | 96,809 | 2.3s | |
| tushare_margin | 3,829 | 0.3s | |
| tushare_block_trade | 42,261 | 1s | |
| tushare_share_float | 0 | | Empty |
| tushare_stk_holdernumber | 0 | | Empty |
| tushare_pledge_stat | 0 | | Empty |

### P3 (Remaining) — 3 tables migrated

| Table | Rows | Notes |
|-------|------|-------|
| tushare_top10_holders | 0 | Empty |
| tushare_stk_holdertrade | 0 | Empty |
| tushare_cb_issue | 0 | Empty |

## P3 Tables NOT Migrated (43 tables)

These tables have no matching columns between PG and CH schemas:

- tushare_index_weight, tushare_fina_mainbz, tushare_moneyflow_ths, tushare_moneyflow_ind_ths, tushare_moneyflow_cnt_ths, tushare_dc_hot, tushare_index_monthly, tushare_fund_nav, tushare_fund_portfolio, tushare_fund_div, tushare_index_daily, tushare_anns_d, tushare_bo_daily, tushare_cctv_news, tushare_cyq_chips, tushare_dc_member, tushare_etf_iopv, tushare_etf_mins, tushare_film_record, tushare_fina_audit, tushare_fut_mins, tushare_index_mins, tushare_irm_qa_sh, tushare_irm_qa_sz, tushare_major_news, tushare_news, tushare_npr, tushare_opt_mins, tushare_pledge_detail, tushare_research_report, tushare_rt_etf_k, tushare_rt_idx_k, tushare_rt_min, tushare_rt_sw_k, tushare_stock_mins, tushare_stock_monthly, tushare_hk_basic, tushare_hk_daily, tushare_us_basic, tushare_us_daily, tushare_api_calls_log, tushare_sync_status, tushare_broker_recommend

**Root cause**: CH tables have different column names from PG (e.g., `n_profit` vs `net_profit`, `tot_op_cost` vs `total_cogs`). Requires schema reconciliation.

## Schema Fixes Applied During Migration

### Type Mismatches (String → Float64)
- **tushare_income**: prem_earned, ebit, ebitda
- **tushare_balancesheet**: money_cap, inventories, fa_avail_for_sale, htm_invest, lt_eqt_invest, notes_payable, acct_payable, adv_receipts, int_payable, div_payable, oth_payable, lt_borr, lt_payable, defer_tax_liab
- **tushare_cashflow**: depr_fa_coga_dpba, loss_disp_fiolta, loss_fv_chg, invest_loss
- **tushare_fina_indicator**: gross_margin, current_ratio, quick_ratio, cash_ratio, ar_turn, ca_turn, fa_turn, ebit, ebitda, fcff, fcfe, interestdebt, netdebt, working_capital, invest_capital, grossprofit_margin, roa, roic
- **tushare_moneyflow_hsgt**: ggt_ss, ggt_sz, hgt, north_money, south_money

### Nullability Fixes (non-nullable → Nullable)
All financial table numeric columns made Nullable to accommodate PG NULL values.

### Normalization Bug Fix
- Removed `"share"` from `_NORMALIZE_X10000_PATTERNS` in `field_resolver.py`
- **Root cause**: `total_share` matched "share" pattern → ×10000 → exceeded `Decimal(18,4)` max value
- **Impact**: Prevented `tushare_balancesheet` migration failure
- **Fix**: Only amount/value fields (revenue, profit, cost, etc.) should be normalized; share count fields should not

## Post-Migration

1. **OPTIMIZE TABLE FINAL** — completed on all 24 tables
2. **sync_state** — 5,299 records written to `_meta.sync_state`
3. **Validation** — pending (`uv run python scripts/migrate.py validate --priority P0`)
