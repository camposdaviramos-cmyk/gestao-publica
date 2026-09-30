import json
import re
from collections import defaultdict

with open('scratch/social_items.json', encoding='utf-8') as f:
    items = json.load(f)

print(f"Total social items: {len(items)}")

# Identify key words and themes
keywords = [
    'cras', 'creas', 'cadúnico', 'cadunico', 'família', 'familia', 'benefício', 'beneficio',
    'paif', 'paefi', 'scfv', 'atendimento', 'acolhimento', 'rma', 'prontuário', 'prontuario',
    'visita', 'encaminhamento', 'violência', 'violencia', 'criança', 'adolescente', 'idoso',
    'deficiência', 'deficiencia', 'gestante', 'alimentar', 'cesta', 'funeral', 'natalidade',
    'sigilo', 'sigiloso', 'lgpd', 'relatório', 'relatorio', 'mapa', 'território', 'territorio',
    'vulnerabilidade', 'bpc', 'bolsa família', 'bolsa familia', 'oficina', 'coletivo',
    'conselho', 'tutelar', 'sinase', 'medida', 'socioeducativa', 'abrigo', 'população de rua',
    'centro pop', 'abordagem', 'crachá', 'biometria', 'notificação'
]

matches = defaultdict(list)
for i in items:
    t = (i['text'] + ' ' + i.get('category', '')).lower()
    matched = False
    for kw in keywords:
        if kw in t:
            matches[kw].append(i['key'])
            matched = True

print("\n--- Distribuição por Palavras-Chave Principais ---")
for kw, keys in sorted(matches.items(), key=lambda x: len(x[1]), reverse=True)[:25]:
    print(f"{kw:20s}: {len(keys)} itens")
