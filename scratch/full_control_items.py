import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

ctrl = [it for it in d['items'] if it.get('module') == 'control']
for it in ctrl:
    print(f"=== {it['key']} (item {it['item']}) ===")
    print(it.get('text', ''))
