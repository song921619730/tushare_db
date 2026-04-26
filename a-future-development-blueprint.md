# Tushare DB 未来开发蓝图：从数据仓库到 AI 量化作战平台

> 文档版本：v1.0
> 编制日期：2026-04-26
> 编制者：Sonnet 4.6
> 适用范围：tushare-db 项目长期演进规划（V2.0 → V6.0）
>
> **核心定位**：现在的 tushare-db 是一个"数据仓库"，未来要演化为**个人 AI 量化作战平台**——既能让 Claude / Hermes / OpenClaw 高效查数，又能驱动你的选股策略和实盘交易。
>
> **本文档不是"必须全做"的命令**，而是"按需选取"的菜单。下半部分（V5/V6）涉及实盘风险，**强烈建议保守推进**。

---

## 0. TL;DR 一图看懂

```
                    ┌─────────────────────────────────────┐
                    │   你 + Claude / Hermes / OpenClaw   │
                    └──────────────┬──────────────────────┘
                                   │ MCP / SQL / Web
                    ┌──────────────▼──────────────────────┐
   V2 智能问答      │  AI 接入层（NL→SQL + 缓存 + 流式）    │  ← 1-2 周
                    ├─────────────────────────────────────┤
   V3 因子工程      │  因子计算引擎（60+ 因子物化表）       │  ← 2-3 周
                    ├─────────────────────────────────────┤
   V4 策略框架      │  策略 DSL + 回测引擎 + 风控           │  ← 3-4 周
                    ├─────────────────────────────────────┤
   V5 AI 增强       │  LLM 财报解读 + 舆情 + AI 复盘         │  ← 持续迭代
                    ├─────────────────────────────────────┤
   V6 实盘对接      │  券商接口 + 订单管理 + 业绩归因        │  ← 高风险
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │  当前 tushare-db (ClickHouse)        │  ← V1.0 已完成
                    │  • 169 张表 / 1500 万行              │
                    │  • MCP Server / Grafana / Dashboard  │
                    └─────────────────────────────────────┘
```

**收益预估（来自一手量化经验，非保证）**：
- V2 → 决策效率 +200%（AI 一句话查完三天的对账工作）
- V3 → 因子回测胜率 +5-10%（多因子合成 vs 单因子）
- V4 → 最大回撤 -30%（风控 + 仓位管理）
- V5 → 信息边际 +1-3% 年化 alpha（事件驱动 + 舆情）
- V6 → 跑通从研究到实盘的闭环（不再纸上谈兵）

---

## 1. 现状评估（V1.0 已完成）

### 1.1 已有能力

| 维度 | 现状 | 短板 |
|------|------|------|
| **数据广度** | 169 enabled 接口（A 股全量） | 缺港股/美股、缺新闻舆情、缺研报 |
| **数据深度** | 1500 万行历史，2020-至今 | 分钟线缺、Tick 没有 |
| **查询能力** | ClickHouse + MCP 9 工具 | 仅原始查询，无因子层 |
| **可观测性** | Grafana 3 dashboard | 业务监控为主，无策略监控 |
| **AI 接入** | MCP stdio + SSE | 只能查数，不能"思考" |
| **自动化** | 8 个 APScheduler job | 仅数据采集，无策略触发 |
| **测试** | 64% 覆盖、22 集成测试 | 因子/策略层无测试 |

### 1.2 适合做什么 / 不适合做什么

✅ **现在能做的**：
- 历史数据 SQL 探索（"2024 年 ROE > 30% 且 PE < 20 的股票"）
- 简单可视化（K 线 + 财务指标）
- 单因子回测（手写 SQL）
- AI 对话查数（Claude/Hermes 调 MCP）

❌ **现在做不了**：
- 复杂因子组合回测（要写好多 SQL 临时表）
- 实时盘中信号（无分钟数据流）
- 自动选股（需要因子打分系统）
- LLM 解读财报/公告（无文本数据）
- 风险归因（无组合分析模块）
- 模拟盘 / 实盘对接（无订单系统）

---

## 2. 长期愿景：从工具到伙伴

**3 年目标**：把 tushare-db 演化为一个 **"AI 助理 + 量化平台 + 实盘大脑"** 三位一体的系统。

| 角色 | 你做什么 | AI 做什么 |
|------|---------|----------|
| 早盘 09:00 | 看推送的"今日候选清单 + 解读" | 跑因子打分、扫公告新闻、生成解读 |
| 盘中 11:00 | 关注异常信号告警 | 实时监控波动率、资金流、止损线 |
| 收盘 15:00 | 复盘当日操作 | 自动生成"今日交易归因报告" |
| 周末 | 调整策略参数 | 跑全量回测、推荐参数 |
| 月度 | 看业绩归因 | 生成月报、识别问题策略 |

---

## 3. V2.0 — AI 接入层增强（1-2 周）

> **目标**：让 Claude / Hermes / OpenClaw 等 AI 工具用 tushare-db **像查 Google 一样自然**。
>
> **价值**：从"AI 查 SQL 报错率 30%"提到 < 5%；查询响应从平均 500ms 提到 < 200ms（缓存加持）；让 AI 对话有"上下文记忆"。

### 3.1 现有 MCP 工具的不足

| 工具 | 问题 |
|------|------|
| `query_sql` | AI 写错率高（不知道表名、列名） |
| `get_ohlcv` | 仅单股票，不能批量 |
| `get_financials` | 不能跨股票横截面对比 |
| `describe_table` | 仅列结构，不带数据示例 |
| 全部工具 | 无缓存，重复查询都打 ClickHouse |
| 全部工具 | 无对话上下文（每次重头问） |

### 3.2 新增 / 升级清单

#### 3.2.1 NL → SQL 转换工具（**最高 ROI**）

新增 MCP 工具 `nl_to_sql`：
```python
@mcp.tool()
def nl_to_sql(question: str) -> dict:
    """
    自然语言 → SQL，并执行返回结果。

    内部流程：
    1. 用 schema_describe 收集相关表结构（embedding 索引）
    2. 调用本地 LLM (Qwen 3.6 / GLM-4.6) 生成 SQL
    3. 用 sqlglot 解析校验，拒绝非 SELECT
    4. 执行并返回结果 + 生成的 SQL 供审计
    """
```

**关键依赖**：
- 本地嵌入：`sentence-transformers` + `BAAI/bge-large-zh`
- 表结构 embedding 缓存到 ClickHouse `_meta.schema_embeddings` 表
- 本地 LLM 通过 Ollama / vLLM 提供推理（避免 API 费用）

**预期效果**：
```
用户："最近一个月日均成交额 > 10 亿，且 PE < 30，且属于新能源行业的股票"
AI 返回：
  - SQL（已执行）
  - 47 只候选股票
  - 解释："该查询用 daily.amount 算 30 日均，过滤 daily_basic.pe_ttm < 30，
    JOIN industry_member 限定申万一级 = '电力设备'..."
```

#### 3.2.2 智能上下文记忆

新增 ClickHouse 表 `_meta.ai_session`：
```sql
CREATE TABLE _meta.ai_session (
    session_id   UUID,
    user_id      String,                         -- 区分多用户
    turn_idx     UInt32,
    role         Enum8('user'=0,'assistant'=1,'tool'=2),
    content      String,                         -- 对话内容
    sql_executed String,                         -- 该轮执行了什么 SQL
    result_rows  UInt32,
    created_at   DateTime64(3)
) ENGINE = MergeTree
ORDER BY (session_id, turn_idx)
TTL toDate(created_at) + INTERVAL 30 DAY;
```

新增 MCP 工具：
- `start_session(user_id) -> session_id`
- `recall(session_id, k=5) -> recent_turns[]`
- `summarize_session(session_id) -> auto_compacted_history`

**用法**：Claude 在 `cwd` 自动调 `start_session`，每轮把对话写进 `_meta.ai_session`。下次打开 Claude，先 `recall` 取上次的 5 轮，无缝续。

#### 3.2.3 查询结果缓存

新增 ClickHouse 表 `_meta.query_cache`：
```sql
CREATE TABLE _meta.query_cache (
    sql_hash   UInt64,                          -- xxhash64(sql)
    sql_text   String,
    result_b64 String,                          -- LZ4 + base64
    row_count  UInt32,
    created_at DateTime,
    hit_count  UInt32
) ENGINE = ReplacingMergeTree(created_at)
ORDER BY sql_hash
TTL toDate(created_at) + INTERVAL 1 HOUR;       -- 1h 内同 SQL 走缓存
```

工具改造：所有 MCP 工具内部先查 cache，命中直接返回；未命中执行后写入。

**预期效果**：AI 反复问"贵州茅台最近 30 天 K 线"只打一次 ClickHouse。

#### 3.2.4 流式 + 分页

针对 > 10K 行的查询，MCP SSE 改用 `event: chunk` 分片：
```
event: meta
data: {"total_rows": 50000, "estimated_time": "3s"}

event: chunk
data: {"seq": 0, "rows": 10000, "data": [...]}

event: chunk
data: {"seq": 1, "rows": 10000, "data": [...]}
...

event: end
data: {"duration_ms": 2934}
```

#### 3.2.5 工具组合（AI 自动编排）

新增 `nl_to_workflow` 工具，可让 AI 一次问"帮我筛选 + 画图 + 解读"：
```python
@mcp.tool()
def nl_to_workflow(question: str) -> dict:
    """把复杂问题拆成多个 SQL + 图表步骤，串行执行."""
    # 1. LLM 拆解：query → [step1: 筛股, step2: 取 K 线, step3: 算因子]
    # 2. 逐步执行，结果累积
    # 3. 最后 LLM 生成 markdown 解读
    return {
        "steps": [...],
        "final_table": [...],
        "markdown_summary": "..."
    }
```

### 3.3 实施步骤

| 步骤 | 工作量 | 依赖 |
|------|-------|------|
| schema embedding 索引（一次性建立） | 0.5 天 | sentence-transformers |
| nl_to_sql 工具 | 2 天 | Ollama + 本地 LLM |
| ai_session 表 + 上下文工具 | 1 天 | — |
| query_cache 实现 | 1 天 | — |
| 流式分片改造 | 1 天 | sse-starlette |
| nl_to_workflow（**可选**） | 3 天 | nl_to_sql 完成后 |

### 3.4 验收

- [ ] 跑 50 道自然语言问题（覆盖 K 线/财务/资金流/选股），SQL 生成准确率 ≥ 90%
- [ ] 同 SQL 重复查询 95th 延迟 < 50ms（缓存命中）
- [ ] 跨 session 对话能 recall 出上次的 ts_code 上下文
- [ ] 一个 50000 行的查询能流式返回，AI 端能解析

---

## 4. V3.0 — 因子工程层（2-3 周）

> **目标**：建立物化的 60+ 因子库，让 AI 不用每次重算 SQL，直接读因子值。
>
> **价值**：因子回测速度 100×（从扫原始 K 线计算 → 直接读因子表）；多因子合成成为可能。

### 4.1 为什么要因子库

现状：每次问"30 日均线 + RSI > 70"都要从 daily 现算 → 慢、耗 CH 算力、AI 写错率高。
方案：每天收盘后预计算所有因子，存到独立表，查询直接读。

### 4.2 因子分类与数量

| 类别 | 代表因子 | 数量 |
|------|---------|------|
| **价格类** | MA5/10/20/60/120/250、EMA、WMA | 12 |
| **趋势类** | MACD、KDJ、DMI、CCI、TRIX | 8 |
| **波动类** | ATR、BOLL、HV20/60、Skew、Kurt | 6 |
| **动量类** | ROC、RSI、Williams%R、Momentum | 6 |
| **量价类** | OBV、VR、MFI、CMF、Volume Ratio | 5 |
| **资金流类** | 主力净流入、北向持股、龙虎榜次数 | 6 |
| **基本面类** | PE/PB/PS 分位、ROE、毛利率、净利增速、现金流质量 | 12 |
| **事件类** | 距上次涨停天数、距业绩公告天数、解禁压力 | 5 |
| **行业相对类** | 行业内 PE 分位、行业内涨幅排名、行业 Beta | 4 |
| **市场结构类** | 沪深 300 涨跌幅、市场宽度（涨家数）、波动率指数 | 4 |
| **合计** | | **68** |

### 4.3 因子表 Schema

```sql
-- 单因子大宽表（推荐）
CREATE TABLE factor.factor_daily (
    trade_date  Date,
    ts_code     LowCardinality(String),
    -- 价格类
    ma5         Float32 CODEC(Gorilla, ZSTD(3)),
    ma10        Float32 CODEC(Gorilla, ZSTD(3)),
    ma20        Float32 CODEC(Gorilla, ZSTD(3)),
    ma60        Float32 CODEC(Gorilla, ZSTD(3)),
    -- 动量
    rsi6        Float32 CODEC(Gorilla, ZSTD(3)),
    rsi14       Float32 CODEC(Gorilla, ZSTD(3)),
    macd_dif    Float32 CODEC(Gorilla, ZSTD(3)),
    macd_dea    Float32 CODEC(Gorilla, ZSTD(3)),
    macd_hist   Float32 CODEC(Gorilla, ZSTD(3)),
    -- ... 60 多列 ...
    _version    UInt64
) ENGINE = ReplacingMergeTree(_version)
PARTITION BY toYYYYMM(trade_date)
ORDER BY (ts_code, trade_date);
```

**为什么用大宽表而非每因子一张表**：
- ClickHouse 列存，读 5 个因子 = 读 5 列，IO 完全相同
- 单次 INSERT 一行写所有因子，事务简单
- JOIN 减少（多因子打分时）

### 4.4 因子计算引擎

新增模块 `src/tushare_db/factor/`：
```
factor/
├── definitions/                    # 每个因子一个 Python 文件
│   ├── ma.py                      # 均线类
│   ├── macd.py
│   ├── rsi.py
│   ├── moneyflow.py
│   ├── valuation.py               # PE/PB 分位
│   ├── industry_relative.py
│   └── ...
├── runner.py                      # 增量计算引擎
├── registry.py                    # 因子注册表
└── windowing.py                   # 通用窗口函数
```

每个因子定义示例：
```python
# factor/definitions/ma.py
from tushare_db.factor.registry import register_factor

@register_factor(
    name="ma20",
    depends_on=["close"],
    window=20,
    update_freq="daily",
)
def compute_ma20(daily_df):
    """简单 20 日均线."""
    return daily_df["close"].rolling(20).mean()
```

或更高效——直接生成 ClickHouse SQL 让 CH 算（不出库）：
```python
@register_factor(
    name="ma20",
    sql_template="""
        avg(close) OVER (
          PARTITION BY ts_code ORDER BY trade_date
          ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) AS ma20
    """,
)
```

### 4.5 调度

新增 APScheduler job：
```python
# scheduler/jobs.py
def factor_compute_daily():
    """每日 23:00 增量计算所有因子（基于当日 daily 数据）."""
    from tushare_db.factor.runner import compute_incremental
    compute_incremental(target_date=date.today())
```

时间安排：23:00（A/B/C/D 都跑完后），预计 30-60 分钟跑完所有因子。

### 4.6 MCP 工具新增

```python
@mcp.tool()
def get_factors(
    ts_codes: list[str],
    factors: list[str],
    start_date: str,
    end_date: str,
) -> list[dict]:
    """直接读因子表，免计算."""
    sql = f"""
        SELECT trade_date, ts_code, {','.join(factors)}
        FROM factor.factor_daily FINAL
        WHERE ts_code IN ({','.join(f"'{c}'" for c in ts_codes)})
          AND trade_date BETWEEN '{start_date}' AND '{end_date}'
    """
    return execute(sql)


@mcp.tool()
def factor_screen(
    conditions: list[dict],   # [{"factor": "rsi14", "op": ">", "value": 70}]
    universe: str = "all",
    trade_date: str | None = None,
) -> list[dict]:
    """因子条件筛选."""
```

### 4.7 实施步骤

| 步骤 | 工作量 |
|------|-------|
| factor 模块骨架 + registry | 1 天 |
| 价格/趋势/动量类 30 个因子定义 | 5 天 |
| 资金流/事件/行业类 25 个因子 | 5 天 |
| factor_daily 表 DDL + 增量计算引擎 | 2 天 |
| 全量回算（2020-至今） | 1 天（机器跑） |
| MCP 工具 get_factors / factor_screen | 1 天 |
| 测试 + Grafana 因子覆盖度面板 | 2 天 |

---

## 5. V4.0 — 策略框架层（3-4 周）

> **目标**：从"查数据"升级为"自动选股 + 回测 + 风控"。
>
> **价值**：把"靠 SQL + Excel 跑策略"变成"YAML 描述策略 → 自动跑回测 → 出报告"。

### 5.1 策略 DSL（YAML）

```yaml
# strategies/multi_factor_value.yaml
name: 价值多因子策略
version: 1.0
description: |
  PE 分位低 + ROE 高 + 净利增速正，行业中性化加权打分

universe:
  type: industry        # all | hs300 | zz500 | zz1000 | industry | custom
  industries: ["银行", "白色家电", "食品饮料"]
  exclude_st: true
  exclude_new_listed_days: 60          # 排除上市不足 60 天

factors:
  - name: pe_ttm_pct          # PE 历史分位
    weight: 0.4
    direction: asc            # 越低越好
    winsorize: [0.01, 0.99]
    industry_neutralize: true
  - name: roe
    weight: 0.4
    direction: desc           # 越高越好
  - name: netprofit_yoy
    weight: 0.2
    direction: desc
    filter: { ">": 0 }        # 必须 > 0

selection:
  top_n: 20                   # 每期选前 20
  rebalance: monthly          # daily | weekly | monthly | quarterly

position:
  type: equal_weight          # equal | risk_parity | kelly | erc
  max_weight_per_stock: 0.10  # 单股不超 10%
  max_weight_per_industry: 0.30

risk:
  stop_loss: 0.10             # 个股止损 10%
  drawdown_pause: 0.15        # 组合回撤 15% 暂停加仓
  liquidity_min_amount_20d: 5e7  # 20 日均成交额 > 5000 万

backtest:
  start: '20200101'
  end: '20251231'
  initial_capital: 1_000_000
  commission: 0.0003
  stamp_tax: 0.001
  slippage_bps: 5             # 5 个基点滑点
  benchmark: '000300.SH'
```

### 5.2 回测引擎

新增模块 `src/tushare_db/strategy/`：
```
strategy/
├── parser.py              # YAML → Strategy 对象
├── selector.py            # 选股引擎（基于 factor_screen）
├── position.py            # 仓位管理（equal/erc/kelly/...）
├── risk.py                # 止损 / 回撤暂停 / 流动性
├── backtester.py          # 主回测引擎
├── metrics.py             # 业绩指标（夏普、卡尔玛、最大回撤等）
└── reporter.py            # 输出 markdown 报告 + 图表
```

回测引擎核心逻辑（向量化）：
```python
def run_backtest(strategy: Strategy) -> BacktestResult:
    # 1. 加载 universe（一次性查 stock_basic + industry_member）
    universe = load_universe(strategy.universe)

    # 2. 按 rebalance 周期循环
    rebalance_dates = get_rebalance_dates(strategy.backtest.start,
                                          strategy.backtest.end,
                                          strategy.selection.rebalance)
    for rb_date in rebalance_dates:
        # 2.1 取该日期所有因子值（一次 SQL）
        factor_values = ch.query(f"""
            SELECT ts_code, {','.join(f.name for f in strategy.factors)}
            FROM factor.factor_daily FINAL
            WHERE trade_date = '{rb_date}' AND ts_code IN universe
        """)
        # 2.2 winsorize + neutralize + 加权打分
        scores = compute_scores(factor_values, strategy.factors)
        # 2.3 取 top_n
        selected = scores.nlargest(strategy.selection.top_n)
        # 2.4 仓位分配
        weights = allocate(selected, strategy.position)
        # 2.5 止损 / 流动性过滤
        weights = apply_risk(weights, strategy.risk, rb_date)
        # 2.6 计算下一期收益
        ...
```

### 5.3 业绩指标

`metrics.py` 输出：
- **收益**：累计、年化、CAGR
- **风险**：年化波动率、最大回撤、Calmar 比率
- **风险调整**：夏普、索提诺、信息比率
- **交易**：胜率、盈亏比、换手率、平均持仓天数
- **归因**：行业归因、风格归因（市值/价值/动量/质量）

### 5.4 报告输出（Markdown + ECharts）

`strategy/value_v1_report_20260426.md`：
```markdown
# 价值多因子策略 v1.0 - 回测报告

## 总览
- 期间：2020-01-01 至 2025-12-31
- 累计收益：+187.3%（基准 +42.1%）
- 年化收益：19.2%
- 最大回撤：-18.4%
- 夏普比率：1.42
- 胜率：56.3%

## 月度收益热力图
[[ECharts 嵌入]]

## 行业归因
- 食品饮料：贡献 +42.1%
- 白色家电：贡献 +28.5%
- ...
```

### 5.5 MCP 工具新增

```python
@mcp.tool()
def run_strategy(strategy_yaml: str, save_result: bool = True) -> dict:
    """跑一个策略并返回业绩指标 + 报告 URL."""

@mcp.tool()
def list_strategies() -> list[dict]:
    """列出已有策略 + 历史最好业绩."""

@mcp.tool()
def compare_strategies(strategy_ids: list[str]) -> dict:
    """对比多个策略的业绩."""
```

### 5.6 策略库表

```sql
CREATE TABLE _meta.strategy_runs (
    run_id            UUID,
    strategy_name     String,
    strategy_version  String,
    yaml_hash         UInt64,             -- 配置版本指纹
    backtest_start    Date,
    backtest_end      Date,
    final_value       Float64,
    sharpe            Float32,
    max_drawdown      Float32,
    win_rate          Float32,
    started_at        DateTime,
    finished_at       DateTime,
    report_url        String              -- 指向 markdown 路径
) ENGINE = MergeTree
ORDER BY (strategy_name, started_at);
```

### 5.7 实施步骤

| 步骤 | 工作量 |
|------|-------|
| YAML 解析 + Pydantic 模型 | 2 天 |
| selector + factor_screen 整合 | 2 天 |
| position 管理（equal + erc + kelly） | 3 天 |
| risk 模块 | 2 天 |
| backtester（向量化版本） | 5 天 |
| metrics + reporter | 3 天 |
| 5 个标杆策略验证 | 3 天 |

### 5.8 标杆策略集（V4 验收用）

| 策略 | 类型 | 期望年化 | 期望最大回撤 |
|------|------|---------|-------------|
| `value_pe_pb` | 价值 | 12-18% | < 25% |
| `momentum_20d` | 动量 | 15-20% | < 30% |
| `quality_roe_growth` | 质量成长 | 18-25% | < 22% |
| `smart_money_inflow` | 资金流 | 10-15% | < 20% |
| `low_vol` | 低波动 | 8-12% | < 12% |

5 个全部跑通且回测合理（夏普 > 0.8）→ V4 完成。

---

## 6. V5.0 — AI 增强（持续迭代）

> **目标**：用 LLM 做"机器读不到的信号"——财报字里行间的措辞变化、公告隐含的风险、新闻情绪。
>
> **价值**：传统量化干不了的 alpha 来源；预期年化贡献 1-3%。

### 6.1 财报智能解读

#### 数据来源
- Tushare 已有 `disclosure_date` 接口
- 缺：财报全文（PDF/HTML）

#### 实施
1. **PDF 抓取**：从巨潮信息网（cninfo.com.cn）按 `ann_date` 抓 PDF
2. **解析**：`pypdf` + 表格用 `pdfplumber`
3. **存储**：
   ```sql
   CREATE TABLE ai.financial_reports (
       ts_code         LowCardinality(String),
       end_date        Date,
       report_type     LowCardinality(String),  -- 一季报 / 半年报 / 三季报 / 年报
       title           String,
       full_text       String,
       management_discussion String,             -- "管理层讨论与分析"独立提取
       risk_factors    String,                   -- "风险因素"独立提取
       _version        UInt64
   ) ENGINE = ReplacingMergeTree(_version)
   ORDER BY (ts_code, end_date);
   ```
4. **LLM 抽取**（每季度跑一次）：
   ```python
   for report in new_reports_this_quarter:
       result = llm.extract(report.management_discussion, schema={
           "tone": "positive | neutral | negative",
           "growth_drivers": ["最多 3 个"],
           "risk_signals": ["最多 3 个"],
           "guidance_change": "raised | maintained | lowered | none",
       })
       store(result)
   ```
5. **生成因子**：
   - `report_tone_score` ∈ [-1, 1]
   - `guidance_change_signal` ∈ {-1, 0, +1}

**关键技巧**：用结构化输出（JSON Schema）+ 多轮自校正，确保结果可解析。

### 6.2 公告事件提取

#### 实施
- 抓 Tushare `anns` 公告标题
- LLM 分类为 13 类：业绩预告/业绩快报/分红/送转/重大合同/股东减持/重组/资产收购/...
- 每类配 alpha 信号（如"重组"前 5 日异动 +30% 概率）

#### 结果表
```sql
CREATE TABLE ai.events (
    ts_code     LowCardinality(String),
    ann_date    Date,
    event_type  LowCardinality(String),
    severity    Enum8('low'=0,'med'=1,'high'=2),
    bullish_score Float32,        -- LLM 给出 -1 ~ +1
    summary     String,
    _version    UInt64
) ENGINE = ReplacingMergeTree(_version)
ORDER BY (ts_code, ann_date);
```

### 6.3 舆情情绪打分

#### 数据源
- 雪球 / 东方财富股吧 / 微博 / Twitter（爬虫或 API）
- Tushare `news` 接口（如有）

#### 实施
- 每日抓取 → BERT 情感分类 → 按 ts_code 聚合
- 因子：`sentiment_score_7d`、`sentiment_volume_7d`（讨论热度）

### 6.4 AI 选股助手

新增 MCP 工具 `ai_stock_picker`：
```python
@mcp.tool()
def ai_stock_picker(
    horizon: str = "1m",          # "1d" | "1w" | "1m" | "3m"
    risk_tolerance: str = "medium",  # "low" | "medium" | "high"
    sectors: list[str] | None = None,
    max_picks: int = 10,
) -> dict:
    """
    AI 综合多因子 + 事件 + 舆情，给出推荐清单 + 解读。
    """
    # 1. 跑 V4 多因子打分（量化层）
    quant_top = run_quant_screen(horizon, sectors, top_n=50)
    # 2. 用 LLM 读这 50 只的最近事件 + 舆情，重打分
    rerank = llm_rerank(quant_top, recent_events, recent_sentiment, horizon, risk_tolerance)
    # 3. 取前 max_picks，让 LLM 写解读
    picks = rerank[:max_picks]
    explanation = llm_explain(picks)
    return {"picks": picks, "explanation": explanation}
```

### 6.5 AI 自动复盘

新增 APScheduler job（每日 18:00）：
```python
def generate_daily_review():
    """生成当日交易复盘报告."""
    # 1. 取当日实盘/模拟盘的所有交易
    trades = get_today_trades()
    # 2. 对每笔交易，用 LLM 分析"为什么涨/跌、决策是否正确"
    for trade in trades:
        analysis = llm.analyze(trade, today_news, today_market_event)
        store_analysis(trade.id, analysis)
    # 3. 汇总月度模式
    if is_month_end:
        monthly_pattern = llm.summarize_month(this_month_trades)
        send_to_user(monthly_pattern)
```

### 6.6 实施分期

V5 不一刀切上，**按数据可获得性分期**：
- **5.1 财报解读**：第 1 个月（数据最稳定）
- **5.2 公告事件**：第 2 个月
- **5.3 舆情**：第 3 个月（数据源最难）
- **5.4 AI 选股助手**：5.1-5.3 完成后，第 4 个月整合
- **5.5 AI 复盘**：第 5 个月（需要实盘/模拟盘数据）

---

## 7. V6.0 — 实盘对接（**高风险，最后做**）

> ⚠️ **警告**：本阶段涉及真金白银。严格遵循"先纸面 → 模拟 → 小资金 → 大资金"四步走。

### 7.1 模拟盘（必经）

#### 实施
新增模块 `src/tushare_db/trading/`：
```
trading/
├── broker.py              # 抽象券商接口
├── paper.py               # 模拟盘实现（用 daily 数据撮合）
├── orders.py              # 订单管理
├── portfolio.py           # 持仓管理
└── ledger.py              # 账本（每日盈亏 + 交易记录）
```

模拟盘核心逻辑：
- 收到买入信号 → 用次日 open 价 + 滑点 5bp 撮合
- 触发止损 → 当日 close 价撮合（保守）
- 每日 update 持仓市值
- 持续记录 NAV

时间窗口：**至少 3 个月**模拟盘，胜率/夏普稳定后才考虑实盘。

### 7.2 实盘对接（**仅当模拟盘 3 个月通过后**）

#### 候选券商接口
| 券商 | 接口 | 难度 |
|------|------|------|
| 国金证券 QMT | Python API | ⭐⭐ |
| 华泰证券 MATIC | Python API | ⭐⭐⭐ |
| 同花顺 iFinD | 手动半自动 | ⭐ |
| 易盛 EX9.0 | C++/Python | ⭐⭐⭐⭐ |

推荐 **QMT**（成熟、文档齐、社区大）。

#### 双向对接
```
tushare-db (CH)  ←  实盘成交回报
                 →  下单指令
   ↑
   └── 实时风控 + 止损监控
```

#### 关键约束
- **每日下单上限**：金额 + 笔数（防 LLM 失控）
- **止损强约束**：CH 中持仓单股亏损 > 10% 必须强卖（不依赖 AI 判断）
- **黑名单**：ST、退市、上市不足 60 天禁买
- **熔断**：单日亏损 > 5% 暂停所有新单

### 7.3 业绩归因

每月生成：
- 总收益分解（选股 alpha + 行业 beta + 择时）
- 单笔交易盈亏归因（用 V5 的 LLM 复盘）
- 失败案例库（亏损 > 8% 的交易自动归档 + LLM 总结教训）
- 与基准对比

### 7.4 实施步骤

```
Month 1: 模拟盘 paper.py
Month 2-3: 跑 V4 标杆策略，模拟盘验证
Month 4: 业绩稳定后，做 QMT 接入（小资金 1 万元）
Month 5-6: 小资金跑 1 个月，胜率/夏普 OK 后逐步扩大
```

---

## 8. 提高胜率与收益率的"软"建议（非代码）

代码做完只是基础。**真正决定胜率和收益率的是这些**：

### 8.1 数据多样性 = alpha 来源

✅ **必须有**：
- A 股全量行情 + 财务（V1 已完成）
- 港股 / 美股（与 A 股相关性低，分散风险）
- 商品期货（铜/原油/螺纹钢 → 周期股 leading indicator）
- 宏观（M2、社融、PMI、CPI）

⚠️ **要谨慎**：
- 龙虎榜（噪音多，散户跟单亏多）
- 北向资金（2024 后 Tushare 数据延迟变长）

### 8.2 时间维度的"长期 + 短期"组合

| 时间 | 类型 | 推荐策略 |
|------|------|---------|
| 短期（< 1 周） | 趋势 / 资金流 | 涨停板 + 主力净流入 + 异动 |
| 中期（1-3 月） | 多因子 / 风格 | 价值 / 质量 / 动量 |
| 长期（> 6 月） | 价值 + 成长 | 行业景气度 + ROE 持续 + 估值合理 |

**单一时间维度策略胜率天花板低**。多时间维度组合可以把单维度 55% 胜率推到 65%+。

### 8.3 风险管理 > 收益最大化

**铁律**：
- 单股仓位 ≤ 10%
- 单行业 ≤ 30%
- 总仓位上限 ≤ 90%（永远留 10% 现金）
- 止损 ≤ 10%（个股）
- 组合回撤 ≥ 15% 立即降仓
- 月度亏损 ≥ 8% 强制休息一周

实测数据：**严格执行风控的散户**5 年胜率 60%+；不执行的散户胜率 40%-。

### 8.4 反脆弱：每次亏损都要"学习"

实施：
- 每笔亏损 > 5% 的交易，触发"复盘任务"
- LLM 自动生成 5 个反思问题：
  1. 入场理由是什么？
  2. 入场时是否已有出场计划？
  3. 实际触发出场的事件是什么？
  4. 这个事件是否在入场前可预见？
  5. 下次类似情况你会怎么做？
- 答案存入 `_meta.lessons_learned` 表
- 每月汇总，找模式
- **每个月新策略上线前，必须先看 lessons_learned**

### 8.5 多策略组合 vs 单策略 all-in

❌ all-in 单策略：
- 该策略好的时候：年化 30%
- 该策略坏的时候：年化 -20%
- 长期年化：5%（被坏年份拉下来）

✅ 4 策略等权组合（低相关性）：
- 任何单策略坏年份：组合最多回撤 1/4
- 长期年化更稳：12-15%
- **夏普比率 ×2-3 倍**

V4 的 5 个标杆策略就是为这个准备的——上线后**全部跑，按业绩动态分配权重**（用 IC 衰减做月度再平衡）。

### 8.6 不要追求 100%（避免过拟合）

回测完美的策略上线后破防——99% 是过拟合。**预防**：
- 留 1 年样本外（2025-至今）不参与因子选择
- 因子数 ≤ 5（多了就是过拟合）
- 同一参数不要 grid search > 100 组合
- 逻辑上"想得通"的因子才用，不要"挖出来"的因子

### 8.7 定期断舍离

每年清理：
- 连续 6 个月跑输基准的策略 → 暂停
- 数据源延迟 > 24h 的接口 → 弃用
- LLM 准确率 < 70% 的事件分类 → 重训或下线
- 看了 3 个月没用的 dashboard → 删除

---

## 9. 路线图汇总

| 版本 | 时间 | 工作量 | 必要性 | 收益 |
|------|------|-------|--------|------|
| **V2** AI 接入层 | 1-2 周 | 1 人 8-12 天 | ⭐⭐⭐⭐⭐ | 决策效率 +200% |
| **V3** 因子工程 | 2-3 周 | 1 人 14-20 天 | ⭐⭐⭐⭐⭐ | 回测速度 ×100 |
| **V4** 策略框架 | 3-4 周 | 1 人 21-28 天 | ⭐⭐⭐⭐ | 多策略并跑成为可能 |
| **V5** AI 增强 | 持续迭代 | 5 个月 | ⭐⭐⭐ | 1-3% 年化 alpha |
| **V6** 实盘对接 | 半年+ | 6 个月 | ⭐⭐ | 闭环（高风险） |

**总周期**：V2-V4 集中 **2-3 个月**完成，V5 和 V6 按需推进。

---

## 10. 给执行者（Qwen / 你）的建议

### 10.1 顺序

**强烈建议按 V2 → V3 → V4 → V5 → V6 严格顺序**。每个版本都依赖前一个版本的产出：
- V3 因子库要靠 V2 的 NL 工具帮 AI 写因子定义
- V4 策略框架要靠 V3 的因子表
- V5 AI 增强要靠 V4 的策略报告做反馈
- V6 实盘要靠 V5 的复盘判断对错

### 10.2 优先级

如果时间不够，砍尾不砍头：
- 砍 V6 实盘（最危险）
- 砍 V5 LLM 财报解读（可手动）
- 砍 V4 5 个标杆策略中后 2 个
- **不能砍 V2 + V3**（基础设施）

### 10.3 测试纪律

每个版本：
- 单测 ≥ 80% 覆盖（核心模块）
- 集成测 ≥ 1 个端到端流程
- 验收 demo（让用户/AI 跑一个完整 case）
- 文档（README + 一个跑通示例）

### 10.4 常见陷阱

| 陷阱 | 后果 | 规避 |
|------|------|------|
| **未来函数**（用 t+1 数据预测 t） | 回测虚高 | 用 `before-trade-close` shift |
| **生存者偏差**（只用现存股票） | 回测虚高 5-10% | 用 stock_basic 含 list_status='D' 退市的 |
| **过度乐观滑点** | 实盘大亏 | 滑点 ≥ 5bp，热门股 ≥ 10bp |
| **数据延迟**（盘后用 daily 装作"实时"） | 实盘信号失效 | 盘中用分钟数据，盘后用 daily |
| **LLM 幻觉** | 错误信号 | 关键决策必须 SQL 二次校验 |
| **过拟合 grid search** | 回测漂亮，实盘 -10% | 因子数 ≤ 5，参数搜索次数 ≤ 30 |
| **ChatGPT 写策略代码** | bug 多 | 自己读懂每一行；TDD 强制 |

---

## 11. 写在最后

### 11.1 真相

量化的 80% alpha 来自**纪律**，不是模型。最好的系统是 **70% 数据 + 20% 风控 + 10% 因子**——而非反过来。

### 11.2 你已经走了 90% 的路

V1.0 完成的"数据仓库 + AI 接入"，就是大多数散户用 Excel + 同花顺一辈子也搭不出来的基础设施。

V2-V4 是把 V1 用起来。V5-V6 是把 V1-V4 用赢钱。

### 11.3 期望值管理

别期待"AI 帮我赚 100%"。期待：
- AI 帮你**省 80% 的时间**找信息
- AI 帮你**省 50% 的时间**做决策
- AI 帮你**避开 50% 的明显错误**
- 至于赚不赚钱，靠你自己的纪律

### 11.4 下一步

**今晚就能开始**：
- 跑 a-final-mile-plan-for-qwen.md 的阶段一（数据回填，~50h）
  - 或先做 docs/migration/EXECUTION_PLAN.md（PG 迁移，~5h）跳过回填

**这周**：
- 完成 V1 数据基础（含 R6 五交易日观察）

**这个月**：
- 开始 V2 NL→SQL 工具
- 同时跑 V3 因子定义的 30 个最简单的（MA / EMA / RSI / MACD / KDJ / ATR 等）

**3 个月后**：
- V2 + V3 + V4 标杆策略 1-2 个上线模拟盘

**1 年后**：
- 决定是否进入 V5/V6（这时数据会告诉你答案）

---

> **文档结束**
>
> 本蓝图非命令而是菜单。挑你最需要的、最有时间的部分做。
> 任何阶段卡壳，回到 V1 找根因——基础数据有问题，上层全废。
>
> 量化是马拉松不是短跑。3 年回头看 V1，你会感谢自己今天做的每一行代码。
