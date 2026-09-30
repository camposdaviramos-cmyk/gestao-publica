import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

mod_counts = {}
for it in d['items']:
    m = it.get('module', 'unknown')
    st = it.get('status', 'unknown')
    if m not in mod_counts:
        mod_counts[m] = {'total': 0, 'Implementado': 0, 'Parcial': 0, 'Nao implementado': 0, 'Dependencia': 0}
    mod_counts[m]['total'] += 1
    if st == 'Implementado':
        mod_counts[m]['Implementado'] += 1
    elif st == 'Parcial':
        mod_counts[m]['Parcial'] += 1
    elif 'Depend' in st:
        mod_counts[m]['Dependencia'] += 1
    else:
        mod_counts[m]['Nao implementado'] += 1

print(f"{'Module':<20} | {'Total':<6} | {'Imp':<6} | {'Parcial':<8} | {'NaoImp':<8} | {'Dep':<6}")
print('-'*65)
for m, c in sorted(mod_counts.items(), key=lambda x: -x[1]['total']):
    print(f"{m:<20} | {c['total']:>5}  | {c['Implementado']:>5}  | {c['Parcial']:>7}  | {c['Nao implementado']:>7}  | {c['Dependencia']:>5}")
