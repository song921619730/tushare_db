"""Audit fetch_strategy vs MCP inputParams. Run periodically and in CI."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = PROJECT_ROOT / "search-index.min.json"
INTERFACES_DIR = PROJECT_ROOT / "config" / "interfaces"

# Allowlist: APIs where strategy/param mismatch is intentional
KNOWN_OK: set[str] = set()


def load_mcp() -> dict[str, list[str]]:
    if not INDEX_PATH.exists():
        print(f"ERROR: search-index not found at {INDEX_PATH}")
        sys.exit(2)
    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return {
        item["name"]: [p for p in item.get("inputParams", []) if p not in ("limit", "offset")]
        for item in data["index"]
    }


def audit() -> int:
    mcp = load_mcp()
    bugs: list[str] = []
    warns: list[str] = []

    for f in sorted(INTERFACES_DIR.glob("*.yaml")):
        if f.name.startswith("_"):
            continue
        for doc in yaml.safe_load_all(f.read_text(encoding="utf-8")):
            if not doc or "name" not in doc:
                continue
            name = doc["name"]
            if name in KNOWN_OK or name not in mcp:
                continue
            strategy = doc.get("fetch_strategy", {}).get("kind", "")
            params = mcp[name]
            if strategy in ("period_loop", "per_symbol_period") and "period" not in params:
                bugs.append(f"BUG  {name}: strategy={strategy} but no 'period' param. {params}")
            if strategy == "date_loop" and "trade_date" not in params:
                warns.append(f"WARN {name}: date_loop but no 'trade_date'. {params}")
            if strategy == "monthly_window" and "month" not in params:
                warns.append(f"WARN {name}: monthly_window but no 'month'. {params}")

    for b in bugs:
        print(b)
    for w in warns:
        print(w)
    print(f"\n{len(bugs)} BUGs + {len(warns)} WARNs")
    return 1 if bugs else 0


if __name__ == "__main__":
    sys.exit(audit())
