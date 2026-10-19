"""Processa a exclusão lógica de um produto e registra a movimentação."""

import logging

from flask import jsonify, request
from flask_jwt_extended.utils import get_jwt_identity

from app import limiter
from app.core.security.authorization import admin_required
from app.models.product import ProductNotFoundError
from app.products import products_bp
from app.products.services.delete_product import delete_product
from app.products.services.find_product import find_product

logger = logging.getLogger(__name__)

REASON_DELETION = 10


@products_bp.route("/ExcluirProduto", methods=["PUT"])
@limiter.limit("30 per minute")
@admin_required
def delete_product_route():
    """Valida o código de barras e exclui logicamente o produto."""
    logged_in_drt = get_jwt_identity()
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict) or "codigo_barras" not in payload:
        return jsonify({"mensagem": "dados inválidos ou incompletos"}), 400

    barcode = payload["codigo_barras"]
    if not isinstance(barcode, str) or not barcode.strip():
        return jsonify({"mensagem": "código de barras inválido"}), 422

    try:
        if not find_product(barcode):
            return jsonify({"mensagem": "produto não encontrado"}), 404
        delete_product(barcode, REASON_DELETION, logged_in_drt)
    except ProductNotFoundError:
        return jsonify({"mensagem": "produto não encontrado"}), 404
    except ValueError:
        # O motivo é fixo no servidor: se não existe na tabela, é erro de configuração.
        logger.exception("motivo de exclusão não existe na tabela motivos")
        return jsonify({"mensagem": "erro inesperado, tente novamente mais tarde"}), 500
    except Exception:
        logger.exception("erro ao excluir produto")
        return jsonify({"mensagem": "erro inesperado, tente novamente mais tarde"}), 500

    return jsonify({"mensagem": "produto excluído com sucesso"}), 200
