# stk_factor_pro

## 接口信息

| 属性 | 值 |
|------|-----|
| 接口名称 | stk_factor_pro |
| 表名 | `tushare_stk_factor_pro` |
| 优先级 | P1 |
| 模式 | incremental |
| 频率分桶 | special |
| 批次 | C |
| 采集策略 | date_loop |
| 日期字段 | trade_date |
| 排序键 | ts_code, trade_date |
| 分区键 | toYYYYMM(trade_date) |
| 起始日期 | 20200101 |

## 数据概览

| 属性 | 值 |
|------|-----|
| 数据库 | tushare |
| 行数 | 7,332,731 |

## 字段列表 (262 个字段)

### 标识 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `ts_code` | LowCardinality(String) |  |

### 日期 (1个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `trade_date` | Date |  |

### 技术指标 (103个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `boll_lower_bfq` | Float64 |  |
| 2 | `boll_lower_hfq` | Float64 |  |
| 3 | `boll_lower_qfq` | Float64 |  |
| 4 | `boll_mid_bfq` | Float64 |  |
| 5 | `boll_mid_hfq` | Float64 |  |
| 6 | `boll_mid_qfq` | Float64 |  |
| 7 | `boll_upper_bfq` | Float64 |  |
| 8 | `boll_upper_hfq` | Float64 |  |
| 9 | `boll_upper_qfq` | Float64 |  |
| 10 | `dfma_dif_bfq` | Float64 |  |
| 11 | `dfma_dif_hfq` | Float64 |  |
| 12 | `dfma_dif_qfq` | Float64 |  |
| 13 | `dfma_difma_bfq` | Float64 |  |
| 14 | `dfma_difma_hfq` | Float64 |  |
| 15 | `dfma_difma_qfq` | Float64 |  |
| 16 | `ema_bfq_10` | Float64 |  |
| 17 | `ema_bfq_20` | Float64 |  |
| 18 | `ema_bfq_250` | Float64 |  |
| 19 | `ema_bfq_30` | Float64 |  |
| 20 | `ema_bfq_5` | Float64 |  |
| 21 | `ema_bfq_60` | Float64 |  |
| 22 | `ema_bfq_90` | Float64 |  |
| 23 | `ema_hfq_10` | Float64 |  |
| 24 | `ema_hfq_20` | Float64 |  |
| 25 | `ema_hfq_250` | Float64 |  |
| 26 | `ema_hfq_30` | Float64 |  |
| 27 | `ema_hfq_5` | Float64 |  |
| 28 | `ema_hfq_60` | Float64 |  |
| 29 | `ema_hfq_90` | Float64 |  |
| 30 | `ema_qfq_10` | Float64 |  |
| 31 | `ema_qfq_20` | Float64 |  |
| 32 | `ema_qfq_250` | Float64 |  |
| 33 | `ema_qfq_30` | Float64 |  |
| 34 | `ema_qfq_5` | Float64 |  |
| 35 | `ema_qfq_60` | Float64 |  |
| 36 | `ema_qfq_90` | Float64 |  |
| 37 | `expma_12_bfq` | Float64 |  |
| 38 | `expma_12_hfq` | Float64 |  |
| 39 | `expma_12_qfq` | Float64 |  |
| 40 | `expma_50_bfq` | Float64 |  |
| 41 | `expma_50_hfq` | Float64 |  |
| 42 | `expma_50_qfq` | Float64 |  |
| 43 | `kdj_bfq` | Float64 |  |
| 44 | `kdj_hfq` | Float64 |  |
| 45 | `kdj_qfq` | Float64 |  |
| 46 | `kdj_d_bfq` | Float64 |  |
| 47 | `kdj_d_hfq` | Float64 |  |
| 48 | `kdj_d_qfq` | Float64 |  |
| 49 | `kdj_k_bfq` | Float64 |  |
| 50 | `kdj_k_hfq` | Float64 |  |
| 51 | `kdj_k_qfq` | Float64 |  |
| 52 | `ma_bfq_10` | Float64 |  |
| 53 | `ma_bfq_20` | Float64 |  |
| 54 | `ma_bfq_250` | Float64 |  |
| 55 | `ma_bfq_30` | Float64 |  |
| 56 | `ma_bfq_5` | Float64 |  |
| 57 | `ma_bfq_60` | Float64 |  |
| 58 | `ma_bfq_90` | Float64 |  |
| 59 | `ma_hfq_10` | Float64 |  |
| 60 | `ma_hfq_20` | Float64 |  |
| 61 | `ma_hfq_250` | Float64 |  |
| 62 | `ma_hfq_30` | Float64 |  |
| 63 | `ma_hfq_5` | Float64 |  |
| 64 | `ma_hfq_60` | Float64 |  |
| 65 | `ma_hfq_90` | Float64 |  |
| 66 | `ma_qfq_10` | Float64 |  |
| 67 | `ma_qfq_20` | Float64 |  |
| 68 | `ma_qfq_250` | Float64 |  |
| 69 | `ma_qfq_30` | Float64 |  |
| 70 | `ma_qfq_5` | Float64 |  |
| 71 | `ma_qfq_60` | Float64 |  |
| 72 | `ma_qfq_90` | Float64 |  |
| 73 | `macd_bfq` | Float64 |  |
| 74 | `macd_hfq` | Float64 |  |
| 75 | `macd_qfq` | Float64 |  |
| 76 | `macd_dea_bfq` | Float64 |  |
| 77 | `macd_dea_hfq` | Float64 |  |
| 78 | `macd_dea_qfq` | Float64 |  |
| 79 | `macd_dif_bfq` | Float64 |  |
| 80 | `macd_dif_hfq` | Float64 |  |
| 81 | `macd_dif_qfq` | Float64 |  |
| 82 | `ma_mass_bfq` | Float64 |  |
| 83 | `ma_mass_hfq` | Float64 |  |
| 84 | `ma_mass_qfq` | Float64 |  |
| 85 | `mtmma_bfq` | Float64 |  |
| 86 | `mtmma_hfq` | Float64 |  |
| 87 | `mtmma_qfq` | Float64 |  |
| 88 | `psyma_bfq` | Float64 |  |
| 89 | `psyma_hfq` | Float64 |  |
| 90 | `psyma_qfq` | Float64 |  |
| 91 | `rsi_bfq_12` | Float64 |  |
| 92 | `rsi_bfq_24` | Float64 |  |
| 93 | `rsi_bfq_6` | Float64 |  |
| 94 | `rsi_hfq_12` | Float64 |  |
| 95 | `rsi_hfq_24` | Float64 |  |
| 96 | `rsi_hfq_6` | Float64 |  |
| 97 | `rsi_qfq_12` | Float64 |  |
| 98 | `rsi_qfq_24` | Float64 |  |
| 99 | `rsi_qfq_6` | Float64 |  |
| 100 | `trma_bfq` | Float64 |  |
| 101 | `trma_hfq` | Float64 |  |
| 102 | `trma_qfq` | Float64 |  |
| 103 | `_version` | UInt64 |  |

### 估值指标 (5个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `pe` | Float64 |  |
| 2 | `pb` | Float64 |  |
| 3 | `ps` | Float64 |  |
| 4 | `dv_ratio` | Float64 |  |
| 5 | `dv_ttm` | Float64 |  |

### 成交量/额 (4个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `vol` | Float64 |  |
| 2 | `amount` | Float64 |  |
| 3 | `turnover_rate` | Float64 |  |
| 4 | `volume_ratio` | Float64 |  |

### 股本/市值 (11个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `total_share` | Decimal(18, 4) |  |
| 2 | `float_share` | Decimal(18, 4) |  |
| 3 | `free_share` | Decimal(18, 4) |  |
| 4 | `total_mv` | Decimal(18, 2) |  |
| 5 | `circ_mv` | Decimal(18, 2) |  |
| 6 | `emv_bfq` | Float64 |  |
| 7 | `emv_hfq` | Float64 |  |
| 8 | `emv_qfq` | Float64 |  |
| 9 | `maemv_bfq` | Float64 |  |
| 10 | `maemv_hfq` | Float64 |  |
| 11 | `maemv_qfq` | Float64 |  |

### 数值 (137个)

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | `open` | Float64 |  |
| 2 | `open_hfq` | Float64 |  |
| 3 | `open_qfq` | Float64 |  |
| 4 | `high` | Float64 |  |
| 5 | `high_hfq` | Float64 |  |
| 6 | `high_qfq` | Float64 |  |
| 7 | `low` | Float64 |  |
| 8 | `low_hfq` | Float64 |  |
| 9 | `low_qfq` | Float64 |  |
| 10 | `close` | Float64 |  |
| 11 | `close_hfq` | Float64 |  |
| 12 | `close_qfq` | Float64 |  |
| 13 | `pre_close` | Float64 |  |
| 14 | `change` | Float64 |  |
| 15 | `pct_chg` | Float64 |  |
| 16 | `turnover_rate_f` | Float64 |  |
| 17 | `pe_ttm` | Float64 |  |
| 18 | `ps_ttm` | Float64 |  |
| 19 | `adj_factor` | Float64 |  |
| 20 | `asi_bfq` | Float64 |  |
| 21 | `asi_hfq` | Float64 |  |
| 22 | `asi_qfq` | Float64 |  |
| 23 | `asit_bfq` | Float64 |  |
| 24 | `asit_hfq` | Float64 |  |
| 25 | `asit_qfq` | Float64 |  |
| 26 | `atr_bfq` | Float64 |  |
| 27 | `atr_hfq` | Float64 |  |
| 28 | `atr_qfq` | Float64 |  |
| 29 | `bbi_bfq` | Float64 |  |
| 30 | `bbi_hfq` | Float64 |  |
| 31 | `bbi_qfq` | Float64 |  |
| 32 | `bias1_bfq` | Float64 |  |
| 33 | `bias1_hfq` | Float64 |  |
| 34 | `bias1_qfq` | Float64 |  |
| 35 | `bias2_bfq` | Float64 |  |
| 36 | `bias2_hfq` | Float64 |  |
| 37 | `bias2_qfq` | Float64 |  |
| 38 | `bias3_bfq` | Float64 |  |
| 39 | `bias3_hfq` | Float64 |  |
| 40 | `bias3_qfq` | Float64 |  |
| 41 | `brar_ar_bfq` | Float64 |  |
| 42 | `brar_ar_hfq` | Float64 |  |
| 43 | `brar_ar_qfq` | Float64 |  |
| 44 | `brar_br_bfq` | Float64 |  |
| 45 | `brar_br_hfq` | Float64 |  |
| 46 | `brar_br_qfq` | Float64 |  |
| 47 | `cci_bfq` | Float64 |  |
| 48 | `cci_hfq` | Float64 |  |
| 49 | `cci_qfq` | Float64 |  |
| 50 | `cr_bfq` | Float64 |  |
| 51 | `cr_hfq` | Float64 |  |
| 52 | `cr_qfq` | Float64 |  |
| 53 | `dmi_adx_bfq` | Float64 |  |
| 54 | `dmi_adx_hfq` | Float64 |  |
| 55 | `dmi_adx_qfq` | Float64 |  |
| 56 | `dmi_adxr_bfq` | Float64 |  |
| 57 | `dmi_adxr_hfq` | Float64 |  |
| 58 | `dmi_adxr_qfq` | Float64 |  |
| 59 | `dmi_mdi_bfq` | Float64 |  |
| 60 | `dmi_mdi_hfq` | Float64 |  |
| 61 | `dmi_mdi_qfq` | Float64 |  |
| 62 | `dmi_pdi_bfq` | Float64 |  |
| 63 | `dmi_pdi_hfq` | Float64 |  |
| 64 | `dmi_pdi_qfq` | Float64 |  |
| 65 | `downdays` | Float64 |  |
| 66 | `updays` | Float64 |  |
| 67 | `dpo_bfq` | Float64 |  |
| 68 | `dpo_hfq` | Float64 |  |
| 69 | `dpo_qfq` | Float64 |  |
| 70 | `madpo_bfq` | Float64 |  |
| 71 | `madpo_hfq` | Float64 |  |
| 72 | `madpo_qfq` | Float64 |  |
| 73 | `ktn_down_bfq` | Float64 |  |
| 74 | `ktn_down_hfq` | Float64 |  |
| 75 | `ktn_down_qfq` | Float64 |  |
| 76 | `ktn_mid_bfq` | Float64 |  |
| 77 | `ktn_mid_hfq` | Float64 |  |
| 78 | `ktn_mid_qfq` | Float64 |  |
| 79 | `ktn_upper_bfq` | Float64 |  |
| 80 | `ktn_upper_hfq` | Float64 |  |
| 81 | `ktn_upper_qfq` | Float64 |  |
| 82 | `lowdays` | Float64 |  |
| 83 | `topdays` | Float64 |  |
| 84 | `mass_bfq` | Float64 |  |
| 85 | `mass_hfq` | Float64 |  |
| 86 | `mass_qfq` | Float64 |  |
| 87 | `mfi_bfq` | Float64 |  |
| 88 | `mfi_hfq` | Float64 |  |
| 89 | `mfi_qfq` | Float64 |  |
| 90 | `mtm_bfq` | Float64 |  |
| 91 | `mtm_hfq` | Float64 |  |
| 92 | `mtm_qfq` | Float64 |  |
| 93 | `obv_bfq` | Float64 |  |
| 94 | `obv_hfq` | Float64 |  |
| 95 | `obv_qfq` | Float64 |  |
| 96 | `psy_bfq` | Float64 |  |
| 97 | `psy_hfq` | Float64 |  |
| 98 | `psy_qfq` | Float64 |  |
| 99 | `roc_bfq` | Float64 |  |
| 100 | `roc_hfq` | Float64 |  |
| 101 | `roc_qfq` | Float64 |  |
| 102 | `maroc_bfq` | Float64 |  |
| 103 | `maroc_hfq` | Float64 |  |
| 104 | `maroc_qfq` | Float64 |  |
| 105 | `taq_down_bfq` | Float64 |  |
| 106 | `taq_down_hfq` | Float64 |  |
| 107 | `taq_down_qfq` | Float64 |  |
| 108 | `taq_mid_bfq` | Float64 |  |
| 109 | `taq_mid_hfq` | Float64 |  |
| 110 | `taq_mid_qfq` | Float64 |  |
| 111 | `taq_up_bfq` | Float64 |  |
| 112 | `taq_up_hfq` | Float64 |  |
| 113 | `taq_up_qfq` | Float64 |  |
| 114 | `trix_bfq` | Float64 |  |
| 115 | `trix_hfq` | Float64 |  |
| 116 | `trix_qfq` | Float64 |  |
| 117 | `vr_bfq` | Float64 |  |
| 118 | `vr_hfq` | Float64 |  |
| 119 | `vr_qfq` | Float64 |  |
| 120 | `wr_bfq` | Float64 |  |
| 121 | `wr_hfq` | Float64 |  |
| 122 | `wr_qfq` | Float64 |  |
| 123 | `wr1_bfq` | Float64 |  |
| 124 | `wr1_hfq` | Float64 |  |
| 125 | `wr1_qfq` | Float64 |  |
| 126 | `xsii_td1_bfq` | Float64 |  |
| 127 | `xsii_td1_hfq` | Float64 |  |
| 128 | `xsii_td1_qfq` | Float64 |  |
| 129 | `xsii_td2_bfq` | Float64 |  |
| 130 | `xsii_td2_hfq` | Float64 |  |
| 131 | `xsii_td2_qfq` | Float64 |  |
| 132 | `xsii_td3_bfq` | Float64 |  |
| 133 | `xsii_td3_hfq` | Float64 |  |
| 134 | `xsii_td3_qfq` | Float64 |  |
| 135 | `xsii_td4_bfq` | Float64 |  |
| 136 | `xsii_td4_hfq` | Float64 |  |
| 137 | `xsii_td4_qfq` | Float64 |  |
