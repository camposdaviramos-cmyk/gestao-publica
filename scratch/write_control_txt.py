import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

ctrl = [it for it in d['items'] if it.get('module') == 'control']
with open('scratch/control_items_utf8.txt', 'w', encoding='utf-8') as out:
    for it in ctrl:
        out.write(f"=== {it['key']} (item {it['item']}) ===\n")
        out.write(f"{it.get('text', '')}\n\n")

print(f"Written {len(ctrl)} items to scratch/control_items_utf8.txt")
