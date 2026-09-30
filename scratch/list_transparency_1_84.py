import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

transp = [it for it in d['items'] if it.get('module') == 'transparency']
for i, it in enumerate(transp[:84]):
    txt = it.get('text', '').replace('\n', ' ')
    print(f"[{it['key']}] Item {it.get('item')}: {txt[:100]}")
