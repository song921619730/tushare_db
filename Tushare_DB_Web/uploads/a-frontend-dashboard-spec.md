# Tushare DB 前端仪表盘设计

## 目标

在局域网内提供一个轻量 Web 仪表盘，用于：
- 实时查看各接口同步状态与数据量
- 查看调度任务运行状态
- 手动触发回补/更新/验证
- 查询并浏览 ClickHouse 中的实际数据
- 查看 API 调用审计日志
- 监控同步健康度

## 技术选型

| 维度 | 选择 | 理由 |
|------|------|------|
| 交付物 | 单文件 HTML + CDN 资源 | 零构建、零部署，丢到任意静态目录即可运行 |
| 框架 | Vue 3 (CDN) + Naive UI (CDN) | 组件丰富、类型安全、Dark 模式内置 |
| 图表 | Apache ECharts (CDN) | 中文友好、时间轴/热力图/仪表盘组件齐全 |
| 通信 | ClickHouse HTTP 接口 (port 8123) | 直连只读用户，无需额外 API 服务 |
| 认证 | 嵌入 `ai_reader` 连接串（LAN 内网） | 只读隔离，max_execution_time=30s |
| 主题 | Dark 模式（数据终端风格） | 长时间盯盘不刺眼 |

## 页面结构

```
/dashboard          # 总览仪表盘
├── /interfaces     # 接口同步状态列表
── /data           # 数据查询与浏览
├── /scheduler      # 调度任务状态
├── /audit          # API 调用审计
├── /verify         # 验证与诊断
└── /settings       # 连接设置
```

## 各页面设计

### 1. /dashboard — 总览仪表盘

**布局：2×3 卡片网格 + 时间轴**

| 卡片 | 内容 |
|------|------|
| 总览指标 | 总表数 / 已同步表数 / 总行数（亿级显示） / 存储占用（GB） / 今日增量行数 |
| 同步健康度 | 环形图：done / running / partial / failed / pending 占比 |
| 今日运行 | 最近一次 run 的进度条 + 耗时 + 单元完成数 |
| P0 优先级 | 核心接口（daily/moneyflow/adj_factor等）最后一次同步时间，超时标红 |
| 存储趋势 | 近 7 天表数量与行数增长折线图 |
| 告警事件 | 最近 24h 内 failed/partial 的接口列表，点击跳转 `/interfaces` |

### 2. /interfaces — 接口同步状态

**布局：可搜索可排序的数据表格 + 右侧详情抽屉**

- 表格列：接口名 | 分类 | 优先级 | 同步模式 | 表名 | 状态 | 最后同步时间 | 总行数 | 操作
- 状态徽章：done=绿色, running=蓝色(带loading), partial=橙色, failed=红色, pending=灰色
- 搜索框：按接口名/表名/分类过滤
- 批量操作：勾选多个接口 → 触发回补/验证
- 点击行 → 右侧抽屉展开：
  - 该接口最近 10 次 run 记录（时间/行数/耗时/状态）
  - 该接口的 scope_key 列表（按日期或股票代码分区）
  - 最近一次 run 的 API 调用明细

### 3. /data — 数据查询与浏览

**布局：查询编辑器 + 结果表格 + 分页**

- 顶部：接口选择下拉框（选择后自动填入默认查询）
- 中间：SQL 编辑区（只读模式，自动注入 LIMIT 5000）
- 结果区：Naive UI DataTable，支持列排序、列显示切换
- 底部：分页器 + 总行数 + 查询耗时
- 预设查询模板：
  - OHLCV 查询：选代码 + 日期范围 → 生成 K 线图
  - 财务数据：选代码 → 收入/利润/现金流表格
  - 资金流向：选日期 → top 30 个股净流入
  - 涨停板：选日期 → 涨停/跌停列表
- K 线可视化：ECharts candlestick + volume 叠加

### 4. /scheduler — 调度任务

**布局：时间轴 + 任务卡片**

- 24h 时间轴（06:00 → 03:00），每个 job 在时间轴上标注
- 任务卡片显示：Job 名称 | 覆盖接口 | 下次执行时间 | 上次执行结果
- 上次执行状态：绿色对勾 / 橙色部分完成 / 红色失败
- 手动触发按钮：每个 job 旁边有"立即执行"按钮（需确认弹窗）
- 历史执行记录：展开查看最近 5 次执行的时间/耗时/单元数

### 5. /audit — API 调用审计

**布局：时间过滤器 + 统计图表 + 调用明细表**

- 顶部：日期范围选择器（默认今天）
- 统计行：总调用次数 / 成功率 / 总耗时 / 总返回行数 / 429 次数
- 接口调用热力图：横轴接口，纵轴小时，色块深浅=调用次数
- 明细表：调用时间 | 接口 | 参数哈希 | 耗时(ms) | 状态 | 返回行数 | 错误信息
- 错误筛选：只看 failed 的调用，展开查看完整 error_msg

### 6. /verify — 验证与诊断

**布局：验证操作面板 + 结果展示**

- 操作面板：
  - 行计数验证：选优先级(P0/P1/P2/P3) → 执行
  - 缺口检测：选接口 + 日期范围 → 执行
  - 数据抽样对比：选接口 + 日期 → 与 Tushare 在线对比
  - 全量哈希校验：选表 → 执行
- 结果展示：
  - 进度条（验证中）
  - 结果表格：接口/表 | 预期行数 | 实际行数 | 差异 | 状态
  - 一键修复：发现差异的接口，显示"补洞"按钮

### 7. /settings — 连接设置

- ClickHouse 连接配置：host / port / user / password / database
- 测试连接按钮
- 本地存储保存（localStorage），下次自动加载
- 主题切换：Dark / Light

## ClickHouse 查询清单

仪表盘依赖以下预定义的只读查询：

```sql
-- 1. 总览：各表行数汇总
SELECT database, table, sum(rows) as rows
FROM system.parts WHERE active GROUP BY database, table
ORDER BY rows DESC;

-- 2. 总存储大小
SELECT formatReadableSize(sum(bytes_on_disk)) FROM system.parts WHERE active AND database = 'tushare';

-- 3. sync_state 汇总
SELECT status, count() FROM _meta.sync_state GROUP BY status;

-- 4. 最近一次 run 进度
SELECT * FROM _meta.sync_runs ORDER BY started_at DESC LIMIT 1;

-- 5. 各接口最后同步时间
SELECT interface, max(last_success_date) as last_sync,
       countIf(status='done') as done_units,
       countIf(status='running') as running_units,
       countIf(status='failed') as failed_units,
       countIf(status='partial') as partial_units,
       sum(rows) as total_rows
FROM _meta.sync_state GROUP BY interface ORDER BY last_sync DESC;

-- 6. 今日 API 调用统计
SELECT interface, count() as calls,
       countIf(status='success') as ok,
       countIf(status='failed') as err,
       avg(duration_ms) as avg_ms,
       sum(rows) as total_rows
FROM _meta.api_calls WHERE started_at >= today()
GROUP BY interface ORDER BY calls DESC;

-- 7. 某接口最近 run 记录
SELECT run_id, started_at, units_total, units_done, status,
       duration_ms = toUnixTimestamp(now()) - toUnixTimestamp(started_at)
FROM _meta.sync_runs WHERE interface = {interface:String}
ORDER BY started_at DESC LIMIT 10;

-- 8. 某接口 scope 详情
SELECT scope_key, status, rows, last_success_date
FROM _meta.sync_state WHERE interface = {interface:String}
ORDER BY last_success_date DESC;

-- 9. 调度相关：无调度表，前端硬编码 job 列表对比最近 sync_runs

-- 10. 数据查询示例：daily OHLCV
SELECT trade_date, ts_code, open, high, low, close, pre_close,
       change, pct_chg, vol, amount
FROM tushare.stock_daily
WHERE ts_code = {ts_code:String}
  AND trade_date >= {start:String} AND trade_date <= {end:String}
ORDER BY trade_date LIMIT 5000;

-- 11. 近 7 天行数增长趋势
SELECT toDate(started_at) as day, sum(rows) as new_rows
FROM _meta.sync_runs WHERE started_at >= now() - INTERVAL 7 DAY
GROUP BY day ORDER BY day;
```

## 与后端交互方式

### 方案 A：直连 ClickHouse HTTP（默认）

```
POST http://<host>:8123/?user=ai_reader&password=xxx&database=tushare&default_format=JSONCompact
Body: SQL query string
```

- 优点：零中间层，响应快
- 缺点：SQL 注入风险（前端已限制为 SELECT 开头 + 强制 LIMIT）
- 安全：只读用户，max_execution_time=30s，max_rows_to_read 限额

### 方案 B：通过 MCP Server（扩展）

如需手动触发回补/更新/验证等操作：
```
# MCP 工具调用需单独的后端桥接服务
# 可后续实现 /api/run-backfill, /api/trigger-verify 等 REST 端点
```

当前仪表盘以 **只读监控** 为主，手动操作通过 CLI 完成。

## 文件结构

```
F:\AIcoding_space\VsCode\tushare_db\dashboard\
├── index.html                          # 主入口，Vue 3 单文件应用
├── assets\
│   ├── vue.global.prod.js
│   ├── naive-ui.global.prod.js
│   └── echarts.min.js
├── css\
│   └── dark-theme.css                   # 自定义深色主题覆盖
└── js\
    ├── app.js                           # Vue app 入口 + 路由
    ├── router.js                        # 页面路由定义
    ├── store.js                         # Pinia 状态管理（连接配置、数据缓存）
    ├── api\
    │   └── clickhouse.js                # ClickHouse HTTP 查询封装
    ├── views\
    │   ├── Dashboard.vue
    │   ├── Interfaces.vue
    │   ├── DataViewer.vue
    │   ├── Scheduler.vue
    │   ├── Audit.vue
    │   ├── Verify.vue
    │   └── Settings.vue
    └── components\
        ├── StatusBadge.vue              # 状态徽章组件
        ├── ProgressCard.vue             # 进度卡片
        ├── OHLCVChart.vue               # K 线图组件
        └── RunTimeline.vue              # 运行时间轴
```

## 启动方式

```bash
# 方式 1：直接双击 index.html 在浏览器打开（需处理 CORS）
# 方式 2：使用 Python 内置 HTTP 服务器
python -m http.server 8080 --directory dashboard/
# 方式 3：集成到 docker-compose，增加 nginx 服务
```

推荐方式 3，在 docker-compose.yml 中添加：

```yaml
  dashboard:
    image: nginx:alpine
    ports: ["3000:80"]
    volumes:
      - ./dashboard:/usr/share/nginx/html:ro
      - ./dashboard/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on: [clickhouse]
```

nginx.conf 配置反向代理处理 CORS：

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ch/ {
        proxy_pass http://clickhouse:8123/;
        proxy_set_header Authorization "";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## AI 实现提示词

> 复制以下内容发送给 AI 来生成前端代码：

---

你是一个资深前端工程师。请为 Tushare DB（一个基于 ClickHouse 的 A 股数据仓库）构建一个管理仪表盘。

**项目上下文：**
- 后端是 Python 数据管道，数据存入 ClickHouse
- 元数据存储在 `_meta.sync_state`（同步状态）、`_meta.sync_runs`（运行记录）、`_meta.api_calls`（API 审计）三张表
- 业务数据在 `tushare` 数据库，182+ 张表
- 只读用户 `ai_reader`，通过 HTTP port 8123 访问

**技术要求：**
- 单文件 HTML + CDN 引入 Vue 3 + Naive UI + ECharts
- Dark 主题，数据终端风格
- 通过 ClickHouse HTTP JSON 接口查询数据
- 所有查询只读，前端自动注入 LIMIT 5000

**页面列表：**
1. Dashboard — 总览卡片（表数/行数/存储/健康度环形图/今日进度/告警）
2. Interfaces — 接口同步状态表格（搜索/排序/批量操作/详情抽屉）
3. Data Viewer — SQL 查询 + 结果表格 + K 线图可视化
4. Scheduler — 调度任务时间轴 + 手动触发
5. Audit — API 调用审计（热力图 + 明细表）
6. Verify — 验证操作面板 + 结果展示
7. Settings — ClickHouse 连接配置

**详细设计文档：** 见同目录 `a-frontend-dashboard-spec.md`

请从 `index.html` 开始，逐步实现各页面组件。优先完成 Dashboard 和 Interfaces 两个核心页面。

---

## 扩展路线

| 阶段 | 功能 |
|------|------|
| V1 | 只读监控仪表盘（本设计） |
| V2 | 手动触发回补/验证（需 API 桥接服务） |
| V3 | 实时日志流（WebSocket 连接 pipeline 日志） |
| V4 | 数据导出（CSV/Parquet 下载） |
| V5 | 用户认证 + 多用户权限管理 |
