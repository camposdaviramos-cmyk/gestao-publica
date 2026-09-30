import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

transp = [it for it in d['items'] if it.get('module') == 'transparency']
with open('docs/transparency_items.txt', 'w', encoding='utf-8') as out:
    for it in transp:
        out.write(f"[{it['key']}] (p. {it.get('page')}) -> {it['text']}\n")

print(f"Exported {len(transp)} items.")
