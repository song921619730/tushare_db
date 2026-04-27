# cb_factor_pro

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | cb_factor_pro |
| 表名 | `tushare_cb_factor_pro` |
| 优先级 | P2 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | A |
| 采集策略 | date_loop |
| 日期字段 | trade_date |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 340 |

## 字段列表 (90 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |

### 技术指标 (35个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `boll_lower_bfq` | Float64 |  |
| 2 | `boll_mid_bfq` | Float64 |  |
| 3 | `boll_upper_bfq` | Float64 |  |
| 4 | `dfma_dif_bfq` | Float64 |  |
| 5 | `dfma_difma_bfq` | Float64 |  |
| 6 | `ema_bfq_10` | Float64 |  |
| 7 | `ema_bfq_20` | Float64 |  |
| 8 | `ema_bfq_250` | Float64 |  |
| 9 | `ema_bfq_30` | Float64 |  |
| 10 | `ema_bfq_5` | Float64 |  |
| 11 | `ema_bfq_60` | Float64 |  |
| 12 | `ema_bfq_90` | Float64 |  |
| 13 | `expma_12_bfq` | Float64 |  |
| 14 | `expma_50_bfq` | Float64 |  |
| 15 | `kdj_bfq` | Float64 |  |
| 16 | `kdj_d_bfq` | Float64 |  |
| 17 | `kdj_k_bfq` | Float64 |  |
| 18 | `ma_bfq_10` | Float64 |  |
| 19 | `ma_bfq_20` | Float64 |  |
| 20 | `ma_bfq_250` | Float64 |  |
| 21 | `ma_bfq_30` | Float64 |  |
| 22 | `ma_bfq_5` | Float64 |  |
| 23 | `ma_bfq_60` | Float64 |  |
| 24 | `ma_bfq_90` | Float64 |  |
| 25 | `macd_bfq` | Float64 |  |
| 26 | `macd_dea_bfq` | Float64 |  |
| 27 | `macd_dif_bfq` | Float64 |  |
| 28 | `ma_mass_bfq` | Float64 |  |
| 29 | `mtmma_bfq` | Float64 |  |
| 30 | `psyma_bfq` | Float64 |  |
| 31 | `rsi_bfq_12` | Float64 |  |
| 32 | `rsi_bfq_24` | Float64 |  |
| 33 | `rsi_bfq_6` | Float64 |  |
| 34 | `trma_bfq` | Float64 |  |
| 35 | `_version` | UInt64 |  |

### 成交量/额 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `vol` | Float64 |  |
| 2 | `amount` | Float64 |  |

### 股本/市值 (2个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `emv_bfq` | Float64 |  |
| 2 | `maemv_bfq` | Float64 |  |

### 数值 (49个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `open` | Float64 |  |
| 2 | `high` | Float64 |  |
| 3 | `low` | Float64 |  |
| 4 | `close` | Float64 |  |
| 5 | `pre_close` | Float64 |  |
| 6 | `change` | Float64 |  |
| 7 | `pct_change` | Float64 |  |
| 8 | `asi_bfq` | Float64 |  |
| 9 | `asit_bfq` | Float64 |  |
| 10 | `atr_bfq` | Float64 |  |
| 11 | `bbi_bfq` | Float64 |  |
| 12 | `bias1_bfq` | Float64 |  |
| 13 | `bias2_bfq` | Float64 |  |
| 14 | `bias3_bfq` | Float64 |  |
| 15 | `brar_ar_bfq` | Float64 |  |
| 16 | `brar_br_bfq` | Float64 |  |
| 17 | `cci_bfq` | Float64 |  |
| 18 | `cr_bfq` | Float64 |  |
| 19 | `dmi_adx_bfq` | Float64 |  |
| 20 | `dmi_adxr_bfq` | Float64 |  |
| 21 | `dmi_mdi_bfq` | Float64 |  |
| 22 | `dmi_pdi_bfq` | Float64 |  |
| 23 | `downdays` | Float64 |  |
| 24 | `updays` | Float64 |  |
| 25 | `dpo_bfq` | Float64 |  |
| 26 | `madpo_bfq` | Float64 |  |
| 27 | `ktn_down_bfq` | Float64 |  |
| 28 | `ktn_mid_bfq` | Float64 |  |
| 29 | `ktn_upper_bfq` | Float64 |  |
| 30 | `lowdays` | Float64 |  |
| 31 | `topdays` | Float64 |  |
| 32 | `mass_bfq` | Float64 |  |
| 33 | `mfi_bfq` | Float64 |  |
| 34 | `mtm_bfq` | Float64 |  |
| 35 | `obv_bfq` | Float64 |  |
| 36 | `psy_bfq` | Float64 |  |
| 37 | `roc_bfq` | Float64 |  |
| 38 | `maroc_bfq` | Float64 |  |
| 39 | `taq_down_bfq` | Float64 |  |
| 40 | `taq_mid_bfq` | Float64 |  |
| 41 | `taq_up_bfq` | Float64 |  |
| 42 | `trix_bfq` | Float64 |  |
| 43 | `vr_bfq` | Float64 |  |
| 44 | `wr_bfq` | Float64 |  |
| 45 | `wr1_bfq` | Float64 |  |
| 46 | `xsii_td1_bfq` | Float64 |  |
| 47 | `xsii_td2_bfq` | Float64 |  |
| 48 | `xsii_td3_bfq` | Float64 |  |
| 49 | `xsii_td4_bfq` | Float64 |  |
