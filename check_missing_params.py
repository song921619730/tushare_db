"""Check interface specs for missing required parameters."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

from tushare_db.config.loader import load_interface_specs

interfaces_to_check = [
    'broker_recommend', 'cyq_chips', 'index_daily', 'pledge_detail',
    'stk_rewards', 'stk_week_month_adj', 'stk_weekly_monthly',
    'fut_weekly_monthly',
]

specs = {s.name: s for s in load_interface_specs()}

for name in interfaces_to_check:
    if name in specs:
        spec = specs[name]
        print(f"\n=== {name} ===")
        print(f"  api_name: {spec.api_name}")
        print(f"  fetch_strategy: {spec.fetch_strategy}")
        print(f"  required_params: {spec.required_params}")
        print(f"  fields: {spec.fields}")
        print(f"  order_by: {spec.order_by}")
    else:
        print(f"\n=== {name} === NOT FOUND in specs")
