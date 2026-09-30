"""Catálogo tipado de cadastros e operações de Obras Públicas."""

def register(CATALOG, F, R, ref, choice, moneyf, datef, qty, text):
    w = CATALOG.setdefault('works', {
        'label': 'Obras públicas',
        'icon': 'building',
        'description': 'Planilhas orçamentárias, cronograma físico-financeiro, diários, fotos, medições e retenções.',
        'resources': {}
    })
    
    # Garantir recursos complementares
    w['resources'].update({
        'measurement_units': R('Unidades de medida', {
            'code': F('Símbolo / código', required=True),
            'name': F('Descrição', required=True),
            'type': choice('Tipo', 'Padrão|Customizada'),
            'active': F('Ativa', 'boolean')
        }),
        'job_roles': R('Funções da obra', {
            'code': F('Código', required=True),
            'name': F('Descrição da função', required=True),
            'category': choice('Categoria', 'Técnica|Operacional|Fiscalização|Administrativa'),
            'active': F('Ativa', 'boolean')
        }),
        'equipments': R('Equipamentos da obra', {
            'code': F('Identificação / patrimônio', required=True),
            'name': F('Descrição do equipamento', required=True),
            'type': choice('Tipo', 'Próprio|Locado|Subcontratado'),
            'capacity': F('Capacidade / potência'),
            'active': F('Ativo', 'boolean')
        }),
        'price_agreements': R('Atas de registro de preços de obras', {
            'code': F('Número da ata', required=True),
            'name': F('Objeto da ata de manutenção', required=True),
            'process': ref('Processo de contratação', 'procurement.processes', False),
            'supplier': ref('Detentor da ata', 'procurement.suppliers', True),
            'start': datef('Vigência inicial', True),
            'end': datef('Vigência final', True),
            'total_amount': moneyf('Valor anual estimado', True),
            'active': F('Ativa', 'boolean')
        }),
        'spreadsheet_versions': R('Versões da planilha orçamentária', {
            'code': F('Versão', required=True),
            'name': F('Título / justificativa', required=True),
            'project': ref('Obra', 'works.projects'),
            'type': choice('Tipo de revisão', 'Inicial|Aditivo de valor|Supressão|Reajuste linear'),
            'adjustment_percent': F('Percentual de reajuste (%)', 'percent'),
            'date': datef('Data da versão', True),
            'total_amount': moneyf('Novo valor total', True)
        }, operations=['linear_adjustment', 'activate_version']),
    })

LABELS = {
    'import_spreadsheet': 'Importar planilha orçamentária',
    'linear_adjustment': 'Aplicar reajuste linear',
    'suppress_items': 'Suprimir itens da planilha',
    'amend_works_deadline': 'Aditivo de prazo da obra',
    'amend_works_value': 'Aditivo de valor da obra',
    'approve_diary_photo': 'Aprovar foto de diário',
    'close_project': 'Registrar recebimento definitivo',
    'activate_version': 'Ativar versão da planilha',
}
