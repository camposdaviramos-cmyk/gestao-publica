import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

proc_items = [i for i in d['items'] if i.get('module') == 'procurement']
print(f"Total procurement items: {len(proc_items)}")

status_count = {}
for i in proc_items:
    st = i.get('status')
    status_count[st] = status_count.get(st, 0) + 1
print("Status count:", status_count)

for i in proc_items:
    print(f"{i['key']} [{i['status']}]: {i['text']}")
