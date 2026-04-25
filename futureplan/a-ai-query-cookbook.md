# AI 查询食谱（Query Cookbook）

> 面向：本机 AI / 局域网 AI / 量化研究员
> 目标：30+ 高频 A 股分析查询模板，每条同时给出 **MCP 工具调用** 与 **直连 ClickHouse SQL** 两种形态，附性能预期与坑点。
>
> 前置：所有查询基于 `db_tushare` schema，使用 ReplacingMergeTree + FINAL 语义；价格类查询默认走 `daily` + `adj_factor`，财务因子走 `fina_indicator`，行业归属走 `stock_basic` + `industry_member`。

---

## 0. 通用约定

- **AI 直连入口**：MCP Server `http://<host>:7800/sse`（局域网 AI）或 `stdio`（本机 AI）
- **SQL 直连入口**：ClickHouse Native `9000`（账号：`ai_reader`，只读）
- **adj_type**：`qfq`（前复权，默认）/ `hfq`（后复权）/ `none`（不复权）
- **trade_date**：`YYYYMMDD` 字符串；内部已建索引，不要用 `toDate(parseDateTimeBestEffort(...))` 包裹
- **FINAL 关键字**：所有 ReplacingMergeTree 表读取都加 `FINAL`，否则可能读到旧版本
- **性能预期**：单股票×3 年 < 100ms，全市场单日 < 300ms，全市场×1 年 < 1.5s（在 NVMe + 16 核 + 32GB 上）

---

## 一、行情类（OHLCV、复权、resample）

### Q1. 单只股票区间复权 K 线

**场景**：取 `000001.SZ` 2020-01-01 到 2024-12-31 的前复权日线。

**MCP**：
```json
{
  "tool": "kline",
  "args": {"ts_code": "000001.SZ", "start": "20200101", "end": "20241231", "adj": "qfq", "freq": "D"}
}
```

**SQL**：
```sql
SELECT
    d.trade_date,
    d.open  * a.adj_factor / latest.adj_factor AS open_qfq,
    d.high  * a.adj_factor / latest.adj_factor AS high_qfq,
    d.low   * a.adj_factor / latest.adj_factor AS low_qfq,
    d.close * a.adj_factor / latest.adj_factor AS close_qfq,
    d.vol, d.amount
FROM db_tushare.daily FINAL d
INNER JOIN db_tushare.adj_factor FINAL a USING (ts_code, trade_date)
CROSS JOIN (
    SELECT adj_factor FROM db_tushare.adj_factor FINAL
    WHERE ts_code = '000001.SZ'
    ORDER BY trade_date DESC LIMIT 1
) AS latest
WHERE d.ts_code = '000001.SZ'
  AND d.trade_date BETWEEN '20200101' AND '20241231'
ORDER BY d.trade_date;
```

**坑**：`adj_factor` 在停牌日不一定有值，必须 INNER JOIN 而非 LEFT JOIN，否则停牌日开高低收会变成 NULL；后复权用 `d.close * a.adj_factor` 即可，不除以 latest。

---

### Q2. 周线 / 月线 resample

**场景**：把日线聚合为周线（自然周收盘 = 周五，含开高低收）。

**SQL**：
```sql
SELECT
    ts_code,
    toMonday(toDate(parseDateTimeBestEffortOrNull(trade_date))) AS week_start,
    argMin(open,  trade_date) AS open,
    max(high)                  AS high,
    min(low)                   AS low,
    argMax(close, trade_date) AS close,
    sum(vol)                   AS vol,
    sum(amount)                AS amount
FROM db_tushare.daily FINAL
WHERE ts_code = '000001.SZ' AND trade_date BETWEEN '20240101' AND '20241231'
GROUP BY ts_code, week_start
ORDER BY week_start;
```

**坑**：用 `argMin/argMax(open/close, trade_date)` 而非 `min/max`，否则会把当周最低开盘价当成周开盘价。

---

### Q3. 全市场单日涨跌幅榜（前 50）

```sql
SELECT ts_code, name, close, pct_chg, vol, amount
FROM db_tushare.daily FINAL d
INNER JOIN db_tushare.stock_basic FINAL b USING (ts_code)
WHERE d.trade_date = '20250424'
ORDER BY pct_chg DESC
LIMIT 50;
```

**性能**：< 200ms（单分区扫描 ~5500 行）。

---

### Q4. 振幅 / 真实波幅 ATR(14)

```sql
WITH t AS (
    SELECT trade_date, high, low, close,
           lagInFrame(close) OVER (ORDER BY trade_date) AS prev_close
    FROM db_tushare.daily FINAL
    WHERE ts_code = '600519.SH' AND trade_date >= '20240101'
)
SELECT trade_date,
       avg(greatest(high - low, abs(high - prev_close), abs(low - prev_close)))
         OVER (ORDER BY trade_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS atr14
FROM t
ORDER BY trade_date;
```

---

### Q5. RSI(14)

```sql
WITH t AS (
    SELECT trade_date, close,
           greatest(close - lagInFrame(close) OVER (ORDER BY trade_date), 0) AS gain,
           greatest(lagInFrame(close) OVER (ORDER BY trade_date) - close, 0) AS loss
    FROM db_tushare.daily FINAL
    WHERE ts_code = '600519.SH' AND trade_date >= '20240101'
)
SELECT trade_date,
       100 - 100 / (1 + avg(gain) OVER w / nullIf(avg(loss) OVER w, 0)) AS rsi14
FROM t
WINDOW w AS (ORDER BY trade_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW)
ORDER BY trade_date;
```

---

### Q6. MACD(12, 26, 9)

```sql
SELECT trade_date,
       exponentialMovingAverage(12)(close, trade_date) OVER w AS ema12,
       exponentialMovingAverage(26)(close, trade_date) OVER w AS ema26,
       ema12 - ema26 AS dif,
       exponentialMovingAverage(9)(dif, trade_date)    OVER w AS dea,
       2 * (dif - dea) AS macd
FROM db_tushare.daily FINAL
WHERE ts_code = '600519.SH' AND trade_date >= '20240101'
WINDOW w AS (ORDER BY trade_date)
ORDER BY trade_date;
```

**坑**：ClickHouse 的 `exponentialMovingAverage` 是 SimpleAggregateFunction 风格，参数顺序是 `(value, time)`，不是 `(time, value)`。

---

### Q7. 布林带 BOLL(20, 2)

```sql
SELECT trade_date, close,
       avg(close)        OVER w AS mid,
       avg(close)        OVER w + 2 * stddevPop(close) OVER w AS upper,
       avg(close)        OVER w - 2 * stddevPop(close) OVER w AS lower
FROM db_tushare.daily FINAL
WHERE ts_code = '600519.SH' AND trade_date >= '20240101'
WINDOW w AS (ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW);
```

---

### Q8. KDJ(9, 3, 3)

```sql
WITH t AS (
    SELECT trade_date, close,
           min(low)  OVER w AS llv,
           max(high) OVER w AS hhv
    FROM db_tushare.daily FINAL
    WHERE ts_code = '600519.SH' AND trade_date >= '20240101'
    WINDOW w AS (ORDER BY trade_date ROWS BETWEEN 8 PRECEDING AND CURRENT ROW)
)
SELECT trade_date,
       100 * (close - llv) / nullIf(hhv - llv, 0) AS rsv,
       avg(rsv) OVER (ORDER BY trade_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS k,
       avg(k)   OVER (ORDER BY trade_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS d,
       3 * k - 2 * d AS j
FROM t
ORDER BY trade_date;
```

---

## 二、资金流类

### Q9. 主力净流入连续 N 日（个股）

```sql
SELECT ts_code, count() AS cont_days, sum(net_mf_amount) AS total_inflow
FROM (
    SELECT ts_code, trade_date, net_mf_amount,
           sum(if(net_mf_amount > 0, 0, 1))
             OVER (PARTITION BY ts_code ORDER BY trade_date) AS reset_grp
    FROM db_tushare.moneyflow FINAL
    WHERE trade_date >= '20250101'
)
WHERE net_mf_amount > 0
GROUP BY ts_code, reset_grp
ORDER BY cont_days DESC, total_inflow DESC
LIMIT 50;
```

**用途**：找连续 N 日主力净流入的票。

---

### Q10. 北向资金持股占比 Top 50

```sql
SELECT ts_code, b.name, hold_ratio, hold_vol, hold_amount
FROM db_tushare.hk_hold FINAL h
INNER JOIN db_tushare.stock_basic FINAL b USING (ts_code)
WHERE h.trade_date = (SELECT max(trade_date) FROM db_tushare.hk_hold FINAL)
ORDER BY hold_ratio DESC
LIMIT 50;
```

---

### Q11. 龙虎榜上榜次数（最近 30 个交易日）

```sql
SELECT ts_code, count() AS appear_cnt, sum(net_amount) AS net_amount_sum
FROM db_tushare.top_list FINAL
WHERE trade_date >= toString(addDays(today(), -45))
GROUP BY ts_code
ORDER BY appear_cnt DESC, net_amount_sum DESC
LIMIT 50;
```

---

### Q12. 单日涨停板数 + 连板天数

```sql
WITH zt AS (
    SELECT ts_code, trade_date, close, pre_close,
           if(round((close - pre_close) / pre_close * 100, 2) >= 9.95, 1, 0) AS is_zt
    FROM db_tushare.daily FINAL
    WHERE trade_date >= '20250101'
)
SELECT trade_date, sum(is_zt) AS zt_cnt
FROM zt
GROUP BY trade_date
ORDER BY trade_date DESC
LIMIT 30;
```

**进阶**：连板用 `groupArray + arrayCumSumNonNegative` 计算，限于篇幅这里略。

---

## 三、财务因子类

### Q13. ROE Top 50（最新季度）

```sql
SELECT i.ts_code, b.name, i.end_date, i.roe, i.roa, i.netprofit_yoy
FROM db_tushare.fina_indicator FINAL i
INNER JOIN db_tushare.stock_basic FINAL b USING (ts_code)
WHERE i.end_date = (SELECT max(end_date) FROM db_tushare.fina_indicator FINAL)
ORDER BY i.roe DESC
LIMIT 50;
```

**坑**：财报披露有时间差，`max(end_date)` 可能只覆盖部分公司，需用 `argMax(end_date, ...) PARTITION BY ts_code` 找每只股票的最新财报。

---

### Q14. 业绩快报 + 预告联合查询

```sql
SELECT
    ts_code,
    coalesce(express.end_date,  forecast.end_date)  AS end_date,
    coalesce(express.revenue,   NULL)               AS express_revenue,
    coalesce(forecast.p_change_min, NULL)           AS forecast_min_pct,
    coalesce(forecast.p_change_max, NULL)           AS forecast_max_pct
FROM db_tushare.express FINAL express
FULL OUTER JOIN db_tushare.forecast FINAL forecast
  USING (ts_code, end_date)
WHERE end_date >= '20250101';
```

---

### Q15. PE/PB 历史分位（个股 vs 自身 5 年）

```sql
WITH t AS (
    SELECT trade_date, pe_ttm, pb,
           rank() OVER (ORDER BY pe_ttm) / count() OVER () AS pe_pct,
           rank() OVER (ORDER BY pb)     / count() OVER () AS pb_pct
    FROM db_tushare.daily_basic FINAL
    WHERE ts_code = '600519.SH' AND trade_date >= toString(addYears(today(), -5))
)
SELECT * FROM t ORDER BY trade_date DESC LIMIT 1;
```

---

### Q16. 现金流质量（经营现金流 / 净利润）

```sql
SELECT i.ts_code, b.name, i.end_date,
       i.netprofit, i.ocf_to_profit
FROM db_tushare.fina_indicator FINAL i
INNER JOIN db_tushare.stock_basic FINAL b USING (ts_code)
WHERE i.end_date = '20241231' AND i.ocf_to_profit > 1.2
ORDER BY i.ocf_to_profit DESC
LIMIT 50;
```

---

## 四、行业 / 板块类

### Q17. 行业涨幅榜（申万一级，单日）

```sql
SELECT b.industry, avg(d.pct_chg) AS avg_pct, count() AS stk_cnt
FROM db_tushare.daily FINAL d
INNER JOIN db_tushare.stock_basic FINAL b USING (ts_code)
WHERE d.trade_date = '20250424' AND b.industry != ''
GROUP BY b.industry
ORDER BY avg_pct DESC;
```

---

### Q18. 概念板块成员涨幅（同花顺概念）

```sql
SELECT c.name AS concept, avg(d.pct_chg) AS avg_pct
FROM db_tushare.ths_member FINAL m
INNER JOIN db_tushare.ths_index  FINAL c ON m.ts_code = c.ts_code
INNER JOIN db_tushare.daily      FINAL d ON m.con_code = d.ts_code
WHERE d.trade_date = '20250424'
GROUP BY c.name
ORDER BY avg_pct DESC
LIMIT 30;
```

---

### Q19. 板块轮动（最近 5/20/60 日涨幅对比）

```sql
SELECT
    b.industry,
    avg(if(d.trade_date >= toString(addDays(today(), -7)),  d.pct_chg, NULL)) AS pct_5d,
    avg(if(d.trade_date >= toString(addDays(today(), -30)), d.pct_chg, NULL)) AS pct_20d,
    avg(if(d.trade_date >= toString(addDays(today(), -90)), d.pct_chg, NULL)) AS pct_60d
FROM db_tushare.daily FINAL d
INNER JOIN db_tushare.stock_basic FINAL b USING (ts_code)
WHERE d.trade_date >= toString(addDays(today(), -90))
GROUP BY b.industry
ORDER BY pct_5d DESC;
```

---

## 五、组合 / 选股类

### Q20. 多因子打分（PE 低 + ROE 高 + 净利增长 > 0）

```sql
WITH ranked AS (
    SELECT
        d.ts_code, b.name,
        d.pe_ttm, i.roe, i.netprofit_yoy,
        (1 - rank() OVER (ORDER BY d.pe_ttm) / count() OVER ()) AS pe_score,
        rank() OVER (ORDER BY i.roe)            / count() OVER ()  AS roe_score,
        rank() OVER (ORDER BY i.netprofit_yoy)  / count() OVER ()  AS yoy_score
    FROM db_tushare.daily_basic FINAL d
    INNER JOIN db_tushare.stock_basic     FINAL b USING (ts_code)
    INNER JOIN db_tushare.fina_indicator  FINAL i USING (ts_code)
    WHERE d.trade_date = '20250424'
      AND i.end_date   = (SELECT max(end_date) FROM db_tushare.fina_indicator FINAL WHERE ts_code = d.ts_code)
      AND d.pe_ttm > 0 AND i.roe > 0 AND i.netprofit_yoy > 0
)
SELECT *, (pe_score + roe_score + yoy_score) / 3 AS total_score
FROM ranked
ORDER BY total_score DESC
LIMIT 50;
```

---

### Q21. 海龟突破（20 日新高）

```sql
SELECT ts_code, trade_date, close, hi20
FROM (
    SELECT ts_code, trade_date, close,
           max(high) OVER (PARTITION BY ts_code ORDER BY trade_date
                            ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING) AS hi20
    FROM db_tushare.daily FINAL
    WHERE trade_date >= toString(addDays(today(), -90))
)
WHERE trade_date = '20250424' AND close > hi20
ORDER BY ts_code;
```

---

### Q22. 金叉信号（5 日均线上穿 20 日均线）

```sql
WITH ma AS (
    SELECT ts_code, trade_date, close,
           avg(close) OVER (PARTITION BY ts_code ORDER BY trade_date ROWS BETWEEN 4  PRECEDING AND CURRENT ROW) AS ma5,
           avg(close) OVER (PARTITION BY ts_code ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ma20,
           lagInFrame(avg(close) OVER (PARTITION BY ts_code ORDER BY trade_date ROWS BETWEEN 4  PRECEDING AND CURRENT ROW)) OVER (PARTITION BY ts_code ORDER BY trade_date) AS ma5_prev,
           lagInFrame(avg(close) OVER (PARTITION BY ts_code ORDER BY trade_date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)) OVER (PARTITION BY ts_code ORDER BY trade_date) AS ma20_prev
    FROM db_tushare.daily FINAL
    WHERE trade_date >= toString(addDays(today(), -60))
)
SELECT ts_code, trade_date, close, ma5, ma20
FROM ma
WHERE trade_date = '20250424'
  AND ma5_prev <= ma20_prev AND ma5 > ma20
ORDER BY ts_code;
```

---

## 六、特殊场景

### Q23. 停牌恢复后首日（缺口检测）

```sql
SELECT ts_code, trade_date, pre_close, open,
       (open - pre_close) / pre_close * 100 AS gap_pct
FROM (
    SELECT ts_code, trade_date, open, pre_close,
           lagInFrame(trade_date) OVER (PARTITION BY ts_code ORDER BY trade_date) AS prev_date
    FROM db_tushare.daily FINAL
    WHERE trade_date >= '20250101'
)
WHERE dateDiff('day', toDate(parseDateTimeBestEffort(prev_date)), toDate(parseDateTimeBestEffort(trade_date))) > 5
ORDER BY abs(gap_pct) DESC
LIMIT 50;
```

---

### Q24. 限售解禁（未来 30 日）

```sql
SELECT b.name, s.ts_code, s.float_date, s.float_share, s.float_ratio
FROM db_tushare.share_float FINAL s
INNER JOIN db_tushare.stock_basic FINAL b USING (ts_code)
WHERE s.float_date BETWEEN toString(today()) AND toString(addDays(today(), 30))
ORDER BY s.float_ratio DESC;
```

---

### Q25. 股东户数环比变化

```sql
SELECT s.ts_code, b.name, s.end_date, s.holder_num,
       (s.holder_num - lagInFrame(s.holder_num) OVER (PARTITION BY s.ts_code ORDER BY s.end_date))
       / nullIf(lagInFrame(s.holder_num) OVER (PARTITION BY s.ts_code ORDER BY s.end_date), 0) AS pct_chg
FROM db_tushare.stk_holdernumber FINAL s
INNER JOIN db_tushare.stock_basic FINAL b USING (ts_code)
WHERE s.end_date = (SELECT max(end_date) FROM db_tushare.stk_holdernumber FINAL)
ORDER BY pct_chg ASC
LIMIT 50;
```

---

### Q26. 大宗交易折溢价 Top

```sql
SELECT bl.ts_code, b.name, bl.trade_date, bl.price, bl.vol, bl.amount, d.close,
       (bl.price - d.close) / d.close * 100 AS premium_pct
FROM db_tushare.block_trade FINAL bl
INNER JOIN db_tushare.daily       FINAL d  USING (ts_code, trade_date)
INNER JOIN db_tushare.stock_basic FINAL b  USING (ts_code)
WHERE bl.trade_date >= toString(addDays(today(), -30))
ORDER BY abs(premium_pct) DESC
LIMIT 50;
```

---

### Q27. 期权 PCR（沽购比）

```sql
SELECT trade_date,
       sumIf(vol, call_put = 'P') / nullIf(sumIf(vol, call_put = 'C'), 0) AS pcr_volume
FROM db_tushare.opt_basic FINAL ob
INNER JOIN db_tushare.opt_daily FINAL od USING (ts_code)
WHERE od.trade_date >= '20250101' AND ob.exchange = 'CFFEX'
GROUP BY trade_date
ORDER BY trade_date DESC LIMIT 30;
```

---

### Q28. 转债折溢价

```sql
SELECT cb.ts_code, cb.bond_short_name, cd.trade_date, cd.close AS bond_price,
       sd.close AS stk_price, cb.conv_price,
       (cd.close - sd.close * 100 / cb.conv_price) / (sd.close * 100 / cb.conv_price) * 100 AS premium
FROM db_tushare.cb_basic FINAL cb
INNER JOIN db_tushare.cb_daily FINAL cd USING (ts_code)
INNER JOIN db_tushare.daily    FINAL sd ON cb.stk_code = sd.ts_code AND cd.trade_date = sd.trade_date
WHERE cd.trade_date = '20250424'
ORDER BY premium ASC
LIMIT 50;
```

---

### Q29. 指数成分股贡献度（如沪深 300）

```sql
SELECT i.con_code, b.name, d.pct_chg, i.weight,
       d.pct_chg * i.weight / 100 AS contribution
FROM db_tushare.index_weight FINAL i
INNER JOIN db_tushare.daily       FINAL d ON i.con_code = d.ts_code
INNER JOIN db_tushare.stock_basic FINAL b ON i.con_code = b.ts_code
WHERE i.index_code = '000300.SH'
  AND i.trade_date = (SELECT max(trade_date) FROM db_tushare.index_weight FINAL WHERE index_code = '000300.SH')
  AND d.trade_date = '20250424'
ORDER BY contribution DESC
LIMIT 30;
```

---

### Q30. 股息率排名（最新年报）

```sql
SELECT div.ts_code, b.name, div.cash_div_tax, db.dv_ratio
FROM db_tushare.dividend FINAL div
INNER JOIN db_tushare.daily_basic FINAL db USING (ts_code)
INNER JOIN db_tushare.stock_basic FINAL b USING (ts_code)
WHERE div.end_date = '20241231'
  AND db.trade_date = '20250424'
  AND div.div_proc = '实施'
ORDER BY db.dv_ratio DESC
LIMIT 50;
```

---

## 七、性能调优清单

| 症状 | 排查 | 修复 |
|------|------|------|
| 查询 > 5s | `EXPLAIN PIPELINE` 看是否全表扫 | 加 `trade_date BETWEEN` 限定分区 |
| FINAL 慢 | `system.parts` 看 part 数 > 100 | 触发 `OPTIMIZE TABLE ... FINAL`（限于小表） |
| 内存 OOM | 看 `max_memory_usage` | 加 `SETTINGS max_bytes_before_external_group_by = 5000000000` |
| JOIN 慢 | 大表 JOIN 大表 | 改写为 `IN (SELECT ...)` 或 dictGet |
| 窗口函数慢 | PARTITION BY 列基数大 | 先 prefilter 缩小行数再开窗 |

---

## 八、AI 调用规范

写给本机/局域网 AI 的提示词模板：

```
你是 A 股量化分析助手。所有查询通过 MCP Server (http://192.168.x.x:7800/sse) 进行。
- 优先使用预制工具（kline, factor_score, sector_rank 等），无对应工具时再用 raw_sql
- 用 raw_sql 时，必须包含 trade_date 范围，禁止全表扫
- ReplacingMergeTree 表必须加 FINAL
- 财务因子数据有 1-3 个月延迟，end_date 不等于今天
- 单次返回行数 > 1000 时，要么聚合，要么分页（LIMIT/OFFSET）
```

---

> 维护：每个 PR 上线新数据集时，对应 `Q##` 模板补充到本食谱。
> 验证：CI 跑一遍所有 SQL（mock 数据），确保 schema 漂移时及时发现。
