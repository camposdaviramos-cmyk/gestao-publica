import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

people = [it for it in d['items'] if it.get('module') == 'people']
print(f"Total people items: {len(people)}")

status_map = {}
for it in people:
    st = it.get('status', 'unknown')
    status_map[st] = status_map.get(st, 0) + 1
print("Status breakdown:", status_map)

for it in people[:25]:
    txt = it.get('text', '').replace('\n', ' ')
    print(f"[{it['key']}] Item {it.get('item')} ({it.get('status')}): {txt[:90]}")
