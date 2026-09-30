import json

items = json.load(open('scratch/finance_items.json', encoding='utf-8'))
print(f"Total finance items: {len(items)}")

with open('scratch/finance_detailed_list.txt', 'w', encoding='utf-8') as out:
    for idx, it in enumerate(items):
        key = it.get('key')
        item_num = it.get('item')
        status = it.get('status')
        text = it.get('text', '').strip()
        page = it.get('page')
        out.write(f"[{idx+1:03d}] {key} (Item {item_num}, Pág {page}, Status: {status}): {text}\n\n")
