-- Create missing tables for tushare-db pipeline
-- Run manually after schema fix decisions were made

-- =============================================================================
-- fina_audit: Financial audit report data
-- Strategy: per_symbol_period (was period_loop, ~137K units)
-- =============================================================================
CREATE TABLE IF NOT EXISTS tushare.tushare_fina_audit
(
    `ts_code` String,
    `ann_date` Date,
    `end_date` Date,
    `audit_result` String,
    `audit_fees` Float64,
    `audit_agency` String,
    `audit_type` String,
    `audit_sign` String,
    `_version` DateTime64(6) DEFAULT now64(),
    INDEX idx_ts_code ts_code TYPE bloom_filter GRANULARITY 4,
    INDEX idx_end_date end_date TYPE minmax GRANULARITY 1
)
ENGINE = ReplacingMergeTree(_version)
PARTITION BY toYYYYMM(end_date)
ORDER BY (ts_code, end_date, ann_date)
SETTINGS index_granularity = 8192;

-- =============================================================================
-- index_monthly: Monthly index行情 data
-- Strategy: date_loop (monthly K-line by date range)
-- =============================================================================
CREATE TABLE IF NOT EXISTS tushare.tushare_index_monthly
(
    `ts_code` String,
    `trade_date` Date,
    `open` Float64,
    `high` Float64,
    `low` Float64,
    `close` Float64,
    `vol` Float64,
    `amount` Float64,
    `_version` DateTime64(6) DEFAULT now64(),
    INDEX idx_ts_code ts_code TYPE bloom_filter GRANULARITY 4,
    INDEX idx_trade_date trade_date TYPE minmax GRANULARITY 1
)
ENGINE = ReplacingMergeTree(_version)
PARTITION BY toYYYYMM(trade_date)
ORDER BY (ts_code, trade_date)
SETTINGS index_granularity = 8192;
