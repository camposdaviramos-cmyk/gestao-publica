import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

fleet_items = [i for i in d['items'] if i['module'] == 'fleet']
print(f"Total fleet items: {len(fleet_items)}")
for i in fleet_items:
    print(f"Key: {i['key']}")
    print(f"  Item: {i['item']} | Page: {i['page']}")
    print(f"  Text: {i['text']}")
    print(f"  Status: {i['status']}")
    print(f"  Coverage: {i.get('coverage')}")
    print("-" * 50)
