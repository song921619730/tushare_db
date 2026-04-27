# 接口字段目录总览

共 **242** 个已知接口，**149** 个已入库，**93** 个未入库，**2,605** 个字段。

## 债券数据 (15 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| bc_bestotcqt | `tushare_bc_bestotcqt` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| bc_otcqt | `tushare_bc_otcqt` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| bond_blk | `tushare_bond_blk` | ✅ 已入库 | 7 | 9 | A | P3 | [查看](interfaces/tushare_bond_blk.md) |
| bond_blk_detail | `tushare_bond_blk_detail` | ✅ 已入库 | 9 | 9 | A | P3 | [查看](interfaces/tushare_bond_blk_detail.md) |
| cb_basic | `tushare_cb_basic` | ✅ 已入库 | 15 | 1,126 | reference | P3 | [查看](interfaces/tushare_cb_basic.md) |
| cb_call | `tushare_cb_call` | ✅ 已入库 | 12 | 1 | A | P3 | [查看](interfaces/tushare_cb_call.md) |
| cb_daily | `tushare_cb_daily` | ✅ 已入库 | 12 | 340 | A | P2 | [查看](interfaces/tushare_cb_daily.md) |
| cb_factor_pro | `tushare_cb_factor_pro` | ✅ 已入库 | 90 | 340 | A | P2 | [查看](interfaces/tushare_cb_factor_pro.md) |
| cb_issue | `tushare_cb_issue` | ✅ 已入库 | 24 | 1 | A | P2 | [查看](interfaces/tushare_cb_issue.md) |
| cb_price_chg | `tushare_cb_price_chg` | ❌ 未入库 | - | - | A | P3 | - |
| cb_rate | `tushare_cb_rate` | ✅ 已入库 | 2 | 478 | reference | P3 | [查看](interfaces/tushare_cb_rate.md) |
| cb_share | `tushare_cb_share` | ✅ 已入库 | 16 | 0 | A | P2 | [查看](interfaces/tushare_cb_share.md) |
| eco_cal | `tushare_eco_cal` | ✅ 已入库 | 9 | 1 | A | P3 | [查看](interfaces/tushare_eco_cal.md) |
| repo_daily | `tushare_repo_daily` | ✅ 已入库 | 13 | 44 | A | P2 | [查看](interfaces/tushare_repo_daily.md) |
| yc_cb | `tushare_yc_cb` | ✅ 已入库 | 7 | 1 | A | P3 | [查看](interfaces/tushare_yc_cb.md) |

## ETF/基金数据 (19 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| etf_basic | `tushare_etf_basic` | ✅ 已入库 | 15 | 3,253 | reference | P1 | [查看](interfaces/tushare_etf_basic.md) |
| etf_index | `tushare_etf_index` | ✅ 已入库 | 9 | 0 | reference | P2 | [查看](interfaces/tushare_etf_index.md) |
| etf_iopv 💰付费 | `tushare_etf_iopv` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| etf_share_size | `tushare_etf_share_size` | ✅ 已入库 | 7 | 1,488 | A | P2 | [查看](interfaces/tushare_etf_share_size.md) |
| ft_mins 💰付费 | `tushare_ft_mins` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| fund_adj | `tushare_fund_adj` | ✅ 已入库 | 4 | 1,971 | A | P2 | [查看](interfaces/tushare_fund_adj.md) |
| fund_daily | `tushare_fund_daily` | ✅ 已入库 | 12 | 91,046 | A | P1 | [查看](interfaces/tushare_fund_daily.md) |
| hk_adjfactor 💰付费 | `tushare_hk_adjfactor` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| hk_balancesheet 💰付费 | `tushare_hk_balancesheet` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| hk_basic 💰付费 | `tushare_hk_basic` | ❌ 未入库 | - | - | ⚠️ reference | P3 | - |
| hk_cashflow 💰付费 | `tushare_hk_cashflow` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| hk_daily 💰付费 | `tushare_hk_daily` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| hk_daily_adj 💰付费 | `tushare_hk_daily_adj` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| hk_fina_indicator 💰付费 | `tushare_hk_fina_indicator` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| hk_income 💰付费 | `tushare_hk_income` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| hk_mins 💰付费 | `tushare_hk_mins` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| rt_etf_k 💰付费 | `tushare_rt_etf_k` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| rt_fut_min 💰付费 | `tushare_rt_fut_min` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| rt_hk_k 💰付费 | `tushare_rt_hk_k` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |

## 外汇数据 (2 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| fx_daily | `tushare_fx_daily` | ✅ 已入库 | 12 | 28,000 | A | P3 | [查看](interfaces/tushare_fx_daily.md) |
| fx_obasic | `tushare_fx_obasic` | ✅ 已入库 | 13 | 138 | reference | P3 | [查看](interfaces/tushare_fx_obasic.md) |

## 公募基金数据 (8 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| fund_basic | `tushare_fund_basic` | ✅ 已入库 | 13 | 15,000 | reference | P1 | [查看](interfaces/tushare_fund_basic.md) |
| fund_company | `tushare_fund_company` | ✅ 已入库 | 18 | 0 | reference | P2 | [查看](interfaces/tushare_fund_company.md) |
| fund_div | `tushare_fund_div` | ❌ 未入库 | - | - | A | P2 | - |
| fund_factor_pro | `tushare_fund_factor_pro` | ✅ 已入库 | 91 | 0 | A | P2 | [查看](interfaces/tushare_fund_factor_pro.md) |
| fund_manager | `tushare_fund_manager` | ✅ 已入库 | 11 | 1 | A | P2 | [查看](interfaces/tushare_fund_manager.md) |
| fund_nav | `tushare_fund_nav` | ❌ 未入库 | - | - | A | P1 | - |
| fund_portfolio | `tushare_fund_portfolio` | ❌ 未入库 | - | - | A | P2 | - |
| fund_share | `tushare_fund_share` | ✅ 已入库 | 6 | 1,574 | A | P2 | [查看](interfaces/tushare_fund_share.md) |

## 期货数据 (11 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| ft_limit | `tushare_ft_limit` | ✅ 已入库 | 9 | 870 | A | P2 | [查看](interfaces/tushare_ft_limit.md) |
| fut_basic | `tushare_fut_basic` | ✅ 已入库 | 16 | 20,000 | reference | P2 | [查看](interfaces/tushare_fut_basic.md) |
| fut_daily | `tushare_fut_daily` | ✅ 已入库 | 16 | 2,000 | A | P2 | [查看](interfaces/tushare_fut_daily.md) |
| fut_holding | `tushare_fut_holding` | ✅ 已入库 | 10 | 1 | A | P2 | [查看](interfaces/tushare_fut_holding.md) |
| fut_index_daily | `tushare_fut_index_daily` | ❌ 未入库 | - | - | A | P2 | - |
| fut_mapping | `tushare_fut_mapping` | ✅ 已入库 | 4 | 202 | A | P2 | [查看](interfaces/tushare_fut_mapping.md) |
| fut_settle | `tushare_fut_settle` | ✅ 已入库 | 11 | 870 | A | P3 | [查看](interfaces/tushare_fut_settle.md) |
| fut_trade_cal | `tushare_fut_trade_cal` | ❌ 未入库 | - | - | reference | P2 | - |
| fut_weekly_detail | `tushare_fut_weekly_detail` | ✅ 已入库 | 18 | 1 | A | P3 | [查看](interfaces/tushare_fut_weekly_detail.md) |
| fut_weekly_monthly | `tushare_fut_weekly_monthly` | ❌ 未入库 | - | - | A | P2 | - |
| fut_wsr | `tushare_fut_wsr` | ✅ 已入库 | 9 | 1 | A | P3 | [查看](interfaces/tushare_fut_wsr.md) |

## 指数数据 (28 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| anns_d 💰付费 | `tushare_anns_d` | ❌ 未入库 | - | - | special | P3 | - |
| cctv_news 💰付费 | `tushare_cctv_news` | ❌ 未入库 | - | - | special | P3 | - |
| ci_daily | `tushare_ci_daily` | ✅ 已入库 | 12 | 437 | A | P2 | [查看](interfaces/tushare_ci_daily.md) |
| ci_index_member | `tushare_ci_index_member` | ✅ 已入库 | 12 | 5,000 | reference | P2 | [查看](interfaces/tushare_ci_index_member.md) |
| daily_info | `tushare_daily_info` | ✅ 已入库 | 15 | 12 | A | P2 | [查看](interfaces/tushare_daily_info.md) |
| idx_factor_pro | `tushare_idx_factor_pro` | ✅ 已入库 | 90 | 3,328 | A | P2 | [查看](interfaces/tushare_idx_factor_pro.md) |
| index_basic | `tushare_index_basic` | ✅ 已入库 | 14 | 8,000 | reference | P0 | [查看](interfaces/tushare_index_basic.md) |
| index_classify | `tushare_index_classify` | ✅ 已入库 | 8 | 1 | reference | P1 | [查看](interfaces/tushare_index_classify.md) |
| index_daily | `tushare_index_daily` | ✅ 已入库 | 12 | 16,808 | A | P0 | [查看](interfaces/tushare_index_daily.md) |
| index_dailybasic | `tushare_index_dailybasic` | ✅ 已入库 | 13 | 12 | A | P1 | [查看](interfaces/tushare_index_dailybasic.md) |
| index_global | `tushare_index_global` | ✅ 已入库 | 12 | 20 | A | P2 | [查看](interfaces/tushare_index_global.md) |
| index_member_all | `tushare_index_member_all` | ✅ 已入库 | 12 | 3,000 | reference | P2 | [查看](interfaces/tushare_index_member_all.md) |
| idx_mins 💰付费 | `tushare_index_mins` | ❌ 未入库 | - | - | special | P3 | - |
| index_monthly | `tushare_index_monthly` | ❌ 未入库 | - | - | A | P1 | - |
| index_weekly | `tushare_index_weekly` | ✅ 已入库 | 12 | 1,000 | A | P1 | [查看](interfaces/tushare_index_weekly.md) |
| index_weight | `tushare_index_weight` | ✅ 已入库 | 5 | 551,558 | A | P1 | [查看](interfaces/tushare_index_weight.md) |
| irm_qa_sh 💰付费 | `tushare_irm_qa_sh` | ❌ 未入库 | - | - | special | P3 | - |
| irm_qa_sz 💰付费 | `tushare_irm_qa_sz` | ❌ 未入库 | - | - | special | P3 | - |
| major_news 💰付费 | `tushare_major_news` | ❌ 未入库 | - | - | special | P3 | - |
| news 💰付费 | `tushare_news` | ❌ 未入库 | - | - | special | P3 | - |
| npr 💰付费 | `tushare_npr` | ❌ 未入库 | - | - | special | P3 | - |
| opt_mins 💰付费 | `tushare_opt_mins` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| research_report 💰付费 | `tushare_research_report` | ❌ 未入库 | - | - | special | P3 | - |
| rt_idx_k 💰付费 | `tushare_rt_idx_k` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| rt_idx_min 💰付费 | `tushare_rt_idx_min` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| rt_sw_k 💰付费 | `tushare_rt_sw_k` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| sw_daily | `tushare_sw_daily` | ✅ 已入库 | 16 | 439 | A | P2 | [查看](interfaces/tushare_sw_daily.md) |
| sz_daily_info | `tushare_sz_daily_info` | ✅ 已入库 | 10 | 14 | A | P2 | [查看](interfaces/tushare_sz_daily_info.md) |

## 宏观经济数据 (18 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| cn_cpi | `tushare_cn_cpi` | ✅ 已入库 | 5 | 507 | D | P3 | [查看](interfaces/tushare_cn_cpi.md) |
| cn_gdp | `tushare_cn_gdp` | ✅ 已入库 | 10 | 176 | D | P3 | [查看](interfaces/tushare_cn_gdp.md) |
| cn_m | `tushare_cn_m` | ✅ 已入库 | 8 | 579 | D | P3 | [查看](interfaces/tushare_cn_m.md) |
| cn_pmi | `tushare_cn_pmi` | ✅ 已入库 | 66 | 0 | D | P3 | [查看](interfaces/tushare_cn_pmi.md) |
| cn_ppi | `tushare_cn_ppi` | ✅ 已入库 | 5 | 414 | D | P3 | [查看](interfaces/tushare_cn_ppi.md) |
| gz_index | `tushare_gz_index` | ✅ 已入库 | 8 | 1 | D | P3 | [查看](interfaces/tushare_gz_index.md) |
| hibor | `tushare_hibor` | ✅ 已入库 | 10 | 119 | D | P3 | [查看](interfaces/tushare_hibor.md) |
| libor | `tushare_libor` | ✅ 已入库 | 10 | 121 | D | P3 | [查看](interfaces/tushare_libor.md) |
| sf_month | `tushare_sf_month` | ✅ 已入库 | 5 | 1 | D | P3 | [查看](interfaces/tushare_sf_month.md) |
| shibor | `tushare_shibor` | ✅ 已入库 | 10 | 4,001 | D | P3 | [查看](interfaces/tushare_shibor.md) |
| shibor_lpr | `tushare_shibor_lpr` | ✅ 已入库 | 4 | 1,601 | D | P3 | [查看](interfaces/tushare_shibor_lpr.md) |
| shibor_quote | `tushare_shibor_quote` | ✅ 已入库 | 19 | 1 | D | P3 | [查看](interfaces/tushare_shibor_quote.md) |
| us_tbr | `tushare_us_tbr` | ✅ 已入库 | 12 | 1 | D | P3 | [查看](interfaces/tushare_us_tbr.md) |
| us_tltr | `tushare_us_tltr` | ✅ 已入库 | 5 | 1 | D | P3 | [查看](interfaces/tushare_us_tltr.md) |
| us_trltr | `tushare_us_trltr` | ✅ 已入库 | 3 | 1 | D | P3 | [查看](interfaces/tushare_us_trltr.md) |
| us_trycr | `tushare_us_trycr` | ✅ 已入库 | 7 | 1 | D | P3 | [查看](interfaces/tushare_us_trycr.md) |
| us_tycr | `tushare_us_tycr` | ✅ 已入库 | 14 | 1 | D | P3 | [查看](interfaces/tushare_us_tycr.md) |
| wz_index | `tushare_wz_index` | ✅ 已入库 | 14 | 1 | D | P3 | [查看](interfaces/tushare_wz_index.md) |

## 期权数据 (12 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| opt_basic | `tushare_opt_basic` | ✅ 已入库 | 19 | 24,438 | reference | P2 | [查看](interfaces/tushare_opt_basic.md) |
| opt_daily | `tushare_opt_daily` | ✅ 已入库 | 14 | 15,000 | A | P2 | [查看](interfaces/tushare_opt_daily.md) |
| pro_bar 💰付费 | `tushare_pro_bar` | ❌ 未入库 | - | - | special | P3 | - |
| rt_k 💰付费 | `tushare_rt_k` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| rt_min 💰付费 | `tushare_rt_min` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| slb_len_mm 💰付费 | `tushare_slb_len_mm` | ❌ 未入库 | - | - | special | P3 | - |
| slb_sec 💰付费 | `tushare_slb_sec` | ❌ 未入库 | - | - | special | P3 | - |
| slb_sec_detail 💰付费 | `tushare_slb_sec_detail` | ❌ 未入库 | - | - | special | P3 | - |
| stk_account 💰付费 | `tushare_stk_account` | ❌ 未入库 | - | - | special | P3 | - |
| stk_mins 💰付费 | `tushare_stock_mins` | ❌ 未入库 | - | - | special | P3 | - |
| us_basic 💰付费 | `tushare_us_basic` | ❌ 未入库 | - | - | ⚠️ reference | P3 | - |
| us_daily 💰付费 | `tushare_us_daily` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |

## 其他 (15 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| cyq_d | `tushare_cyq_d` | ❌ 未入库 | - | - | ⚠️ C | P3 | - |
| film_boxoffice | `tushare_film_boxoffice` | ❌ 未入库 | - | - | ⚠️ D | P3 | - |
| film_daily | `tushare_film_daily` | ❌ 未入库 | - | - | ⚠️ D | P3 | - |
| hk_dividend | `tushare_hk_dividend` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| hk_hold_detail | `tushare_hk_hold_detail` | ❌ 未入库 | - | - | ⚠️ C | P3 | - |
| hk_moneyflow | `tushare_hk_moneyflow` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| hk_monthly | `tushare_hk_monthly` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| hk_top10 | `tushare_hk_top10` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| hk_weekly | `tushare_hk_weekly` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| idx_mins | `tushare_idx_mins` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| us_dividend | `tushare_us_dividend` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| us_moneyflow | `tushare_us_moneyflow` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| us_monthly | `tushare_us_monthly` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| us_top10 | `tushare_us_top10` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| us_weekly | `tushare_us_weekly` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |

## 现货数据 (2 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| sge_basic | `tushare_sge_basic` | ✅ 已入库 | 15 | 26 | reference | P3 | [查看](interfaces/tushare_sge_basic.md) |
| sge_daily | `tushare_sge_daily` | ✅ 已入库 | 15 | 14,041 | A | P3 | [查看](interfaces/tushare_sge_daily.md) |

## 股票基础信息 (13 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| bak_basic | `tushare_bak_basic` | ✅ 已入库 | 25 | 5,517 | reference | P3 | [查看](interfaces/tushare_bak_basic.md) |
| bse_mapping | `tushare_bse_mapping` | ✅ 已入库 | 5 | 1 | reference | P2 | [查看](interfaces/tushare_bse_mapping.md) |
| namechange | `tushare_namechange` | ✅ 已入库 | 7 | 2,709 | reference | P2 | [查看](interfaces/tushare_namechange.md) |
| new_share | `tushare_new_share` | ✅ 已入库 | 13 | 1 | reference | P1 | [查看](interfaces/tushare_new_share.md) |
| st | `tushare_st` | ✅ 已入库 | 8 | 1 | B | P2 | [查看](interfaces/tushare_st.md) |
| stk_managers | `tushare_stk_managers` | ✅ 已入库 | 12 | 0 | reference | P1 | [查看](interfaces/tushare_stk_managers.md) |
| stk_premarket | `tushare_stk_premarket` | ❌ 未入库 | - | - | B | P2 | - |
| stk_rewards | `tushare_stk_rewards` | ❌ 未入库 | - | - | reference | P1 | - |
| stock_basic | `tushare_stock_basic` | ✅ 已入库 | 11 | 11,020 | reference | P0 | [查看](interfaces/tushare_stock_basic.md) |
| stock_company | `tushare_stock_company` | ✅ 已入库 | 17 | 6,272 | reference | P0 | [查看](interfaces/tushare_stock_company.md) |
| stock_hsgt | `tushare_stock_hsgt` | ✅ 已入库 | 6 | 1,747 | reference | P1 | [查看](interfaces/tushare_stock_hsgt.md) |
| stock_st | `tushare_stock_st` | ✅ 已入库 | 6 | 185 | B | P2 | [查看](interfaces/tushare_stock_st.md) |
| trade_cal | `tushare_trade_cal` | ✅ 已入库 | 5 | 13,162 | reference | P0 | [查看](interfaces/tushare_trade_cal.md) |

## 股票行情数据 (15 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| adj_factor | `tushare_adj_factor` | ✅ 已入库 | 4 | 7,647,726 | A | P0 | [查看](interfaces/tushare_adj_factor.md) |
| bak_daily | `tushare_bak_daily` | ✅ 已入库 | 32 | 5,517 | A | P3 | [查看](interfaces/tushare_bak_daily.md) |
| daily_basic | `tushare_daily_basic` | ✅ 已入库 | 19 | 11,926,529 | B | P0 | [查看](interfaces/tushare_daily_basic.md) |
| ggt_daily | `tushare_ggt_daily` | ✅ 已入库 | 6 | 1 | A | P2 | [查看](interfaces/tushare_ggt_daily.md) |
| ggt_monthly | `tushare_ggt_monthly` | ✅ 已入库 | 10 | 1 | A | P3 | [查看](interfaces/tushare_ggt_monthly.md) |
| ggt_top10 | `tushare_ggt_top10` | ✅ 已入库 | 18 | 13 | A | P2 | [查看](interfaces/tushare_ggt_top10.md) |
| hsgt_top10 | `tushare_hsgt_top10` | ✅ 已入库 | 12 | 20 | A | P2 | [查看](interfaces/tushare_hsgt_top10.md) |
| stk_limit | `tushare_stk_limit` | ✅ 已入库 | 5 | 7,560 | B | P1 | [查看](interfaces/tushare_stk_limit.md) |
| stk_week_month_adj | `tushare_stk_week_month_adj` | ❌ 未入库 | - | - | A | P2 | - |
| stk_weekly_monthly | `tushare_stk_weekly_monthly` | ❌ 未入库 | - | - | A | P2 | - |
| daily | `tushare_stock_daily` | ✅ 已入库 | 12 | 7,447,997 | A | P0 | [查看](interfaces/tushare_stock_daily.md) |
| monthly | `tushare_stock_monthly` | ✅ 已入库 | 14 | 357,979 | A | P1 | [查看](interfaces/tushare_stock_monthly.md) |
| weekly | `tushare_stock_weekly` | ✅ 已入库 | 12 | 1,544,344 | A | P0 | [查看](interfaces/tushare_stock_weekly.md) |
| suspend_d | `tushare_suspend_d` | ✅ 已入库 | 5 | 22 | B | P1 | [查看](interfaces/tushare_suspend_d.md) |
| us_daily_adj 💰付费 | `tushare_us_daily_adj` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |

## 财务数据 (10 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| balancesheet | `tushare_balancesheet` | ✅ 已入库 | 153 | 122,180 | D | P0 | [查看](interfaces/tushare_balancesheet.md) |
| cashflow | `tushare_cashflow` | ✅ 已入库 | 98 | 123,676 | D | P0 | [查看](interfaces/tushare_cashflow.md) |
| disclosure_date | `tushare_disclosure_date` | ✅ 已入库 | 6 | 6,000 | reference | P2 | [查看](interfaces/tushare_disclosure_date.md) |
| dividend | `tushare_dividend` | ✅ 已入库 | 15 | 0 | D | P1 | [查看](interfaces/tushare_dividend.md) |
| express | `tushare_express` | ✅ 已入库 | 16 | 0 | D | P2 | [查看](interfaces/tushare_express.md) |
| fina_audit | `tushare_fina_audit` | ❌ 未入库 | - | - | D | P1 | - |
| fina_indicator | `tushare_fina_indicator` | ✅ 已入库 | 109 | 118,565 | D | P0 | [查看](interfaces/tushare_fina_indicator.md) |
| fina_mainbz | `tushare_fina_mainbz` | ✅ 已入库 | 9 | 35,734 | saturday | P1 | [查看](interfaces/tushare_fina_mainbz.md) |
| forecast | `tushare_forecast` | ✅ 已入库 | 14 | 0 | D | P2 | [查看](interfaces/tushare_forecast.md) |
| income | `tushare_income` | ✅ 已入库 | 87 | 123,800 | D | P0 | [查看](interfaces/tushare_income.md) |

## 涨跌板/板块数据 (22 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| dc_daily | `tushare_dc_daily` | ✅ 已入库 | 14 | 151,295 | C | P1 | [查看](interfaces/tushare_dc_daily.md) |
| dc_hot | `tushare_dc_hot` | ❌ 未入库 | - | - | C | P2 | - |
| dc_index | `tushare_dc_index` | ✅ 已入库 | 14 | 1,018 | reference | P1 | [查看](interfaces/tushare_dc_index.md) |
| dc_member | `tushare_dc_member` | ❌ 未入库 | - | - | reference | P2 | - |
| hm_detail | `tushare_hm_detail` | ✅ 已入库 | 9 | 74 | C | P2 | [查看](interfaces/tushare_hm_detail.md) |
| hm_list | `tushare_hm_list` | ✅ 已入库 | 4 | 1 | reference | P2 | [查看](interfaces/tushare_hm_list.md) |
| kpl_concept_cons | `tushare_kpl_concept_cons` | ✅ 已入库 | 8 | 6 | reference | P3 | [查看](interfaces/tushare_kpl_concept_cons.md) |
| kpl_list | `tushare_kpl_list` | ✅ 已入库 | 25 | 68 | C | P2 | [查看](interfaces/tushare_kpl_list.md) |
| limit_cpt_list | `tushare_limit_cpt_list` | ✅ 已入库 | 10 | 20 | C | P2 | [查看](interfaces/tushare_limit_cpt_list.md) |
| limit_list_d | `tushare_limit_list_d` | ✅ 已入库 | 19 | 153,233 | C | P1 | [查看](interfaces/tushare_limit_list_d.md) |
| limit_list_ths | `tushare_limit_list_ths` | ✅ 已入库 | 19 | 68 | C | P2 | [查看](interfaces/tushare_limit_list_ths.md) |
| limit_step | `tushare_limit_step` | ✅ 已入库 | 5 | 10 | C | P1 | [查看](interfaces/tushare_limit_step.md) |
| stk_auction | `tushare_stk_auction` | ❌ 未入库 | - | - | ⚠️ C | P2 | - |
| tdx_daily | `tushare_tdx_daily` | ❌ 未入库 | - | - | ⚠️ C | P2 | - |
| tdx_index | `tushare_tdx_index` | ✅ 已入库 | 10 | 481 | reference | P2 | [查看](interfaces/tushare_tdx_index.md) |
| tdx_member | `tushare_tdx_member` | ✅ 已入库 | 5 | 20 | reference | P2 | [查看](interfaces/tushare_tdx_member.md) |
| ths_daily | `tushare_ths_daily` | ✅ 已入库 | 13 | 229,232 | C | P1 | [查看](interfaces/tushare_ths_daily.md) |
| ths_hot | `tushare_ths_hot` | ✅ 已入库 | 12 | 0 | C | P2 | [查看](interfaces/tushare_ths_hot.md) |
| ths_index | `tushare_ths_index` | ✅ 已入库 | 7 | 1,724 | reference | P1 | [查看](interfaces/tushare_ths_index.md) |
| ths_member | `tushare_ths_member` | ✅ 已入库 | 4 | 2 | reference | P1 | [查看](interfaces/tushare_ths_member.md) |
| top_inst | `tushare_top_inst` | ✅ 已入库 | 11 | 95,907 | C | P2 | [查看](interfaces/tushare_top_inst.md) |
| top_list | `tushare_top_list` | ✅ 已入库 | 16 | 96,885 | C | P1 | [查看](interfaces/tushare_top_list.md) |

## 资金流向 (8 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| moneyflow | `tushare_moneyflow` | ✅ 已入库 | 21 | 7,475,714 | B | P1 | [查看](interfaces/tushare_moneyflow.md) |
| moneyflow_cnt_ths | `tushare_moneyflow_cnt_ths` | ❌ 未入库 | - | - | C | P2 | - |
| moneyflow_dc | `tushare_moneyflow_dc` | ✅ 已入库 | 16 | 5,000 | C | P2 | [查看](interfaces/tushare_moneyflow_dc.md) |
| moneyflow_hsgt | `tushare_moneyflow_hsgt` | ✅ 已入库 | 8 | 350 | B | P1 | [查看](interfaces/tushare_moneyflow_hsgt.md) |
| moneyflow_ind_dc | `tushare_moneyflow_ind_dc` | ✅ 已入库 | 19 | 1,018 | C | P2 | [查看](interfaces/tushare_moneyflow_ind_dc.md) |
| moneyflow_ind_ths | `tushare_moneyflow_ind_ths` | ❌ 未入库 | - | - | C | P2 | - |
| moneyflow_mkt_dc | `tushare_moneyflow_mkt_dc` | ✅ 已入库 | 16 | 1 | C | P2 | [查看](interfaces/tushare_moneyflow_mkt_dc.md) |
| moneyflow_ths | `tushare_moneyflow_ths` | ❌ 未入库 | - | - | C | P2 | - |

## 融资融券/质押/大宗交易等参考数据 (18 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| block_trade | `tushare_block_trade` | ✅ 已入库 | 8 | 42,305 | B | P1 | [查看](interfaces/tushare_block_trade.md) |
| margin | `tushare_margin` | ✅ 已入库 | 13 | 3,829 | B | P1 | [查看](interfaces/tushare_margin.md) |
| margin_detail | `tushare_margin_detail` | ✅ 已入库 | 11 | 460,394 | B | P1 | [查看](interfaces/tushare_margin_detail.md) |
| margin_secs | `tushare_margin_secs` | ✅ 已入库 | 5 | 4,412 | B | P2 | [查看](interfaces/tushare_margin_secs.md) |
| pledge_detail | `tushare_pledge_detail` | ❌ 未入库 | - | - | B | P2 | - |
| pledge_stat | `tushare_pledge_stat` | ✅ 已入库 | 8 | 1 | B | P2 | [查看](interfaces/tushare_pledge_stat.md) |
| repurchase | `tushare_repurchase` | ✅ 已入库 | 10 | 1 | B | P2 | [查看](interfaces/tushare_repurchase.md) |
| share_float | `tushare_share_float` | ✅ 已入库 | 8 | 1 | B | P2 | [查看](interfaces/tushare_share_float.md) |
| slb_len | `tushare_slb_len` | ✅ 已入库 | 7 | 0 | B | P2 | [查看](interfaces/tushare_slb_len.md) |
| stk_account_old | `tushare_stk_account_old` | ✅ 已入库 | 10 | 1 | reference | P3 | [查看](interfaces/tushare_stk_account_old.md) |
| stk_holdernumber | `tushare_stk_holdernumber` | ✅ 已入库 | 5 | 1 | B | P2 | [查看](interfaces/tushare_stk_holdernumber.md) |
| stk_holdertrade | `tushare_stk_holdertrade` | ✅ 已入库 | 12 | 22,012 | saturday | P2 | [查看](interfaces/tushare_stk_holdertrade.md) |
| top10_floatholders | `tushare_top10_floatholders` | ✅ 已入库 | 10 | 119,217 | saturday | P2 | [查看](interfaces/tushare_top10_floatholders.md) |
| top10_holders | `tushare_top10_holders` | ✅ 已入库 | 10 | 26,806 | saturday | P2 | [查看](interfaces/tushare_top10_holders.md) |
| us_adjfactor 💰付费 | `tushare_us_adjfactor` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| us_balancesheet 💰付费 | `tushare_us_balancesheet` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| us_cashflow 💰付费 | `tushare_us_cashflow` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| us_income 💰付费 | `tushare_us_income` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |

## 特色数据 (13 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| broker_recommend | `tushare_broker_recommend` | ❌ 未入库 | - | - | C | P2 | - |
| ccass_hold | `tushare_ccass_hold` | ✅ 已入库 | 7 | 0 | C | P2 | [查看](interfaces/tushare_ccass_hold.md) |
| ccass_hold_detail | `tushare_ccass_hold_detail` | ✅ 已入库 | 8 | 922 | C | P2 | [查看](interfaces/tushare_ccass_hold_detail.md) |
| cyq_chips | `tushare_cyq_chips` | ❌ 未入库 | - | - | C | P2 | - |
| cyq_perf | `tushare_cyq_perf` | ✅ 已入库 | 12 | 7,536,060 | C | P1 | [查看](interfaces/tushare_cyq_perf.md) |
| hk_hold | `tushare_hk_hold` | ✅ 已入库 | 8 | 924 | C | P2 | [查看](interfaces/tushare_hk_hold.md) |
| report_rc | `tushare_report_rc` | ✅ 已入库 | 22 | 1 | C | P2 | [查看](interfaces/tushare_report_rc.md) |
| stk_ah_comparison | `tushare_stk_ah_comparison` | ❌ 未入库 | - | - | C | P2 | - |
| stk_auction_c | `tushare_stk_auction_c` | ✅ 已入库 | 10 | 5,510 | C | P2 | [查看](interfaces/tushare_stk_auction_c.md) |
| stk_auction_o | `tushare_stk_auction_o` | ✅ 已入库 | 10 | 5,487 | C | P2 | [查看](interfaces/tushare_stk_auction_o.md) |
| stk_factor_pro | `tushare_stk_factor_pro` | ✅ 已入库 | 262 | 7,332,731 | C | P1 | [查看](interfaces/tushare_stk_factor_pro.md) |
| stk_nineturn | `tushare_stk_nineturn` | ✅ 已入库 | 14 | 0 | C | P2 | [查看](interfaces/tushare_stk_nineturn.md) |
| stk_surv | `tushare_stk_surv` | ✅ 已入库 | 10 | 0 | C | P2 | [查看](interfaces/tushare_stk_surv.md) |

## 文娱产业数据 (8 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| bo_cinema | `tushare_bo_cinema` | ❌ 未入库 | - | - | D | P3 | - |
| bo_daily | `tushare_bo_daily` | ❌ 未入库 | - | - | D | P3 | - |
| bo_monthly | `tushare_bo_monthly` | ❌ 未入库 | - | - | D | P3 | - |
| bo_weekly | `tushare_bo_weekly` | ❌ 未入库 | - | - | D | P3 | - |
| film_record | `tushare_film_record` | ❌ 未入库 | - | - | ⚠️ D | P3 | - |
| teleplay_record | `tushare_teleplay_record` | ✅ 已入库 | 14 | 1 | D | P3 | [查看](interfaces/tushare_teleplay_record.md) |
| tmt_twincome | `tushare_tmt_twincome` | ❌ 未入库 | - | - | ⚠️ D | P3 | - |
| tmt_twincomedetail | `tushare_tmt_twincomedetail` | ❌ 未入库 | - | - | ⚠️ D | P3 | - |

## 其他 (3 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| hk_tradecal 💰付费 | `tushare_hk_tradecal` | ❌ 未入库 | - | - | ⚠️ reference | P3 | - |
| us_fina_indicator 💰付费 | `tushare_us_fina_indicator` | ❌ 未入库 | - | - | ⚠️ A | P3 | - |
| us_tradecal 💰付费 | `tushare_us_tradecal` | ❌ 未入库 | - | - | ⚠️ reference | P3 | - |

## 财富销售数据 (2 个接口)

| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |
|------|------|------|--------|------|------|--------|------|
| fund_sales_ratio | `tushare_fund_sales_ratio` | ✅ 已入库 | 7 | 1 | D | P3 | [查看](interfaces/tushare_fund_sales_ratio.md) |
| fund_sales_vol | `tushare_fund_sales_vol` | ✅ 已入库 | 7 | 1 | D | P3 | [查看](interfaces/tushare_fund_sales_vol.md) |

## 统计摘要

- 已入库: 149 个接口
- 未入库(已配置): 78 个接口
- 未入库(付费/未配置): 15 个接口

## 未入库接口明细

- **anns_d** (`tushare_anns_d`) — 指数数据 | 状态: 未配置 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **bc_bestotcqt** (`tushare_bc_bestotcqt`) — 债券数据 | 状态: 已禁用 | 优先级: P3 | 模式: incremental | 频率: normal
- **bc_otcqt** (`tushare_bc_otcqt`) — 债券数据 | 状态: 已禁用 | 优先级: P3 | 模式: incremental | 频率: normal
- **bo_cinema** (`tushare_bo_cinema`) — 文娱产业数据 | 状态: 已启用 | 优先级: P3 | 模式: incremental | 频率: normal
- **bo_daily** (`tushare_bo_daily`) — 文娱产业数据 | 状态: 已启用 | 优先级: P3 | 模式: incremental | 频率: normal
- **bo_monthly** (`tushare_bo_monthly`) — 文娱产业数据 | 状态: 已启用 | 优先级: P3 | 模式: incremental | 频率: normal
- **bo_weekly** (`tushare_bo_weekly`) — 文娱产业数据 | 状态: 已启用 | 优先级: P3 | 模式: incremental | 频率: normal
- **broker_recommend** (`tushare_broker_recommend`) — 特色数据 | 状态: 已启用 | 优先级: P2 | 模式: incremental | 频率: special
- **cb_price_chg** (`tushare_cb_price_chg`) — 债券数据 | 状态: 已启用 | 优先级: P3 | 模式: incremental | 频率: normal
- **cctv_news** (`tushare_cctv_news`) — 指数数据 | 状态: 未配置 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **cyq_chips** (`tushare_cyq_chips`) — 特色数据 | 状态: 已启用 | 优先级: P2 | 模式: incremental | 频率: special
- **dc_hot** (`tushare_dc_hot`) — 涨跌板/板块数据 | 状态: 已启用 | 优先级: P2 | 模式: incremental | 频率: special
- **dc_member** (`tushare_dc_member`) — 涨跌板/板块数据 | 状态: 已启用 | 优先级: P2 | 模式: full | 频率: special
- **etf_iopv** (`tushare_etf_iopv`) — ETF/基金数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **film_record** (`tushare_film_record`) — 文娱产业数据 | 状态: 已禁用 | 优先级: P3 | 模式: incremental | 频率: normal
- **fina_audit** (`tushare_fina_audit`) — 财务数据 | 状态: 已启用 | 优先级: P1 | 模式: incremental | 频率: special
- **ft_mins** (`tushare_ft_mins`) — ETF/基金数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **fund_div** (`tushare_fund_div`) — 公募基金数据 | 状态: 已启用 | 优先级: P2 | 模式: incremental | 频率: normal
- **fund_nav** (`tushare_fund_nav`) — 公募基金数据 | 状态: 已启用 | 优先级: P1 | 模式: incremental | 频率: normal
- **fund_portfolio** (`tushare_fund_portfolio`) — 公募基金数据 | 状态: 已启用 | 优先级: P2 | 模式: incremental | 频率: normal
- **fut_index_daily** (`tushare_fut_index_daily`) — 期货数据 | 状态: 已启用 | 优先级: P2 | 模式: incremental | 频率: normal
- **fut_trade_cal** (`tushare_fut_trade_cal`) — 期货数据 | 状态: 已启用 | 优先级: P2 | 模式: full | 频率: normal
- **fut_weekly_monthly** (`tushare_fut_weekly_monthly`) — 期货数据 | 状态: 已启用 | 优先级: P2 | 模式: incremental | 频率: normal
- **hk_adjfactor** (`tushare_hk_adjfactor`) — ETF/基金数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **hk_balancesheet** (`tushare_hk_balancesheet`) — ETF/基金数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **hk_basic** (`tushare_hk_basic`) — ETF/基金数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **hk_cashflow** (`tushare_hk_cashflow`) — ETF/基金数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **hk_daily** (`tushare_hk_daily`) — ETF/基金数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **hk_daily_adj** (`tushare_hk_daily_adj`) — ETF/基金数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **hk_fina_indicator** (`tushare_hk_fina_indicator`) — ETF/基金数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **hk_income** (`tushare_hk_income`) — ETF/基金数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **hk_mins** (`tushare_hk_mins`) — ETF/基金数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **hk_tradecal** (`tushare_hk_tradecal`) — 其他 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **idx_mins** (`tushare_index_mins`) — 指数数据 | 状态: 未配置 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **index_monthly** (`tushare_index_monthly`) — 指数数据 | 状态: 已启用 | 优先级: P1 | 模式: incremental | 频率: special
- **irm_qa_sh** (`tushare_irm_qa_sh`) — 指数数据 | 状态: 未配置 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **irm_qa_sz** (`tushare_irm_qa_sz`) — 指数数据 | 状态: 未配置 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **major_news** (`tushare_major_news`) — 指数数据 | 状态: 未配置 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **moneyflow_cnt_ths** (`tushare_moneyflow_cnt_ths`) — 资金流向 | 状态: 已启用 | 优先级: P2 | 模式: incremental | 频率: special
- **moneyflow_ind_ths** (`tushare_moneyflow_ind_ths`) — 资金流向 | 状态: 已启用 | 优先级: P2 | 模式: incremental | 频率: special
- **moneyflow_ths** (`tushare_moneyflow_ths`) — 资金流向 | 状态: 已启用 | 优先级: P2 | 模式: incremental | 频率: special
- **news** (`tushare_news`) — 指数数据 | 状态: 未配置 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **npr** (`tushare_npr`) — 指数数据 | 状态: 未配置 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **opt_mins** (`tushare_opt_mins`) — 指数数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **pledge_detail** (`tushare_pledge_detail`) — 融资融券/质押/大宗交易等参考数据 | 状态: 已启用 | 优先级: P2 | 模式: incremental | 频率: special
- **pro_bar** (`tushare_pro_bar`) — 期权数据 | 状态: 未配置 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **research_report** (`tushare_research_report`) — 指数数据 | 状态: 未配置 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **rt_etf_k** (`tushare_rt_etf_k`) — ETF/基金数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **rt_fut_min** (`tushare_rt_fut_min`) — ETF/基金数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **rt_hk_k** (`tushare_rt_hk_k`) — ETF/基金数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **rt_idx_k** (`tushare_rt_idx_k`) — 指数数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **rt_idx_min** (`tushare_rt_idx_min`) — 指数数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **rt_k** (`tushare_rt_k`) — 期权数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **rt_min** (`tushare_rt_min`) — 期权数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **rt_sw_k** (`tushare_rt_sw_k`) — 指数数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **slb_len_mm** (`tushare_slb_len_mm`) — 期权数据 | 状态: 未配置 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **slb_sec** (`tushare_slb_sec`) — 期权数据 | 状态: 未配置 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **slb_sec_detail** (`tushare_slb_sec_detail`) — 期权数据 | 状态: 未配置 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **stk_account** (`tushare_stk_account`) — 期权数据 | 状态: 未配置 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **stk_ah_comparison** (`tushare_stk_ah_comparison`) — 特色数据 | 状态: 已启用 | 优先级: P2 | 模式: incremental | 频率: special
- **stk_auction** (`tushare_stk_auction`) — 涨跌板/板块数据 | 状态: 已禁用 | 优先级: P2 | 模式: incremental | 频率: special
- **stk_premarket** (`tushare_stk_premarket`) — 股票基础信息 | 状态: 已启用 | 优先级: P2 | 模式: incremental | 频率: special
- **stk_rewards** (`tushare_stk_rewards`) — 股票基础信息 | 状态: 已启用 | 优先级: P1 | 模式: full | 频率: normal
- **stk_week_month_adj** (`tushare_stk_week_month_adj`) — 股票行情数据 | 状态: 已启用 | 优先级: P2 | 模式: incremental | 频率: special
- **stk_weekly_monthly** (`tushare_stk_weekly_monthly`) — 股票行情数据 | 状态: 已启用 | 优先级: P2 | 模式: incremental | 频率: special
- **stk_mins** (`tushare_stock_mins`) — 期权数据 | 状态: 未配置 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **tdx_daily** (`tushare_tdx_daily`) — 涨跌板/板块数据 | 状态: 已禁用 | 优先级: P2 | 模式: incremental | 频率: special
- **tmt_twincome** (`tushare_tmt_twincome`) — 文娱产业数据 | 状态: 已禁用 | 优先级: P3 | 模式: incremental | 频率: normal
- **tmt_twincomedetail** (`tushare_tmt_twincomedetail`) — 文娱产业数据 | 状态: 已禁用 | 优先级: P3 | 模式: incremental | 频率: normal
- **us_adjfactor** (`tushare_us_adjfactor`) — 融资融券/质押/大宗交易等参考数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **us_balancesheet** (`tushare_us_balancesheet`) — 融资融券/质押/大宗交易等参考数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **us_basic** (`tushare_us_basic`) — 期权数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **us_cashflow** (`tushare_us_cashflow`) — 融资融券/质押/大宗交易等参考数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **us_daily** (`tushare_us_daily`) — 期权数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **us_daily_adj** (`tushare_us_daily_adj`) — 股票行情数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **us_fina_indicator** (`tushare_us_fina_indicator`) — 其他 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **us_income** (`tushare_us_income`) — 融资融券/质押/大宗交易等参考数据 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
- **us_tradecal** (`tushare_us_tradecal`) — 其他 | 状态: 已禁用 💰付费 | 优先级: P3 | 模式: N/A | 频率: special
