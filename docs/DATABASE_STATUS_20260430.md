# 数据库状态报告 — 2026-04-30

## 总体概览

| 指标 | 数值 |
|------|------|
| 总表数 | 154 |
| 空表 (0 行) | 0 |
| 仅 1 行的表 | 33 |
| 数据量极少 (2-100 行) | 20 |
| 总数据行数 | ~8175 万 |
| 成功同步 scope | 504,208 |
| 失败 scope | 1,473 |

## 服务状态

所有 5 个 Docker 服务正常运行：ClickHouse、Pipeline Scheduler、Pipeline MCP、Grafana、Dashboard。

---

## 一、空表 / 仅 1 行的表（33 个）

这些表虽然不为空，但仅有 1 行数据，意味着 backfill 从未成功执行或增量同步仅抓到 1 条。

| 表名 | 行数 | 说明 |
|------|------|------|
| `bse_mapping` | 1 | 北交所股票映射 |
| `cb_call` | 1 | 可转债赎回 |
| `cb_issue` | 1 | 可转债发行 |
| `cb_share` | 1 | 可转债份额 |
| `cn_pmi` | 1 | 宏观经济 PMI |
| `eco_cal` | 1 | 经济日历 |
| `fund_company` | 1 | 基金公司（**schema 错误阻塞**） |
| `fund_manager` | 1 | 基金经理 |
| `fund_sales_ratio` | 1 | 基金销售比例 |
| `fund_sales_vol` | 1 | 基金销售量 |
| `fut_holding` | 1 | 期货持仓 |
| `fut_weekly_detail` | 1 | 期货周度明细 |
| `fut_wsr` | 1 | 期货仓单 |
| `ggt_daily` | 1 | 港股通每日 |
| `ggt_monthly` | 1 | 港股通每月 |
| `gz_index` | 1 | 广证指数 |
| `hm_list` | 1 | 沪深港通名单 |
| `index_classify` | 1 | 指数分类 |
| `moneyflow_mkt_dc` | 1 | 大盘资金流向（DC） |
| `new_share` | 1 | 新股数据 |
| `report_rc` | 1 | 研报 |
| `sf_month` | 1 | 宏观月度 |
| `shibor_quote` | 1 | Shibor 报价 |
| `st` | 1 | ST 股票列表 |
| `stk_account_old` | 1 | 股票账户（旧） |
| `teleplay_record` | 1 | 影视剧集 |
| `us_tbr` | 1 | 美股相关 |
| `us_trltr` | 1 | 美股相关 |
| `us_tltr` | 1 | 美股相关 |
| `us_trycr` | 1 | 美股相关 |
| `us_tycr` | 1 | 美股相关 |
| `wz_index` | 1 | 微众指数 |
| `yc_cb` | 1 | 银行间存单 |

---

## 二、数据量极少表（2-100 行，20 个）

| 表名 | 行数 | 说明 |
|------|------|------|
| `ths_member` | 2 | 同花顺概念成员 |
| `bond_blk` | 9 | 债券板块 |
| `bond_blk_detail` | 9 | 债券板块明细 |
| `limit_step` | 10 | 涨跌停阶梯 |
| `daily_info` | 12 | 每日信息 |
| `index_dailybasic` | 12 | 指数每日基础 |
| `kpl_concept_cons` | 12 | 科创板概念成分 |
| `sge_basic` | 13 | 上海黄金交易所基础 |
| `ggt_top10` | 13 | 港股通十大活跃股 |
| `sz_daily_info` | 14 | 深证每日信息 |
| `hsgt_top10` | 20 | 沪深港通十大 |
| `limit_cpt_list` | 20 | 涨跌停竞争股 |
| `index_global` | 20 | 全球指数 |
| `tdx_member` | 20 | 通达信会员 |
| `suspend_d` | 22 | 停牌 |
| `repo_daily` | 44 | 回购每日 |
| `kpl_list` | 68 | 科创板列表 |
| `limit_list_ths` | 68 | 涨跌停列表（THS） |
| `fx_obasic` | 69 | 外汇基础 |
| `hm_detail` | 74 | 沪深港通明细 |

---

## 三、失败的同步任务（1,473 个 scope）

### 3.1 Schema 缺失列（1,213 个失败）

**原因**：上游 API 返回了新列，但 ClickHouse 表结构未同步更新。

| 接口 | 失败数 | 缺失列 | 目标表 |
|------|--------|--------|--------|
| `moneyflow_ths` | 431 | `name` | `tushare_moneyflow_ths` |
| `moneyflow_cnt_ths` | 391 | `lead_stock` | `tushare_moneyflow_cnt_ths` |
| `moneyflow_ind_ths` | 391 | `industry` | `tushare_moneyflow_ind_ths` |

**修复方案**：对这三张表执行 `ALTER TABLE ADD COLUMN`，添加缺失字段。

### 3.2 SSL / 网络超时（66 个失败）

| 接口 | 失败数 | 错误信息 |
|------|--------|----------|
| `fina_audit` | 587 | （空错误，`per_symbol` 策略未注册导致） |
| `fina_audit` | 59 | `_ssl.c:993: The handshake operation timed out` |
| `fina_audit` | 8 | `The read operation timed out` |
| `fut_weekly_monthly` | 1 | `_ssl.c:999: The handshake operation timed out` |

**fina_audit 特殊情况**：
- 587 个空错误是因为 scheduler 使用了 `per_symbol` 策略但 planner 未注册该策略名
- 其余 67 个为 Tushare API 超时，需限速重试

### 3.3 日期类型序列化错误（2 个失败）

| 接口 | 失败数 | 错误列 | 错误信息 |
|------|--------|--------|----------|
| `stk_managers` | 1 | `begin_date` | `unsupported operand type(s) for -: 'str' and 'datetime.date'` |
| `fund_company` | 1 | （同日期字段） | 同上 |

**原因**：API 返回的日期是字符串，但 `_normalize_items` 未正确转换，直接传入 ClickHouse `Date` 类型列。
**修复方案**：在 `_normalize_items` 中增加日期字符串解析逻辑。

### 3.4 Nullable 列插入 None（2 个失败）

| 接口 | 失败数 | 错误列 | 错误信息 |
|------|--------|--------|----------|
| `etf_index` | 1 | `pub_date` | `Unable to create Python array for source column 'pub_date'. This is usually caused by trying to insert None values into a ClickHouse column that is not Nullable` |
| `index_basic` | 1 | `base_date` | 同上 |

**修复方案**：将对应列改为 `Nullable(Date)` 或在插入前过滤/填充 None 值。

### 3.5 已清理 stale running（2 个）

| 接口 | 失败数 | 错误信息 |
|------|--------|----------|
| `fut_weekly_monthly` | 2 | `stale running - cleaned by admin` |

已手动清理，可正常 resume。

---

## 四、当前活跃的 running 任务

6 条 `fina_audit` 记录（`000591.SZ` 相关），心跳正常，正在运行中。

---

## 五、修复优先级

| 优先级 | 问题 | 影响范围 | 预计工作量 |
|--------|------|----------|------------|
| **P0** | `moneyflow_*` 缺列 | 1,213 个 scope | 3 条 ALTER TABLE |
| **P0** | `fina_audit` per_symbol 策略 | 587 个 scope | 注册策略 + resume |
| **P1** | `stk_managers`/`fund_company` 日期转换 | 2 个 scope，多行受影响 | 修改 _normalize_items |
| **P1** | `etf_index`/`index_basic` Nullable | 2 个 scope | ALTER TABLE MODIFY COLUMN |
| **P2** | 33 个仅 1 行的表 | 33 个接口 | 需排查是否从未 backfill |
| **P2** | `fina_audit` SSL 超时 | 67 个 scope | 限速重试 |
| **P3** | 20 个数据量极少表 | 20 个接口 | 需排查增量策略是否正确 |
