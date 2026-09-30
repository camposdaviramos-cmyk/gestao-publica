"""
API REST do Módulo de Pregão Eletrônico e Intercâmbio de Compras Públicas
Município de Rio das Ostras - Edital PE 552/2026 e Anexo III (Item auction.1)
"""

from flask import Blueprint, request, jsonify, g
from auth import require, ApiError
from db import audit
import auction_core as core

def install_auction(app):
    auction_bp = Blueprint('auction', __name__, url_prefix='/api/auction')

    @auction_bp.before_request
    def ensure_db():
        core.init_auction_db()

    @auction_bp.get('/platforms')
    def list_platforms():
        require('procurement', 'read')
        configs = core.list_platform_configs()
        return jsonify({
            'supported_count': len(core.SUPPORTED_PLATFORMS),
            'platforms': core.SUPPORTED_PLATFORMS,
            'configs': configs
        })

    @auction_bp.post('/platforms/configure')
    def configure():
        require('procurement', 'write')
        body = request.get_json(force=True)
        provider = body.get('provider')
        endpoint = body.get('api_endpoint')
        client_id = body.get('client_id')
        token = body.get('client_token', '')
        env = body.get('environment', 'HOMOLOGACAO')

        if not provider or not endpoint or not client_id:
            raise ApiError('Provider, api_endpoint e client_id são obrigatórios.', 400)

        res = core.configure_platform(provider, endpoint, client_id, token, env)
        audit('Configuração de Plataforma de Pregão', 'auction_platforms', provider)
        return jsonify(res)

    @auction_bp.post('/exchanges/prepare')
    def prepare_exchange():
        require('procurement', 'write')
        body = request.get_json(force=True)
        process_code = body.get('process_code', 'PE-001/2026')
        provider = body.get('provider', 'BLL')
        items = body.get('items')
        notice = body.get('edital_notice', '')

        res = core.prepare_exchange_package(process_code, provider, items, notice)
        audit('Preparação de Intercâmbio de Pregão', 'auction_exchanges', res['exchange_id'])
        return jsonify(res), 201

    @auction_bp.post('/exchanges/<int:exchange_id>/transmit')
    def transmit(exchange_id):
        require('procurement', 'write')
        res = core.transmit_exchange_package(exchange_id)
        audit('Transmissão de Pregão Eletrônico', 'auction_exchanges', exchange_id)
        return jsonify(res)

    @auction_bp.post('/exchanges/<int:exchange_id>/import-results')
    def import_results(exchange_id):
        require('procurement', 'write')
        body = request.get_json(silent=True) or {}
        res = core.import_exchange_results(exchange_id, body.get('results'))
        audit('Importação de Resultados do Pregão', 'auction_exchanges', exchange_id)
        return jsonify(res)

    @auction_bp.post('/webhook/<provider>')
    def webhook(provider):
        body = request.get_json(silent=True) or {}
        # Webhook assíncrono para receber atualização de sessão de lances do portal
        return jsonify({'status': 'RECEBIDO', 'provider': provider, 'timestamp': core.datetime.now().isoformat()})

    app.register_blueprint(auction_bp)
