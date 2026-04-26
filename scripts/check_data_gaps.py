#!/usr/bin/env python3
"""Check all tushare tables for missing trading days."""

import os
import clickhouse_connect

client = clickhouse_connect.get_client(
    host='localhost', port=8123,
    user='pipeline', password='wpTVy_qC36mKOQVKvC9ItPZh9Eue8xt0TWWRCCJ8Q3E'
)

# Tables grouped by date column name
DATE_COL = 'trade_date'

# Tables to check: those with trade_date
tables_with_trade_date = [
    'adj_factor', 'daily_basic', 'stock_daily', 'moneyflow',
    'limit_list_d', 'top_list', 'margin', 'margin_detail',
    'top_inst', 'stk_factor_pro', 'cyq_perf', 'dc_daily',
    'ths_daily', 'index_daily', 'fund_daily', 'index_weight',
    'moneyflow_hsgt', 'block_trade', 'fut_daily', 'fx_daily',
    'sge_daily', 'sw_daily', 'ggt_daily', 'opt_daily',
    'ths_index', 'ths_member', 'bak_basic', 'bak_daily',
    'sz_daily_info', 'stk_limit', 'stk_auction_o', 'stk_auction_c',
    'hk_hold', 'hs_tbr', 'us_tbr',
]

# Tables with end_date
tables_with_end_date = [
    'fina_mainbz', 'stock_monthly',
]

# Tables with ann_date (event-driven, not every trading day)
tables_with_ann_date = [
    'balancesheet', 'income', 'cashflow', 'fina_indicator',
    'stk_holdertrade', 'top10_holders', 'top10_floatholders',
    'share_float', 'pledge_stat', 'express', 'forecast',
    'repurchase', 'dividend',
]

def check_trade_date(table, date_col='trade_date'):
    """Check if a table has all trading days covered."""
    try:
        table_name = f'tushare.tushare_{table}'
        # Get min/max/count
        result = client.query(f"""
            SELECT
                min({date_col}) AS min_date,
                max({date_col}) AS max_date,
                count(DISTINCT {date_col}) AS unique_dates
            FROM {table_name} FINAL
            WHERE {date_col} IS NOT NULL
        """)
        if not result.result_rows:
            return None
        min_date, max_date, unique_dates = result.result_rows[0]

        # Get expected trade days
        trade_result = client.query(f"""
            SELECT count() FROM _meta.trade_cal FINAL
            WHERE exchange = 'SSE' AND is_open = 1
            AND cal_date BETWEEN '{min_date}' AND '{max_date}'
        """)
        trade_days = trade_result.result_rows[0][0]
        missing = trade_days - unique_dates

        return {
            'table': table,
            'date_col': date_col,
            'min_date': str(min_date),
            'max_date': str(max_date),
            'unique_dates': unique_dates,
            'trade_days': trade_days,
            'missing': missing,
            'pct': round(100.0 * unique_dates / trade_days, 1) if trade_days > 0 else 0,
        }
    except Exception as e:
        return {'table': table, 'error': str(e)}


def check_row_count(table):
    """Simple row count for reference tables."""
    try:
        table_name = f'tushare.tushare_{table}'
        result = client.query(f"SELECT count() FROM {table_name} FINAL")
        return {'table': table, 'rows': result.result_rows[0][0]}
    except Exception as e:
        return {'table': table, 'error': str(e)}


def check_date_gaps(table, date_col='trade_date'):
    """Find specific missing dates for a table."""
    try:
        table_name = f'tushare.tushare_{table}'
        result = client.query(f"""
            SELECT cal_date AS missing_date
            FROM _meta.trade_cal FINAL
            WHERE exchange = 'SSE' AND is_open = 1
              AND cal_date BETWEEN (SELECT min({date_col}) FROM {table_name} FINAL WHERE {date_col} IS NOT NULL)
                                AND (SELECT max({date_col}) FROM {table_name} FINAL WHERE {date_col} IS NOT NULL)
              AND cal_date NOT IN (SELECT DISTINCT {date_col} FROM {table_name} FINAL WHERE {date_col} IS NOT NULL)
            ORDER BY cal_date
            LIMIT 20
        """)
        return [str(r[0]) for r in result.result_rows]
    except Exception as e:
        return [f'Error: {e}']


print("=" * 120)
print(f"{'Table':<25} {'DateCol':<12} {'Date Range':<30} {'UniqueDates':>12} {'TradeDays':>10} {'Missing':>8} {'Pct':>6}")
print("=" * 120)

all_results = []
for table in tables_with_trade_date:
    r = check_trade_date(table)
    if r and 'error' not in r:
        all_results.append(r)
        date_range = f"{r['min_date']} ~ {r['max_date']}"
        print(f"{r['table']:<25} {r['date_col']:<12} {date_range:<30} {r['unique_dates']:>12} {r['trade_days']:>10} {r['missing']:>8} {r['pct']:>6.1f}%")
    elif r:
        print(f"{r['table']:<25} ERROR: {r['error'][:60]}")

print("=" * 120)

# Show tables with missing dates
missing_tables = [r for r in all_results if r['missing'] > 0]
if missing_tables:
    print("\n### TABLES WITH MISSING DATES ###")
    for r in missing_tables:
        gaps = check_date_gaps(r['table'], r['date_col'])
        print(f"\n{r['table']} ({r['date_col']}): {r['missing']} missing dates")
        if gaps:
            print(f"  First 20: {gaps[:10]}{'...' if len(gaps) > 10 else ''}")
else:
    print("\nAll trade_date tables have 100% trading day coverage.")

# Check end_date tables
print("\n### End-date tables (event-driven) ###")
for table in tables_with_end_date:
    r = check_trade_date(table, date_col='end_date')
    if r and 'error' not in r:
        date_range = f"{r['min_date']} ~ {r['max_date']}"
        print(f"{r['table']:<25} end_date     {date_range:<30} {r['unique_dates']:>12} {r['trade_days']:>10} {r['missing']:>8} {r['pct']:>6.1f}%")

# Check ann_date tables
print("\n### Ann-date tables (event-driven, not expected to cover all days) ###")
for table in tables_with_ann_date:
    r = check_trade_date(table, date_col='ann_date')
    if r and 'error' not in r:
        date_range = f"{r['min_date']} ~ {r['max_date']}"
        print(f"{r['table']:<25} ann_date     {date_range:<30} {r['unique_dates']:>12} {r['trade_days']:>10} {r['missing']:>8} {r['pct']:>6.1f}%")

client.close()
