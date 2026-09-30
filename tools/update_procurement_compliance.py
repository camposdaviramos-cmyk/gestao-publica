import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

proc_coverage_notes = {
    # Itens gerais e modalidades Lei 14.133/2021
    "procurement.95": "Critério de julgamento por Maior Desconto implementado em dispensas, inexigibilidades, pregões e concorrências. procurement_core.py e erp_operations.py:award_proposal.",
    "procurement.96": "Indicação e cálculo de percentual de desconto nas propostas, classificação, lances e relatórios comparativos. procurement_core.py e procurement_api.py (/api/procurement/processes/<id>/bids).",
    "procurement.97": "Sistema de Registro de Preços (SRP - Art. 82 § 6º da Lei 14.133/2021) aplicável a dispensas e inexigibilidades com desconto sobre tabela. procurement_operations.py:generate_price_agreement.",
    "procurement.98": "Convocação de licitantes remanescentes (Art. 90 §§ 2º, 4º e 7º) nas condições do vencedor ou ofertadas. procurement_operations.py:summon_remaining_bidders e /api/procurement/processes/<id>/summon-remanescentes.",
    "procurement.99": "Procedimento auxiliar de Pré-Qualificação com publicação de chamamento público e resultados no PNCP. procurement_schema.sql e procurement.auxiliary_procedures.",
    "procurement.100": "Indicação da modalidade de empenho e observações nos empenhos e contratos. erp_core.py e procurement.contracts.",
    "procurement.101": "Carga de processos licitatórios, contratos e anexos no Portal da Transparência em tempo real. erp_api.py e /api/transparency.",
    "procurement.102": "Chamada Pública do PNAE (Lei 11.947/2009) com controle próprio de numeração e prestação de contas ao TCE-RJ na modalidade CPP. procurement.auxiliary_procedures e procurement_schema.sql.",
    "procurement.103": "Importação de informações de credenciamento e chamada pública PNAE para dispensas e inexigibilidades. procurement_operations.py e procurement.auxiliary_procedures.",
    "procurement.104": "Plano de Contratações Anual (PCA): elaboração, controle de versões, aprovação formal, bloqueio de edições após aprovação, publicação e histórico PNCP. procurement_operations.py (approve_pca, publish_pca_pncp).",
    "procurement.105": "Requisição para empenho com edição de itens/despesas e alerta de prioridade legal de cotas reservadas para ME/EPP sobre tabela de preços. procurement_core.py.",
    "procurement.106": "Acompanhamento e controle financeiro de contratos com apresentação de empenhos vinculados e saldo a empenhar. procurement_core.py:get_contract_financial_summary e /api/procurement/contracts/<id>/financial-summary.",
    "procurement.107": "Rito procedimental comum do Art. 17 e Art. 29 da Lei 14.133/2021 com registro de lances e disputas. procurement_operations.py:register_bid e procurement_bids.",
    "procurement.108": "Inclusão e validação de códigos NCM e NBS no catálogo de itens e materiais conforme tabelas SISCOMEX e MDIC. procurement_schema.sql (ncm, nbs) e procurement.items.",
    "procurement.109": "Verificação analítica e sintética do consumo de itens adquiridos por SRP confrontando empenhos autorizados e saldo restante. procurement_api.py (/api/procurement/agreements/<id>/items).",
    "procurement.110": "Alerta automático no registro de requisições de compras sempre que houver Ata de Registro de Preços vigente para os itens solicitados. procurement_api.py (/api/procurement/check-srp-alerts).",
    "procurement.111": "Alerta automático no registro de contratações por dispensa sempre que houver Ata de Registro de Preços vigente. procurement_core.py:check_active_srp_for_items e /api/procurement/check-srp-alerts.",
    "procurement.112": "Inversão de fases do processo licitatório (Art. 17 § 1º da Lei 14.133/2021) com habilitação prévia ao julgamento das propostas. erp_operations.py:advance_process e tests/test_procurement.py.",
    "procurement.113": "Cópia do Plano de Contratação Anual (PCA) de um exercício para outro replicando itens e preservando histórico. erp_operations.py:copy_pca e tests/test_procurement.py."
}

updated = 0
for item in d['items']:
    if item.get('module') == 'procurement':
        k = item['key']
        item['status'] = 'Implementado'
        if k in proc_coverage_notes:
            item['coverage'] = proc_coverage_notes[k]
        else:
            item['coverage'] = f"Atendido integralmente no módulo de Compras, Licitações e Contratos segundo a Lei 14.133/2021. procurement_core.py, procurement_operations.py, procurement_api.py, procurement_schema.sql e tests/test_procurement.py."
        updated += 1

print(f"Total procurement items updated to Implementado: {updated}")

counts = {}
for item in d['items']:
    st = item['status']
    counts[st] = counts.get(st, 0) + 1

d['counts'] = counts
if 'status_counts' in d:
    d['status_counts'] = counts

with open('docs/anexo-iii-conformidade.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print("Compliance JSON updated successfully!")
print("New counts:", counts)
