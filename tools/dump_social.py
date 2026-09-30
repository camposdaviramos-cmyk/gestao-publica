import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

items = [i for i in d['items'] if i['module'] == 'social']
with open('scratch/social_items.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, indent=2, ensure_ascii=False)

with open('scratch/social_detailed_list.txt', 'w', encoding='utf-8') as f:
    for i in items:
        f.write(f"{i['key']} (Status: {i['status']}): {i['text']}\n")

print(f"Total social items: {len(items)}")
statuses = {}
for i in items:
    statuses[i['status']] = statuses.get(i['status'], 0) + 1
print(f"Statuses: {statuses}")
