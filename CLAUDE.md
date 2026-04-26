# tushare-db Project Context

## What This Is

A **Tushare Pro A-share data warehouse** that syncs Chinese stock market data into **ClickHouse**, with scheduled incremental updates, historical backfill, data verification, and an MCP server for AI access.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Database | ClickHouse 24.8 |
| Scheduler | APScheduler |
| API | Tushare Pro (rate-limited ~500 req/min) |
| AI Access | MCP server (SSE on port 7800) |
| Dashboard | Grafana 11.0 |
| Package | hatchling, pyproject.toml |
| Linting | ruff (120 line length) |
| Testing | pytest + pytest-cov |

## Architecture

```
src/tushare_db/
├── cli.py              # CLI entry: init, bootstrap, backfill, status, resume, update, verify, scheduler-run, mcp-serve
├── config/             # YAML interface specs + settings loader (pydantic models)
├── core/               # TushareClient, DualRateLimiter, clock, errors
├── meta/               # _meta table bootstrap, sync_state, sync_runs, api_calls, sql_utils
├── planner/            # Work unit planning (date-range splitting), strategies
├── runner/             # executor, backfill, incremental, worker
├── scheduler/          # APScheduler service + job definitions
├── schema/             # DDL builder, type inference (from samples), evolver, type_map
├── sink/               # ClickHouse sink with deduplication
├── verify/             # Row counts, gap detection, checksums
├── mcp_server/         # MCP tools (query, status, backfill trigger), SSE/stdio transport
```

## Data Flow

1. **Bootstrap** (cold start): Sample APIs → infer schema → CREATE tables → seed trade_cal
2. **Backfill**: Historical data by layer/priority, split into date-range work units
3. **Incremental**: Daily T-1 updates via scheduler (APScheduler cron jobs)
4. **Verify**: Row counts, gap detection, checksums
5. **MCP**: AI agents query data via SSE endpoint

## Key Tables

| Database | Table | Purpose |
|----------|-------|---------|
| `_meta` | `sync_state` | Per-scope sync tracking (status, rows, attempts, heartbeat) |
| `_meta` | `sync_runs` | Run-level audit log |
| `_meta` | `trade_cal` | Trading calendar (seeded from Tushare) |
| `tushare` | `{interface}_*` | Data tables (ReplacingMergeTree, partitioned by month/year) |

## Configuration

- **Settings**: `config/settings.yaml` (rate limits, CH connection, timezone Asia/Shanghai)
- **Interface specs**: `config/interfaces/*.yaml` (per-interface config: fetch strategy, schema overrides, order_by, partition_key)
- **Env vars**: `TUSHARE_TOKEN`, `CH_HOST`, `CH_PIPELINE_PASSWORD`, `CH_AI_READER_PASSWORD`
- **Default start date**: 2020-01-01

## Docker Services

| Service | Ports | Purpose |
|---------|-------|---------|
| clickhouse | 8123, 9000 | Data store |
| pipeline-scheduler | - | APScheduler daemon |
| pipeline-mcp | 7800 | MCP SSE server |
| grafana | 3000 | Dashboards |
| dashboard | 3001 | Web dashboard |

## Development Commands

```bash
# Init (first time)
tushare-db init

# Bootstrap cold start
tushare-db bootstrap

# Backfill historical data
tushare-db backfill --layer 0    # or --all

# View sync status
tushare-db status [--detail]

# Resume failed units
tushare-db resume [--dry-run]

# Incremental update (T-1)
tushare-db update --incremental

# Verify data integrity
tushare-db verify [--gaps] [--checksums]

# Start scheduler
tushare-db scheduler-run

# Start MCP server
tushare-db mcp-serve --transport sse

# Run tests
pytest --cov=src --cov-report=term-missing
```

## Important Design Decisions

- **ReplacingMergeTree** with `_version` column for deduplication
- **Work unit model**: Each interface split into date-range scopes, tracked in `_meta.sync_state`
- **Dual rate limiter**: Separate RPM limits for normal (475) and special (285) APIs
- **Schema evolution**: Evolver handles ALTER TABLE ADD/MODIFY COLUMN when upstream changes
- **MCP tools**: Expose query, status, and backfill operations to AI agents
- **Multi-document YAML**: Interface configs use `---` separated documents

## Current Branch Status

- Branch: `master` (main branch is `main`)
- Has uncommitted changes in config, docker, and source files
- Multiple untracked test files and scripts
