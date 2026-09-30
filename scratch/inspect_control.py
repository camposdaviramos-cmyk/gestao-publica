import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

ctrl = [it for it in d['items'] if it.get('module') == 'control']
for it in ctrl[:30]:
    txt = it.get('text', '').replace('\n', ' ')
    print(f"[{it['key']}] Item {it.get('item')} ({it.get('status')}): {txt[:100]}")
