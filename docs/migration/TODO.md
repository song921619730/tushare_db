# Tushare DB — TODO 任务清单

> 更新日期：2026-04-26
> 数据来源：ClickHouse 24.8 (localhost:8123, tushare) — 149 张表，41.7M 行
> PG 源：PostgreSQL 16.13 — PG→CH 迁移已完成（55 张表，20.6M 行）

---

## 一、当前数据概况

### 1.1 已完成（48 张有数据表）

| 表名 | FINAL 行数 | 说明 |
|------|-----------|------|
| tushare_adj_factor | 7,631,371 | 复权因子 |
| tushare_daily_basic | 12,032,982 | 每日指标 |
| tushare_moneyflow | 7,488,474 | 资金流 |
| tushare_stock_daily | 7,442,501 | 日线行情 |
| tushare_stk_factor_pro | 7,327,235 | 因子 Pro |
| tushare_stock_weekly | 1,538,761 | 周线行情 |
| tushare_index_weight | 551,558 | 指数权重 |
| tushare_margin_detail | 456,000 | 融资融券明细 |
| tushare_stock_monthly | 357,979 | 月线行情 |
| tushare_cyq_perf | 239,077 | 筹码分布（⚠️ 仅 157/5510 只股票） |
| tushare_ths_daily | 228,000 | 同花顺日线 |
| tushare_limit_list_d | 153,134 | 涨跌停列表 |
| tushare_dc_daily | 150,277 | 董监高交易 |
| tushare_income | 123,800 | 利润表 |
| tushare_cashflow | 123,676 | 现金流表 |
| tushare_balancesheet | 122,180 | 资产负债表 |
| tushare_fina_indicator | 118,565 | 财务指标 |
| tushare_top_list | 96,809 | 龙虎榜 |
| tushare_top_inst | 95,831 | 龙虎榜机构 |
| tushare_fund_daily | 89,098 | 基金日线 |
| tushare_index_daily | 16,808 | 指数日线 |
| tushare_fina_mainbz | 35,734 | 主营构成 |
| tushare_top10_holders | 26,806 | 十大股东 |
| tushare_stk_holdertrade | 22,012 | 股东增减持 |
| tushare_limit_list_d | 153,134 | 涨跌停 |
| *(其余 23 张)* | 各类 | 基础表、宏观表、期货基金等 |

**总计：48 张表有数据，41,699,983 行**

### 1.2 空表（101 张）— 全部有 enabled interface

| 类别 | 表数 | 优先级 | 示例 |
|------|------|--------|------|
| 股东/财务事件 | ~10 | P1-P2 | top10_floatholders, dividend, express, forecast, repurchase |
| 筹码/限制/专题 | ~8 | P1-P2 | limit_list_ths, limit_step, limit_cpt_list, ths_index, ths_member, sw_daily |
| 筹码覆盖 | 1 | P2 | **cyq_perf** — 日期完整，但仅 157/5510 只股票 |
| 港股通 | ~6 | P2 | ggt_daily, ggt_top10, hk_hold, ccass_hold |
| 期货/期权 | ~8 | P2-P3 | fut_holding, fut_settle, fut_mapping, opt_daily |
| 基金 | ~6 | P2 | fund_adj, fund_company, fund_manager, fund_share |
| 宏观/其他 | ~15 | P2-P3 | cn_pmi, eco_cal, sf_month, namechange |
| 参考表/分类 | ~20 | P1-P2 | index_classify, stock_hsgt, stock_st, suspend_d |
| 美股相关 | 5 | P3 | us_tycr, us_trycr, us_tltr, us_trltr, us_tbr |
| 其他专题 | ~13 | P2-P3 | stk_auction_o/c, kpl_list, hm_list, report_rc |

**总计：101 张空表，全部有 enabled 接口配置**

---

## 二、数据回填任务（按优先级排序）

### P0 — A 股核心补充

| ID | 表名 | 类型 | 预计时间 | 说明 |
|----|------|------|----------|------|
| D1 | cyq_perf 全量 | backfill | ~4-6h | 当前仅 157/5510 只股票，需补全所有股票 |

### P1 — A 股重要补充

| ID | 表名 | 类型 | 预计时间 | 说明 |
|----|------|------|----------|------|
| D2 | top10_floatholders | backfill | ~8h | 十大流通股东 |
| D3 | stk_holdernumber | backfill | ~4h | 股东人数 |
| D4 | dividend | backfill | ~2h | 分红送转 |
| D5 | express | backfill | ~3h | 业绩快报 |
| D6 | forecast | backfill | ~3h | 业绩预告 |
| D7 | repurchase | backfill | ~2h | 股票回购 |
| D8 | pledge_stat | backfill | ~4h | 股权质押 |
| D9 | share_float | backfill | ~4h | 限售股解禁 |

### P2 — A 股专题/分类补充

| ID | 表名 | 类型 | 预计时间 | 说明 |
|----|------|------|----------|------|
| D10 | limit_list_ths | backfill | ~3h | 同花顺涨跌停 |
| D11 | limit_cpt_list | backfill | ~2h | 涨跌停连板 |
| D12 | limit_step | backfill | ~1h | 涨跌停阶梯 |
| D13 | ths_index | backfill | ~1h | 同花顺行业指数 |
| D14 | ths_member | backfill | ~1h | 同花顺行业成分股 |
| D15 | sw_daily | backfill | ~4h | 申万日线 |
| D16 | cn_pmi | backfill | ~0.5h | PMI 宏观数据 |
| D17 | index_classify | backfill | ~0.5h | 指数分类 |
| D18 | index_dailybasic | backfill | ~2h | 指数每日指标 |
| D19 | index_weekly | backfill | ~1h | 指数周线 |
| D20 | stock_st | backfill | ~0.5h | ST 股票记录 |
| D21 | suspend_d | backfill | ~0.5h | 停牌日历 |
| D22 | stk_managers | backfill | ~2h | 上市公司董监高 |
| D23 | stk_limit | backfill | ~1h | 股票涨跌停统计 |

### P3 — 港股/基金

| ID | 表名 | 类型 | 预计时间 | 说明 |
|----|------|------|----------|------|
| D24 | ggt_daily | backfill | ~3h | 港股通每日数据 |
| D25 | ggt_top10 | backfill | ~2h | 港股通十大活跃股 |
| D26 | hk_hold | backfill | ~3h | 港股持仓 |
| D27 | fund_adj | backfill | ~2h | 基金复权因子 |
| D28 | fund_company | backfill | ~0.5h | 基金公司 |
| D29 | fund_manager | backfill | ~2h | 基金经理 |
| D30 | fund_share | backfill | ~4h | 基金份额 |

### P4 — 期货/期权（按需开启）

| ID | 表名 | 类型 | 预计时间 | 说明 |
|----|------|------|----------|------|
| D31 | fut_holding | backfill | ~2h | 期货持仓 |
| D32 | fut_settle | backfill | ~2h | 期货结算 |
| D33 | fut_mapping | backfill | ~1h | 期货合约映射 |
| D34 | opt_daily | backfill | ~3h | 期权日线 |

### P5 — 其他低优先级

| ID | 表名 | 类型 | 预计时间 | 说明 |
|----|------|------|----------|------|
| D35 | ~65 张剩余表 | backfill | ~20-30h | 美股、参考表、专题类等 |

---

## 三、工程质量任务

| ID | 任务 | 状态 | 优先级 | 说明 |
|----|------|------|--------|------|
| R10 | GitHub Actions 跑通 | 待执行 | P1 | CI 流程验证，测试 + lint |
| R6 | 5 交易日 scheduler 增量验证 | 待时间窗口 | P0 | 需等下周一至周五 |
| R7 | weekly_reconcile + verify_row_counts | 待时间窗口 | P1 | 今天周日可跑 |
| R13 | Tushare token 失效测试 | 待执行 | P2 | 异常场景验证 |
| R14 | clickhouse_data 卷损坏全量重跑 | 待执行 | P2 | 灾难恢复演练 |

---

## 四、已完成任务

| ID | 任务 | 状态 | 说明 |
|----|------|------|------|
| R1 | adj_factor 全量到今日 | 完成 | 7.57M 行 |
| R2 | stock_daily + daily_basic 全量 | 完成 | 7.4M+ 行 |
| R3 | moneyflow + moneyflow_hsgt 全量 | 完成 | 7.1M 行 |
| R4 | 财务 5 表扩量 | 完成 | income 123K 行等 |
| R5 | fina_mainbz / top10_holders / stk_holdertrade | 完成 | 35,734 / 26,806 / 22,012 行 |
| R8 | qfq/hfq 数学正确性验证 | 完成 | 茅台 600519.SH |
| R9 | Grafana API 配额监控面板 | 完成 | 5 个新 panel |
| R11 | 5 个 empty_sample 接口复活 | 完成 | fina_mainbz, dc_hot, index_monthly, moneyflow_ths/ind_ths/cnt_ths |
| R12 | 设计文档更新为 174 enabled | 完成 | 实际 175 enabled |
| R15 | PG→CH 迁移 6 表 + 排序键修复 6 表 | 完成 | 全部行数一致 |
| R16 | planner.py get_symbols 表名修复 | 完成 | stock_basic → tushare_stock_basic |
| R17 | 全量 PG 扫描 27 张新表 Bootstrap + 迁移 | 完成 | 55 张表，20.6M 行 |

---

## 五、建议执行顺序

### 立即执行（今天）
1. **R7** — weekly_reconcile + verify_row_counts（今天周日正好）
2. **D1** — cyq_perf 全量回填（唯一一张"有数据但不完整"的表）
3. **D2** — top10_floatholders（与 R5 同策略，已有经验）

### 本周（周一至周五）
4. **D3-D9** — A 股重要补充表（股东类、财务事件类）
5. **R6** — 观察 5 交易日 scheduler 增量是否正常
6. **D10-D23** — A 股专题表（limit_list_ths、ths_index、sw_daily 等）

### 有空再说
7. **R10** — GitHub Actions
8. **D24-D30** — 港股/基金
9. **D31-D34** — 期货/期权
10. **D35** — 其他剩余 65 张表
11. **R13/R14** — 灾难演练

---

## 六、已知问题

| 问题 | 影响 | 状态 |
|------|------|------|
| hermes-agent 外部进程干扰 backfill | 导致 sync_state 膨胀、数据重复 | 已修复（杀掉进程 + OPTIMIZE） |
| 排序键使用不存在的 period 列 | top10_holders/stk_holdertrade 数据丢失 | 已修复（改为 end_date/ann_date） |
| scheduler 并发导致孤儿 running 单元 | 5-6 个单元永远不完成 | 已修复（手动标记 failed + resume） |
| Decimal NaN 写入 ClickHouse 失败 | limit_list_d 迁移失败 | 已修复（normalize_value 处理） |
| Nullable(Date) 序列化 bug | clickhouse_connect 库 bug | 已修复（直接 SQL INSERT） |
