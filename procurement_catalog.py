"""Catálogo tipado de cadastros e operações complementares de Compras e Contratos."""

def register(CATALOG, F, R, ref, choice, moneyf, datef, qty, text):
    p = CATALOG.setdefault('procurement', {
        'label': 'Compras e contratos',
        'icon': 'file',
        'description': 'Fornecedores, fases de contratação, propostas, contratos, SRP e PCA.',
        'resources': {}
    })
    
    # Atualizar/estender recursos de compras e contratos
    p['resources'].update({
        'price_registrations': R('Atas de registro de preços (SRP)', {
            'code': F('Número da ata', required=True),
            'name': F('Objeto da ata', required=True),
            'process': ref('Processo de licitação', 'procurement.processes', True),
            'supplier': ref('Detentor da ata', 'procurement.suppliers', True),
            'year': F('Exercício', 'integer', True),
            'start': datef('Vigência inicial', True),
            'end': datef('Vigência final', True),
            'total_amount': moneyf('Valor total registrado', True),
            'carona_permitted': F('Permite adesão de outros órgãos (carona)', 'boolean'),
            'active': F('Ativa', 'boolean'),
            'notes': text('Observações / regras de fornecimento')
        }, operations=['register_carona']),
        'auxiliary_procedures': R('Procedimentos auxiliares', {
            'code': F('Identificação do procedimento', required=True),
            'name': F('Objeto do chamamento / credenciamento', required=True),
            'type': choice('Tipo', 'Credenciamento|Pré-qualificação|Chamada Pública PNAE|PMI'),
            'legal_basis': F('Fundamentação legal', required=True),
            'tce_modality': choice('Classificação TCE-RJ', 'CPP|Outra'),
            'notice_date': datef('Data da publicação do edital', True),
            'status': choice('Situação', 'Edital Publicado|Inscrições Abertas|Homologado|Encerrado'),
            'total_estimated': moneyf('Valor total estimado'),
            'notes': text('Observações e regras')
        }),
        'supplier_certificates': R('Certidões de regularidade e CNDs', {
            'code': F('Número do documento / código de autenticação', required=True),
            'name': F('Órgão emissor', required=True),
            'supplier': ref('Fornecedor', 'procurement.suppliers', True),
            'type': choice('Tipo', 'Federal/INSS|Estadual|Municipal|Trabalhista CNDT|FGTS|Falência/Concordata'),
            'issue_date': datef('Data de emissão', True),
            'expiration_date': datef('Data de validade', True),
            'status': choice('Situação', 'Válida|Vence em breve|Vencida'),
            'verification_url': F('URL de autenticidade', 'url')
        }),
        'supplier_sanctions': R('Sanções e penalidades administrativas', {
            'code': F('Processo sancionatório', required=True),
            'name': F('Descrição da infração', required=True),
            'supplier': ref('Fornecedor sancionado', 'procurement.suppliers', True),
            'type': choice('Penalidade', 'Advertência|Multa|Impedimento de licitar|Declaração de inidoneidade'),
            'legal_basis': F('Fundamento legal', required=True),
            'start': datef('Data inicial', True),
            'end': datef('Data final'),
            'fine_amount': moneyf('Valor da multa aplicada'),
            'active': F('Penalidade ativa', 'boolean'),
            'notes': text('Histórico e despacho')
        }),
        'pca_versions': R('Versões do Plano de Contratações Anual', {
            'code': F('Número da versão', required=True),
            'name': F('Título / justificativa', required=True),
            'exercise': F('Exercício', 'integer', True),
            'status': choice('Situação', 'Rascunho|Aprovado|Reprovado|Publicado PNCP'),
            'total_amount': moneyf('Total estimado', True),
            'items_count': F('Quantidade de itens', 'integer'),
            'justification': text('Justificativa da decisão')
        }, operations=['approve_pca', 'reject_pca', 'publish_pca_pncp'])
    })

LABELS = {
    'register_bids': 'Registrar lances da sessão pública',
    'summon_remaining_bidders': 'Convocar licitantes remanescentes',
    'approve_pca': 'Aprovar Plano de Contratação Anual',
    'reject_pca': 'Reprovar Plano de Contratação Anual',
    'publish_pca_pncp': 'Publicar PCA no PNCP',
    'generate_price_agreement': 'Gerar Ata de Registro de Preços',
    'register_carona': 'Registrar adesão (carona)',
    'apply_procurement_amendment': 'Aplicar termo aditivo contratual'
}
