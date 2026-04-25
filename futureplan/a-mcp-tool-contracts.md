# MCP 工具契约（Tool Contracts）

> 面向：MCP Server 实现者 + AI 客户端开发者
> 目标：精确定义每个 MCP 工具的输入输出 JSON Schema、错误码、流式 vs 批式边界、复权计算语义。
>
> 前置：MCP Server 运行在 `7800` 端口，传输支持 `sse`（局域网）+ `stdio`（本机），返回内容默认 LZ4 压缩 + Arrow IPC 编码（行数 > 1000 时启用）。

---

## 0. 通用约定

### 0.1 请求信封

所有工具调用遵循 MCP 标准协议：

```json
{
  "jsonrpc": "2.0",
  "id": "<uuid>",
  "method": "tools/call",
  "params": {
    "name": "<tool_name>",
    "arguments": { ... }
  }
}
```

### 0.2 响应信封

```json
{
  "jsonrpc": "2.0",
  "id": "<uuid>",
  "result": {
    "content": [
      {"type": "text", "text": "<json_payload | arrow_ipc_base64>"},
      {"type": "resource", "resource": {"uri": "...", "mimeType": "..."}}
    ],
    "isError": false,
    "_meta": {
      "row_count": 1234,
      "encoding": "arrow_ipc_lz4 | json",
      "duration_ms": 56,
      "cache_hit": false
    }
  }
}
```

### 0.3 错误信封

```json
{
  "jsonrpc": "2.0",
  "id": "<uuid>",
  "error": {
    "code": -32001,
    "message": "<human_readable>",
    "data": {
      "error_code": "QUERY_TIMEOUT",
      "retry_after_ms": 5000,
      "details": { ... }
    }
  }
}
```

### 0.4 错误码表

| code | error_code | 含义 | 客户端动作 |
|------|------------|------|------------|
| -32600 | INVALID_REQUEST | JSON-RPC 格式错误 | 修正请求 |
| -32602 | INVALID_PARAMS | 参数 schema 不匹配 | 检查参数 |
| -32001 | QUERY_TIMEOUT | 单查询超 30s | 缩小范围或加索引列 |
| -32002 | ROW_LIMIT_EXCEEDED | 返回行 > 1M | 启用分页或聚合 |
| -32003 | TABLE_NOT_FOUND | 表不存在 | 检查表名（可能未冷启动） |
| -32004 | DATA_NOT_READY | 当日数据未刷新 | 等待 / 检查 sync_state |
| -32005 | RATE_LIMIT_EXCEEDED | 客户端 QPS 超限 | 退避 retry_after_ms |
| -32006 | UNAUTHORIZED | IP 不在白名单 | 联系管理员 |
| -32007 | INTERNAL_ERROR | 服务端异常 | 重试或上报 |

### 0.5 流式 vs 批式边界

| 行数预估 | 编码 | 传输 |
|----------|------|------|
| < 100 | JSON | 单 response |
| 100 - 1000 | JSON | 单 response |
| 1000 - 100K | Arrow IPC + LZ4 | 单 response（base64） |
| 100K - 1M | Arrow IPC + LZ4 | SSE 分片（每片 ~10K 行） |
| > 1M | 拒绝 | 返回 ROW_LIMIT_EXCEEDED |

**SSE 分片协议**：
```
event: chunk
data: {"seq": 0, "rows": 10000, "arrow_b64": "..."}

event: chunk
data: {"seq": 1, "rows": 10000, "arrow_b64": "..."}

event: end
data: {"total_rows": 23456, "duration_ms": 1234}
```

---

## 1. 工具列表

| 工具名 | 类别 | 用途 |
|--------|------|------|
| `kline` | 行情 | OHLCV + 复权 |
| `tick_resample` | 行情 | 1min → N min/D/W/M |
| `quote_snapshot` | 行情 | 单日快照（多股） |
| `factor_score` | 因子 | 多因子打分 |
| `sector_rank` | 板块 | 行业/概念排名 |
| `money_flow` | 资金 | 资金流向 |
| `top_list_query` | 资金 | 龙虎榜 |
| `fina_query` | 财务 | 财务指标查询 |
| `holder_change` | 股东 | 股东户数/持股 |
| `event_query` | 事件 | 公告/分红/解禁 |
| `index_constituent` | 指数 | 成分股 + 权重 |
| `option_chain` | 衍生 | 期权链 |
| `convertible_bond` | 衍生 | 转债折溢价 |
| `raw_sql` | 兜底 | 任意只读 SQL |
| `schema_describe` | 元 | 表结构查询 |
| `data_freshness` | 元 | 数据新鲜度 |

---

## 2. 工具详细契约

### 2.1 `kline`

**用途**：取单只股票的 K 线数据。

**输入 Schema**：
```json
{
  "type": "object",
  "required": ["ts_code", "start", "end"],
  "properties": {
    "ts_code": {"type": "string", "pattern": "^[0-9]{6}\\.(SH|SZ|BJ)$"},
    "start":   {"type": "string", "pattern": "^[0-9]{8}$"},
    "end":     {"type": "string", "pattern": "^[0-9]{8}$"},
    "freq":    {"type": "string", "enum": ["D", "W", "M", "60min", "30min", "15min", "5min", "1min"], "default": "D"},
    "adj":     {"type": "string", "enum": ["qfq", "hfq", "none"], "default": "qfq"},
    "fields":  {"type": "array", "items": {"type": "string"}, "default": ["open", "high", "low", "close", "vol", "amount"]}
  }
}
```

**输出 Schema**：
```json
{
  "type": "object",
  "properties": {
    "ts_code": {"type": "string"},
    "freq":    {"type": "string"},
    "adj":     {"type": "string"},
    "rows":    {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "trade_date": {"type": "string"},
          "open":       {"type": "number"},
          "high":       {"type": "number"},
          "low":        {"type": "number"},
          "close":      {"type": "number"},
          "vol":        {"type": "number"},
          "amount":     {"type": "number"}
        }
      }
    }
  }
}
```

**复权语义**：
- `qfq`（前复权）：`price * adj_factor / latest_adj_factor`，起点价格调整为最新基准；连续可比。
- `hfq`（后复权）：`price * adj_factor`，终点不调整，反映绝对累积涨幅。
- `none`：原始价格，跨除权日不可比。
- **停牌处理**：停牌日不返回行（不补 NaN，由调用方决定是否插值）。
- **退市处理**：`stock_basic.list_status = 'D'` 时，`end` 自动 clip 到 `delist_date`。
- **未上市**：`start < list_date` 时，从 `list_date` 开始返回。

**性能预期**：单股票 × 5 年日线 < 80ms；分钟线 × 1 月 < 200ms。

---

### 2.2 `tick_resample`

**用途**：把分钟数据聚合为指定频率。

**输入 Schema**：
```json
{
  "required": ["ts_code", "start", "end", "src_freq", "dst_freq"],
  "properties": {
    "ts_code":  {"type": "string"},
    "start":    {"type": "string"},
    "end":      {"type": "string"},
    "src_freq": {"enum": ["1min", "5min", "15min"]},
    "dst_freq": {"enum": ["5min", "15min", "30min", "60min", "D", "W", "M"]},
    "session":  {"enum": ["regular", "all"], "default": "regular"}
  }
}
```

**聚合规则**：
- `open` = 区间内第一笔 (`argMin(open, ts)`)
- `high` = `max(high)`
- `low`  = `min(low)`
- `close` = 区间内最后一笔 (`argMax(close, ts)`)
- `vol`  = `sum(vol)`
- `amount` = `sum(amount)`

**会话边界**：`session=regular` 仅含 09:30-11:30 + 13:00-15:00；`all` 包含集合竞价。

---

### 2.3 `quote_snapshot`

**用途**：取一批股票指定日期的行情快照。

**输入**：
```json
{
  "required": ["ts_codes", "trade_date"],
  "properties": {
    "ts_codes":   {"type": "array", "items": {"type": "string"}, "maxItems": 5500},
    "trade_date": {"type": "string"},
    "fields":     {"type": "array", "items": {"type": "string"}, "default": ["close", "pct_chg", "vol", "amount", "turnover_rate", "pe_ttm", "pb"]}
  }
}
```

**输出**：长表格式（每行一只股票），便于 AI 横截面分析。

---

### 2.4 `factor_score`

**用途**：多因子打分。

**输入**：
```json
{
  "required": ["trade_date", "factors"],
  "properties": {
    "trade_date": {"type": "string"},
    "universe":   {"type": "string", "enum": ["all", "hs300", "zz500", "zz1000", "custom"], "default": "all"},
    "custom_codes": {"type": "array", "items": {"type": "string"}},
    "factors": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "weight"],
        "properties": {
          "name":      {"enum": ["pe_ttm", "pb", "ps_ttm", "roe", "roa", "netprofit_yoy", "or_yoy", "dv_ratio", "turnover_rate", "amount_ma20"]},
          "weight":    {"type": "number"},
          "direction": {"enum": ["asc", "desc"], "default": "desc"},
          "winsorize": {"type": "boolean", "default": true},
          "neutralize_industry": {"type": "boolean", "default": false}
        }
      }
    },
    "limit": {"type": "integer", "default": 100, "maximum": 5500}
  }
}
```

**输出**：每只股票的因子原值、分位、加权得分、最终排名。

**计算语义**：
1. 取 `trade_date` 当日 universe
2. 财务因子用 `argMax(value, end_date)` 取最新可披露值
3. winsorize：用 1%/99% 分位 clip
4. neutralize_industry：行业内 z-score 标准化
5. 加权 `sum(rank_pct * weight)` 排序

---

### 2.5 `sector_rank`

**用途**：行业 / 概念板块排名。

**输入**：
```json
{
  "required": ["trade_date", "level"],
  "properties": {
    "trade_date": {"type": "string"},
    "level":      {"enum": ["sw_l1", "sw_l2", "sw_l3", "ths_concept", "dc_concept"]},
    "metrics":    {"type": "array", "items": {"enum": ["avg_pct", "median_pct", "money_in", "limit_up_cnt", "broad_breadth"]}},
    "windows":    {"type": "array", "items": {"enum": ["1d", "5d", "20d", "60d"]}, "default": ["1d", "5d", "20d"]}
  }
}
```

---

### 2.6 `money_flow`

**用途**：资金流向（个股 / 板块）。

**输入**：
```json
{
  "properties": {
    "ts_code":    {"type": "string"},
    "sector":     {"type": "string"},
    "start":      {"type": "string"},
    "end":        {"type": "string"},
    "granularity": {"enum": ["main", "super_large", "large", "medium", "small"], "default": "main"}
  },
  "oneOf": [{"required": ["ts_code", "start", "end"]}, {"required": ["sector", "start", "end"]}]
}
```

---

### 2.7 `top_list_query`

**用途**：龙虎榜查询。

**输入**：
```json
{
  "required": ["start", "end"],
  "properties": {
    "start":   {"type": "string"},
    "end":     {"type": "string"},
    "ts_code": {"type": "string"},
    "reason":  {"type": "string"},
    "min_net_amount": {"type": "number"}
  }
}
```

---

### 2.8 `fina_query`

**用途**：财务指标查询。

**输入**：
```json
{
  "required": ["ts_codes"],
  "properties": {
    "ts_codes":  {"type": "array", "items": {"type": "string"}, "maxItems": 100},
    "end_date":  {"type": "string"},
    "report_type": {"enum": ["1", "2", "3", "4"], "default": "1"},
    "fields":    {"type": "array", "items": {"type": "string"}}
  }
}
```

**报告类型**：
- `1` 合并报表（默认）
- `2` 单季合并
- `3` 调整单季合并表
- `4` 调整合并报表

---

### 2.9 `holder_change`

**用途**：股东户数 / 大股东持股变动。

**输入**：
```json
{
  "properties": {
    "ts_code":    {"type": "string"},
    "start":      {"type": "string"},
    "end":        {"type": "string"},
    "type":       {"enum": ["holder_num", "top10", "top10_float", "trade"]}
  }
}
```

---

### 2.10 `event_query`

**用途**：公司事件（分红、解禁、回购、股权激励）。

**输入**：
```json
{
  "properties": {
    "ts_code":  {"type": "string"},
    "start":    {"type": "string"},
    "end":      {"type": "string"},
    "category": {"enum": ["dividend", "share_float", "repurchase", "incentive", "block_trade"]}
  }
}
```

---

### 2.11 `index_constituent`

**用途**：指数成分股 + 权重。

**输入**：
```json
{
  "required": ["index_code"],
  "properties": {
    "index_code": {"type": "string"},
    "trade_date": {"type": "string"}
  }
}
```

---

### 2.12 `option_chain`

**用途**：期权链。

**输入**：
```json
{
  "required": ["underlying", "trade_date"],
  "properties": {
    "underlying": {"type": "string"},
    "trade_date": {"type": "string"},
    "expire":     {"type": "string"}
  }
}
```

---

### 2.13 `convertible_bond`

**用途**：可转债折溢价 / 强赎。

**输入**：
```json
{
  "properties": {
    "ts_code":    {"type": "string"},
    "stk_code":   {"type": "string"},
    "trade_date": {"type": "string"}
  }
}
```

---

### 2.14 `raw_sql` ⚠️

**用途**：兜底执行只读 SQL（DBA / AI 探索）。

**输入**：
```json
{
  "required": ["sql"],
  "properties": {
    "sql":    {"type": "string", "maxLength": 8192},
    "params": {"type": "object", "default": {}},
    "format": {"enum": ["json", "arrow"], "default": "arrow"}
  }
}
```

**安全约束**：
- 只允许 `SELECT` / `WITH`
- 拒绝 `INSERT / UPDATE / DELETE / DROP / TRUNCATE / ALTER / RENAME / GRANT`
- 拒绝 `system.*` 表中的非白名单（仅放行 `system.parts`, `system.tables`, `system.columns`, `system.processes`）
- 单查询超时 30s
- `max_result_rows = 1000000`
- `max_memory_usage = 8GB`
- 通过 `ai_reader` 账号执行（DB 层只读权限二次保险）

---

### 2.15 `schema_describe`

**用途**：表结构查询（供 AI 自动构建 SQL）。

**输入**：
```json
{
  "properties": {
    "table":    {"type": "string"},
    "include_sample": {"type": "boolean", "default": false}
  }
}
```

**输出**：列名、类型、注释、3 行采样、行数估计、最新 trade_date / end_date。

---

### 2.16 `data_freshness`

**用途**：数据新鲜度检查（AI 决策"今天数据有了吗"）。

**输入**：
```json
{
  "properties": {
    "tables": {"type": "array", "items": {"type": "string"}}
  }
}
```

**输出**：
```json
{
  "tables": [
    {"name": "daily",          "last_trade_date": "20250424", "row_count_today": 5500, "sync_state": "ok",      "updated_at": "2026-04-25T16:30:12Z"},
    {"name": "fina_indicator", "last_end_date":   "20241231", "row_count_today": 0,    "sync_state": "ok",      "updated_at": "2026-04-23T09:12:00Z"},
    {"name": "moneyflow",      "last_trade_date": "20250424", "row_count_today": 5500, "sync_state": "partial", "heartbeat_at": "2026-04-25T16:25:00Z"}
  ]
}
```

---

## 3. 鉴权与限流

- **鉴权**：IP 白名单（`users.xml` 的 `host_regexp`），无需 token；MCP Server 在 SSE 握手时拒绝非白名单 IP
- **限流**：客户端级别 100 QPS（按 source IP），全局 500 QPS；超限返回 -32005 + `retry_after_ms`
- **跨域**：MCP Server 启用 CORS（`Access-Control-Allow-Origin: *`），允许浏览器内 AI 调用

---

## 4. 客户端示例（Python）

```python
import json
import httpx
import pyarrow.ipc as ipc
import base64
import lz4.frame as lz4

async def call_tool(name: str, args: dict) -> dict:
    async with httpx.AsyncClient(http2=True) as client:
        r = await client.post(
            "http://192.168.1.100:7800/rpc",
            json={"jsonrpc": "2.0", "id": "1", "method": "tools/call",
                  "params": {"name": name, "arguments": args}},
            timeout=60.0,
        )
        r.raise_for_status()
        result = r.json()["result"]
        encoding = result["_meta"]["encoding"]
        text = result["content"][0]["text"]
        if encoding == "arrow_ipc_lz4":
            buf = lz4.decompress(base64.b64decode(text))
            return ipc.open_stream(buf).read_all().to_pylist()
        return json.loads(text)
```

---

## 5. 版本与兼容

- 所有工具加 `tool_version` 字段（`_meta.tool_version`），客户端可比对
- BREAKING change（输入参数语义变更）必须升 major 版本，老版本至少保留 2 个月
- 字段添加（向后兼容）只升 minor

---

## 6. 实现 Checklist

- [ ] 每个工具一个文件（`src/mcp/tools/<name>.py`），单元测试覆盖输入校验 + 边界
- [ ] JSON Schema 用 Pydantic v2 model 定义，`.model_json_schema()` 自动生成
- [ ] Arrow IPC 用 `pyarrow.ipc.RecordBatchStreamWriter`，LZ4 压缩 level=3
- [ ] SSE 分片用 `sse-starlette` 实现，心跳 15s
- [ ] `raw_sql` 用 `sqlglot` parse + AST 校验，拒绝非 SELECT
- [ ] 集成测试：`testcontainers` 起 ClickHouse + Mock Tushare → 跑全部工具
