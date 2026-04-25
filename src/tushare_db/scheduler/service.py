"""Scheduler service: APScheduler with MemoryJobStore.

Registers all jobs and starts the scheduler.
Uses Asia/Shanghai timezone.
"""

from __future__ import annotations

import structlog
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.memory import MemoryJobStore
import zoneinfo

from tushare_db.scheduler import jobs

logger = structlog.get_logger()

_TZ = zoneinfo.ZoneInfo("Asia/Shanghai")


def create_scheduler() -> BlockingScheduler:
    """Create and configure the APScheduler instance."""
    scheduler = BlockingScheduler(
        jobstores={"default": MemoryJobStore()},
        timezone=_TZ,
    )

    # Batch A: Daily Quotes — 17:00 Mon-Fri
    scheduler.add_job(
        jobs.run_batch,
        trigger="cron",
        day_of_week="mon-fri",
        hour=17,
        minute=0,
        args=("A",),
        id="batch_a",
        name="Batch A: Daily Quotes",
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    # Batch B: Money Flow & Reference — 18:00 Mon-Fri
    scheduler.add_job(
        jobs.run_batch,
        trigger="cron",
        day_of_week="mon-fri",
        hour=18,
        minute=0,
        args=("B",),
        id="batch_b",
        name="Batch B: Money Flow & Reference",
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    # Batch C: Special & Limit Board — 19:00 Mon-Fri
    scheduler.add_job(
        jobs.run_batch,
        trigger="cron",
        day_of_week="mon-fri",
        hour=19,
        minute=0,
        args=("C",),
        id="batch_c",
        name="Batch C: Special & Limit Board",
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    # Batch D: Macro / Financial / TMT / Others — 19:45 Mon-Fri
    scheduler.add_job(
        jobs.run_batch,
        trigger="cron",
        day_of_week="mon-fri",
        hour=19,
        minute=45,
        args=("D",),
        id="batch_d",
        name="Batch D: Macro / Financial / TMT / Others",
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    # Saturday Long-tail: per_symbol_period — 02:00 Sat
    scheduler.add_job(
        jobs.run_saturday_longtail,
        trigger="cron",
        day_of_week="sat",
        hour=2,
        minute=0,
        id="saturday_longtail",
        name="Saturday Long-tail: per_symbol_period",
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    # refresh_reference: daily at 06:00
    scheduler.add_job(
        jobs.run_refresh_reference,
        trigger="cron",
        hour=6,
        minute=0,
        id="refresh_reference",
        name="Refresh Reference Tables",
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    # weekly_reconcile: 02:00 Sun
    scheduler.add_job(
        jobs.run_weekly_reconcile,
        trigger="cron",
        day_of_week="sun",
        hour=2,
        minute=0,
        id="weekly_reconcile",
        name="Weekly Reconciliation",
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    # verify_row_counts: 03:00 daily
    scheduler.add_job(
        jobs.run_verify_row_counts,
        trigger="cron",
        hour=3,
        minute=0,
        id="verify_row_counts",
        name="Verify Row Counts",
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
    )

    return scheduler


def start_scheduler() -> None:
    """Start the scheduler and block until shutdown."""
    # Pre-flight: ensure _meta.trade_cal has data
    from tushare_db.scheduler.jobs import _get_ch_client

    ch_client = _get_ch_client()
    try:
        cnt = ch_client.query("SELECT count() FROM _meta.trade_cal").result_rows
        if not cnt or int(cnt[0][0]) == 0:
            logger.error("trade_cal is empty — run `tushare-db bootstrap` before scheduler-run")
            raise SystemExit(2)
        logger.info("Pre-flight check passed", trade_cal_rows=cnt[0][0])
    finally:
        ch_client.close()

    scheduler = create_scheduler()

    logger.info(
        "Scheduler starting",
        jobs=[j.id for j in scheduler.get_jobs()],
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shutting down")
        scheduler.shutdown()
