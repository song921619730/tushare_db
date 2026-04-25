"""Schema inference from sampled Tushare API responses.

Pipeline: sample JSON (scripts/sample_api_responses.py) -> infer types -> build DDL.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

from tushare_db.schema.type_map import infer_ch_type

logger = structlog.get_logger()


def load_sample(sample_path: str | Path) -> tuple[list[str], list[dict[str, Any]]]:
    """Load a sample JSON file.

    Expected format (Tushare pro_api response):
    {
        "fields": ["ts_code", "trade_date", "open", ...],
        "items": [["000001.SZ", "20240101", 12.5, ...], ...]
    }

    Returns:
        (field_names, list_of_row_dicts)
    """
    path = Path(sample_path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Tushare pro_api wraps fields/items under "data"
    payload = data.get("data", data)
    fields = payload.get("fields", [])
    items = payload.get("items", [])

    rows = []
    for item in items:
        row = {}
        for i, field in enumerate(fields):
            row[field] = item[i] if i < len(item) else None
        rows.append(row)

    return fields, rows


def infer_schema(
    sample_path: str | Path,
    field_names: list[str] | None = None,
    overrides: dict[str, str] | None = None,
    max_sample_rows: int = 1000,
) -> list[tuple[str, str]]:
    """Infer ClickHouse column types from sampled API response.

    Args:
        sample_path: Path to sample JSON file.
        field_names: Override field order (from YAML spec). If None, use sample order.
        overrides: Field name -> ClickHouse type overrides from YAML schema_overrides.
        max_sample_rows: Limit samples for inference.

    Returns:
        List of (field_name, clickhouse_type) tuples.
    """
    _fields, rows = load_sample(sample_path)

    if field_names is None:
        field_names = _fields

    overrides = overrides or {}

    # Collect sample values per field
    sample_rows = rows[:max_sample_rows]
    schema = []
    for field in field_names:
        if field in overrides:
            schema.append((field, overrides[field]))
            continue

        values = [row.get(field) for row in sample_rows]
        ch_type = infer_ch_type(field, values)
        schema.append((field, ch_type))

    # Always append internal columns
    schema.append(("_version", "UInt64"))

    return schema


def infer_schemas_batch(
    sample_dir: str | Path,
    interface_fields: dict[str, tuple[list[str] | None, dict[str, str] | None]],
) -> dict[str, list[tuple[str, str]]]:
    """Infer schemas for multiple interfaces at once.

    Args:
        sample_dir: Directory containing sample JSON files.
        interface_fields: {interface_name: (field_names, overrides)}.

    Returns:
        {interface_name: [(field, type), ...]}
    """
    dir_path = Path(sample_dir)
    results: dict[str, list[tuple[str, str]]] = {}

    for interface, (field_names, overrides) in interface_fields.items():
        sample_file = dir_path / f"{interface}.json"
        if not sample_file.exists():
            logger.warning("No sample found", interface=interface, path=str(sample_file))
            continue

        schema = infer_schema(sample_file, field_names=field_names, overrides=overrides)
        results[interface] = schema
        logger.info("Schema inferred", interface=interface, columns=len(schema))

    return results
