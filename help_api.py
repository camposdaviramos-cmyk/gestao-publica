"""
API de Ajuda Online Contextualizada e Manuais do Sistema
Município de Rio das Ostras - Edital PE 552/2026 e Anexo III (Item general.4)
"""

from flask import Blueprint, request, jsonify, g
from auth import require, ApiError
from db import settings

HELP_KNOWLEDGE_BASE = {
    'general': {
        'title': 'Ambiente Geral e Navegação',
        'summary': 'Diretrizes gerais de navegação, pesquisa global, atalhos de teclado e segurança.',
        'shortcuts': [
            {'key': 'Alt + 1 a 9', 'action': 'Navegação rápida entre módulos principais'},
            {'key': 'Ctrl + K / Ctrl + /', 'action': 'Busca global unificada de registros e cidadãos'},
            {'key': 'Ctrl + Enter', 'action': 'Salvar ou submeter formulário ativo'},
            {'key': 'Esc', 'action': 'Fechar modal ou diálogo aberto'}
        ],
        'legal_basis': 'Constituição Federal de 1988, Lei Federal nº 14.129/2021 (Governo Digital).',
        'sections': [
            {'title': 'Acesso Remoto Seguro', 'content': 'O Rio Gestão é 100% web, compatível com Microsoft Windows e navegadores modernos (Edge, Chrome, Firefox), utilizando HTTPS/TLS e autenticação com proteção contra força bruta.'},
            {'title': 'Política de Senhas', 'content': 'Senhas devem possuir no mínimo 12 caracteres, alternando maiúsculas, minúsculas, números e caracteres especiais, com bloqueio temporário após 5 tentativas incorretas.'},
            {'title': 'Dupla Custódia', 'content': 'Operações sensíveis (como estornos e alterações cadastrais críticas) exigem validação e aprovação por uma segunda autoridade competente (princípio dos quatro olhos).'}
        ]
    },
    'finance': {
        'title': 'Execução Orçamentária e Financeira',
        'summary': 'Planejamento (PPA, LDO, LOA), Dotações, Empenhos, Liquidações, Pagamentos, Arrecadação e Partidas Dobradas.',
        'shortcuts': [
            {'key': 'F2', 'action': 'Consultar dotação orçamentária disponível'},
            {'key': 'F4', 'action': 'Visualizar saldo bancário por conta e fonte'}
        ],
        'legal_basis': 'Lei Federal nº 4.320/1964, Lei Complementar nº 101/2000 (LRF), Normas Brasileiras de Contabilidade Aplicadas ao Setor Público (NBC TSP).',
        'sections': [
            {'title': 'Ciclo da Despesa', 'content': 'Toda despesa segue estritamente a sequência constitucional: Fixação da Dotação ➔ Empenho Prévio ➔ Liquidação com atesto de nota fiscal ➔ Pagamento por ordem bancária eletrônica.'},
            {'title': 'Bloqueio de Período', 'content': 'Após o fechamento mensal da contabilidade, movimentações retroativas são bloqueadas para garantir a integridade dos balancetes e envio ao TCE/SICONFI.'}
        ]
    },
    'bi': {
        'title': 'Business Intelligence (BI) e Painel Estratégico',
        'summary': 'Acompanhamento em tempo real de metas fiscais da LRF, disponibilidade de caixa, funil da despesa e visão 360º.',
        'shortcuts': [
            {'key': 'F11', 'action': 'Alternar tela cheia'},
            {'key': 'Ctrl + P', 'action': 'Imprimir visão atual do painel ou exportar PDF'}
        ],
        'legal_basis': 'LC nº 101/2000 (Arts. 19, 20, 29, 32 e 38), CF/88 Arts. 198 e 212.',
        'sections': [
            {'title': 'Semáforos da LRF', 'content': 'Verde: Limite cumprido / normal; Laranja: Limite de alerta (90%) ou prudencial (95%); Vermelho: Limite máximo ultrapassado com restrições imediatas.'},
            {'title': 'Modo Kiosk TV', 'content': 'Permite projetar os painéis em televisores corporativos de secretarias com rotação automática configurável entre os slides.'},
            {'title': 'Assistente Virtual NLP', 'content': 'Permite realizar perguntas em linguagem natural diretamente no chat para obter respostas imediatas sem dependência de relatórios estáticos.'}
        ]
    },
    'social': {
        'title': 'Assistência Social e Cidadania (SUAS)',
        'summary': 'CRAS, CREAS, Centro POP, Prontuário Eletrônico SUAS 360º, RMA Oficial MDS, Benefícios Eventuais, IVS e MROSC.',
        'shortcuts': [
            {'key': 'Alt + F', 'action': 'Localizar família por NIS ou CPF do Responsável'},
            {'key': 'Alt + A', 'action': 'Registrar atendimento com sigilo técnico'}
        ],
        'legal_basis': 'Lei Orgânica da Assistência Social (LOAS nº 8.742/1993), NOB/SUAS, Lei nº 13.019/2014 (MROSC).',
        'sections': [
            {'title': 'Sigilo Profissional CRESS/CRP', 'content': 'Prontuários de violação de direitos e violência doméstica contra a mulher possuem camada criptográfica de acesso restrito a profissionais habilitados.'},
            {'title': 'RMA Oficial do MDS', 'content': 'Os atendimentos alimentam automaticamente os Blocos I, II e III do RMA com geração e validação de arquivo XML para envio ao Censo SUAS.'}
        ]
    },
    'procurement': {
        'title': 'Compras, Licitações e Contratos',
        'summary': 'Plano de Contratações Anual (PCA), Processos Licitatórios, Julgamento, Homologação, Contratos e Aditivos.',
        'shortcuts': [
            {'key': 'Alt + P', 'action': 'Consultar processo pelo número/ano'}
        ],
        'legal_basis': 'Nova Lei de Licitações e Contratos Administrativos (Lei Federal nº 14.133/2021).',
        'sections': [
            {'title': 'Fases da Contratação', 'content': 'Fase preparatória (ETP, TR, Pesquisa de Preços) ➔ Divulgação do Edital ➔ Julgamento das Propostas ➔ Habilitação ➔ Homologação ➔ Formalização Contratual.'}
        ]
    }
}

def install_help(app):
    help_bp = Blueprint('help', __name__, url_prefix='/api/help')

    @help_bp.get('/contextual')
    def get_contextual_help():
        mod = request.args.get('module', 'general').lower()
        cfg = settings()
        data = HELP_KNOWLEDGE_BASE.get(mod, HELP_KNOWLEDGE_BASE['general'])
        resp = {
            **data,
            'module': mod,
            'support': {
                'email': cfg.get('support_email') or 'suporte@riodasostras.rj.gov.br',
                'phone': cfg.get('support_phone') or '(22) 2771-6000',
                'municipality': cfg.get('municipality', 'Rio das Ostras')
            }
        }
        return jsonify(resp)

    @help_bp.get('/search')
    def search_help():
        q = request.args.get('q', '').lower().strip()
        results = []
        for mod, content in HELP_KNOWLEDGE_BASE.items():
            if q in content['title'].lower() or q in content['summary'].lower() or any(q in s['title'].lower() or q in s['content'].lower() for s in content.get('sections', [])):
                results.append({
                    'module': mod,
                    'title': content['title'],
                    'summary': content['summary']
                })
        return jsonify({'query': q, 'results': results})

    app.register_blueprint(help_bp)
