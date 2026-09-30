import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

remaining = [x for x in d['items'] if x.get('status') != 'Implementado']
print(f"Total de itens restantes: {len(remaining)}")

with open('scratch/remaining_items.json', 'w', encoding='utf-8') as f:
    json.dump(remaining, f, indent=2, ensure_ascii=False)

with open('scratch/remaining_items.txt', 'w', encoding='utf-8') as f:
    for x in remaining:
        f.write(f"{x['key']} [{x.get('module')}] ({x.get('status')}): {x['text']}\n")

print("Salvo em scratch/remaining_items.json e scratch/remaining_items.txt")
