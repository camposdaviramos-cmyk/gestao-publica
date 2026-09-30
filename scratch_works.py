import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

works_items = [i for i in d['items'] if i['module'] == 'works']
print(f"Total works items: {len(works_items)}")
for i in works_items:
    print(f"{i['key']} [{i['status']}]: {i['text'][:120]}")
