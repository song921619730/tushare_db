# Tushare DB — 第二轮修复计划（生产就绪冲刺）

> 面向：VSCode + Claude Code + Qwen 3.6 Plus
> 文档作者：Sonnet 4.6（审计者）
> 生成日期：2026-04-26
> 前置文档：
> - `a-ai-ai-tushare-pro-kind-gizmo.md`（权威设计）
> - `a-implementation-handoff-guide.md`（PR 剧本）
> - `a-remediation-plan-for-qwen.md`（第一轮修复，B1-B23 已完成）
> - `data/logs/remaining_validation.md`（Qwen 自评：F1-F3 已补丁）

---

## 0. 当前状态（一句话总结）

**代码层 92% 完成；生产层 NO**——三个阻塞项：
1. **F1 是安全降级**——MCP 用 write-capable 的 `pipeline` 用户（违反 ai_reader 只读设计）
2. **真实数据从未跑通**——adj_factor 仅 1 天，财务表全空，B1 万元归一化的招牌修复 **从未在真数据上验证过**
3. **测试覆盖率 30%**——MCP 工具（外部暴露面）覆盖率 0%

加上 6 个新发现的 bug（N1-N6）和 7 个运维空白（O1-O7），合计 **16 项**剩余工作。

---

## 1. 全景：16 项待办

| ID | 严重度 | 类别 | 文件 | 一句话 |
|----|--------|------|------|--------|
| **N1** | 🔴 P0 安全 | `mcp_server/tools.py:34` | F1 修复用 `pipeline` 用户绕开了 ai_reader 密码问题，开放了写权限 |
| **N2** | 🔴 P0 安全 | `mcp_server/tools.py:108,275,302,332,363,401` | 6 个 MCP 工具用 f-string 拼 SQL，注入漏洞 |
| **N3** | 🟡 P1 正确性 | `runner/worker.py:35` | `_COLUMN_TYPE_CACHE` 永不失效，schema 变更后 worker 仍用旧类型 |
| **N4** | 🟡 P1 并发安全 | `runner/worker.py:158` | 心跳线程与主线程共用同一个 ClickHouse client，HTTP client 非线程安全 |
| **N5** | 🟢 P2 安全（潜在） | `schema/evolver.py:53,101,159` | DDL 用 f-string 拼接，目前调用方可控但缺乏校验 |
| **N6** | 🟢 P2 性能 | `mcp_server/tools.py:223` | `describe_table` 跑 `count() FROM ... FINAL`，大表会慢到分钟级 |
| **O1** | 🔴 P0 运维 | bootstrap 状态 | 58 个接口被静默禁用（45 paid + 10 empty + 3 offline），实际 enabled 169 个，与设计的 182 缺口不明 |
| **O2** | 🔴 P0 运维 | `tushare_adj_factor` 仅 1 天数据 | get_ohlcv 复权对任意日期返回 1 行 |
| **O3** | 🔴 P0 运维 | 财务表全空 | B1 财务归一化在真数据上从未验证 |
| **O4** | 🟡 P1 测试 | 覆盖率 30% | CLI/MCP/verify 接近 0%，违反 80% 标准 |
| **O5** | 🟡 P1 测试 | 集成测试在 Windows 失败 | testcontainers + WSL2 兼容性，CI/CD 跑不起来 |
| **O6** | 🟡 P1 运维 | 高并发未测 | 12/6 worker 在真数据上未跑过；结合 N4 心跳竞争，可能在长跑中段崩 |
| **O7** | 🟡 P1 运维 | 无备份 | `docker volume rm` 一发命令 6 年数据归零 |
| **O8** | 🟢 P2 测试 | F1-F3 没回归测试 | 上轮 Docker 验证发现的 3 个 bug 改完后没补 unit/integration test |
| **O9** | 🟢 P2 文档 | YAML 禁用清单未公开 | 哪 58 个被禁用、为什么禁、何时复活，没有清单 |
| **O10** | 🟢 P2 部署 | nginx + dashboard 未做端到端验证 | validation log 里没看到 `curl http://localhost:3001/api/ch/?query=SELECT 1` 的实际输出 |

---

## 2. P0 必须修（不修不能上生产）

### N1. MCP 用 pipeline 用户 → 给 AI 开了写权限

**位置**：`src/tushare_db/mcp_server/tools.py:32-37`

**当前代码**：
```python
def _get_client() -> clickhouse_connect.driver.Client:
    return clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),
        user="pipeline",                                        # ⚠️ 应该是 ai_reader
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),    # ⚠️ 应该是 CH_AI_READER_PASSWORD
        database="tushare",
    )
```

**为什么这是大问题**：
- `users.xml` 中 `pipeline` 没有 `<readonly>` 限制，profile=`default` → 读写全权
- AI 通过 MCP 调 `query_sql("WITH _ AS (SELECT 1) INSERT INTO tushare.tushare_stock_daily VALUES ...")` —— `_SELECT_RE` 只检查开头是 SELECT/WITH/SHOW/DESCRIBE，**WITH 后面的 INSERT 会被放行**
- 即使 SQL 注入挡住了，本地 / 局域网内任何调用 MCP 的脚本都可以 `DROP TABLE` / `TRUNCATE`
- 设计文档 §10.2 明确要求 ai_reader 走 `readonly=2`（DB 层强制只读，应用层失误也兜得住）

**根本原因**：F1 时 ai_reader 密码不一致，Qwen 选择改用户绕开，而不是修密码。

**修复（顺序很重要）**：

#### Step 1：修 ai_reader 密码加载

打开 `docker/clickhouse/users.xml`，确认 ai_reader 用 `from_env`：
```xml
<ai_reader>
    <password from_env="CH_AI_READER_PASSWORD"/>
    <networks>
        <host_regexp>192\.168\..*|10\..*|172\.(1[6-9]|2[0-9]|3[0-1])\..*|127\.0\.0\.1|.*</host_regexp>
        <!-- 注意：容器内 MCP 调用走 docker network，IP 是 172.x，必须包括；最后 .* 兜底测试用 -->
    </networks>
    <profile>ai_reader_profile</profile>
    <quota>unlimited</quota>
</ai_reader>
```

如果 `from_env` 在 users.d 不工作（progress.md 提到过这个坑），改用明文，但通过 docker-compose 的 `secrets:` 注入或 `entrypoint` 脚本 `sed` 替换：

```yaml
# docker-compose.yml
clickhouse:
  environment:
    CH_AI_READER_PASSWORD: ${CH_AI_READER_PASSWORD}
  command: >
    sh -c "sed -i 's/__AI_READER_PWD__/'$$CH_AI_READER_PASSWORD'/g' /etc/clickhouse-server/users.d/00-users.xml &&
           /entrypoint.sh"
```

users.xml 模板里写 `<password>__AI_READER_PWD__</password>`。

#### Step 2：恢复 MCP 用 ai_reader

```python
# src/tushare_db/mcp_server/tools.py

def _get_client() -> clickhouse_connect.driver.Client:
    """ClickHouse client for MCP — read-only via ai_reader."""
    return clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),
        username="ai_reader",                                   # ✅
        password=os.environ.get("CH_AI_READER_PASSWORD", ""),   # ✅
        database="tushare",
    )
```

#### Step 3：加入纵深防御测试

新建 `tests/integration/test_mcp_readonly.py`：

```python
import pytest
from tushare_db.mcp_server.tools import _get_client, query_sql

def test_query_sql_rejects_insert_via_with_clause():
    """WITH ... INSERT 攻击应被 ClickHouse readonly=2 拒绝（DB 层兜底）。"""
    with pytest.raises(Exception) as exc:
        query_sql("WITH x AS (SELECT 1) INSERT INTO tushare.test VALUES (1)")
    assert "readonly" in str(exc.value).lower() or "denied" in str(exc.value).lower()

def test_query_sql_rejects_drop_table():
    with pytest.raises(Exception):
        query_sql("DROP TABLE tushare.tushare_stock_daily")

def test_query_sql_rejects_truncate():
    with pytest.raises(Exception):
        query_sql("TRUNCATE TABLE tushare.tushare_stock_daily")

def test_query_sql_allows_select():
    result = query_sql("SELECT 1 AS x")
    assert result == [{"x": 1}]
```

---

### N2. MCP 6 个工具 SQL 注入

**位置**：`tools.py:108, 275, 302, 332, 363, 401` —— 几乎所有 `_safe_query` 之前的 SQL 构建处

**当前代码**（举一例）：
```python
sql = (
    f"SELECT * FROM tushare.tushare_income WHERE ts_code = '{ts_code}'"  # ⚠️ 直接 f-string 拼接
)
if periods:
    period_list = ", ".join(f"'{p}'" for p in periods)
    sql += f" AND period IN ({period_list})"
```

**攻击 PoC**：
```python
get_financials(ts_code="000001.SZ' UNION ALL SELECT * FROM system.users--", statement="income")
# 实际执行：
# SELECT * FROM tushare.tushare_income WHERE ts_code = '000001.SZ' UNION ALL SELECT * FROM system.users--'
```

虽然 ai_reader（修复 N1 后）只读，无法改数据，但能**读 system.users / system.tables / 其他敏感系统表**。

**修复方案**：用 `clickhouse_connect` 的参数化查询。

```python
# src/tushare_db/mcp_server/tools.py

@mcp.tool()
def get_financials(ts_code: str, statement: str = "income", periods: list[str] | None = None):
    # 1. 白名单校验枚举字段（不能参数化的部分）
    table_map = {
        "income": "tushare.tushare_income",
        "balancesheet": "tushare.tushare_balancesheet",
        "cashflow": "tushare.tushare_cashflow",
        "fina_indicator": "tushare.tushare_fina_indicator",
    }
    table = table_map.get(statement)
    if not table:
        raise ValueError(f"Unknown statement: {statement}")

    # 2. 参数化用户输入
    client = _get_client()
    try:
        sql = f"SELECT * FROM {table} FINAL WHERE ts_code = %(ts_code)s"
        params = {"ts_code": ts_code}

        if periods:
            # ts_code, periods 都是不可信，必须参数化
            sql += " AND period IN %(periods)s"
            params["periods"] = tuple(periods)

        sql += " ORDER BY period DESC"

        result = client.query(sql, parameters=params)
        return _rows_to_dicts(result)
    finally:
        client.close()
```

**校验输入格式**（在参数化之上再加一层防御）：

```python
import re

_TS_CODE_RE = re.compile(r"^[0-9]{6}\.(SH|SZ|BJ)$")
_DATE_RE    = re.compile(r"^[0-9]{8}$")
_INDEX_RE   = re.compile(r"^[0-9]{6}\.(SH|SZ|CSI|CICC)$")

def _validate_ts_code(ts_code: str) -> str:
    if not _TS_CODE_RE.match(ts_code):
        raise ValueError(f"Invalid ts_code format: {ts_code!r}")
    return ts_code

def _validate_date(date: str, name: str = "date") -> str:
    if not _DATE_RE.match(date):
        raise ValueError(f"Invalid {name} format (expected YYYYMMDD): {date!r}")
    return date
```

每个工具入口先调 `_validate_*`，再传给参数化 SQL。

**改的清单**：
- `get_ohlcv`: ts_code, start_date, end_date, adjust（adjust 已是 enum 校验）
- `get_financials`: ts_code, statement, periods
- `get_index_components`: index_code, date
- `get_moneyflow`: ts_code, start_date, end_date
- `trade_calendar`: start_date, end_date, exchange（exchange 也要白名单）
- `coverage_report`: interface, priority（白名单）
- `describe_table`: table（白名单 from list_interfaces）
- `query_sql`: 这个本就允许任意 SELECT —— 但加 `EXPLAIN AST` 解析检查不允许 `system.*` 之外的元数据访问？太复杂，改用 ClickHouse 配置 `<query_complexity>` 限制

**测试**：每个工具加 SQLi PoC 测试：

```python
@pytest.mark.parametrize("payload", [
    "000001.SZ' OR 1=1--",
    "000001.SZ'; DROP TABLE foo--",
    "' UNION SELECT * FROM system.users--",
])
def test_get_ohlcv_rejects_injection(payload):
    with pytest.raises(ValueError, match="Invalid ts_code format"):
        get_ohlcv(payload, "20240101", "20240131")
```

---

### O1. Bootstrap 缺口隐藏，需要重新对账

**位置**：`config/interfaces/*.yaml` —— 当前 169 enabled，设计应 182

**问题**：B11 + B22 修复时把"采样失败"的接口标 `enabled: false` 而不是修复采样逻辑。结果是：
- 设计文档说"182 enabled + 45 paid"
- 实际：169 enabled，58 disabled（45 paid + 13 跑不通）
- 用户/AI 不知道哪些数据在仓库里、哪些没有

**修复**：

#### Step 1：生成对账表

```bash
cd F:/AIcoding_space/VsCode/tushare_db
.venv/Scripts/python.exe -c "
from tushare_db.config.loader import load_all_interface_specs
specs = load_all_interface_specs()
print(f'total: {len(specs)}')
print(f'enabled: {sum(1 for s in specs if s.enabled)}')
disabled = [(s.name, getattr(s, \"_disabled_reason\", \"unknown\")) for s in specs if not s.enabled]
for name, reason in sorted(disabled):
    print(f'  {name}: {reason}')
"
```

#### Step 2：把禁用原因写进 YAML

在每个 disabled spec 加 `disabled_reason` 字段：

```yaml
- name: film_record
  enabled: false
  disabled_reason: "tushare_offline_2024"   # 接口已下线
  ...

- name: dc_hot
  enabled: false
  disabled_reason: "empty_sample"           # 采样返回 0 行
  ...

- name: bak_basic
  enabled: false
  disabled_reason: "paid_5000"              # 5000 积分付费接口
  ...
```

枚举值：
- `paid_<level>` — 付费分级（5000/10000/15000）
- `tushare_offline_<year>` — Tushare 已下线
- `empty_sample` — 采样为空，需要特殊参数
- `auth_denied` — 权限不足
- `needs_investigation` — 还没排查

#### Step 3：生成对账文档

新建 `data/logs/coverage_audit.md`：

```markdown
# Coverage 对账（2026-04-XX 生成）

| Source | Count | 备注 |
|--------|-------|------|
| 设计文档承诺 enabled | 182 | a-ai-ai-tushare-pro-kind-gizmo.md §11 |
| 实际 enabled | 169 | 当前 YAML |
| 缺口 | 13 | 需要逐个排查 |

## 缺口明细

| 接口 | 当前状态 | disabled_reason | 处理建议 |
|------|---------|-----------------|---------|
| film_record | disabled | tushare_offline_2024 | 接受，从设计文档 §11 列表删除 |
| dc_hot | disabled | empty_sample | 修采样器，传 trade_date 参数 |
| ... | ... | ... | ... |
```

#### Step 4：尝试恢复 5 个最重要的禁用接口

对 `disabled_reason: empty_sample` 的，重写 `cli.py:_sample_one_interface` 的策略分支：

```python
def _sample_one_interface(client, spec) -> dict | None:
    strategy = spec.fetch_strategy.kind
    name = spec.name

    # Special-case 那些通用模板搞不定的接口
    if name == "dc_hot":
        return client.call(name, bucket=spec.freq_bucket, trade_date="20240315")
    if name == "moneyflow_ths":
        return client.call(name, bucket=spec.freq_bucket, trade_date="20240315", ts_code="000001.SZ")
    if name == "stk_auction":
        return client.call(name, bucket=spec.freq_bucket, ts_code="000001.SZ", start_date="20240101", end_date="20240301")
    # ... 列表见 progress.md

    # 默认策略
    if strategy in ("date_loop", "offset_paging"):
        return client.call(name, bucket=spec.freq_bucket, trade_date="20240102")
    # ... 其余按现有逻辑
```

每修一个，跑 `tushare-db sample-apis --only <name>` 验证有数据，再 `tushare-db rebuild-schema --interface <name>`。

---

### O2 + O3. 真数据从未跑通 → B1 招牌修复未验证

**位置**：`tushare_adj_factor` 5,513 行（仅 1 天）；`tushare_income` 等 0 行

**问题**：
- N1+N2 修完，MCP 安全了
- 但是 get_ohlcv qfq/hfq 对 2026-04-23 之外的日期都返回 1 行（adj_factor 数据缺）
- 财务表全空 → B1 万元归一化在真数据从未跑过 → 不知道是否真的有效

**修复**：执行完整 P0 + P1 backfill。

#### Step 1：先在小时间窗口跑通

```bash
# 测试 daily（5500 stocks × 22 days × 1 接口）
docker compose exec pipeline-scheduler tushare-db backfill \
  --interface daily --from 20240101 --to 20240131

# 验证行数（约 121K，5500 × 22）
docker compose exec clickhouse clickhouse-client --query \
  "SELECT count() FROM tushare.tushare_stock_daily FINAL WHERE trade_date BETWEEN '20240101' AND '20240131'"

# 测试 adj_factor
docker compose exec pipeline-scheduler tushare-db backfill \
  --interface adj_factor --from 20200101 --to 20240131

# 验证 get_ohlcv qfq 返回 22 行
docker compose exec pipeline-mcp curl -X POST http://localhost:7800/mcp \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_ohlcv","arguments":{"ts_code":"000001.SZ","start_date":"20240101","end_date":"20240131","adjust":"qfq"}},"id":1}'
```

#### Step 2：跑财务表（关键 B1 验证）

```bash
docker compose exec pipeline-scheduler tushare-db backfill \
  --interface income --from 20231001 --to 20231231

# 验证 B1：贵州茅台 2023 年报营收应在 1.5e11 量级（约 1500 亿元）
docker compose exec clickhouse clickhouse-client --query \
"SELECT ts_code, end_date, total_revenue, n_income
 FROM tushare.tushare_income FINAL
 WHERE ts_code='600519.SH' AND end_date='20231231'
 FORMAT Vertical"
```

**期望输出**：
```
ts_code:       600519.SH
end_date:      2023-12-31
total_revenue: 150560000000.00       # 1505 亿元，正确
n_income:      74734000000.00        # 747 亿元，正确
```

**如果是这样就是 bug**：
```
total_revenue: 15056000.00           # ⚠️ 1500 万元，B1 没生效
```

#### Step 3：全量 P0 + P1 跑一次

成功后跑全量：
```bash
docker compose exec -d pipeline-scheduler tushare-db backfill --priority P0 --all
docker compose logs -f pipeline-scheduler | tee data/logs/backfill_p0.log
```

**预算**：
- daily/daily_basic/adj_factor 等 6 年 × 84 normal 接口 ≈ 4-5 小时
- moneyflow 等 special 接口 ≈ 4-6 小时
- 财务表 period_loop（24 期 × 8 接口）≈ 2 小时
- **合计约 12-14 小时**（如果 N3+N4 没爆的话）

#### Step 4：验证完整性

```bash
docker compose exec pipeline-scheduler tushare-db verify --priority P0 --gaps --checksums
```

期望：所有接口 OK，无 gap，checksums 跑两次结果一致。

---

## 3. P1 高优先级（影响生产稳定性）

### N3. `_COLUMN_TYPE_CACHE` 永不失效

**位置**：`src/tushare_db/runner/worker.py:35`

**问题**：进程级缓存，schema 变更后 worker 仍用旧类型。`evolver.change_type()` 把 Float64 改成 Decimal64 后，正在跑的 backfill 还按 Float64 走，跳过 normalize_value，数据错。

**修复**：

```python
# src/tushare_db/runner/worker.py

import threading
import time

_COLUMN_TYPE_CACHE: dict[str, tuple[dict[str, str], float]] = {}  # (types, expires_at)
_CACHE_TTL = 300  # 5 分钟
_CACHE_LOCK = threading.Lock()


def _get_column_types(ch_client, table: str, database: str = "tushare") -> dict[str, str]:
    cache_key = f"{database}.{table}"
    now = time.monotonic()

    with _CACHE_LOCK:
        cached = _COLUMN_TYPE_CACHE.get(cache_key)
        if cached and cached[1] > now:
            return cached[0]

    # 缓存过期或不存在，重新查询
    result = ch_client.query(
        f"SELECT name, type FROM system.columns "
        f"WHERE database = '{database}' AND table = '{table}'"
    )
    types = {row[0]: row[1] for row in result.result_rows}

    with _CACHE_LOCK:
        _COLUMN_TYPE_CACHE[cache_key] = (types, now + _CACHE_TTL)

    return types


def invalidate_column_cache(database: str = None, table: str = None) -> None:
    """Schema 变更后调用。table=None 清整个 db；db=None 清全局。"""
    with _CACHE_LOCK:
        if database is None:
            _COLUMN_TYPE_CACHE.clear()
        elif table is None:
            keys_to_del = [k for k in _COLUMN_TYPE_CACHE if k.startswith(f"{database}.")]
            for k in keys_to_del:
                del _COLUMN_TYPE_CACHE[k]
        else:
            _COLUMN_TYPE_CACHE.pop(f"{database}.{table}", None)
```

并在 `schema/evolver.py` 的 `change_type` / `rename_column` 末尾调用：

```python
from tushare_db.runner.worker import invalidate_column_cache

def change_type(client, table, col, new_type, database="tushare"):
    # ... 原有影子表逻辑 ...
    invalidate_column_cache(database=database, table=table)
```

---

### N4. 心跳 + 主线程共用 client → 并发崩溃风险

**位置**：`src/tushare_db/runner/worker.py:158`（heartbeat thread）

**问题**：
- `executor.py` 给每个 worker 分配 thread-local client（B2 修复）
- 但 `worker.py:execute_unit` 内部启的心跳线程 `_heartbeat_loop` 用的是同一个 client
- `clickhouse_connect.HttpClient` 内部 `requests.Session` 在并发请求时会复用 socket，**主线程 INSERT 数据 + 心跳线程 INSERT sync_state 同时跑**会导致请求 body 错乱
- 长跑（>4 小时）的 backfill 概率会有奇怪的"insert 半截"或"connection reset"

**修复**：心跳线程用独立 client：

```python
# src/tushare_db/runner/worker.py

def execute_unit(unit, tushare_client, ch_client, run_id):
    # ... 主线程逻辑用 ch_client ...

    stop_event = threading.Event()
    heartbeat_client = _new_ch_client_for_heartbeat()  # 新建独立 client

    def _heartbeat_loop():
        try:
            while not stop_event.is_set():
                try:
                    _do_heartbeat(heartbeat_client, unit, attempt)  # 用独立 client
                except Exception as e:
                    logger.warning("Heartbeat failed", error=str(e))
                stop_event.wait(HEARTBEAT_INTERVAL)
        finally:
            heartbeat_client.close()

    heartbeat_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
    heartbeat_thread.start()

    try:
        # ... 主逻辑 ...
    finally:
        stop_event.set()
        heartbeat_thread.join(timeout=5)


def _new_ch_client_for_heartbeat() -> clickhouse_connect.driver.Client:
    import clickhouse_connect
    return clickhouse_connect.get_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=int(os.environ.get("CH_HTTP_PORT", "8123")),
        username="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
        database="_meta",
    )
```

**测试**：写一个真起 ClickHouse 容器的并发压力测试

```python
# tests/integration/test_worker_concurrency.py

import threading
import time
from concurrent.futures import ThreadPoolExecutor

def test_heartbeat_does_not_corrupt_main_insert(ch_container):
    """跑 50 个 worker，每个 60s，断言所有 sync_state 行可读且数据无乱码。"""
    # ... 起 50 worker 跑 mock unit，每 unit 60s ...
    # ... 断言 _meta.sync_state 行数 == 50 × (1 + 2 心跳) ...
    # ... 断言每个 _version 都 > 0 且单调递增 ...
```

---

### O4. 测试覆盖率 30% → 60%

**当前**：150 测试，30% 覆盖
**目标**：60%+

**优先补的模块**（按 ROI 排序）：

| 模块 | 当前 | 目标 | 测试类型 | 工作量 |
|------|------|------|----------|--------|
| `cli.py` | ~5% | 50% | subprocess 测试 | 1 天 |
| `mcp_server/tools.py` | 0% | 80% | 集成测试（testcontainers） | 1.5 天 |
| `verify/*.py` | 0% | 70% | 集成测试 | 0.5 天 |
| `runner/worker.py` | ~30% | 70% | 集成测试（含 N3/N4 回归） | 1 天 |
| `scheduler/jobs.py` | ~20% | 60% | mock APScheduler 单元测试 | 0.5 天 |

**框架**：Linux/WSL2 内跑（避免 testcontainers 在 Windows 的兼容性问题）

```bash
# 在 WSL2 Ubuntu 中
cd /mnt/f/AIcoding_space/VsCode/tushare_db
uv sync --all-extras
uv run pytest tests/ --cov=src --cov-report=term-missing --cov-report=html
```

**MCP 工具测试样板**：

```python
# tests/integration/test_mcp_tools.py

import pytest
from testcontainers.clickhouse import ClickHouseContainer

@pytest.fixture(scope="module")
def ch():
    with ClickHouseContainer("clickhouse/clickhouse-server:24.8") as c:
        # 创建测试 schema + 种数据
        client = c.get_connection_client()
        client.command("CREATE DATABASE tushare")
        client.command("""
            CREATE TABLE tushare.tushare_stock_daily (
                ts_code String, trade_date Date, open Float64, ...
            ) ENGINE = ReplacingMergeTree() ORDER BY (ts_code, trade_date)
        """)
        client.insert("tushare.tushare_stock_daily", [...])
        yield c

def test_get_ohlcv_returns_correct_rows(ch):
    os.environ["CH_HOST"] = ch.get_container_host_ip()
    os.environ["CH_HTTP_PORT"] = str(ch.get_exposed_port(8123))
    os.environ["CH_AI_READER_PASSWORD"] = "test"

    from tushare_db.mcp_server.tools import get_ohlcv
    result = get_ohlcv("000001.SZ", "20240101", "20240131", "qfq")
    assert len(result) == 22
    assert all("trade_date" in r for r in result)

def test_query_sql_blocks_insert(ch):
    from tushare_db.mcp_server.tools import query_sql
    with pytest.raises(Exception):
        query_sql("INSERT INTO tushare.tushare_stock_daily VALUES (...)")
```

---

### O5. 集成测试在 Windows 失败

**问题**：testcontainers 用 Docker socket，Windows + WSL2 配置复杂。

**修复方案**：

#### 方案 A：本地用 Linux/WSL2

更新 `README` 写明：
> 集成测试只在 Linux / WSL2 环境运行。Windows 用户进入 WSL2 Ubuntu shell 跑。

#### 方案 B：CI/CD（推荐长期）

新建 `.github/workflows/test.yml`：

```yaml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --all-extras
      - run: uv run pytest tests/unit -v
      - run: uv run pytest tests/integration -v
        env:
          DOCKER_HOST: unix:///var/run/docker.sock
      - uses: codecov/codecov-action@v4
```

#### 方案 C：本地 docker-compose 跑测试

```yaml
# docker-compose.test.yml
services:
  test-runner:
    build: ./docker/pipeline
    volumes:
      - ./tests:/app/tests:ro
      - ./src:/app/src:ro
    environment:
      CH_HOST: clickhouse
      CH_HTTP_PORT: 8123
      CH_AI_READER_PASSWORD: testpw
    command: pytest tests/integration -v
    depends_on:
      clickhouse: {condition: service_healthy}
```

`docker compose -f docker-compose.test.yml run --rm test-runner` 即可。

---

### O6. 高并发未在真数据上验证

**修复**：增加并发回归测试

```python
# tests/integration/test_concurrent_backfill.py

def test_concurrent_backfill_no_data_loss(ch_container, mock_tushare):
    """启 12 + 6 worker 跑 100 个 mock 单元，断言：
    1. 所有单元最终 status = 'done'
    2. _meta.sync_state 中没有重复 scope_key
    3. 业务表行数 == 期望
    4. 所有 _version 单调递增
    """
```

**手工压测**：

```bash
# 跑一个完整月份的 daily backfill（22 个交易日）
time docker compose exec pipeline-scheduler tushare-db backfill \
  --interface daily --from 20240101 --to 20240131

# 期望：< 10 分钟（22 × 5500 = 121K 行，HTTP/2 + 12 worker 跑得过）
# 如果 > 30 分钟，N3 或 N4 在跑长跑时露馅了
```

---

### O7. 无备份策略

**修复**：加备份脚本和定时任务。

#### Step 1：备份脚本

新建 `scripts/backup_clickhouse.sh`：

```bash
#!/bin/bash
# 用 ClickHouse 自带 BACKUP 命令做增量备份
# 必须 ClickHouse 22.8+

BACKUP_DIR="/var/lib/clickhouse/backups"
BACKUP_NAME="weekly_$(date +%Y%m%d).zip"

docker compose exec -T clickhouse clickhouse-client --query "
BACKUP DATABASE tushare TO Disk('backups', '$BACKUP_NAME')
SETTINGS compression_method='lz4', compression_level=3
"

# 拷贝到 host
docker cp clickhouse:$BACKUP_DIR/$BACKUP_NAME /backups/

# 删除 30 天前的备份
find /backups -name "weekly_*.zip" -mtime +30 -delete
```

`docker/clickhouse/config.xml` 加：
```xml
<storage_configuration>
    <disks>
        <backups>
            <type>local</type>
            <path>/var/lib/clickhouse/backups/</path>
        </backups>
    </disks>
</storage_configuration>
<backups>
    <allowed_disk>backups</allowed_disk>
</backups>
```

#### Step 2：定时备份

加到 APScheduler `scheduler/jobs.py`：

```python
def register_jobs(scheduler):
    # ... 原有 8 个 job ...

    scheduler.add_job(
        backup_clickhouse,
        trigger=CronTrigger(day_of_week='sun', hour=4, minute=0, timezone='Asia/Shanghai'),
        id='weekly_backup',
        name='Weekly ClickHouse Backup',
        misfire_grace_time=3600,
    )
```

#### Step 3：恢复演练

新建 `scripts/restore_clickhouse.sh`：

```bash
#!/bin/bash
# 用法：./restore_clickhouse.sh weekly_20260420.zip

BACKUP_NAME=$1
docker compose exec -T clickhouse clickhouse-client --query "
RESTORE DATABASE tushare FROM Disk('backups', '$BACKUP_NAME')
"
```

每月跑一次"假灾难恢复"演练，验证备份可用。

---

## 4. P2 锦上添花

### N5. evolver DDL 字符串拼接

**位置**：`schema/evolver.py:53,101,159`

**修复**：加输入校验

```python
import re
_IDENT_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

def _validate_ident(name: str, kind: str = "identifier") -> str:
    if not _IDENT_RE.match(name):
        raise ValueError(f"Invalid {kind}: {name!r}")
    return name

def rename_column(client, table, old_name, new_name):
    table = _validate_ident(table, "table")
    old_name = _validate_ident(old_name, "column")
    new_name = _validate_ident(new_name, "column")
    # ... 原有逻辑 ...
```

### N6. describe_table 用 system.parts

**位置**：`tools.py:223`

**当前**：`SELECT count() FROM {full_name} FINAL` —— 大表 1+ 分钟

**修复**：
```python
count_result = client.query(
    f"SELECT sum(rows) FROM system.parts "
    f"WHERE database = %(db)s AND table = %(tbl)s AND active = 1",
    parameters={"db": db_name, "tbl": tbl_name},
)
```

注意：`system.parts.rows` 不去重 ReplacingMergeTree 的旧版本，但作为粗略行数足够 describe 用途。如果要精确，加注释提示用户。

### O8. F1-F3 没回归测试

为 F1（用户切换）、F2（FINAL 语法）、F3（return type）各补一个集成测试，固化在 `tests/integration/test_mcp_tools.py`。

### O9. YAML 禁用清单

详见 O1 Step 3 —— 生成 `data/logs/coverage_audit.md`，定期更新。

### O10. Dashboard 端到端验证

```bash
# 容器外 curl
curl http://localhost:3001/                          # SPA HTML
curl 'http://localhost:3001/api/ch/?query=SELECT+1'  # 通过 nginx 反代

# 浏览器
http://localhost:3001/?ch_password=<pwd>
# 验证 URL 参数注入工作，密码自动存 localStorage 后从 URL 清除
```

把验证 SQL 写进 `data/logs/dashboard_e2e.md`。

---

## 5. 给 Qwen 的执行建议

### 5.1 顺序（强约束）

```
Day 1：N1 + N2（安全 P0）
  - 先修 ai_reader 密码加载（先在 docker compose down -v 后从干净状态起）
  - 改 MCP 用 ai_reader
  - 把 6 个工具的 f-string 全改成参数化
  - 加 SQLi 回归测试
  - Docker 端到端验证 query_sql 拒绝写入

Day 2：O1（对账）
  - 生成 coverage_audit.md
  - 修 5 个最重要的 disabled 接口（dc_hot, moneyflow_ths 等）
  - YAML 加 disabled_reason 字段

Day 3：O2 + O3（真数据 backfill）
  - daily 一个月跑通
  - adj_factor 6 年跑通
  - income 一个季度跑通
  - 验证 B1 财务数字 ×10000 正确（贵州茅台营收 1500 亿）

Day 4：N3 + N4（并发安全）
  - 缓存 TTL + invalidate
  - 心跳独立 client
  - 跑一个完整月度 backfill（压测）

Day 5：O4 + O5（测试覆盖率）
  - 在 WSL2 起跑集成测试
  - MCP tools 测试（含 SQLi、readonly、F1-F3 回归）
  - verify 模块测试
  - 覆盖率冲到 60%+

Day 6：O6 + O7（运维）
  - 全量 P0+P1 backfill（12-14h，半天 + 一晚）
  - 备份脚本 + 调度 + 恢复演练

Day 7：N5 + N6 + O8-O10 + 收尾
  - DDL 输入校验
  - describe_table 优化
  - 文档更新
```

### 5.2 沟通节奏

- **N1 修完立即汇报**——这是安全问题，不能拖
- **O3 财务数字验证完立即汇报**——这是 B1 修复的最终判决
- **每天结束更新 progress.md**

### 5.3 不要做的事

- ❌ 不要再"绕过"问题（F1 那样切用户来回避密码 bug，是反模式）
- ❌ 不要省略 SQLi 测试（即使你认为输入"应该是安全的"）
- ❌ 不要在没修 N4 的情况下跑长时间 backfill（中段会崩，浪费配额）
- ❌ 不要继续"声明完成"而不在真数据上验证（这是这一轮发现的最大的方法论问题）

---

## 6. 完成定义（DoD V2）

### 6.1 安全

- ✅ MCP 用 `ai_reader`，readonly=2 在 DB 层强制
- ✅ 所有 MCP 工具用参数化 SQL
- ✅ 输入格式校验在所有 ts_code/date/index_code 入口
- ✅ 集成测试覆盖：SQLi 拒绝、INSERT 拒绝、DROP 拒绝

### 6.2 数据正确性

- ✅ 全量 P0 backfill 成功（daily/daily_basic/adj_factor/moneyflow 6 年）
- ✅ 财务表至少 8 期（2 年）数据
- ✅ B1 验证：贵州茅台 2023 营收 = 1505 亿（10^11 量级）
- ✅ get_ohlcv qfq 任意股票任意 6 年 < 500ms 返回正确数据

### 6.3 并发与稳定

- ✅ N3 缓存 TTL + 失效钩子
- ✅ N4 心跳独立 client
- ✅ 跑一次完整 6 年 daily backfill 不崩，elapsed < 6h

### 6.4 测试

- ✅ 总覆盖率 ≥ 60%
- ✅ MCP tools 模块覆盖率 ≥ 80%
- ✅ 集成测试在 WSL2 / CI 都跑得通
- ✅ F1/F2/F3 都有回归测试

### 6.5 运维

- ✅ 备份脚本 + 调度
- ✅ 恢复演练成功一次
- ✅ coverage_audit.md 列出所有 disabled 接口及原因
- ✅ Dashboard / Grafana / MCP 三端在文档中都有可复制的 e2e 验证命令

---

## 7. 长期运行的"健康指标"

修完之后，项目要长期跑，每天 / 每周看以下指标判断健康：

```sql
-- 每天看：增量是否正常
SELECT max(trade_date), count(DISTINCT ts_code)
FROM tushare.tushare_stock_daily FINAL
WHERE trade_date >= today() - 7;
-- 期望：max=今天 or 昨天，count >= 5000

-- 每天看：API 调用 p99
SELECT
  toStartOfHour(started_at) AS hour,
  quantile(0.99)(duration_ms) AS p99,
  countIf(status >= 500) AS errors
FROM _meta.api_calls
WHERE started_at > now() - INTERVAL 24 HOUR
GROUP BY hour ORDER BY hour;
-- 期望：p99 < 3000ms，errors == 0

-- 每周看：sync_state 健康度
SELECT interface, status, count() FROM _meta.sync_state FINAL
GROUP BY interface, status HAVING status != 'done';
-- 期望：仅有少量 partial / failed，total < 50

-- 每月看：磁盘
SELECT
  formatReadableSize(sum(bytes_on_disk)) AS used,
  formatReadableSize(sum(data_uncompressed_bytes)) AS uncompressed
FROM system.parts WHERE database = 'tushare' AND active;
-- 期望：6 年数据 < 50GB
```

把这些查询写进 `data/logs/health_check.sql`，定期手工跑或加到 Grafana dashboard。

---

> 维护：每修复一项，把表 §1 该行的"待"改成 ✅ 并加 commit hash + 验证日期。
> 复盘：本轮做完后写一份"经验教训"——为什么 F1 这种"绕开问题"的修复发生了？为什么"声明完成"先于"真数据验证"？写进 `data/logs/post-mortem.md`。
