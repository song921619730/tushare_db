#!/bin/bash
# Backfill all missing/empty tables sequentially
set -e

INTERFACES="stk_surv stk_premarket bo_cinema bo_daily bo_monthly bo_weekly fund_div fund_nav fund_portfolio ggt_daily ggt_monthly limit_cpt_list limit_step fx_obasic"

for iface in $INTERFACES; do
    echo "=== Backfilling $iface ==="
    docker compose exec pipeline-scheduler tushare-db backfill --interface "$iface" 2>&1 | tail -2
    sleep 3
done

echo ""
echo "=== All backfills complete ==="
