#!/usr/bin/env python
"""Diagnostic: inspect raw Tushare income API responses.

Run inside pipeline-scheduler container:
    python scripts/debug_income_response.py
"""

from __future__ import annotations

import os

from tushare_db.core.tushare_client import TushareClient

tushare = TushareClient(token=os.environ.get("TUSHARE_TOKEN", ""))

# Test a few combos
combos = [
    ("600519.SH", "20231231"),  # Known working
    ("000001.SZ", "20230331"),
    ("000002.SZ", "20230331"),
]

for ts_code, period in combos:
    print(f"\n=== {ts_code} {period} ===")
    try:
        resp = tushare.call("income", ts_code=ts_code, period=period)
        print(f"  resp type: {type(resp)}")
        print(f"  resp keys: {list(resp.keys()) if isinstance(resp, dict) else resp}")

        data = resp.get("data")
        print(f"  data type: {type(data)}")

        if isinstance(data, dict):
            fields = data.get("fields", [])
            items = data.get("items", [])
            print(f"  fields count: {len(fields)}")
            print(f"  fields (first 5): {fields[:5]}")
            print(f"  items type: {type(items)}")
            print(f"  items count: {len(items)}")
            if items:
                print(f"  items[0] type: {type(items[0])}")
                print(f"  items[0]: {items[0]}")
        elif isinstance(data, list):
            print(f"  data is list, len={len(data)}")
            print(f"  data[0]: {data[0]}")
        else:
            print(f"  data value: {data}")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")

tushare.close()
