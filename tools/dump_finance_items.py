import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

finance_items = [it for it in d['items'] if it.get('module') == 'finance']

with open('scratch/finance_items.json', 'w', encoding='utf-8') as f:
    json.dump(finance_items, f, indent=2, ensure_ascii=False)

with open('scratch/finance_items.txt', 'w', encoding='utf-8') as f:
    for it in finance_items:
        f.write(f"[{it['key']}] Item {it['item']} (Status: {it.get('status')} | Pag. {it.get('page')}): {it['text']}\n\n")

print(f"Dumped {len(finance_items)} finance items.")
