"""Check sample data for missing-param interfaces."""
import json, os

sample_dir = os.path.join(os.path.dirname(__file__), 'data', 'samples')
interfaces = ['broker_recommend', 'cyq_chips', 'index_daily', 'pledge_detail',
              'stk_rewards', 'stk_week_month_adj', 'stk_weekly_monthly', 'fut_weekly_monthly']

for name in interfaces:
    path = os.path.join(sample_dir, f'{name}.json')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        fields = data.get('data', {}).get('fields', [])
        items = data.get('data', {}).get('items', [])
        print(f"\n=== {name} ===")
        print(f"  fields: {fields}")
        if items:
            print(f"  first item: {dict(zip(fields, items[0]))}")
        else:
            print(f"  items: EMPTY (count={data.get('data', {}).get('count', '?')})")
    else:
        print(f"\n=== {name} === NO SAMPLE FILE")
