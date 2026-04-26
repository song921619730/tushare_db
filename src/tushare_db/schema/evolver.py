"""Schema evolution: safely add columns to existing ClickHouse tables.

Only ADD COLUMN is supported natively. RENAME COLUMN and CHANGE TYPE
use a shadow-table pattern (CREATE → INSERT → RENAME → DROP) for safety.
"""

from __future__ import annotations

import re

import clickhouse_connect.driver
import structlog

from tushare_db.runner.worker import invalidate_column_cache

logger = structlog.get_logger()

_IDENT_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def _validate_ident(name: str, kind: str = "identifier") -> str:
    """Validate a ClickHouse identifier to prevent DDL injection."""
    if not _IDENT_RE.match(name):
        raise ValueError(f"Invalid {kind}: {name!r}")
    return name


def get_existing_columns(
    client: clickhouse_connect.driver.Client,
    database: str,
    table: str,
) -> set[str]:
    """Get the set of existing column names for a table."""
    database = _validate_ident(database, "database")
    table = _validate_ident(table, "table")
    result = client.command(
        f"SELECT name FROM system.columns WHERE database = '{database}' AND table = '{table}'"
    )
    if not result:
        return set()
    return set(result.strip().split("\n"))


def evolve_schema(
    client: clickhouse_connect.driver.Client,
    database: str,
    table: str,
    desired_columns: list[tuple[str, str]],
) -> list[str]:
    """ADD COLUMN for any columns that don't exist yet.

    Args:
        client: ClickHouse client.
        database: Database name.
        table: Table name.
        desired_columns: List of (column_name, type) pairs.

    Returns:
        List of ALTER statements that were executed.
    """
    database = _validate_ident(database, "database")
    table = _validate_ident(table, "table")
    existing = get_existing_columns(client, database, table)
    alterations: list[str] = []

    for col_name, col_type in desired_columns:
        col_name = _validate_ident(col_name, "column")
        if col_name not in existing:
            alter = f"ALTER TABLE {database}.{table} ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
            client.command(alter)
            alterations.append(alter)
            logger.info("Column added", table=table, column=col_name, type=col_type)

    if alterations:
        logger.info("Schema evolved", table=table, added=len(alterations))
    else:
        logger.debug("Schema up to date", table=table)

    return alterations


def rename_column(
    client: clickhouse_connect.driver.Client,
    database: str,
    table: str,
    old_name: str,
    new_name: str,
) -> None:
    """Rename a column using shadow-table pattern.

    Steps:
    1. CREATE TABLE {table}_new AS {table}
    2. ALTER TABLE {table}_new RENAME COLUMN {old} TO {new}
    3. INSERT INTO {table}_new SELECT * FROM {table}
    4. RENAME {table} → {table}_old, {table}_new → {table}
    5. DROP TABLE {table}_old

    Args:
        client: ClickHouse client.
        database: Database name.
        table: Table name (without database prefix).
        old_name: Current column name.
        new_name: New column name.
    """
    database = _validate_ident(database, "database")
    table = _validate_ident(table, "table")
    old_name = _validate_ident(old_name, "old column")
    new_name = _validate_ident(new_name, "new column")
    full = f"{database}.{table}"
    shadow = f"{full}_new"
    old = f"{full}_old"

    logger.info("Renaming column via shadow table", table=full, old=old_name, new=new_name)

    try:
        # 1. Create shadow table identical to current
        client.command(f"CREATE TABLE IF NOT EXISTS {shadow} AS {full}")

        # 2. Rename column in shadow table
        client.command(
            f"ALTER TABLE {shadow} RENAME COLUMN {old_name} TO {new_name}"
        )

        # 3. Copy data
        client.command(
            f"INSERT INTO {shadow} SELECT * FROM {full}"
        )

        # 4. Atomic swap
        client.command(
            f"RENAME TABLE {full} TO {old}, {shadow} TO {full}"
        )

        # 5. Drop old table
        client.command(f"DROP TABLE IF EXISTS {old}")

        logger.info("Column renamed", table=full, old=old_name, new=new_name)
    except Exception:
        # Cleanup shadow on failure
        client.command(f"DROP TABLE IF EXISTS {shadow}")
        raise
    finally:
        invalidate_column_cache(database=database, table=table)


def change_type(
    client: clickhouse_connect.driver.Client,
    database: str,
    table: str,
    column: str,
    new_type: str,
) -> None:
    """Change a column type using shadow-table pattern.

    Steps:
    1. CREATE TABLE {table}_new AS {table}
    2. ALTER TABLE {table}_new MODIFY COLUMN {col} {new_type}
    3. INSERT INTO {table}_new SELECT * FROM {table}
    4. RENAME {table} → {table}_old, {table}_new → {table}
    5. DROP TABLE {table}_old

    Args:
        client: ClickHouse client.
        database: Database name.
        table: Table name (without database prefix).
        column: Column name to change.
        new_type: New ClickHouse type (e.g., "Decimal64(4)").
    """
    database = _validate_ident(database, "database")
    table = _validate_ident(table, "table")
    column = _validate_ident(column, "column")
    full = f"{database}.{table}"
    shadow = f"{full}_new"
    old = f"{full}_old"

    logger.info("Changing column type via shadow table", table=full, column=column, new_type=new_type)

    try:
        # 1. Create shadow table identical to current
        client.command(f"CREATE TABLE IF NOT EXISTS {shadow} AS {full}")

        # 2. Modify column type in shadow table
        client.command(
            f"ALTER TABLE {shadow} MODIFY COLUMN {column} {new_type}"
        )

        # 3. Copy data (ClickHouse will cast values)
        client.command(
            f"INSERT INTO {shadow} SELECT * FROM {full}"
        )

        # 4. Atomic swap
        client.command(
            f"RENAME TABLE {full} TO {old}, {shadow} TO {full}"
        )

        # 5. Drop old table
        client.command(f"DROP TABLE IF EXISTS {old}")

        logger.info("Column type changed", table=full, column=column, new_type=new_type)
    except Exception:
        # Cleanup shadow on failure
        client.command(f"DROP TABLE IF EXISTS {shadow}")
        raise
    finally:
        invalidate_column_cache(database=database, table=table)


def evolve_schema_full(
    client: clickhouse_connect.driver.Client,
    database: str,
    table: str,
    desired_columns: list[tuple[str, str]],
    rename_map: dict[str, str] | None = None,
    type_changes: dict[str, str] | None = None,
) -> dict[str, list[str]]:
    """Full schema evolution: ADD COLUMN + RENAME + CHANGE TYPE.

    Order of operations:
    1. Rename columns first (shadow table)
    2. Change types (shadow table)
    3. Add new columns (lightweight ALTER)

    Args:
        client: ClickHouse client.
        database: Database name.
        table: Table name.
        desired_columns: List of (column_name, type) pairs.
        rename_map: {old_name: new_name} mappings.
        type_changes: {column_name: new_type} mappings.

    Returns:
        Dict of operation type → list of executed statements.
    """
    result: dict[str, list[str]] = {
        "renames": [],
        "type_changes": [],
        "add_columns": [],
    }

    # Step 1: Renames
    for old_name, new_name in (rename_map or {}).items():
        rename_column(client, database, table, old_name, new_name)
        result["renames"].append(f"{old_name} → {new_name}")

    # Step 2: Type changes
    for col_name, new_type in (type_changes or {}).items():
        change_type(client, database, table, col_name, new_type)
        result["type_changes"].append(f"{col_name} → {new_type}")

    # Step 3: Add new columns
    adds = evolve_schema(client, database, table, desired_columns)
    result["add_columns"] = adds

    return result
