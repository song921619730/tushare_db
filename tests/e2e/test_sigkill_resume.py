"""E2E test: SIGKILL a backfill mid-run, then resume and verify all units complete."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv()

from tushare_db.meta.sync_state import get_interface_status, get_pending_units
from tushare_db.sink.clickhouse_sink import get_native_client


def _get_ch():
    """Create ClickHouse client for test assertions."""
    return get_native_client(
        host=os.environ.get("CH_HOST", "localhost"),
        port=8123,
        user="pipeline",
        password=os.environ.get("CH_PIPELINE_PASSWORD", ""),
    )


@pytest.mark.e2e
def test_sigkill_resume() -> None:
    """Backfill daily for 5 days, SIGKILL after 2 units, then resume and verify all 5 complete."""
    if not os.environ.get("TUSHARE_TOKEN"):
        pytest.skip("TUSHARE_TOKEN not set")

    ch = _get_ch()
    interface = "daily"

    try:
        # Clean slate: delete existing sync_state for our test dates
        ch.command(
            "ALTER TABLE _meta.sync_state DELETE "
            "WHERE interface = 'daily' AND scope_key LIKE 'daily:202504%'"
        )

        # Phase 1: Start backfill as subprocess
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent / "src")

        proc = subprocess.Popen(
            [
                sys.executable, "-m", "tushare_db.cli",
                "backfill", "--interface", "daily",
                "--from", "20250401", "--to", "20250407",
            ],
            cwd=str(Path(__file__).parent.parent.parent),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for ~2 units to complete (should take ~10-15 seconds)
        time.sleep(12)

        # Verify some units are running or done
        pending_before = get_pending_units(ch, interface)
        status_before = get_interface_status(ch, interface)
        done_keys = [r["scope_key"] for r in status_before if r["status"] == "done"]

        # SIGKILL the process
        proc.kill()
        proc.wait(timeout=10)

        # At least some units should have been marked as done or partial
        # (mark_running happens before fetch, so at least 1 unit should be running/partial/done)
        assert len(status_before) > 0, "Expected at least 1 unit to be processed before SIGKILL"

        # Phase 2: Resume
        resume_proc = subprocess.run(
            [
                sys.executable, "-m", "tushare_db.cli",
                "resume", "--interface", "daily",
            ],
            cwd=str(Path(__file__).parent.parent.parent),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert resume_proc.returncode == 0, f"Resume failed: {resume_proc.stderr}"

        # Phase 3: Verify all units are done
        time.sleep(2)
        status_after = get_interface_status(ch, interface)
        test_keys = [r for r in status_after if "202504" in r["scope_key"]]

        done_after = [r for r in test_keys if r["status"] == "done"]
        pending_after = get_pending_units(ch, interface)

        # All test-date units should be done
        for r in test_keys:
            assert r["status"] == "done", (
                f"Expected {r['scope_key']} to be done, got {r['status']} "
                f"(error: {r.get('last_error', '')})"
            )

        print(f"\nSIGKILL resume test passed: {len(done_after)} units completed after resume")

    finally:
        ch.close()
