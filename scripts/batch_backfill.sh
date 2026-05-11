#!/bin/bash
# Batch backfill for all rebuilt tables
# Run inside pipeline-scheduler container

set -e

INTERFACES="fund_sales_ratio fund_sales_vol moneyflow_mkt_dc cb_share cb_call cb_issue fund_manager cn_pmi us_tbr us_trltr us_tltr us_trycr us_tycr wz_index yc_cb st sf_month shibor_quote teleplay_record stk_account_old new_share fut_wsr fut_holding fut_weekly_detail gz_index eco_cal report_rc index_classify fund_company"

for iface in $INTERFACES; do
    rm -f /root/.tushare_db/process.lock
    echo "=== Backfilling $iface ==="
    tushare-db backfill --interface "$iface" 2>&1 | grep -E "(Backfill|Unit complete|ERROR|failed|done)" | tail -5
    sleep 2
done

echo "=== All backfills complete ==="
