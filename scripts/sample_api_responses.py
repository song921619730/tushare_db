"""Sample Tushare API responses for schema inference.

Usage:
    tushare-db sample-apis                  # Sample all enabled interfaces
    tushare-db sample-apis --only daily,income  # Sample specific interfaces

Outputs:
    data/samples/{interface}.json for each sampled interface
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import structlog
from dotenv import load_dotenv

from tushare_db.core.tushare_client import TushareClient
from tushare_db.config.loader import load_interface_specs
from tushare_db.logging_setup import setup_logging

logger = structlog.get_logger()
load_dotenv()


def sample_apis(only: str | None = None, output_dir: str = "data/samples") -> None:
    """Sample API responses from Tushare.

    For each enabled interface, make a single API call with minimal params
    and save the response as JSON for schema inference.
    """
    setup_logging()
    token = os.environ["TUSHARE_TOKEN"]
    if token == "PASTE_YOUR_NEW_TUSHARE_TOKEN_HERE":
        raise ValueError("TUSHARE_TOKEN not set in .env")

    specs = load_interface_specs()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Filter to specific interfaces if requested
    if only:
        target_names = {n.strip() for n in only.split(",")}
        specs = [s for s in specs if s.name in target_names]
    else:
        # Only sample enabled interfaces
        specs = [s for s in specs if s.enabled]

    logger.info("Starting API sampling", count=len(specs))

    with TushareClient(token=token) as client:
        for spec in specs:
            try:
                response = _sample_interface(client, spec)
                if response is None:
                    continue

                output_file = output_path / f"{spec.name}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(response, f, indent=2, ensure_ascii=False)

                fields = response.get("data", {}).get("fields", [])
                items = response.get("data", {}).get("items", [])
                logger.info(
                    "Sampled interface",
                    interface=spec.name,
                    fields=len(fields),
                    rows=len(items),
                    output=str(output_file),
                )

                # Brief pause between calls
                time.sleep(0.2)

            except Exception as e:
                logger.warning(
                    "Failed to sample",
                    interface=spec.name,
                    error=str(e),
                )


def _sample_interface(client: TushareClient, spec) -> dict | None:
    """Make a minimal API call for schema sampling."""
    strategy = spec.fetch_strategy.kind

    params: dict = {}
    if strategy in ("date_loop", "offset_paging"):
        params = {"trade_date": "20240102"}  # first trading day of 2024 (Jan 1 is holiday)
    elif strategy == "period_loop":
        params = {"period": "20240331"}
    elif strategy == "per_symbol_period":
        # For per_symbol, just get one symbol's data
        params = {"ts_code": "000001.SZ", "period": "20240331"}
    elif strategy == "monthly_window":
        params = {"month": "202401"}

    return client.call(spec.name, bucket=spec.freq_bucket, **params)


def main() -> None:
    sample_apis()


if __name__ == "__main__":
    main()
