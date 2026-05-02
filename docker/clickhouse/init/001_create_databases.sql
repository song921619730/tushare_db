-- PR1: Create databases and _meta tables
-- This script runs once on first ClickHouse startup via docker-entrypoint-initdb.d

CREATE DATABASE IF NOT EXISTS tushare;

CREATE DATABASE IF NOT EXISTS _meta;

-- sync_state: checkpoint table for each work unit
CREATE TABLE IF NOT EXISTS _meta.sync_state (
    interface         LowCardinality(String),
    scope_key         String,
    status            Enum8('pending'=0, 'running'=1, 'done'=2, 'partial'=3, 'failed'=4, 'biz_err'=5),
    rows              UInt64,
    last_success_at   DateTime64(3, 'Asia/Shanghai'),
    heartbeat_at      DateTime64(3, 'Asia/Shanghai'),
    attempts          UInt8,
    last_error        String,
    _version          UInt64
) ENGINE = ReplacingMergeTree(_version)
ORDER BY (interface, scope_key);

-- sync_runs: audit log for each sync run
CREATE TABLE IF NOT EXISTS _meta.sync_runs (
    run_id            UUID,
    interface         LowCardinality(String),
    batch             LowCardinality(String),
    scope             String,
    started_at        DateTime64(3, 'Asia/Shanghai'),
    finished_at       Nullable(DateTime64(3, 'Asia/Shanghai')),
    units_total       UInt32,
    units_done        UInt32,
    units_failed      UInt32,
    status            Enum8('running'=1, 'done'=2, 'partial'=3, 'failed'=4),
    normalize_version UInt16
) ENGINE = MergeTree
ORDER BY (started_at, interface);

-- api_calls: audit log for each Tushare API call
CREATE TABLE IF NOT EXISTS _meta.api_calls (
    run_id            UUID,
    interface         LowCardinality(String),
    params_hash       UInt64,
    started_at        DateTime64(3, 'Asia/Shanghai'),
    duration_ms       UInt32,
    status            UInt16,
    rows              UInt32,
    error_msg         String
) ENGINE = MergeTree
ORDER BY (started_at, interface)
TTL toDate(started_at) + INTERVAL 90 DAY;
