"""Extract ClickHouse table schemas and generate interface field catalogs."""

import os
import json
import subprocess
import yaml
from pathlib import Path

CH_CONTAINER = "tushare_db-clickhouse-1"
CATALOG_DIR = Path(__file__).parent.parent / "docs" / "catalog"

# Load interface configs to map table names to interface metadata
def load_interface_configs() -> dict:
    """Map table_name -> interface config."""
    result = {}
    config_dir = Path(__file__).parent.parent / "config" / "interfaces"
    for yaml_file in sorted(config_dir.glob("*.yaml")):
        with open(yaml_file, "r", encoding="utf-8") as f:
            content = f.read()
        for doc in yaml.safe_load_all(content):
            if doc and doc.get("table"):
                result[doc["table"]] = doc
    return result

def run_clickhouse_query(sql: str) -> list:
    """Run a ClickHouse query and return rows."""
    cmd = [
        "docker", "exec", CH_CONTAINER,
        "clickhouse-client",
        "--query", sql,
        "--format", "JSON",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"ClickHouse error: {result.stderr}")
    return json.loads(result.stdout).get("data", [])

def get_all_tables(database: str) -> list:
    """Get list of tables in a database."""
    rows = run_clickhouse_query(
        f"SELECT name FROM system.tables WHERE database = '{database}' ORDER BY name"
    )
    return [r["name"] for r in rows]

def get_table_schema(database: str, table: str) -> list:
    """Get column info for a table."""
    rows = run_clickhouse_query(
        f"SELECT name, type, comment FROM system.columns "
        f"WHERE database = '{database}' AND table = '{table}' ORDER BY position"
    )
    return rows

def get_table_row_count(database: str, table: str) -> int:
    """Get row count for a table."""
    try:
        rows = run_clickhouse_query(
            f"SELECT count() as cnt FROM {database}.{table}"
        )
        return int(rows[0]["cnt"]) if rows else 0
    except Exception:
        return -1

def get_table_comment(database: str, table: str) -> str:
    """Get table comment/description."""
    rows = run_clickhouse_query(
        f"SELECT comment FROM system.tables WHERE database = '{database}' AND name = '{table}'"
    )
    return rows[0]["comment"] if rows else ""

def categorize_field(name: str, field_type: str) -> str:
    """Guess field category based on name."""
    n = name.lower()
    if "code" in n or "ts_code" == n:
        return "标识"
    if "date" in n or n in ("ann_date", "end_date", "trade_date"):
        return "日期"
    if "yoy" in n:
        return "增长率/同比"
    if "pe" == n or "pb" == n or "ps" == n or "dv" in n:
        return "估值指标"
    if "macd" in n or "kdj" in n or "rsi" in n or "boll" in n or "ma_" in n or "ema" in n:
        return "技术指标"
    if n in ("vol", "amount", "turnover_rate", "volume_ratio", "volume"):
        return "成交量/额"
    if "mv" in n or "share" in n or "float" in n or "total" in n:
        return "股本/市值"
    if "roe" in n or "roa" in n or "roic" in n or "npta" in n:
        return "回报指标"
    if "margin" in n or "ratio" in n:
        return "比率/率"
    return "数值"

def generate_table_catalog(table: str, database: str, schema: list, row_count: int,
                           table_comment: str, iface_config: dict | None) -> str:
    """Generate markdown catalog for a single table."""
    lines = []

    # Header
    iface_name = table.replace("tushare_", "")
    lines.append(f"# {iface_name}")
    lines.append("")

    # Interface config info
    if iface_config:
        lines.append(f"## 接口信息")
        lines.append("")
        lines.append(f"| 属性 | 值 |")
        lines.append(f"|------|-----|")
        lines.append(f"| 接口名称 | {iface_config.get('name', '')} |")
        lines.append(f"| 表名 | `{table}` |")
        lines.append(f"| 优先级 | {iface_config.get('priority', 'N/A')} |")
        lines.append(f"| 模式 | {iface_config.get('mode', 'N/A')} |")
        lines.append(f"| 频率分桶 | {iface_config.get('freq_bucket', 'N/A')} |")
        batch = iface_config.get('batch', 'N/A')
        lines.append(f"| 批次 | {batch} |")
        strategy = iface_config.get('fetch_strategy', {})
        lines.append(f"| 采集策略 | {strategy.get('kind', 'N/A')} |")
        if strategy.get('date_field'):
            lines.append(f"| 日期字段 | {strategy['date_field']} |")
        lines.append(f"| 排序键 | {iface_config.get('order_by', 'N/A')} |")
        lines.append(f"| 分区键 | {iface_config.get('partition_key', 'N/A')} |")
        if iface_config.get('start_date'):
            lines.append(f"| 起始日期 | {iface_config['start_date']} |")
        lines.append("")

    # Table info
    lines.append(f"## 数据概览")
    lines.append("")
    lines.append(f"| 属性 | 值 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 数据库 | {database} |")
    lines.append(f"| 行数 | {row_count:,} |")
    if table_comment:
        lines.append(f"| 说明 | {table_comment} |")
    lines.append("")

    # Fields grouped by category
    categories = {}
    for col in schema:
        cat = categorize_field(col["name"], col["type"])
        categories.setdefault(cat, []).append(col)

    lines.append(f"## 字段列表 ({len(schema)} 个字段)")
    lines.append("")

    # Show grouped fields
    for cat in ["标识", "日期", "技术指标", "估值指标", "回报指标", "增长率/同比",
                "成交量/额", "股本/市值", "比率/率", "数值"]:
        cols = categories.get(cat)
        if not cols:
            continue
        lines.append(f"### {cat} ({len(cols)}个)")
        lines.append("")
        lines.append(f"| # | 字段名 | 类型 | 说明 |")
        lines.append(f"|---|--------|------|------|")
        for i, col in enumerate(cols, 1):
            comment = col.get("comment", "") or ""
            lines.append(f"| {i} | `{col['name']}` | {col['type']} | {comment} |")
        lines.append("")

    # Other categories not in the predefined list
    for cat, cols in categories.items():
        if cat not in ["标识", "日期", "技术指标", "估值指标", "回报指标", "增长率/同比",
                       "成交量/额", "股本/市值", "比率/率", "数值"]:
            lines.append(f"### {cat} ({len(cols)}个)")
            lines.append("")
            lines.append(f"| # | 字段名 | 类型 | 说明 |")
            lines.append(f"|---|--------|------|------|")
            for i, col in enumerate(cols, 1):
                comment = col.get("comment", "") or ""
                lines.append(f"| {i} | `{col['name']}` | {col['type']} | {comment} |")
            lines.append("")

    return "\n".join(lines)

def generate_master_index(all_tables: dict) -> str:
    """Generate master index of all tables."""
    lines = []
    lines.append("# 接口字段目录总览")
    lines.append("")
    lines.append(f"共 **{sum(len(v) for v in all_tables.values())}** 张表，"
                 f"分布在 **{len(all_tables)}** 个数据库中。")
    lines.append("")

    for database, tables in all_tables.items():
        lines.append(f"## {database} ({len(tables)} 张表)")
        lines.append("")
        lines.append("| 接口 | 表名 | 字段数 | 行数 | 批次 | 优先级 | 文件 |")
        lines.append("|------|------|--------|------|------|--------|------|")

        for tname, info in tables.items():
            iface_name = tname.replace("tushare_", "")
            schema = info["schema"]
            row_count = info["row_count"]
            config = info.get("config")

            batch = config.get("batch", "-") if config else "-"
            priority = config.get("priority", "-") if config else "-"
            enabled = config.get("enabled", True) if config else True
            enabled_mark = "" if enabled else "⚠️ 已禁用"

            file_link = f"[查看](interfaces/{tname}.md)"

            lines.append(
                f"| {iface_name} | `{tname}` | {len(schema)} | {row_count:,} | "
                f"{batch} | {priority} {enabled_mark} | {file_link} |"
            )
        lines.append("")

    return "\n".join(lines)

def main():
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    (CATALOG_DIR / "interfaces").mkdir(exist_ok=True)

    iface_configs = load_interface_configs()

    all_tables = {}
    databases = ["_meta", "tushare"]

    for db in databases:
        print(f"\nProcessing database: {db}")
        tables = get_all_tables(db)
        all_tables[db] = {}

        for i, table in enumerate(tables):
            if (i + 1) % 20 == 0:
                print(f"  {i+1}/{len(tables)}: {table}")
            else:
                print(f"  {i+1}/{len(tables)}: {table}", end="\r")

            schema = get_table_schema(db, table)
            row_count = get_table_row_count(db, table)
            table_comment = get_table_comment(db, table)
            config = iface_configs.get(table)

            all_tables[db][table] = {
                "schema": schema,
                "row_count": row_count,
                "table_comment": table_comment,
                "config": config,
            }

            # Generate per-table catalog
            md = generate_table_catalog(table, db, schema, row_count, table_comment, config)
            outfile = CATALOG_DIR / "interfaces" / f"{table}.md"
            with open(outfile, "w", encoding="utf-8") as f:
                f.write(md)

        print(f"\n  Done: {len(tables)} tables in {db}")

    # Generate master index
    print("\nGenerating master index...")
    master_md = generate_master_index(all_tables)
    with open(CATALOG_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write(master_md)

    # Summary stats
    total_tables = sum(len(v) for v in all_tables.values())
    total_fields = sum(
        len(info["schema"])
        for db_tables in all_tables.values()
        for info in db_tables.values()
    )
    print(f"\nDone! Generated {total_tables} table catalogs with {total_fields} total fields.")
    print(f"Master index: {CATALOG_DIR / 'README.md'}")

if __name__ == "__main__":
    main()
