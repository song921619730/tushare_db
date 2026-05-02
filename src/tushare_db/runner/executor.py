"""Executor: dispatch work units to a thread pool with rate-limited concurrency and optional verification hook.

Features:
- Per-worker thread-local ClickHouse clients (avoids shared-state races)
- Normal/special bucket split: 12/6 default workers
- Heartbeat every 30s for running units (handled in worker)
- Optional verify_hook: called after each unit writes data, triggers retry on failure
"""

from __future__ import annotations

import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import clickhouse_connect
import clickhouse_connect.driver
import structlog

from tushare_db.core.tushare_client import TushareClient
from tushare_db.planner.strategies import WorkUnit
from tushare_db.runner.worker import execute_unit, VerifyHook

logger = structlog.get_logger()

_thread_local = threading.local()


def _get_thread_ch_client() -> clickhouse_connect.driver.Client:
    """Return a thread-local ClickHouse client (one HTTP connection per worker)."""
    if not hasattr(_thread_local, "client"):
        _thread_local.client = clickhouse_connect.get_client(
            host=os.environ.get("CH_HOST", "localhost"),
            port=int(os.environ.get("CH_HTTP_PORT", "8123")),
            username="pipeline",
            password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
            database="tushare",
        )
    return _thread_local.client


def execute_batch(
    units: list[WorkUnit],
    tushare_client: TushareClient,
    ch_client: clickhouse_connect.driver.Client,
    run_id: uuid.UUID | None = None,
    max_workers: int | None = None,
    verify_hook: VerifyHook | None = None,
) -> tuple[int, int, int]:
    """Execute work units concurrently with per-worker ClickHouse clients.

    Each worker thread holds its own clickhouse_connect.Client (thread-local),
    avoiding shared-state races on the HTTP client.

    Units are split by bucket: normal → 12 workers, special → 6 workers.

    Args:
        verify_hook: Optional callback(ch_client, unit, rows_written) -> bool.
            Called after each unit writes data. Returns False to trigger
            automatic retry (re-fetch + re-write, up to 2 attempts).
    """
    if run_id is None:
        run_id = uuid.uuid4()

    normal_units = [u for u in units if u.bucket == "normal"]
    special_units = [u for u in units if u.bucket == "special"]

    done_count = 0
    failed_count = 0
    total_rows = 0

    lock = threading.Lock()

    def _run(unit_list: list[WorkUnit], workers: int) -> None:
        nonlocal done_count, failed_count, total_rows
        if not unit_list:
            return

        def _wrapped(unit: WorkUnit) -> int:
            client = _get_thread_ch_client()
            return execute_unit(unit, tushare_client, client, run_id, verify_hook=verify_hook)

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(_wrapped, u): u for u in unit_list}
            for future in as_completed(futures):
                unit = futures[future]
                try:
                    result = future.result()
                    with lock:
                        if result >= 0:
                            done_count += 1
                            total_rows += max(result, 0)
                        else:
                            failed_count += 1
                except Exception as e:
                    with lock:
                        failed_count += 1
                    logger.error(
                        "Unit crashed",
                        interface=unit.interface,
                        scope_key=unit.scope_key,
                        error=str(e),
                    )

                progress = done_count + failed_count
                if progress % 10 == 0 or progress == len(units):
                    logger.info(
                        "Batch progress",
                        total=len(units),
                        done=done_count,
                        failed=failed_count,
                        rows=total_rows,
                    )

    nw = int(os.environ.get("TUSHARE_NORMAL_WORKERS", "12"))
    sw = int(os.environ.get("TUSHARE_SPECIAL_WORKERS", "6"))
    if max_workers is not None:
        nw = sw = max_workers

    _run(normal_units, nw)
    _run(special_units, sw)

    logger.info(
        "Batch complete",
        total=len(units),
        done=done_count,
        failed=failed_count,
        rows=total_rows,
    )

    return len(units), done_count, failed_count
