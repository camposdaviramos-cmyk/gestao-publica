import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

people_items = [it for it in d['items'] if it.get('module') == 'people']
with open('scratch/people_items.txt', 'w', encoding='utf-8') as out:
    for it in people_items:
        out.write(f"=== {it['key']} (item {it['item']}) [{it.get('status')}] ===\n")
        out.write(f"{it.get('text', '')}\n\n")

print(f"Dumped {len(people_items)} people items to scratch/people_items.txt")
