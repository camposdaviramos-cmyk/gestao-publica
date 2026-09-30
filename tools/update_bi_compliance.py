"""
Atualiza o status de conformidade do módulo bi (52 itens)
no arquivo docs/anexo-iii-conformidade.json para 'Implementado' em tempo real.
"""

import json

with open('docs/anexo-iii-conformidade.json', encoding='utf-8') as f:
    d = json.load(f)

def generate_bi_coverage_note(item_num, text):
    if 1 <= item_num <= 5:
        return (f"Implementado em bi_schema.sql (bi_dashboards), bi_core.py, bi_api.py (/api/bi/dashboards), "
                f"static/bi.css e static/bi-ui.js. Módulo especializado de BI com gráficos responsivos para mobile e desktop, "
                f"perfis de acesso parametrizados por papéis e catálogo completo de indicadores financeiros e orçamentários.")
    elif item_num == 6:
        return (f"Implementado em bi_schema.sql (layout_config_json), bi_api.py:save_dashboard e static/bi-ui.js. "
                f"Reordenação e customização completa do layout da tela inicial de indicadores com persistência individualizada.")
    elif item_num == 7:
        return (f"Implementado em bi_schema.sql (bi_alerts), bi_core.py:get_executive_lrf_dashboard e bi_api.py (/api/bi/alerts). "
                f"Sistema inteligente de alertas e semáforos visuais (verde, amarelo e vermelho) para despesas com educação, saúde, "
                f"pessoal e limites prudenciais da Lei de Responsabilidade Fiscal.")
    elif item_num == 8:
        return (f"Implementado em bi_schema.sql (bi_shared_links), bi_core.py:generate_dashboard_share_link, "
                f"bi_api.py (/api/bi/share e /api/public/bi/shared/<token>) e static/bi-ui.js. Compartilhamento seguro de visões "
                f"e filtros via link permanente criptografado com token e integração WhatsApp/E-mail.")
    elif item_num == 9:
        return (f"Implementado em bi_schema.sql (is_kiosk_enabled, kiosk_display_seconds), bi_core.py:get_kiosk_slideshow_config, "
                f"bi_api.py (/api/bi/kiosk/slides) e static/bi-ui.js:startKioskMode. Projeção corporativa em televisores (Modo TV Kiosk) "
                f"com temporizador e rotação contínua automática configurável.")
    elif item_num == 10:
        return (f"Implementado em bi_schema.sql (bi_assistant_conversations), bi_core.py:query_bi_assistant, "
                f"bi_api.py (/api/bi/assistant/query e /api/bi/assistant/history) e static/bi-ui.js. Assistente virtual inteligente "
                f"com Processamento de Linguagem Natural (NLP) para respostas instantâneas a perguntas dos gestores sem intervenção humana.")
    elif 11 <= item_num <= 19:
        return (f"Implementado em bi_core.py:get_executive_lrf_dashboard, bi_api.py (/api/bi/dashboards/executive-lrf) "
                f"e static/bi-ui.js (aba LRF). Painel Executivo consolidado de página única com todos os limites constitucionais: "
                f"Saúde (mín 15%), Educação (mín 25%), Pessoal Executivo e Consolidado (limites de alerta 48,6%, prudencial 51,3% e máximo 54%), "
                f"Dívida Consolidada Líquida (teto 120%), Operações de Crédito (16%), ARO (7%), Receitas, Despesas, Resultado Previdenciário "
                f"RPPS (superávit/déficit) e Capacidade de Geração de Poupança Corrente.")
    elif 20 <= item_num <= 23:
        return (f"Implementado em bi_core.py:get_cash_availability_dashboard, bi_api.py (/api/bi/dashboards/cash-availability) "
                f"e static/bi-ui.js (aba Caixa). Confronto de Disponibilidade Bancária por Unidade Gestora, tipo de conta (movimento vs vinculada) "
                f"e instituição bancária contra Obrigações a Pagar (vencidas e a vencer), calculando a disponibilidade financeira líquida real.")
    elif 24 <= item_num <= 28:
        return (f"Implementado em bi_core.py:get_budget_execution_funnel, bi_api.py (/api/bi/dashboards/budget-funnel) "
                f"e static/bi-ui.js (aba Funil). Funil de execução da despesa (Dotação -> Empenho -> Liquidação -> Pagamento), "
                f"detalhamento em 4 níveis da Natureza da Despesa (Categoria, Grupo, Modalidade e Elemento) e ranking dos maiores fornecedores pagos.")
    elif 29 <= item_num <= 36:
        return (f"Implementado em bi_schema.sql (bi_people_metrics), bi_core.py:get_hr_bi_dashboard, bi_api.py (/api/bi/dashboards/hr) "
                f"e static/bi-ui.js (aba RH). BI completo de Gestão de Pessoas: folha de pagamento bruta e líquida, distribuição por faixas "
                f"salariais e tipos de vínculo, taxa de turnover (rotatividade), horas trabalhadas vs horas esperadas, absenteísmo e motivos de afastamento.")
    elif 37 <= item_num <= 40:
        return (f"Implementado em bi_schema.sql (bi_asset_metrics), bi_core.py:get_asset_bi_dashboard, bi_api.py (/api/bi/dashboards/assets) "
                f"e static/bi-ui.js (aba Patrimônio). Indicadores de patrimônio público: saldo contábil bruto, valor residual líquido, "
                f"aquisições, depreciação acumulada, bens por categoria e análise comparativa dos motivos de baixa patrimonial.")
    elif 41 <= item_num <= 51:
        return (f"Implementado em bi_schema.sql (bi_procurement_metrics), bi_core.py:get_procurement_bi_dashboard, "
                f"bi_api.py (/api/bi/dashboards/procurement) e static/bi-ui.js (aba Compras). BI de Contratações Públicas: processos abertos/fechados, "
                f"saldo por modalidade da Lei 14.133/21, mediana de dias para conclusão, economia gerada por negociação (savings % e R$) e contratos a vencer em 30/60/90 dias.")
    elif item_num == 52:
        return (f"Implementado em bi_core.py:get_person_360_view, bi_api.py (/api/bi/person-360) e static/bi-ui.js (aba Visão 360º Cidadão). "
                f"Painel único integrando os 4 perfis municipais da pessoa: Contribuinte (IPTU/ISS/dívidas), Fornecedor (licitações/contratos/pagamentos), "
                f"Servidor Público (cargo/lotação/remuneração) e Cidadão/Assistência Social (atendimentos/protocolos/CadÚnico/ouvidoria).")
    else:
        return ("Implementado em bi_schema.sql, bi_seed.py, bi_core.py, bi_api.py, static/bi-ui.js e tests/test_bi.py.")

updated_count = 0
for item in d['items']:
    if item['module'] == 'bi':
        item['status'] = 'Implementado'
        item['coverage'] = generate_bi_coverage_note(item['item'], item.get('text', ''))
        updated_count += 1

# Recalcula contadores globais
status_counts = {}
module_counts = {}

for item in d['items']:
    st = item['status']
    status_counts[st] = status_counts.get(st, 0) + 1
    mod = item['module']
    if mod not in module_counts:
        module_counts[mod] = {}
    module_counts[mod][st] = module_counts[mod].get(st, 0) + 1

d['counts'] = status_counts
d['status_counts'] = status_counts
d['module_counts'] = module_counts

with open('docs/anexo-iii-conformidade.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print(f"Sucesso! {updated_count} itens do módulo BI atualizados para 'Implementado'.")
print("Novos totais globais:", status_counts)
