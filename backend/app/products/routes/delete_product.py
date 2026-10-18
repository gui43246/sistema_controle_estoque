"""Processa a exclusão lógica de um produto e registra a movimentação."""

import logging

from flask import jsonify, request
from flask_jwt_extended.utils import get_jwt_identity

from app import limiter
from app.core.security.authorization import admin_required
from app.models.product import ProdutoNaoEncontradoError
from app.products import produtos_bp
from app.products.services.delete_product import excluir_produto

logger = logging.getLogger(__name__)

MOTIVO_EXCLUSAO = 10  


@produtos_bp.route("/ExcluirProduto", methods=["PUT"])
@limiter.limit("30 per minute")
@admin_required
def excluir_produto_rota():
    """Valida o código de barras e exclui logicamente o produto."""
    usuario_logado = get_jwt_identity()
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict) or "codigo_barras" not in dados:
        return jsonify({"mensagem": "dados invalidos ou incompletos"}), 400

    codigo_barras = dados["codigo_barras"]
    if not isinstance(codigo_barras, str) or not codigo_barras.strip():
        return jsonify({"mensagem": "codigo de barras invalido"}), 422

    try:
        excluir_produto(codigo_barras, MOTIVO_EXCLUSAO, usuario_logado)
    except ProdutoNaoEncontradoError:
        return jsonify({"mensagem": "produto nao encontrado"}), 404
    except ValueError:
        # O motivo é fixo no servidor: se não existe na tabela, é erro de configuração.
        logger.exception("motivo de exclusao nao existe na tabela motivos")
        return jsonify({"mensagem": "erro inesperado, tente novamente mais tarde"}), 500
    except Exception:
        logger.exception("erro ao excluir produto")
        return jsonify({"mensagem": "erro inesperado, tente novamente mais tarde"}), 500

    return jsonify({"mensagem": "produto excluido com sucesso"}), 200