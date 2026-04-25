# 待讨论：实施前遗留问题

> 基于 [a-ai-ai-tushare-pro-kind-gizmo.md](a-ai-ai-tushare-pro-kind-gizmo.md) 设计文档，记录未阻塞 PR1 启动但需要后续确认的细节。
> 2026-04-25 整理。

---

## 1. dc_daily 特殊起点日期缺失

**位置**：设计文档第 11 行

**现状**：
```
7 个特殊起点（bak_basic=20160101、stk_account_old=20080101、fund_sales_vol=20210101、
hm_detail=20220801、stk_nineturn=20230101、moneyflow_dc=20230911、limit_list_ths=20231101）
```

**问题**：`dc_daily`（东财概念日行情）未标注起点。它和 `moneyflow_dc`（东财概念资金流）同源，起点大概率都是 `20230911`。

**影响**：如果不写，planner 按默认 `2020-01-01` 计算会生成约 3 年无效 work units（每个交易日一次调用，浪费 ~750 次请求）。

**建议**：确认 `dc_daily` 起点后补上，变成 8 个特殊起点。

**解决时机**：PR1 生成 `config/interfaces/stock_special.yaml` 时顺手处理。

---

## 2. per_symbol_period 接口名单完整性

**位置**：设计文档第 88 行

**现状**：
```
per_symbol_period：按股票循环（fina_mainbz, top10_holders, top10_floatholders, stk_holdertrade 等长尾）
```

**问题**：用了"等"字，名单可能不全。以下接口从 Tushare 10k 清单看也可能是 `per_symbol_period` 策略：

| 接口 | 说明 | 起点 | 备注 |
|------|------|------|------|
| `hm_detail` | 大宗交易明细 | 20220801 | 按 ts_code+trade_date 循环 |
| `stk_surv` | 机构调研 | 2020 | 按上市公司循环 |
| `stk_holdernumber` | 股东人数 | 2020 | 按 ts_code 循环 |
| `holder_detail` | 股东明细 | 2020 | 按 ts_code+period 循环 |
| `top10_holders` | 前十大股东 | 2020 | 按 ts_code 循环 |
| `top10_floatholders` | 前十大流通股东 | 2020 | 按 ts_code 循环 |

**建议**：不在设计文档硬编码名单。PR2 写 `planner/strategies.py` 时，以 YAML 实际注册的 `fetch_strategy.kind == "per_symbol_period"` 为准动态统计，自动归入周六批次。

**解决时机**：PR2 实现 planner 时。

---

## 3. clickhouse-io skill 在后续 PR 的使用

**位置**：设计文档第 215–224 行 Skills/Agents 表格

**现状**：`clickhouse-io` 只在 PR1 标注。

**实际覆盖范围**：

| PR | 涉及内容 |
|----|---------|
| PR1 | 表 DDL 创建、MergeTree 引擎选择、CODEC 配置、named volume |
| PR2 | schema/inferer 类型推断 → ClickHouse 列类型映射 |
| PR4 | 增量 INSERT 性能优化（batch insert、flush 策略） |
| PR6 | verify SQL 查询（gap_detector、row_counts、checksums）的性能 |

**建议**：这不是设计缺陷，只是在 PR2/PR4/PR6 实施时记得也调 `clickhouse-io`，不要只看表格里 PR1 有标注。

**解决时机**：对应 PR 实施时提醒即可。

---

## 4. 回补执行节奏的细化

**位置**：设计文档第 146 行

**现状**：
```
周末 Day1 白天 Layer 0–2，Day1 夜间 Layer 3 长尾，Day2 白天 Layer 4–5 + weekly_reconcile 补洞。
```

**需要细化的点**：

- Layer 3 的 per_symbol_period 长尾 ~14h/接口，如果有 6 个，总共 ~84h，不是"一个夜间"能跑完的
- 是否需要在 `runner/backfill.py` 里加 `--parallel-symbols N` 参数加速？
- 是否需要按 priority 分层跑（先 P0/P1，P2/P3 后面再补）？

**建议**：第一次回补时先跑 Layer 0–2 + Layer 3 的 P0/P1，确认单接口耗时后再决定 long-tail 的并发策略。

**解决时机**：PR3 实现 backfill.py 时设计并发参数，首次回补时观察。

---

## 5. Layer 0 是否应该包含 bond_basic

**位置**：设计文档第 139 行

**现状**：Layer 0 列了 `trade_cal, stock_basic, stock_company, index_basic, fund_basic 等参考表`。

**问题**：`bond_basic`（可转债基础信息）和 `etf_basic`、`fut_basic`、`opt_basic` 等品种基础表也没明确列出。这些虽然数据量小（单次 full_once），但属于品种代码来源，应该在 Layer 0 一次性跑完。

**建议**：Layer 0 补全为：`trade_cal, stock_basic, stock_company, index_basic, etf_basic, fund_basic, bond_basic, fut_basic, opt_basic`。

**解决时机**：PR2 写 planner 时按 `priority` 和 `fetch_strategy.kind == "full_once"` 自动归入 Layer 0。

---

## 6. 7 个特殊起点接口的 batch 归属

**位置**：设计文档第 11 行 + 第 122–131 行调度表

**问题**：7 个特殊起点接口在调度表里没明确分到哪个批次（A/B/C/D/saturday）。实施时需要在 YAML 的 `batch` 字段标注清楚。

| 接口 | 分类 | 建议批次 |
|------|------|---------|
| `bak_basic` | 股票基础 | D（参考数据） |
| `stk_account_old` | 股东账户 | D |
| `fund_sales_vol` | 基金销量 | B（基金相关） |
| `hm_detail` | 大宗交易明细 | Saturday（per_symbol_period 长尾） |
| `stk_nineturn` | 九转序列 | C（特色指标） |
| `moneyflow_dc` | 东财资金流 | C（概念板块资金流） |
| `limit_list_ths` | 同花顺涨跌停 | C（涨跌停板） |

**解决时机**：PR1 生成 YAML 时标注。

---

## 状态：不阻塞 PR1 启动

以上问题均可在实施过程中顺手处理，不需要先讨论完再开工。
