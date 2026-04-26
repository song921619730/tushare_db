# Tushare DB — 最后一公里：从"代码完成"到"可长期运行"

> 面向：VSCode + Claude Code + Qwen 3.6 Plus（执行者）
> 文档作者：Sonnet 4.6（审计者）
> 生成日期：2026-04-26（第三轮）
> 基线：`project_status_2026-04-26.md` 报告"16/16 完成、覆盖率 64%"
>
> **核心发现**：代码层确实 99% 完成，但**项目尚不能长期运行**。差距不在代码，而在 4 件事：
>   1. **数据未回填**（最大瓶颈：169 enabled，仅 10 张表有数据）
>   2. **长跑稳定性从未实测**（scheduler 没跑过完整一周）
>   3. **CI 写好了但没真跑过**（22 个集成测试只在代码里）
>   4. **设计承诺与实际状态不一致**（设计 182 vs 实际 169，DoD 4 项未达成）
>
> 本文档列出 14 个待办（**R1-R14**），分 4 个阶段执行。

---

## 0. 全景：14 项待办

| ID | 阶段 | 严重度 | 类别 | 一句话 |
|----|------|--------|------|--------|
| **R1** | 阶段一 | 🔴 P0 | 数据回填 | adj_factor 全量到今日（4.67M → 8M+ 行） |
| **R2** | 阶段一 | 🔴 P0 | 数据回填 | stock_daily + daily_basic 全量 6 年（27K → 8M+ 行） |
| **R3** | 阶段一 | 🔴 P0 | 数据回填 | moneyflow + moneyflow_hsgt 全量 6 年 |
| **R4** | 阶段一 | 🟡 P1 | 数据回填 | 财务 5 表扩量（20 stocks → 全市场，8 季度 → 24 季度） |
| **R5** | 阶段一 | 🟡 P1 | 数据回填 | per_symbol_period 长尾 4 接口首跑（设计 §7 周六批次） |
| **R6** | 阶段二 | 🔴 P0 | 长跑验证 | 连续 5 交易日 scheduler 自动增量无人工干预 |
| **R7** | 阶段二 | 🟡 P1 | 长跑验证 | weekly_reconcile + verify_row_counts 实跑 |
| **R8** | 阶段二 | 🟡 P1 | 长跑验证 | get_ohlcv 真数据下 qfq/hfq 数学正确性验证 |
| **R9** | 阶段二 | 🟢 P2 | 长跑验证 | API 配额监控（_meta.api_calls 实时告警） |
| **R10** | 阶段三 | 🟡 P1 | CI/CD | GitHub Actions 真跑通（unit + integration） |
| **R11** | 阶段三 | 🟡 P1 | CI/CD | 10 个 empty_sample 接口排查与复活 |
| **R12** | 阶段三 | 🟢 P2 | 文档同步 | 把"169 enabled"现状回写设计文档 §11 |
| **R13** | 阶段四 | 🟢 P2 | 灾难演练 | Tushare token 失效场景测试 |
| **R14** | 阶段四 | 🟢 P2 | 灾难演练 | clickhouse_data 卷损坏全量重跑（设计要求） |

---

## 1. 与原始设计/交接指南的对账（21 项 DoD 逐条核对）

### 1.1 设计文档 (`a-ai-ai-tushare-pro-kind-gizmo.md`)

| § | 承诺 | 当前状态 | 差距 |
|---|------|----------|------|
| §3 | 双桶 475/285 rpm，95% 利用率 | ✅ 代码到位 | ⚠️ **未在真负载下验证** |
| §3 | normal 12 worker / special 6 worker | ✅ thread-local 修复后到位 | ⚠️ 未实测吞吐量基线 |
| §4 | 万元→元归一化 | ✅ B1 修复，茅台营收 1505.6 亿验证通过 | ✅ |
| §4 | async_insert + Native protocol | ⚠️ async_insert OK；HTTP 替代 Native（已知偏差） | 接受 |
| §5.1 | sync_state 三表 DDL + 心跳 30s | ✅ | ✅ |
| §5.4 | 稳定指纹（`sum(cityHash64(*)) FINAL`） | ✅ B17/checksums.py | ✅ |
| §7 | A/B/C/D 四批次 + 周六长尾 + refresh_reference + weekly_reconcile + verify_row_counts | ✅ scheduler/jobs.py 8 jobs 注册 | ⚠️ **从未真触发过完整一周** |
| §8 | 五层回补，P0+P1 单次 12-18h，全量 48-60h | ❌ **从未跑过完整 P0+P1 回补** | **R1-R5** |
| §9 | CLI 命令完整 | ✅ | ✅ |
| §10 | LAN 信任 + ai_reader + IP 白名单 | ✅ N1 + readonly=2 + host_regexp | ✅ |
| §10.3 | MCP 工具 9 个，复权在工具内 | ✅ B4 修复后正确 | ⚠️ **R8 在真数据下未验证** |
| §10.3 | LZ4 + Arrow IPC 压缩 | ✅ B9/encode_response | ⚠️ MCP 客户端未实测解码 |
| §11 | 表数 = 185 (182 enabled + 3 元表) | ❌ **实际 169 enabled → R11 后 174** | **R11/R12 ✅** |
| §11 | 行数 150-250M | ❌ **当前约 5M 行**（不到 5%） | **R1-R5** |
| §11 | 增量稳态每日 ≤30 min | ❌ **未在真数据下验证** | **R6** |
| §风险 | Token 失效自动暂停 + 5 次 401/403 | ⚠️ B12/B16 错误码分类已做 | ⚠️ **R13 未实测告警链路** |
| §风险 | 硬盘 < 20GB 自动暂停新 backfill | ⚠️ scheduler 预检 trade_cal 已加，但**磁盘检查未实现** | **新增 R15** |
| §验证 | 9 项验证计划 | ⚠️ 1, 2, 4 部分；**3, 5, 6, 7, 8, 9 未跑** | **R6-R8** |

### 1.2 交接指南 (`a-implementation-handoff-guide.md`) §13 收尾标志

| 项 | 状态 |
|----|------|
| 7 个 PR 全部合并 | ✅（虽然只 1 commit，但代码全在） |
| 全量 P0+P1 历史回补成功（≤18h） | ❌ **未执行** |
| Saturday 长尾 4 接口跑完（≤32h） | ❌ **未执行** |
| 连续 5 个交易日 A/B/C/D 自动增量无人工干预 | ❌ **未执行** |
| 本机 Claude + 1 台 LAN 机器都能通过 ai_reader 查数 | ⚠️ 本机 OK，LAN 未实测 |
| 三个 Grafana dashboard 都有数据 | ⚠️ 数据少，Panel 大半空白 |
| 单元测试覆盖率 ≥80% | ⚠️ 64%（已超 60% 目标，但低于设计 80%） |
| python-reviewer 在所有文件上无 CRITICAL / HIGH 告警 | ⚠️ 第二轮未跑 |
| `RUNBOOK.md` | ✅ 已写 |

**收尾标志 9 项中：3 项 ✅、4 项 ⚠️、2 项 ❌。**

---

## 2. 阶段一：数据回填（最大瓶颈，3-4 天）

### R1. adj_factor 全量到今日（**最高优先级**）

**目标**：从 4.67M 行（截至 2024-01-31）扩到 8M+ 行（覆盖到 2026-04-26）。

**为什么最高优**：
- adj_factor 缺失 → `get_ohlcv` qfq/hfq 全坏（基准日数据缺）
- 设计文档 §10.3 明文要求"复权在 MCP 工具内计算"
- 之所以 R1 不是 R2 是因为 adj_factor 数据量大但单表小（5MB），完成快

**执行**：
```bash
# 在容器内
docker compose exec pipeline-scheduler tushare-db backfill \
  --interface adj_factor \
  --from 20240201 \
  --to 20260426

# 预计耗时：~30 分钟（normal bucket，475 rpm × 12 worker）
# 预计行数增量：~3.5M 行
```

**验收**：
```sql
SELECT min(trade_date), max(trade_date), count(), uniqExact(ts_code)
FROM tushare.tushare_adj_factor FINAL;
-- 期望：min=2020-01-02, max=2026-04-26（或最近交易日），count > 8M, uniqExact > 5400
```

**潜在坑**：
- 如果 `_meta.sync_state` 已记录 2020-2024 的单元为 `done`，planner 会跳过 → 必须用 `--from 20240201` 不重叠
- 验证后顺手刷一遍 2020-2024 范围，确保无 `partial`/`failed`：
  ```bash
  tushare-db status --interface adj_factor --detail | grep -v "done"
  ```

---

### R2. stock_daily + daily_basic 全量 6 年（**容量最大**）

**目标**：daily 27K → 8M+ 行，daily_basic 117K → 8M+ 行。

**执行**：
```bash
# stock_daily（normal bucket）
docker compose exec pipeline-scheduler tushare-db backfill \
  --interface daily \
  --from 20200101 \
  --to 20260426

# daily_basic（special bucket，慢一倍）
docker compose exec pipeline-scheduler tushare-db backfill \
  --interface daily_basic \
  --from 20200101 \
  --to 20260426
```

**预计耗时**：
- daily：~6 小时（设计 §3 估算 normal 桶 4.5h，多接口并行）
- daily_basic：~12 小时（special 桶 285 rpm）

**期间监控**：
```bash
# 每 30 分钟看一次进度
docker compose exec pipeline-scheduler tushare-db status --interface daily
docker compose exec pipeline-scheduler tushare-db status --interface daily_basic

# 看 API 桶是否打满 95%
docker compose exec clickhouse clickhouse-client --query \
  "SELECT count()/60 AS rps, count() AS calls
   FROM _meta.api_calls
   WHERE started_at > now() - INTERVAL 1 MINUTE"
# 期望：normal bucket rps ≈ 7.9（475/60），special ≈ 4.75
# 实测如果 < 50% 说明 worker 数不够或 HTTP/2 没生效
```

**验收**：
```sql
-- daily 应该 ≥ 8M 行（5500 stocks × 1500 trade_dates ≈ 8.25M）
SELECT count(), uniqExact(ts_code), uniqExact(trade_date)
FROM tushare.tushare_stock_daily FINAL;
-- 期望 count > 8M, uniqExact(ts_code) > 5400, uniqExact(trade_date) > 1500

-- 数据完整性（无空缺日）
SELECT trade_date, count() AS daily_rows
FROM tushare.tushare_stock_daily FINAL
WHERE trade_date BETWEEN '20200101' AND '20260426'
GROUP BY trade_date
HAVING daily_rows < 5000  -- 健康日应该 ≥ 5000 只股票
ORDER BY trade_date;
-- 期望：返回行数为 0（或仅停牌特殊日）
```

---

### R3. moneyflow + moneyflow_hsgt 全量 6 年

**执行**：
```bash
docker compose exec pipeline-scheduler tushare-db backfill \
  --interface moneyflow --from 20200101 --to 20260426

docker compose exec pipeline-scheduler tushare-db backfill \
  --interface moneyflow_hsgt --from 20200101 --to 20260426
```

**注意**：moneyflow 是 `offset_paging` 策略（设计 §2），单日多页，与 daily 的 `date_loop` 不同；planner 应自动识别。

**验收**：
```sql
SELECT count(), uniqExact(ts_code) FROM tushare.tushare_moneyflow FINAL;
-- 期望 ≥ 6M 行
```

---

### R4. 财务 5 表扩量（设计 §7 batch D 完整执行）

**目标**：从"20 stocks × 8 quarters"扩到"全市场 × 24 季度（2020Q1-2025Q4）"。

**当前限制**：`scripts/backfill_financials.py` 中应该有 `MAX_STOCKS = 20` 之类的样本限制。

**执行**：
```bash
# 1. 修改 scripts/backfill_financials.py
#    把 MAX_STOCKS = 20 改为 MAX_STOCKS = None（或删除该限制）

# 2. 跑全量
docker compose exec pipeline-scheduler python scripts/backfill_financials.py

# 或用 CLI 的 period_loop 策略（推荐，可断点续传）
docker compose exec pipeline-scheduler tushare-db backfill \
  --interface income       --from 20200101 --to 20251231
docker compose exec pipeline-scheduler tushare-db backfill \
  --interface balancesheet --from 20200101 --to 20251231
docker compose exec pipeline-scheduler tushare-db backfill \
  --interface cashflow     --from 20200101 --to 20251231
docker compose exec pipeline-scheduler tushare-db backfill \
  --interface fina_indicator --from 20200101 --to 20251231
docker compose exec pipeline-scheduler tushare-db backfill \
  --interface dividend     --from 20200101 --to 20251231
```

**预计耗时**：每个接口 24 个 period × 1 call = 24 calls，单接口 < 10s（special bucket）。**5 个接口总计 ~1 分钟。**

**验收**：
```sql
SELECT 'income' AS tbl, count(), uniqExact(ts_code), uniqExact(end_date)
FROM tushare.tushare_income FINAL
UNION ALL SELECT 'balancesheet', count(), uniqExact(ts_code), uniqExact(end_date)
FROM tushare.tushare_balancesheet FINAL
UNION ALL SELECT 'cashflow', count(), uniqExact(ts_code), uniqExact(end_date)
FROM tushare.tushare_cashflow FINAL
UNION ALL SELECT 'fina_indicator', count(), uniqExact(ts_code), uniqExact(end_date)
FROM tushare.tushare_fina_indicator FINAL
UNION ALL SELECT 'dividend', count(), uniqExact(ts_code), uniqExact(end_date)
FROM tushare.tushare_dividend FINAL;

-- 期望（每行）：
--   count > 100K
--   uniqExact(ts_code) > 5400
--   uniqExact(end_date) ≥ 24
```

**潜在坑**：
- `dividend` 当前 575 行 19 stocks 57 quarters，比其他财务表多——可能策略不一样（事件驱动而非季报）。检查 YAML 配置确认 strategy
- `period_loop` 假设 period 即可拿全市场；如果接口实际需要 ts_code+period，会单股票循环慢 5500x

---

### R5. per_symbol_period 长尾 4 接口（设计 §7 周六批次）

**目标**：fina_mainbz / top10_holders / top10_floatholders / stk_holdertrade 全部跑完一次。

**预计耗时**：设计 §7 算的"~7.85h/接口 × 4 ≈ 31h"。**必须用 `run_in_background` 启动，不要让 Bash 工具超时。**

**执行**：
```bash
# 周六凌晨可手动触发（或等 scheduler 自动 02:00）
# 这里直接手动跑（更可控）

# 因为是 31h 总时长，分 4 次起，每个用 detach
docker compose exec -d pipeline-scheduler tushare-db backfill \
  --interface fina_mainbz --from 20200101 --to 20251231
# 等 ~8h 后跑下一个
docker compose exec -d pipeline-scheduler tushare-db backfill \
  --interface top10_holders --from 20200101 --to 20251231
# 等 ~8h 后
docker compose exec -d pipeline-scheduler tushare-db backfill \
  --interface top10_floatholders --from 20200101 --to 20251231
# 等 ~8h 后
docker compose exec -d pipeline-scheduler tushare-db backfill \
  --interface stk_holdertrade --from 20200101 --to 20251231
```

**注意 fina_mainbz 当前在 coverage_audit.md 中标记为 `empty_sample`**——需要在 R11 解决采样参数后才能跑。

**验收**：
```sql
SELECT 'fina_mainbz' AS tbl, count(), uniqExact(ts_code), uniqExact(end_date)
FROM tushare.tushare_fina_mainbz FINAL
UNION ALL SELECT 'top10_holders', count(), uniqExact(ts_code), uniqExact(end_date)
FROM tushare.tushare_top10_holders FINAL
UNION ALL SELECT 'top10_floatholders', count(), uniqExact(ts_code), uniqExact(end_date)
FROM tushare.tushare_top10_floatholders FINAL
UNION ALL SELECT 'stk_holdertrade', count(), uniqExact(ts_code), uniqExact(end_date)
FROM tushare.tushare_stk_holdertrade FINAL;

-- 每张应该 > 1M 行
```

---

## 3. 阶段二：长跑稳定性验证（5-7 天）

### R6. 连续 5 交易日 scheduler 自动增量（**收尾标志硬指标**）

**目标**：交接指南 §13 明文要求 → 必须达成。

**执行**：
```bash
# Day 0：把所有 P0/P1 表 backfill 到昨日
# Day 1-5（工作日）：什么都不做，只观察

# 每天检查（每个工作日 20:00 跑一次）
docker compose exec clickhouse clickhouse-client --query "
  SELECT batch, status, count()
  FROM _meta.sync_runs
  WHERE started_at > today() - INTERVAL 1 DAY
  GROUP BY batch, status
  ORDER BY batch
"

# 期望 5 天后看到（每天）：
#   A done
#   B done
#   C done
#   D done
#   refresh_reference done
#   verify_row_counts done
# 没有 partial / failed
```

**验收清单**（每天检查）：
- [ ] 17:00 batch A 完成（行情类）
- [ ] 18:00 batch B 完成（资金流）
- [ ] 19:00 batch C 完成（特色板块）
- [ ] 19:45 batch D 完成（财务/宏观）
- [ ] 06:00 refresh_reference 完成
- [ ] 03:00 verify_row_counts 完成
- [ ] T-1 数据 vs Tushare 网页抽样对比 5 只股票收盘价 → 误差 ≤ 1 分钱

**失败处理**：
- 某天发现 partial → `tushare-db resume` 续跑
- 某天发现 failed → 记录错误进 `data/logs/progress.md`，**不要立即修代码**，先看是否是 Tushare 服务侧的偶发

---

### R7. weekly_reconcile + verify_row_counts 实跑

**目标**：两个 job 在第一个真实周末（周日 02:00）和每天 03:00 真触发。

**预触发测试**：
```bash
# 手动触发 weekly_reconcile（不等周日）
docker compose exec pipeline-scheduler python -c "
from tushare_db.scheduler.jobs import weekly_reconcile
weekly_reconcile()
"

# 手动触发 verify_row_counts
docker compose exec pipeline-scheduler tushare-db verify --priority P0 --gaps --checksums
```

**验收**：
- weekly_reconcile：检查 `_meta.sync_runs` 中是否有 `interface=*reconcile*` 的运行记录，且无 failed
- verify_row_counts：日志中应有"OK: N, Issues: 0"

---

### R8. get_ohlcv 真数据下 qfq/hfq 数学正确性

**目标**：数据回填完成后，回归测试 `tools.py:get_ohlcv` 的复权公式。

**执行**：
```bash
# 通过 MCP 调用（或直接 ClickHouse 验证）
curl -X POST http://localhost:7800/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "method":"tools/call",
    "params":{"name":"get_ohlcv","arguments":{
      "ts_code":"600519.SH",
      "start_date":"20100101",
      "end_date":"20250101",
      "adjust":"qfq"
    }},
    "id":1
  }' | jq '.result' | head -50
```

**验收 4 项**：
1. **行数**：2010-2024 茅台应该有 ~3500 个交易日
2. **qfq 起点价**：2010 年的 close 应该 < 100（除权后回视）
3. **qfq 终点价**：最新 close 应该接近 Tushare 网页查询的真值（误差 < 1%）
4. **hfq 起点价**：等于原始价；终点价 >> 原始价（无除权日累积）

**Bug 触发器**：如果 qfq 起点价 > 1000 → 公式仍错（可能 R1 没修干净）。

---

### R9. API 配额监控（避免触发 429 / 封号）

**目标**：把 `_meta.api_calls` 的实时频次接入 Grafana，超 90% 桶时告警。

**执行**：

新建 Grafana panel（或在现有 `pipeline_health.json` 加一个）：
```sql
-- 滑动 1 分钟内的 API call 数量，按 bucket 分组
SELECT
    toStartOfMinute(started_at) AS minute,
    countIf(interface IN (
      SELECT name FROM file('/app/config/normal_interfaces.txt', 'TSV', 'name String')
    )) AS normal_rpm,
    countIf(interface IN (
      SELECT name FROM file('/app/config/special_interfaces.txt', 'TSV', 'name String')
    )) AS special_rpm
FROM _meta.api_calls
WHERE started_at > now() - INTERVAL 1 HOUR
GROUP BY minute
ORDER BY minute
```

或更简单的（用接口名前缀近似）：
```sql
SELECT
    toStartOfMinute(started_at) AS minute,
    count() AS total_rpm,
    countIf(status = 429) AS rate_limited
FROM _meta.api_calls
WHERE started_at > now() - INTERVAL 1 HOUR
GROUP BY minute
```

**告警规则**：
- `total_rpm > 760`（normal 475 + special 285 = 760，超即异常）
- `rate_limited > 0` 持续 5 分钟

---

## 4. 阶段三：CI/CD + 接口复活（2-3 天）

### R10. GitHub Actions 真跑通

**目标**：`.github/workflows/test.yml` 已写好，但**仅 1 个 git commit**意味着 CI 从未执行过。

**执行**：

1. **建仓 + 推送**：
   ```bash
   cd F:/AIcoding_space/VsCode/tushare_db
   gh repo create tushare-db --private --source=. --remote=origin --push
   # 推送后 GitHub Actions 自动触发
   ```

2. **观察首次跑**：
   ```bash
   gh run watch
   ```

3. **Unit 测试 PASS 是基线，Integration 测试可能失败的点**：
   - `astral-sh/setup-uv@v5` 版本是否存在
   - `uv sync --frozen`：要求有 `uv.lock` —— **如果没有，先 `uv lock` 生成并 commit**
   - testcontainers 起 ClickHouse 镜像：CI runner 默认有 Docker
   - codecov upload：`CODECOV_TOKEN` secret 没设也不阻塞（`fail_ci_if_error: false`）

4. **集成测试覆盖率应该把总数从 64% 提到 75%+**（CLI/MCP/verify 模块在集成测试中能跑到）。

**验收**：
- [ ] GitHub Actions 首次执行全绿
- [ ] codecov 报告显示覆盖率
- [ ] CI 时长 < 10 分钟（unit）+ < 20 分钟（integration）

---

### R11. 10 个 empty_sample 接口排查

**清单**（来自 `coverage_audit.md`）：dc_hot, fina_mainbz, index_monthly, moneyflow_cnt_ths, moneyflow_ind_ths, moneyflow_ths, stk_auction（共 7 个有效）+ bc_bestotcqt/bc_otcqt/tdx_daily（这 3 个还是付费）。

**逐个排查方法**：
```python
# 用 Python 直连 Tushare 测每个接口的最小可用参数
import tushare as ts
pro = ts.pro_api(token='你的 token')

# 1. dc_hot — 试 trade_date
df = pro.dc_hot(trade_date='20240315')
# 如果有数据 → 修改 cli.py:_sample_one_interface 增加分支

# 2. fina_mainbz — 试 ts_code + period
df = pro.fina_mainbz(ts_code='600519.SH', period='20231231')
# 应该有数据

# 3. index_monthly — 试 ts_code
df = pro.index_monthly(ts_code='000001.SH', start_date='20240101', end_date='20240131')

# 4-6. moneyflow_*_ths — 试 trade_date
df = pro.moneyflow_ths(trade_date='20240315')

# 7. stk_auction — 试 ts_code + start_date
df = pro.stk_auction(ts_code='000001.SZ', start_date='20240101', end_date='20240131')
```

**修复**：
1. 在 `src/tushare_db/cli.py:_sample_one_interface` 增加特殊分支
2. 在对应 YAML 文件中改 `enabled: true` 并删除 `disabled_reason`
3. 重跑 `tushare-db sample-apis --only <name>`
4. 重跑 `tushare-db rebuild-schema --interface <name>`

**预期复活**：7/10（3 个付费的不动）。完成后 enabled = 169 + 5 = **174**（stk_auction/tdx_daily 保持禁用），与设计 182 仍差 8（3 下线 + 2 付费 + 3 其他，可接受）。

**状态**：✅ 5 个已复活（dc_hot, index_monthly, moneyflow_ths, moneyflow_ind_ths, moneyflow_cnt_ths, fina_mainbz）。

---

### R12. 文档同步：把"169 enabled"现状回写

**问题**：
- 设计文档 §11 写的是"185 = 182 enabled + 3 元表"
- 实际是 169 enabled
- coverage_audit.md 已经记录了原因，但**设计文档本身没更新**

**修复**：

在 `a-ai-ai-tushare-pro-kind-gizmo.md` §11 加一段：
```markdown
> **2026-04-26 更新**：实际 enabled 数量为 169（R11 完成后为 174）。
> 13 个偏差来源：
> - 3 个 Tushare 已下线（film_record / tmt_twincome / tmt_twincomedetail）
> - 7 个需特殊采样参数（详见 `data/logs/coverage_audit.md`）
>   - 5 个已复活（dc_hot, index_monthly, moneyflow_ths, moneyflow_ind_ths, moneyflow_cnt_ths, fina_mainbz）
>   - 2 个保留禁用（stk_auction 付费, tdx_daily 待验证）
> - 3 个付费接口（升级积分后可启用）
>
> 表数 = 172（169 enabled + 3 元表）= 暂时基线；R11 完成后为 177。
```

**状态**：✅ 已完成。设计文档 §11 已更新。

---

## 5. 阶段四：灾难演练 + 长尾运维（2 天）

### R13. Tushare token 失效场景

**设计 §风险**：连续 5 次 401/403 → scheduler 自动暂停所有非 reference job。

**测试**：
```bash
# 1. 备份原 token
cp .env .env.bak

# 2. 改成假 token
sed -i 's/TUSHARE_TOKEN=.*/TUSHARE_TOKEN=fake_invalid_token/' .env

# 3. 重启 scheduler
docker compose restart pipeline-scheduler

# 4. 手动触发一个 batch
docker compose exec pipeline-scheduler tushare-db update --batch A

# 5. 等 1 分钟后检查
docker compose exec clickhouse clickhouse-client --query "
  SELECT interface, status, last_error, count()
  FROM _meta.sync_state FINAL
  WHERE last_error LIKE '%401%' OR last_error LIKE '%403%'
  GROUP BY interface, status, last_error
  LIMIT 10
"

# 期望：看到 5 次 401 后 scheduler 应自动 pause
docker compose logs pipeline-scheduler | grep -i "token.*invalid\|paused\|disabled"

# 6. 恢复原 token
mv .env.bak .env
docker compose restart pipeline-scheduler
```

**如果 scheduler 没自动暂停**：补一段 `scheduler/service.py` 监听 `TushareAuthError` 计数，超 5 次调 `scheduler.pause()`。

---

### R14. clickhouse_data 卷损坏全量重跑（设计要求）

**设计 §风险**：数据卷损坏 → 接受重跑（用户已确认）。

**测试**（建议在低峰期，且数据已备份过）：
```bash
# 1. 备份当前数据
docker compose exec pipeline-scheduler bash scripts/backup_clickhouse.sh

# 2. 模拟卷损坏
docker compose down
docker volume rm tushare_db_clickhouse_data

# 3. 全量重启
docker compose up -d clickhouse
sleep 30  # 等 healthy
docker compose up -d  # 启动 pipeline + grafana + dashboard

# 4. 重新初始化 + bootstrap
docker compose exec pipeline-scheduler tushare-db init
docker compose exec pipeline-scheduler tushare-db bootstrap

# 5. 从备份恢复
docker compose exec pipeline-scheduler bash scripts/restore_clickhouse.sh /backup/latest.sql

# 6. 验证
docker compose exec clickhouse clickhouse-client --query "
  SELECT count() FROM system.tables WHERE database = 'tushare'
"
# 期望：≥ 169

docker compose exec clickhouse clickhouse-client --query "
  SELECT count() FROM tushare.tushare_stock_daily FINAL
"
# 期望：与备份前一致
```

**验收时长**：< 1 小时（备份恢复路径）；如果走全量 backfill 路径 < 60 小时（设计承诺）。

---

## 6. 给 Qwen 的执行节奏

### 6.1 时间表（10 个工作日）

| Day | 任务 | 监督方式 |
|-----|------|---------|
| 1 | R1 (adj_factor) + R4 (财务扩量，period_loop 部分） | 跑完后看行数 |
| 2-3 | R2 (daily + daily_basic 全量 6 年) | `run_in_background`，每 4h 看一次进度 |
| 4 | R3 (moneyflow + hsgt) + R11 (empty_sample 排查) | |
| 5 | R5 启动（per_symbol_period 4 接口，背景跑 ~36h） | 启动后挂着 |
| 6-7 | R5 继续 + R10 (CI 跑通) + R12 (文档同步) | |
| 8 | R5 收尾 + R8 (get_ohlcv 真数据验证) + R9 (配额监控) | |
| 9 | R6 启动（连续 5 交易日观察）— 第 1 天观察 | scheduler 自动跑 |
| 10 | R7 (weekly_reconcile) + R13 (token 失效) + R14 (灾难演练) | |
| ~14 | R6 收尾（5 交易日观察完毕） | 报告 |

### 6.2 每日操作流程（Qwen 必读）

每天**开机**：
```bash
# 1. 看昨日进度
type data\logs\progress.md | Select-Object -Last 30

# 2. 检查容器
docker compose ps

# 3. 检查 sync_state 健康度
docker compose exec clickhouse clickhouse-client --query "
  SELECT status, count() FROM _meta.sync_state FINAL GROUP BY status
"
# 期望：done >> 任何其他状态；partial / failed = 0

# 4. 检查 API 配额（昨日有无 429）
docker compose exec clickhouse clickhouse-client --query "
  SELECT toDate(started_at) AS d, status, count()
  FROM _meta.api_calls
  WHERE started_at > now() - INTERVAL 24 HOUR
  GROUP BY d, status
  ORDER BY d, status
"
# 期望：status=200 占绝大部分；status=429 < 1%

# 5. 启动当天任务（用 TodoWrite 追踪）
```

每天**关机**前：
- 在 `data/logs/progress.md` 追加（不覆盖）当天进度
- 把所有 `run_in_background` 任务的状态确认（哪些跑完了、哪些还在跑）

### 6.3 长任务监控

**所有 `backfill --from --to` 跑超过 30 分钟的，必须用 `docker compose exec -d` 后台执行 + 单独的进度监控**：

```bash
# 启动
docker compose exec -d pipeline-scheduler tushare-db backfill \
  --interface daily --from 20200101 --to 20260426

# 监控（另开窗口）
watch -n 60 'docker compose exec clickhouse clickhouse-client --query \
  "SELECT count() FROM tushare.tushare_stock_daily FINAL"'

# 或看 sync_state
watch -n 300 'docker compose exec pipeline-scheduler tushare-db status --interface daily'
```

### 6.4 Agent 编排建议

| 任务 | 推荐 Agent / Skill |
|------|---------------------|
| R1-R5 数据回填 | 不调 agent，直接 CLI 命令 + 监控 |
| R6 长跑观察 | 不调 agent，每天人工 / TodoWrite |
| R8 数学正确性验证 | `data:validate-data` skill |
| R10 CI 调试 | `gh-cli` skill + `build-error-resolver` agent |
| R11 empty_sample 排查 | `python-reviewer` agent（修完代码后审） |
| R13 / R14 灾难演练 | 不调 agent，按文档步骤执行 |

---

## 7. 终极完成定义（Project DoD v3）

修完本文档 14 项后，**真正的"长期运行"判定**：

✅ **数据完整性**：
- `tushare_stock_daily` ≥ 8M 行，覆盖 2020-01-01 至今
- `tushare_adj_factor` ≥ 8M 行
- `tushare_daily_basic` ≥ 8M 行
- 5 张财务表每张 ≥ 100K 行
- 至少 169（R11 后 174）张表非空

✅ **运行稳定性**：
- 连续 5 个工作日 scheduler 自动增量，0 partial / 0 failed
- weekly_reconcile 至少跑过 1 次
- verify_row_counts 至少跑过 5 次

✅ **错误处理**：
- Tushare token 失效 → 5 次 401 后 scheduler 自动暂停（R13 验证）
- 单个接口失败不影响其他接口
- partial → resume 能续跑

✅ **可观测性**：
- 3 个 Grafana dashboard 都有数据
- API 配额监控告警接入
- `_meta.sync_state` / `_meta.sync_runs` / `_meta.api_calls` 三表数据丰富

✅ **CI/CD**：
- GitHub Actions 全绿
- 覆盖率 ≥ 75%（集成测试加进来）
- codecov 持续跟踪

✅ **MCP / 客户端**：
- get_ohlcv qfq/hfq 在 6 年茅台数据上数学正确
- LAN 机器（非本机）通过 ai_reader 查数成功
- 浏览器 Dashboard 显示真实数据

✅ **灾难恢复**：
- 备份/恢复演练完成（已 ✅）
- clickhouse_data 卷损坏后 < 1h 恢复（R14）
- Tushare token 切换不影响数据（R13）

---

## 8. 不要做什么（重申）

❌ 不要在 R1-R5 期间反复修代码（看到错误先记 progress.md，跑完再统一修）
❌ 不要并发跑多个 `backfill` 命令（会争抢 worker，违反 §3 设计）
❌ 不要为了赶进度跳过 R8 数学正确性验证
❌ 不要在 CI 没过的情况下做 R6 长跑（CI 是基础保障）
❌ 不要在阶段一未完成时做阶段四演练（基础数据没有，演练无意义）

---

## 9. 卡壳处理

如果某项卡住超过 1 小时：

1. 在本文档末尾追加 `## 阻塞 R<id>` 段落
2. 写清楚：什么命令、什么报错、试过什么、怀疑什么
3. **停下来等用户**，不要瞎试

---

## 10. 完成后输出物

修完所有 14 项后，在 `data/logs/` 生成：
- `project_status_<date>.md`（最终状态报告）
- `long_run_5days.md`（R6 五交易日实测日志）
- `disaster_recovery_test.md`（R13 + R14 演练记录）

并把本文档 §0 全景表的 14 项全部打上 ✅ + commit hash + 完成时间。

---

> **写在最后**：第二轮"代码 99% 完成"是真的，但**"项目可长期运行"的关键在数据和时间，不在代码**。本文档的 R1-R14 大部分耗时在等数据下载、等 scheduler 跑过去——Qwen 的角色是耐心的运维工程师，而非急切的 coding agent。
>
> **预计总时长**：10-14 个日历日（其中 ~36h 用于 R5 长尾，5 个工作日用于 R6 长跑观察）。
