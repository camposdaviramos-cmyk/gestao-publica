import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

transp = [it for it in d['items'] if it.get('module') == 'transparency']
print(f"Total transparency items: {len(transp)}")

for it in transp:
    print(f"[{it['key']}] (Page {it.get('page')}) -> {it['text']}")
