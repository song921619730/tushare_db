# -*- coding: utf-8 -*-
"""Compare current YAML configs against @tushare/mcp search index.

Usage:
    python sync_config_from_mcp.py search-index.min.json [report|missing|optimize]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
INTERFACES_DIR = PROJECT_ROOT / "config" / "interfaces"

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_search_index(path: str) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {item["name"]: item for item in data["index"]}


def load_existing_configs() -> dict[str, dict]:
    configs = {}
    for yaml_file in sorted(INTERFACES_DIR.glob("*.yaml")):
        if yaml_file.name.startswith("_"):
            continue
        with open(yaml_file, encoding="utf-8") as f:
            docs = list(yaml.safe_load_all(f))
        for doc in docs:
            if doc and "name" in doc:
                configs[doc["name"]] = {
                    "file": yaml_file.name,
                    "config": doc,
                }
    return configs


def guess_strategy(item: dict) -> str:
    params = item.get("inputParams", [])
    name = item["name"]
    has_trade_date = "trade_date" in params
    has_start_end = "start_date" in params or "end_date" in params
    has_period = "period" in params
    has_ts_code = "ts_code" in params

    if not has_trade_date and not has_start_end and not has_period:
        if has_ts_code and "basic" in name:
            return "per_symbol"
        return "full_once"

    if "trade_date" in params and "start_date" not in params:
        return "date_loop"

    if has_period:
        return "period_loop"

    if has_ts_code and has_start_end and any(k in name for k in ("fina", "dividend", "forecast")):
        return "per_symbol_period"

    if "moneyflow" in name:
        return "offset_paging"

    if "month" in params:
        return "monthly_window"

    return "date_loop"


def guess_bucket(item: dict) -> str:
    name = item["name"]
    special = [
        "fut_", "opt_", "cb_", "bond_", "fund_",
        "margin", "pledge", "express", "forecast", "fina_",
        "moneyflow_", "ggt_", "hsgt_",
        "stk_factor", "stk_nineturn", "cyq_", "ccass_",
        "ths_", "kpl_", "dc_", "tdx_", "hm_",
    ]
    for p in special:
        if name.startswith(p) or p in name:
            return "special"
    return "normal"


def guess_batch(item: dict) -> str:
    name = item["name"]
    category = " > ".join(item.get("categoryPath", []))
    if any(k in category for k in ("参考数据", "基础数据", "交易日历")):
        return "reference"
    if any(k in name for k in ("fina_mainbz", "dividend")):
        return "saturday"
    if "财务数据" in category:
        return "D"
    if any(k in category for k in ("资金流向", "行情数据")):
        return "A"
    if any(k in category for k in ("打板", "两融")):
        return "B"
    return "A"


def guess_mode(item: dict) -> str:
    params = item.get("inputParams", [])
    has_date = any(p in params for p in ("trade_date", "start_date", "end_date", "period"))
    return "incremental" if has_date else "full"


def generate_yaml_entry(item: dict) -> dict:
    name = item["name"]
    params = item.get("inputParams", [])
    presets = item.get("presets", {})
    basic_fields = presets.get("basic", item.get("outputFields", [])[:12])
    order_by = "ts_code" if "ts_code" in params else "trade_date"
    strategy = guess_strategy(item)
    date_field = None
    if strategy == "date_loop":
        date_field = "trade_date"
    elif strategy == "period_loop":
        date_field = "end_date"

    strategy_cfg = {"kind": strategy}
    if date_field:
        strategy_cfg["date_field"] = date_field

    return {
        "name": name,
        "table": f"tushare_{name}",
        "enabled": False,
        "priority": "P2",
        "mode": guess_mode(item),
        "freq_bucket": guess_bucket(item),
        "start_date": "20200101",
        "fetch_strategy": strategy_cfg,
        "partition_key": "tuple()",
        "order_by": order_by,
        "required_params": [p for p in params if p not in ("limit", "offset")],
        "fields": basic_fields,
        "schema_overrides": {},
        "batch": guess_batch(item),
    }


def cmd_report(mcp_apis, existing):
    existing_names = set(existing)
    mcp_names = set(mcp_apis)

    missing = mcp_names - existing_names
    extra = existing_names - mcp_names
    common = existing_names & mcp_names

    print(f"{'='*60}")
    print(f"MCP index: {len(mcp_names)} APIs")
    print(f"Your configs: {len(existing_names)} APIs")
    print(f"Common: {len(common)} | Missing: {len(missing)} | Extra: {len(extra)}")
    print(f"{'='*60}")

    if extra:
        print(f"\n[EXTRA] In your YAML but not in MCP index ({len(extra)}):")
        for name in sorted(extra):
            print(f"  {name} ({existing[name]['file']})")

    if missing:
        print(f"\n[MISSING] In MCP but not in your config ({len(missing)}):")
        for name in sorted(missing):
            item = mcp_apis[name]
            cat = " > ".join(item.get("categoryPath", []))
            params_str = ", ".join(item["inputParams"][:5])
            print(f"  {name:32s} [{cat[:50]}] params: {params_str}")

    print(f"\n[OPTIMIZE] Existing configs with room for improvement ({len(common)}):")
    fix_count = 0
    for name in sorted(common):
        item = mcp_apis[name]
        cfg = existing[name]["config"]
        issues = []

        cfg_params = cfg.get("required_params") or []
        mcp_params = [p for p in item.get("inputParams", []) if p not in ("limit", "offset")]
        if not cfg_params and mcp_params:
            issues.append(f"required_params: [] -> {mcp_params[:6]}")

        cfg_fields = cfg.get("fields") or []
        preset = item.get("presets", {}).get("basic", [])
        if not cfg_fields and preset:
            issues.append(f"fields: [] -> basic preset ({len(preset)} cols)")

        suggested_bucket = guess_bucket(item)
        if cfg.get("freq_bucket") != suggested_bucket:
            issues.append(f"freq_bucket: {cfg.get('freq_bucket')} -> {suggested_bucket}")

        if issues:
            fix_count += 1
            print(f"  [{name}]")
            for issue in issues:
                print(f"    - {issue}")

    print(f"\nTotal: {fix_count} configs can be improved")


def cmd_missing(mcp_apis, existing):
    """Print missing APIs in YAML-entry format ready to paste."""
    existing_names = set(existing)
    mcp_names = set(mcp_apis)
    missing = sorted(mcp_names - existing_names)

    print(f"# {len(missing)} missing APIs ready for review\n")
    for name in missing:
        item = mcp_apis[name]
        entry = generate_yaml_entry(item)
        print("---")
        yaml.dump(entry, sys.stdout, allow_unicode=True, default_flow_style=False, sort_keys=False)


def cmd_optimize(mcp_apis, existing):
    """Show specific fixes for each common API."""
    existing_names = set(existing)
    common = sorted(existing_names & set(mcp_apis))

    for name in common:
        item = mcp_apis[name]
        cfg = existing[name]["config"]

        # Build optimized version
        mcp_params = [p for p in item.get("inputParams", []) if p not in ("limit", "offset")]
        preset = item.get("presets", {}).get("basic", [])
        optimized = dict(cfg)
        if mcp_params:
            optimized["required_params"] = mcp_params
        if preset:
            optimized["fields"] = preset

        if optimized != cfg:
            print(f"--- # {name} (optimized from MCP)")
            yaml.dump(optimized, sys.stdout, allow_unicode=True, default_flow_style=False, sort_keys=False)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    index_path = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else "report"

    mcp_apis = load_search_index(index_path)
    existing = load_existing_configs()

    if action == "report":
        cmd_report(mcp_apis, existing)
    elif action == "missing":
        cmd_missing(mcp_apis, existing)
    elif action == "optimize":
        cmd_optimize(mcp_apis, existing)
    else:
        print(f"Unknown action: {action}")
        print(__doc__)


if __name__ == "__main__":
    main()
