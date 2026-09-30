import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

for mod in ['works', 'procurement', 'fleet']:
    items = [i for i in d['items'] if i['module'] == mod]
    print(f"=== Module: {mod} ({len(items)} items) ===")
    for i in items[:15]:
        print(f"  {i['key']} [{i['status']}]: {i['text'][:90]}")
