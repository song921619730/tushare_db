# MCP Config Analysis — 2026-04-29

## Source

`@tushare/mcp@0.2.1` (npm) → `assets/search-index.min.json`

The MCP search index contains **232 APIs** with complete `inputParams`, `outputFields`, and `field_presets` — derived from `@tushare/sdk@^1.2.0` TypeScript SDK registry.

## How @tushare/mcp Works (No YAML Configs)

```
sdk_call("stock_basic", {params})
  → SDKCaller.call()
    → findSDKMethod("stock_basic")
      → generateMethodNames: getStockBasic / stockBasic / stock_basic
        → iterate SDK modules by reflection
          → method(params, fields)
            → Tushare API
```

The SDK has a **registry.auto** containing all 232 API definitions with typed parameters and fields. No configuration files — all metadata is in TypeScript code.

## Overall Stats

| Metric | Count |
|--------|-------|
| MCP indexed APIs | 232 |
| Our YAML configured APIs | 227 |
| APIs in both (can optimize) | **201** |
| APIs missing from our configs | **31** |
| Our APIs not in MCP (paid/VIP) | 26 |

## Critical Finding: 201 Configs Have Empty required_params

Every single one of our 201 common interfaces has `required_params: []` in YAML. The MCP index provides the complete parameter list for all of them. This is the root cause of many configuration errors — we don't validate params before calling the API.

### Required Params Examples

| API | Our Config | MCP Says |
|-----|-----------|----------|
| income | `[]` | `[ts_code, ann_date, f_ann_date, start_date, end_date, period]` |
| daily | `[]` | `[ts_code, trade_date, start_date, end_date]` |
| fina_indicator | `[]` | `[ts_code, ann_date, start_date, end_date, period, update_flag]` |
| dividend | `[]` | `[ts_code, ann_date, end_date, record_date, ex_date, imp_ann_date]` |
| moneyflow | `[]` | `[ts_code, trade_date, start_date, end_date]` |
| fund_basic | `[]` | `[ts_code, market, update_flag, status, name]` |
| fut_daily | `[]` | `[trade_date, ts_code, exchange, start_date, end_date]` |
| cb_basic | `[]` | `[ts_code, list_date, exchange]` |
| margin | `[]` | `[trade_date, exchange_id, start_date, end_date]` |
| index_weight | `[]` | `[index_code, trade_date, start_date, end_date, ts_code]` |

## Field Presets Available

Most configs use `fields: []` (pull all fields). MCP provides 3-tier presets:

| Preset | Description | Example (daily) |
|--------|-------------|-----------------|
| minimal | 3-5 core fields | `[ts_code, trade_date, close]` |
| basic | 8-12 common fields | `[ts_code, trade_date, open, high, low, close, vol, amount]` |
| full | All fields (omit param) | (all 11 fields) |

Using `basic` preset instead of full can reduce data transfer by **60-80%** for wide tables like income (100+ columns).

## freq_bucket Classification Errors

~50+ interfaces have wrong `freq_bucket`:

**Should be `normal` but set to `special`:**
daily_basic, bak_daily, bak_basic, balancesheet, cashflow, block_trade, ci_daily, ci_index_member, dc_daily, dc_hot, dc_index, disclosure_date, dividend, ft_limit, ft_mins, hk_balancesheet, hk_basic, hk_cashflow, hk_daily, hk_daily_adj, hk_hold, hk_income, hk_mins, hk_tradecal, idx_factor_pro, income, index_classify, index_daily, index_dailybasic, index_global, index_member_all, index_monthly, index_weekly, index_weight, limit_cpt_list, limit_list_d, limit_list_ths, limit_step, moneyflow, report_rc, repurchase, rt_hk_k, rt_k, rt_min, share_float, slb_len, stk_account_old, stk_ah_comparison, stk_auction, stk_auction_c, stk_auction_o, stk_holdernumber, stk_holdertrade, stk_limit, stk_premarket, stk_surv, stk_week_month_adj, stk_weekly_monthly, stock_st, sw_daily, sz_daily_info, top10_floatholders, top10_holders, top_inst, top_list, us_balancesheet, us_basic, us_cashflow, us_daily, us_daily_adj, us_income, us_tradecal

**Should be `special` but set to `normal`:**
bond_blk, bond_blk_detail, cb_basic, cb_call, cb_daily, cb_factor_pro, cb_issue, cb_price_chg, cb_rate, cb_share, fund_adj, fund_basic, fund_company, fund_daily, fund_div, fund_factor_pro, fund_manager, fund_nav, fund_portfolio, fund_sales_ratio, fund_sales_vol, fund_share, fut_basic, fut_daily, fut_holding, fut_mapping, fut_settle, fut_weekly_detail, fut_weekly_monthly, fut_wsr, opt_basic, opt_daily

## 31 Missing APIs

| API | Category | Params |
|-----|----------|--------|
| anns_d | 大模型语料 > 上市公司公告 | ts_code, ann_date, start_date, end_date, title |
| bishijie | 另类数据 > 币世界 | start_date, end_date |
| btc8 | 另类数据 > 巴比特 | start_date, end_date |
| btc_marketcap | 另类数据 > 比特币市值 | start_date, end_date |
| btc_pricevol | 另类数据 > 比特币量价 | start_date, end_date |
| cctv_news | 大模型语料 > 新闻联播 | date |
| coin_bar | 另类数据 > 数字货币K线 | ts_code, symbol, exchange, freq |
| coin_pair | 另类数据 > 交易所交易对 | exchange, ts_code, status |
| coincap | 另类数据 > 数字货币市值 | trade_date, coin |
| coinexchanges | 另类数据 > 交易所列表 | exchange, area_code |
| coinfees | 另类数据 > 交易所费率 | exchange, asset_type |
| coinlist | 另类数据 > 数字货币列表 | issue_date, start_date, end_date |
| coinpair | 另类数据 > 交易所交易对(旧) | trade_date, exchange |
| concept | 参考数据 > 概念股分类 | src |
| concept_detail | 参考数据 > 概念股明细 | id, ts_code |
| exchange_ann | 另类数据 > 交易所公告 | start_date, end_date |
| exchange_twitter | 另类数据 > 交易所Twitter | start_date, end_date |
| irm_qa_sh | 大模型语料 > 上证e互动 | ts_code, trade_date |
| irm_qa_sz | 大模型语料 > 深证易互动 | ts_code, trade_date |
| jinse | 另类数据 > 金色财经 | start_date, end_date |
| kpl_concept | 打板专题 > 题材数据 | trade_date, ts_code, name |
| major_news | 大模型语料 > 新闻通讯 | src, start_date, end_date |
| news | 大模型语料 > 新闻快讯 | start_date, end_date, src |
| slb_len_mm | 两融 > 做市借券 | trade_date, ts_code |
| slb_sec | 两融 > 转融券汇总 | trade_date, ts_code |
| slb_sec_detail | 两融 > 转融券明细 | trade_date, ts_code |
| stk_account | 参考数据 > 开户数据 | date |
| stk_factor | 特色数据 > 技术面因子 | ts_code, trade_date |
| stk_mins | ETF > 分钟行情 | ts_code, freq |
| twitter_kol | 另类数据 > Twitter大V | start_date, end_date |
| ubindex_constituents | 另类数据 > 优币指数成分 | index_name |

## 26 Paid/VIP APIs (In Our YAML, Not In MCP Free Index)

These are our paid-tier interfaces that don't appear in the free MCP index:
cyq_d, etf_iopv, etf_share_size, film_boxoffice, film_daily, fut_index_daily, fut_trade_cal, hk_adjfactor, hk_dividend, hk_hold_detail, hk_moneyflow, hk_monthly, hk_top10, hk_weekly, idx_mins, rt_etf_k, rt_idx_k, rt_idx_min, rt_sw_k, st, us_adjfactor, us_dividend, us_moneyflow, us_monthly, us_top10, us_weekly

## Tool

`sync_config_from_mcp.py` — compare, generate, and optimize YAML configs from MCP search index.

## Recommended Actions

1. **Immediate:** Fix `required_params` for P0/P1 interfaces (daily, income, stock_basic, etc.) — these are the most critical data pipelines
2. **Short-term:** Fix `fields` to use basic presets — reduce data transfer and type inference errors
3. **Short-term:** Fix `freq_bucket` misclassifications — prevent rate limit issues
4. **Medium-term:** Review and enable the 31 missing APIs (prioritize 大模型语料 and 打板专题 for AI use cases)
5. **Ongoing:** Use `sync_config_from_mcp.py` to keep configs in sync with SDK updates
