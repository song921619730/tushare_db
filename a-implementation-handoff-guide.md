# Tushare DB 实施交接指南

> 交接对象：VSCode + Claude Code 插件 + **Qwen 3.6 Plus** 后端
> 目标：把 [a-ai-ai-tushare-pro-kind-gizmo.md](a-ai-ai-tushare-pro-kind-gizmo.md) 翻译成可运行的代码仓库
> 受众：执行该任务的 AI（以下称"你"）

---

## 0. 你是谁、你在哪、你要做什么

- **你**：Claude Code 插件中由 Qwen 3.6 Plus 驱动的 coding agent
- **工作目录**：`F:\AIcoding_space\VsCode\tushare_db\`（Windows 11 + WSL2 + Docker Desktop）
- **任务**：从零搭建一个 Tushare Pro A 股本地数据仓库（ClickHouse），按 7 个 PR 的顺序逐步实现
- **权威设计文档**：[a-ai-ai-tushare-pro-kind-gizmo.md](a-ai-ai-tushare-pro-kind-gizmo.md)（800 行，是单一事实来源，**不可偏离**）
- **前端规格**：[a-frontend-dashboard-spec.md](a-frontend-dashboard-spec.md)（PR7 才用，前期可忽略）

### 关于 Qwen 3.6 Plus 的几点自觉

1. **上下文窗口小于 Claude**：避免一次性 Read 整个 800 行的设计文档，用 `offset+limit` 分段读、用 Grep 找定位
2. **指令遵循强、自主推理弱**：当设计文档已写明"做 X"，照做；不要自己发挥"也许 Y 更好"
3. **中文指令更稳**：内部思考可中文，写 commit message 和代码注释建议英文（生态兼容）
4. **工具调用和 Claude 兼容**：所有 `~/.claude/agents/`、skills、hooks 都正常可用

---

## 1. 开工前的准备清单（**必须全部勾完才动手写代码**）

### 1.1 环境验证

```powershell
# Windows PowerShell 中逐条执行，确认无报错
docker --version                       # Docker Desktop 已装
wsl --status                           # WSL2 已启用
docker compose version                 # compose v2
python --version                       # 3.11+
where uv                               # uv 已装（推荐用 uv 替代 pip/poetry）
```

如果 `uv` 没装：`powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

### 1.2 资源验证

```powershell
# F: 盘剩余空间至少 80 GB
Get-PSDrive F | Select-Object Used, Free
# host 内存至少 16 GB
Get-ComputerInfo | Select-Object TotalPhysicalMemory
# 端口 8123/9000/7800/3000 没被占用
Test-NetConnection -ComputerName localhost -Port 8123  # 应该 False
```

### 1.3 关键凭证

`.env` 文件**先准备好**（参考设计文档 §docker-compose 编排末尾的 `.env.example`）：

```
TUSHARE_TOKEN=<你的 10k 积分 token>
CH_PIPELINE_PASSWORD=<生成 32 位随机串>
CH_AI_READER_PASSWORD=<生成 32 位随机串>
CH_GRAFANA_PASSWORD=<生成 32 位随机串>
```

随机串生成：`python -c "import secrets; print(secrets.token_urlsafe(32))"`

### 1.4 阅读顺序（**第一次工作日的前 30 分钟**）

| 顺序 | 文件 | 怎么读 | 重点 |
|---|---|---|---|
| 1 | `a-ai-ai-tushare-pro-kind-gizmo.md` 第 1-130 行 | 整段读 | 选型、文件系统布局、目录结构、§1-§4 |
| 2 | 同上 第 131-265 行 | 整段读 | §5 sync_state DDL（背下来）、§7 调度、§8 回补五层 |
| 3 | 同上 第 266-410 行 | 整段读 | §9 CLI、§10 访问层 |
| 4 | 同上 第 411-799 行 | 跳读 | 风险、监控、验证、PR 列表、依赖、附录 A |
| 5 | `tushare_rate_limits.md` | 整段读 | 桶分配的权威依据（不要二次猜测） |
| 6 | `tushare_10k_interfaces.md` | 用 Grep 按需读 | 写 YAML 时回查 |
| 7 | `TODO_discussion.md` | 整段读 | 已决议项不要重新讨论 |

读完后**用 TodoWrite 列出 PR1 的所有子任务**，再下笔写第一行代码。

---

## 2. Skills 使用指南（**何时该 invoke 哪个**）

Claude Code 内置 + 用户已装的 skills 中，与本项目相关的，按使用频率排序：

| 频次 | Skill | 触发场景 | 备注 |
|---|---|---|---|
| 高 | `python-patterns` | 写 Python 模块前 | pydantic v2、structlog、tenacity 的最佳实践 |
| 高 | `python-testing` | 写测试前 | pytest、testcontainers、responses |
| 高 | `tdd-workflow` | 每个新模块 | 强制 RED → GREEN → REFACTOR |
| 高 | `clickhouse-io` | 写 schema/sink 前 | DDL 语法、async_insert 设置、性能调优 |
| 中 | `docker-patterns` | 写 docker-compose / Dockerfile 前 | healthcheck、named volume、env 注入 |
| 中 | `mcp-builder` 或 `mcp-server-patterns` | PR5 实施前 | MCP SSE/stdio、tools 注册 |
| 中 | `database-migrations` | schema_evolver 设计 | ADD COLUMN 安全模式 |
| 中 | `eval-harness` | PR6 验证脚本设计 | 离线 eval 模式 |
| 低 | `regex-vs-llm-structured-text` | 解析 Tushare 字段说明 | 仅在样本驱动推断遇阻时 |
| 低 | `gh-cli` | 创建 PR 时 | 用户已装 gh |
| 低 | `verification-loop` / `quality-gate` | 每个 PR 完工前 | 自检清单 |

**调用方式**（Claude Code 中）：直接在用户对话里说"使用 python-testing skill"或在工具调用中按需载入。Qwen 后端处理 skill 加载和 Claude 一致。

**陷阱**：skills 是参考资料不是命令，**读完当作背景知识，不要照搬代码片段**。本项目的设计已经决定了的事（比如 MemoryJobStore），即便 skill 推荐 SQLAlchemyJobStore 也不要改。

---

## 3. Agent 编排策略

`~/.claude/agents/` 中可用的 agent，按本项目使用顺序：

### 3.1 实施前

- **planner**（每个 PR 开工前一次）：把 PR 描述拆成具体的任务列表 + 验收 checklist。Qwen 自主拆解能力较弱时尤其需要。
- **architect**（仅 PR2 开工前）：核对采集引擎的并发模型与文档一致；后续 PR 不需要。

### 3.2 实施中

- **tdd-guide**（**每个新模块**）：先写测试再写实现。本项目要求 80%+ 覆盖率。
- **Explore**（**找代码 / 文档时**）：搜索 Tushare 接口字段定义、ClickHouse 函数语法等。比直接 Grep 更结构化。

### 3.3 实施后

- **python-reviewer**（**每写完一个文件立即调**）：PEP 8、类型注解、async/await、异常处理。**这是硬性流程**，写一个文件审一个。
- **code-reviewer**（PR 提交前一次）：跨文件的架构一致性、模块边界。
- **security-reviewer**（PR1 写 users.xml 后、PR5 写 mcp_server 后）：凭证管理、SQL 注入、CORS 安全。
- **database-reviewer**（PR1 写 DDL 后、PR2 schema_evolver 后）：ClickHouse 特定的索引/分区/TTL 审核。

### 3.4 出问题时

- **build-error-resolver**：`uv run pytest` 或 `docker compose up` 报错时第一个调
- **e2e-runner**（PR3+）：SIGKILL 续跑、补洞、关机补跑这种 e2e 场景
- **refactor-cleaner**（每 2-3 个 PR 完工后）：清理 ts-prune / ruff / dead code

### 3.5 编排原则（**重要**）

- **串行 > 并行**：Qwen 跨 agent 的上下文同步比 Claude 弱，能串就别并发
- **单一目标**：每次 agent 调用解决一个具体问题，不要"同时审代码 + 修 bug + 写测试"
- **写完再审，不要边写边审**：tdd-guide → 写实现 → python-reviewer，三步分开
- **不嵌套**：不要在 agent 内部再起 agent；浅层调用最稳

---

## 4. 工具使用纪律

### 4.1 文件操作

| 场景 | 用 | 不用 |
|---|---|---|
| 找文件 | Glob | `find` / `dir` |
| 找内容 | Grep | `grep` / `findstr` |
| 读文件 | Read（带 `offset+limit`） | `cat` |
| 编辑 | Edit（小改）/ Write（新建） | `sed` / `echo >>` |
| 通信 | 直接输出 | `echo` / `printf` |

### 4.2 Bash 使用

- **一律加 timeout**：`timeout: 60000`（毫秒）。Tushare 调用、Docker 启动这种长任务给 600000
- **后台任务用 `run_in_background: true`**：`docker compose up -d`、`scheduler-run` 这种常驻任务
- **路径用正斜杠**：在 Bash shell 中 `F:/AIcoding_space/...` 而非 `F:\\...`

### 4.3 TodoWrite 节奏

- **每个 PR 开工时**：列出本 PR 全部任务（粒度：每个 task 1-3 小时）
- **每完成一个 task**：立即标 `completed`，不要批量
- **同时只能有 1 个 `in_progress`**

### 4.4 并行调用

Qwen 对并行 tool call 有时会出顺序问题。安全做法：
- **只在完全独立时并行**（如同时 `git status` + `git diff` + `git log`）
- **依赖关系不明的 → 串行**

---

## 5. 7 个 PR 的执行剧本

每个 PR 完工后**必须**：通过其验收 checklist + python-reviewer 审过 + 提交 commit + 更新 `data/logs/progress.md` 记录所遇到的坑。

### PR1 骨架（预计 1 工作日）

**做什么**：
1. `pyproject.toml`（依赖列表抄设计文档 §关键依赖）
2. `docker-compose.yml`（抄 §docker-compose 编排）
3. `docker/clickhouse/{config.xml, users.xml, init/001_create_databases.sql}`
4. 全部 227 个 `config/interfaces/*.yaml`（按附录 A 路由表 + tushare_10k_interfaces.md 填）
5. `src/tushare_db/{config/loader.py, config/models.py, meta/bootstrap.py, cli.py}`
6. `cli init` 实现：仅创建 `_meta.{sync_state, sync_runs, api_calls}` 三张表（DDL 抄 §5.1）+ 空 `tushare` 数据库

**不做什么**：
- ❌ 不创建 182 张业务表（留给 PR2）
- ❌ 不实现 sample_apis / probe / backfill（留给 PR2）

**验收**：
```powershell
docker compose up -d
docker compose exec pipeline tushare-db init
docker compose exec clickhouse clickhouse-client -q "SHOW TABLES FROM _meta"
# 应输出 sync_state / sync_runs / api_calls 三张表
docker compose exec clickhouse clickhouse-client -q "SHOW DATABASES"
# 应包含 tushare 和 _meta，但 tushare 内无表
```

### PR2 采集引擎（预计 3-4 工作日，本项目最重）

**做什么**（顺序很重要）：
1. `core/clock.py`（注入式时钟，便于测试）
2. `core/rate_limiter.py`（双桶 + deque + Lock，**先写并发测试**）
3. `core/tushare_client.py`（httpx http2=True、重试、429 整桶冷却）
4. `scripts/sample_api_responses.py`
5. `schema/{type_map.py, inferer.py, ddl_builder.py, evolver.py}`
6. `sink/clickhouse_sink.py`（async_insert 默认开）
7. `planner/{strategies.py, work_units.py, planner.py}`（六种策略 + scope_key 严格按 §5.2）
8. `runner/{worker.py, executor.py}`（heartbeat 30s 周期）
9. `cli probe / sample-apis / rebuild-schema / bootstrap` 实现
10. `cli bootstrap` 内部按顺序：sample → infer → CREATE 182 张业务表 → seed trade_cal → probe → 写回 YAML `enabled` 字段

**验收**：
```powershell
docker compose exec pipeline tushare-db bootstrap
# 应在 5-10 分钟内跑完，CREATE 出 182 张表
docker compose exec pipeline tushare-db backfill --interface daily --from 20240101 --to 20240110
# 应在 30 秒内完成 7 个交易日的 daily 数据回补
docker compose exec clickhouse clickhouse-client -q "SELECT count() FROM tushare.daily"
# 应返回 ~37000 行（5300 stocks × 7 days）
```

### PR3 回补 + 检查点（预计 2 工作日）

**做什么**：
1. `runner/backfill.py`（支持 `--layer` / `--priority` / `--interface`）
2. `meta/sync_state.py` 完整实现（heartbeat、partial 标记、续跑）
3. `cli backfill / status / resume` 实现
4. SIGKILL 续跑 e2e 测试（用 `subprocess.Popen` + 30 秒后 `os.kill`）

**验收**：
```powershell
docker compose exec pipeline tushare-db backfill --layer 0
# 应在 2 分钟内完成全部参考表
docker compose exec pipeline tushare-db backfill --priority P0 --layer 1
# 应在 4-5 小时内完成 daily/daily_basic/adj_factor 等 6 年数据
docker compose exec pipeline tushare-db status --interface daily --detail
# 应显示 1500 个 done 单元
```

### PR4 调度 + 增量（预计 2 工作日）

**做什么**：
1. `scheduler/jobs.py`（A/B/C/D + saturday + refresh_reference + weekly_reconcile + verify_row_counts）
2. `scheduler/service.py`（APScheduler MemoryJobStore）
3. `runner/incremental.py`
4. `cli update / scheduler-run` 实现

**验收**：手动改本机时间到周五 17:00，scheduler 应自动跑 batch A；改到周六 02:00 应跑长尾。

### PR5 访问层（预计 2 工作日）

**做什么**：
1. `mcp_server/{server.py, tools.py}` 全套工具（设计文档 §10.3）
2. `users.xml` 完整三用户配置
3. `cli mcp-serve` 实现，支持 stdio 和 sse 两种 transport
4. **复权计算在 `tools.py` 内**：`get_ohlcv` 用 `JOIN adj_factor` 实现前/后复权

**验收**：
- 本机 Claude Desktop 连 stdio MCP，调 `get_ohlcv("000001.SZ", "20240101", "20240301", "qfq")` 应返回正确复权数据
- LAN 机器浏览器 fetch `http://<host>:8123/?database=tushare&query=SELECT 1` 应返回 `1`，且响应头含 `Access-Control-Allow-Origin: *`

### PR6 验证与监控（预计 1.5 工作日）

**做什么**：
1. `verify/{row_counts.py, gap_detector.py, checksums.py}`
2. `docker/grafana/{provisioning/, dashboards/{pipeline_health.json, data_coverage.json, clickhouse_io.json}}`
3. `cli verify` 实现

**验收**：浏览器开 `http://<host>:3000`，三个 dashboard 都有数据。

### PR7 前端仪表盘（预计 2-3 工作日）

照抄 [a-frontend-dashboard-spec.md](a-frontend-dashboard-spec.md)。已有 `Tushare_DB_Web/*.jsx` 起点，整理成单文件 SPA。

---

## 6. 高频陷阱与硬性约束（**违反这些 = 返工**）

### 6.1 不准做的事

| ❌ 不要 | ✅ 应该 | 原因 |
|---|---|---|
| 把 ClickHouse 数据 bind mount 到 Windows 目录 | 用 named volume `clickhouse_data` 落 WSL2 ext4 | 性能差 30-50% |
| 用 SQLAlchemyJobStore | MemoryJobStore | 已被 SQLite 锁竞争证明不可行 |
| 给 ai_reader 加 `max_rows_to_read` 等限制 | 仅 `readonly=2` + `host_regexp` IP 白名单 | 用户明确"AI 无限制访问" |
| MCP 工具注入 LIMIT 5000 | 让客户端自己决定 | 同上 |
| 用 cityHash64 做全表幂等指纹 | `SELECT count(), sum(cityHash64(*)) FROM ... FINAL` | ReplacingMergeTree 未 OPTIMIZE 时不稳定 |
| 让 per_symbol_period 单元独立 INSERT 不开 async_insert | `async_insert=1` 默认全开 | 4 接口 × 5300 ts_code × 24 期 = 50 万次单行 INSERT 会崩 |
| 用 `tushare.pro_api()` 默认 requests | `httpx.Client(http2=True)` | HTTP/2 多路复用快 30% |
| 给 MCP 加 OAuth/token 鉴权 | 仅 IP 白名单 | 用户明确"局域网无障碍" |
| 创建 `config/schemas/overrides/` 目录 | 字段覆盖直接写 YAML 内 `schema_overrides` | 设计文档已删该目录 |
| 创建 `data/apscheduler.sqlite` | 不创建任何 jobstore 文件 | MemoryJobStore 决议 |
| backfill 时把 6 年×5300 股×24 期循环并行 | 受 special bucket 285 rpm 上限，并发 6 worker 已是天花板 | 多余的 worker 没用 |

### 6.2 容易写错的小细节

- **CORS header**：必须是 `Access-Control-Allow-Origin: *`（LAN 信任）；如果想严格限定 Origin，用 `<host_regexp>` 在 users.xml 而非 CORS 层
- **Tushare 时间字段**：返回 `String("YYYYMMDD")`，**写入前转成 ClickHouse `Date`**，否则压缩失效
- **ts_code**：必须 `LowCardinality(String)`，否则 5300 个 distinct 值的 GROUP BY 慢 5x
- **trade_cal 冷启动**：`cli init` 后 `tushare` 库还没 trade_cal 表，所以 PR1 阶段任何 job 都不能调度。必须先跑 `cli bootstrap`（PR2）才能启动 scheduler
- **付费 45 接口**：YAML 写但 `enabled:false`，**bootstrap 时跳过 sample/CREATE**；将来用户开通后改 enabled 重跑 bootstrap
- **结构化日志**：用 structlog 不要 print。每条日志必带 `run_id, interface, scope_key, params_hash`

### 6.3 性能基线（达不到 = 你写错了）

| 操作 | 期望耗时 | 不达标的可能原因 |
|---|---|---|
| 6 个月 `daily` 回补 | ≤24 min | rate_limiter 利用率不到 95%；HTTP/2 没开 |
| `update --batch A` 单日增量 | ≤30 sec | async_insert 没开；用了 HTTP 8123 而非 Native 9000 |
| ClickHouse `SELECT count() FROM tushare.daily` | <100 ms | 没建分区；分区键不是 `toYYYYMM(trade_date)` |
| MCP `get_ohlcv` 单股 1 年 | <500 ms | adj_factor JOIN 没用 ASOF JOIN；返回格式不是 Arrow IPC |

---

## 7. 测试纪律

### 7.1 测试金字塔

| 层 | 占比 | 工具 | 例 |
|---|---|---|---|
| 单元 | 60% | pytest + 假时钟 | rate_limiter、planner、type_map |
| 集成 | 30% | testcontainers[clickhouse] + responses | sink、bootstrap、backfill |
| E2E | 10% | 直接 docker compose + 真 Tushare token | 整 PR 验收脚本 |

### 7.2 必写的关键测试（**否则 PR 不能合**）

- `test_rate_limiter_concurrent.py`：10 worker 同步抢 token，断言 1 分钟内总 calls ≤ 桶上限
- `test_planner_scope_key.py`：六种策略每种至少一个用例，验证 scope_key 格式
- `test_sync_state_heartbeat.py`：模拟 worker 30s 不写心跳，启动后被标 partial
- `test_idempotent_replay.py`：连跑 daily 三个月两遍，第二遍 rows=0、指纹一致
- `test_sigkill_resume.py`（PR3）：subprocess + SIGKILL + 重启对比

---

## 8. 提交、PR、文档维护

### 8.1 Commit 格式

```
<type>(<scope>): <description>

<body>
```

`type`：feat / fix / refactor / docs / test / chore / perf / ci
`scope`：rate_limiter / sink / scheduler / mcp / ...

例：
```
feat(rate_limiter): add http2 client with 95% bucket utilization

- httpx.Client(http2=True, timeout=10s)
- bucket capacity raised from 90% to 95%
- normal worker 8→12, special 4→6
```

### 8.2 PR 标题

`<type>: <PR 编号> <简述>`，例 `feat: PR2 ingestion engine with rate limiter and schema inference`

### 8.3 进度记录

每天工作结束前，**追加**到 `data/logs/progress.md`（不是覆盖）：

```markdown
## 2026-04-26 PR1 day 1
- ✅ docker-compose 跑通，3 服务启动健康
- ✅ 写完 22 个 reference YAML
- 🚧 开始写 stock_daily.yaml (60+ 接口)
- ⚠️ 坑：clickhouse 24.8 image 在 WSL2 启动慢，加了 healthcheck retries=10
```

---

## 9. 紧急情况处置

| 症状 | 排查路径 |
|---|---|
| Tushare 一直 429 | 检查 `_meta.api_calls` p99 频次；可能桶利用率算错（应 95% = 475/min） |
| ClickHouse OOM 崩溃 | `system.parts` 看 part 数；如 >10000 说明 async_insert 没开 |
| docker compose up 卡住 | 确认 healthcheck 通过；用 `docker compose logs clickhouse` 看启动日志 |
| 容器拿不到 .env 变量 | docker-compose 必须用 `${VAR}` 语法 + `.env` 文件同目录 |
| MemoryJobStore job 重启丢失 | 这是预期行为，job 在代码里可重建；用户已接受 |
| WSL2 占内存太多 | `%USERPROFILE%/.wslconfig` 加 `[wsl2]\nmemory=12GB` |
| Tushare token 失效 | 换 `.env` → `docker compose restart pipeline`；scheduler 自动恢复 |

---

## 10. 不要做的事（**最后一次强调**）

- ❌ 不要"优化"已决策项（MemoryJobStore、ai_reader 无限制、95% 桶利用率）
- ❌ 不要在 PR1 创建 230 张占位表
- ❌ 不要给 MCP 加 OAuth/JWT/token
- ❌ 不要把 ClickHouse 数据放 Windows 挂载
- ❌ 不要从 cityHash64 全表哈希做幂等校验
- ❌ 不要尝试迁移已删除的 AKshare 老脚本
- ❌ 不要为付费 45 接口在 bootstrap 时建表
- ❌ 不要在 cli init 中调用 Tushare API（init 必须 offline）
- ❌ 不要跳过测试直接合 PR
- ❌ 不要并发跑 backfill 和 update（资源竞争）

---

## 11. 当你不确定时

1. 第一选择：**重读 [a-ai-ai-tushare-pro-kind-gizmo.md](a-ai-ai-tushare-pro-kind-gizmo.md) 的相关章节**
2. 第二选择：**读 `tushare_rate_limits.md` / `tushare_10k_interfaces.md`** 等参考文档
3. 第三选择：**调用 `Explore` agent** 在已有代码中查找前置实现
4. 最后才：**问用户**（用 AskUserQuestion）

不要：
- 自己发挥设计
- 搜索互联网（除非用 docs-lookup agent 查官方文档）
- 用 `pip install` 装计划外的库

---

## 12. 工作日开始检查清单

每次 VSCode 打开本项目，**先做**：

```powershell
# 1. 拉最新（如果用 git）
git status && git pull

# 2. 看上次的进度
type data\logs\progress.md | Select-Object -Last 30

# 3. 验证容器状态
docker compose ps

# 4. 看一眼 sync_state 健康度
docker compose exec clickhouse clickhouse-client -q "SELECT status, count() FROM _meta.sync_state FINAL GROUP BY status"

# 5. TodoWrite 列出今天的任务
```

---

## 13. 收尾标志

整个项目完成的判定：

- ✅ 7 个 PR 全部合并
- ✅ 全量 P0+P1 历史回补成功（≤18h）
- ✅ Saturday 长尾 4 接口跑完（≤32h）
- ✅ 连续 5 个交易日 A/B/C/D 自动增量无人工干预
- ✅ 本机 Claude + 1 台 LAN 机器都能通过 ai_reader 查数
- ✅ 三个 Grafana dashboard 都有数据
- ✅ 单元测试覆盖率 ≥80%
- ✅ python-reviewer 在所有文件上无 CRITICAL / HIGH 告警

完成后写一份 `RUNBOOK.md` 给用户日常运维参考（如何重启、如何换 token、如何查日志）。

---

## 附：Qwen 3.6 Plus 特有提醒

- 你的 system prompt 里可能没有 Claude Code 默认的 `~/.claude/rules/common/*.md`，**主动 Read 一下**这些规则文件以补齐：
  - `~/.claude/rules/common/coding-style.md`
  - `~/.claude/rules/common/testing.md`
  - `~/.claude/rules/common/git-workflow.md`
  - `~/.claude/rules/common/security.md`
- 如果某个工具调用返回值的格式与你预期不同（如 Bash 输出乱码），**优先怀疑编码问题**：Windows PowerShell 默认 GBK，加 `chcp 65001` 切 UTF-8
- 中文输出乱码：`$OutputEncoding = [System.Text.UTF8Encoding]::new()`
- 长任务（如 backfill --all）**必须 `run_in_background: true`**，否则 Claude Code 会超时

---

**最后**：这份指南是给 AI 看的，但用户也会看。所以**所有动作都要有可观测性**：每一步说一句话，每一个错误说清楚原因和修法。用户开 VSCode 看到一片绿勾时，就是项目交付时。
