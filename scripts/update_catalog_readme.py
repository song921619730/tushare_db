"""Update catalog README with ALL known interfaces (including missing ones)."""

import json
import subprocess
import re
import yaml
from pathlib import Path

CH_CONTAINER = "tushare_db-clickhouse-1"
CATALOG_DIR = Path(__file__).parent.parent / "docs" / "catalog"
DOCS_FILE = Path(__file__).parent.parent / "tushare_10k_interfaces.md"
CONFIG_DIR = Path(__file__).parent.parent / "config" / "interfaces"

# Category names from the docs file
CATEGORIES = {
    "bonds": ("bonds", "债券数据"),
    "etf": ("etf", "ETF/基金数据"),
    "forex": ("forex", "外汇数据"),
    "fund": ("fund", "公募基金数据"),
    "futures": ("futures", "期货数据"),
    "index": ("index", "指数数据"),
    "macro": ("macro", "宏观经济数据"),
    "options": ("options", "期权数据"),
    "spot": ("spot", "现货数据"),
    "stock_basic": ("stock_basic", "股票基础信息"),
    "stock_daily": ("stock_daily", "股票行情数据"),
    "stock_financial": ("stock_financial", "财务数据"),
    "stock_limit_board": ("stock_limit_board", "涨跌板/板块数据"),
    "stock_moneyflow": ("stock_moneyflow", "资金流向"),
    "stock_reference": ("stock_reference", "融资融券/质押/大宗交易等参考数据"),
    "stock_special": ("stock_special", "特色数据"),
    "tmt": ("tmt", "文娱产业数据"),
    "wealth": ("wealth", "财富销售数据"),
}

def run_clickhouse(sql: str) -> list:
    cmd = ["docker", "exec", CH_CONTAINER, "clickhouse-client", "--query", sql, "--format", "JSON"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return []
    return json.loads(result.stdout).get("data", [])

def get_db_tables() -> set:
    rows = run_clickhouse("SELECT name FROM system.tables WHERE database = 'tushare'")
    return {r["name"] for r in rows}

def get_row_counts() -> dict:
    rows = run_clickhouse(
        "SELECT name, total_rows FROM system.tables WHERE database = 'tushare' ORDER BY name"
    )
    return {r["name"]: int(r["total_rows"]) for r in rows}

def get_field_counts() -> dict:
    rows = run_clickhouse(
        "SELECT table, count() as cnt FROM system.columns WHERE database = 'tushare' GROUP BY table"
    )
    return {r["table"]: int(r["cnt"]) for r in rows}

def load_configs() -> dict:
    result = {}
    for yaml_file in sorted(CONFIG_DIR.glob("*.yaml")):
        with open(yaml_file, "r", encoding="utf-8") as f:
            content = f.read()
        for doc in yaml.safe_load_all(content):
            if doc and doc.get("table"):
                result[doc["table"]] = doc
    return result

def parse_docs() -> dict:
    """Parse tushare_10k_interfaces.md to extract all interface info by category."""
    text = DOCS_FILE.read_text(encoding="utf-8")
    interfaces = {}

    # Parse available interfaces from markdown tables
    current_category = None
    for line in text.split("\n"):
        # Match category headers like "### bonds -- 债券数据（15 个接口）"
        cat_match = re.match(r"### (\w+) -- (.+?)（", line)
        if cat_match:
            current_category = cat_match.group(1)
            continue

        # Match table rows: | interface | table | priority | mode | freq | ... |
        row_match = re.match(
            r"\|\s*(\w+)\s*\|\s*(tushare_\w+)\s*\|\s*(P\d)\s*\|\s*(\w+)\s*\|\s*(\w+)\s*\|",
            line
        )
        if row_match and current_category:
            interfaces[row_match.group(2)] = {
                "api_name": row_match.group(1),
                "table": row_match.group(2),
                "priority": row_match.group(3),
                "mode": row_match.group(4),
                "freq": row_match.group(5),
                "category": current_category,
                "paid": False,
            }

    # Parse paid interfaces: **api_name** -> table_name
    for m in re.finditer(r"\*\*(\w+)\*\*\s*->\s*(tushare_\w+)", text):
        api_name = m.group(1)
        table = m.group(2)
        # Guess category from context (scan backwards)
        pos = m.start()
        cat = "unknown"
        for cat_key, (cat_id, cat_name) in CATEGORIES.items():
            if cat_id in text[max(0, pos-500):pos]:
                cat = cat_key
                break
        interfaces[table] = {
            "api_name": api_name,
            "table": table,
            "priority": "P3",
            "mode": "N/A",
            "freq": "special",
            "category": cat,
            "paid": True,
        }

    return interfaces

def generate_updated_readme():
    db_tables = get_db_tables()
    row_counts = get_row_counts()
    field_counts = get_field_counts()
    configs = load_configs()
    doc_interfaces = parse_docs()

    # All known interfaces = doc_interfaces ∪ configs
    all_tables = set(doc_interfaces.keys()) | set(configs.keys())
    business_tables = {t for t in all_tables if t.startswith("tushare_")}

    in_db = business_tables & db_tables
    missing = business_tables - db_tables

    lines = []
    lines.append("# 接口字段目录总览")
    lines.append("")
    lines.append(f"共 **{len(all_tables)}** 个已知接口，"
                 f"**{len(in_db)}** 个已入库，**{len(missing)}** 个未入库，"
                 f"**{sum(field_counts.get(t, 0) for t in in_db):,}** 个字段。")
    lines.append("")

    # Group by category
    by_category = {}
    for table in sorted(business_tables):
        info = doc_interfaces.get(table, {})
        cat = info.get("category", "other")
        cat_name = CATEGORIES.get(cat, ("other", "其他"))[1]
        by_category.setdefault((cat, cat_name), []).append((table, info))

    for (cat_id, cat_name), tables in sorted(by_category.items(), key=lambda x: x[0]):
        lines.append(f"## {cat_name} ({len(tables)} 个接口)")
        lines.append("")
        lines.append("| 接口 | 表名 | 状态 | 字段数 | 行数 | 批次 | 优先级 | 文件 |")
        lines.append("|------|------|------|--------|------|------|--------|------|")

        for table, info in tables:
            iface_name = info.get("api_name", table.replace("tushare_", ""))
            in_db_status = "✅ 已入库" if table in db_tables else "❌ 未入库"
            fields = field_counts.get(table, "-")
            rows = row_counts.get(table, "-")
            if isinstance(rows, int):
                rows = f"{rows:,}"

            config = configs.get(table, {})
            batch = config.get("batch", info.get("freq", "-"))
            priority = config.get("priority", info.get("priority", "-"))
            enabled = config.get("enabled", True)
            if not enabled:
                batch = f"⚠️ {batch}"

            paid_tag = " 💰付费" if info.get("paid") else ""

            if table in db_tables:
                file_link = f"[查看](interfaces/{table}.md)"
            else:
                file_link = "-"

            lines.append(
                f"| {iface_name}{paid_tag} | `{table}` | {in_db_status} | "
                f"{fields} | {rows} | {batch} | {priority} | {file_link} |"
            )
        lines.append("")

    # Summary stats
    lines.append("## 统计摘要")
    lines.append("")
    lines.append(f"- 已入库: {len(in_db)} 个接口")
    lines.append(f"- 未入库(已配置): {len(missing & set(configs.keys()))} 个接口")
    lines.append(f"- 未入库(付费/未配置): {len(missing - set(configs.keys()))} 个接口")
    lines.append("")

    # Show missing tables in detail
    lines.append("## 未入库接口明细")
    lines.append("")
    for table, info in sorted(doc_interfaces.items()):
        if table in db_tables:
            continue
        if not table.startswith("tushare_"):
            continue
        config = configs.get(table, {})
        paid_tag = " 💰付费" if info.get("paid") else ""
        enabled = config.get("enabled", "未配置")
        if enabled is False:
            enabled = "已禁用"
        elif enabled is True:
            enabled = "已启用"
        else:
            enabled = "未配置"
        cat_name = CATEGORIES.get(info.get("category", "other"), ("", "其他"))[1]
        lines.append(
            f"- **{info['api_name']}** (`{table}`) — {cat_name} | "
            f"状态: {enabled}{paid_tag} | 优先级: {info.get('priority', '-')} | "
            f"模式: {info.get('mode', '-')} | 频率: {info.get('freq', '-')}"
        )
    lines.append("")

    outfile = CATALOG_DIR / "README.md"
    with open(outfile, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Updated: {outfile}")
    print(f"  Total interfaces: {len(all_tables)}")
    print(f"  In DB: {len(in_db)}")
    print(f"  Missing: {len(missing)}")

if __name__ == "__main__":
    generate_updated_readme()
