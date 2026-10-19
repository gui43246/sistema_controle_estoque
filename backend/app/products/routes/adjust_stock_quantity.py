"""Valida o ajuste de estoque e registra a movimentação associada."""

import logging
import sqlite3

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity

from app import limiter
from app.core.security.authorization import admin_required
from app.models.movement import StockNotFoundError
from app.products import products_bp
from app.products.services.find_product import find_product
from app.products.services.update_stock_quantity import update_stock_quantity

logger = logging.getLogger(__name__)

LIMITE_SQLITE = 9_223_372_036_854_775_807
REASON_STOCK_ADJUSTMENT = 4  # Padrão quando nenhum motivo é informado.

# IDs de motivos da tabela aceitos neste endpoint.
ALLOWED_REASONS = (
    3,  # Devolução
    4,  # Ajuste de estoque
    6,  # Produto danificado
    7,  # Produto vencido
    9,  # Ruptura
)


@products_bp.route("/EditarQuantidade", methods=["POST"])
@limiter.limit("30 per minute")
@admin_required
def adjust_stock_quantity_route():
    """Valida a quantidade e o motivo e delega a atualização transacional do estoque."""
    logged_in_drt = get_jwt_identity()
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"mensagem": "JSON inválido"}), 400

    required_fields = ("codigo_barras", "quantidade")
    if any(field not in payload for field in required_fields):
        return jsonify({"mensagem": "campo obrigatório ausente"}), 400

    barcode = payload["codigo_barras"]
    if not isinstance(barcode, str) or not barcode.strip():
        return jsonify({"mensagem": "código de barras inválido"}), 422

    try:
        original_quantity = payload["quantidade"]
        original_reason = payload.get("motivo")
        if original_reason is None:
            original_reason = REASON_STOCK_ADJUSTMENT

        if isinstance(original_quantity, bool) or isinstance(original_reason, bool):
            raise ValueError
        if isinstance(original_quantity, float) and not original_quantity.is_integer():
            raise ValueError
        if isinstance(original_reason, float) and not original_reason.is_integer():
            raise ValueError

        quantity = int(original_quantity)
        reason_id = int(original_reason)
    except (ValueError, TypeError, OverflowError):
        return jsonify({"mensagem": "quantidade ou motivo inválido"}), 422

    if quantity < 0:
        return jsonify({"mensagem": "quantidade não pode ser negativa"}), 422
    if quantity > LIMITE_SQLITE:
        return jsonify({"mensagem": "quantidade inválida"}), 422
    if reason_id not in ALLOWED_REASONS:
        return jsonify({"mensagem": "motivo não aceito para este ajuste"}), 422

    try:
        # Produto excluído conta como não encontrado.
        if not find_product(barcode):
            return jsonify({"mensagem": "produto não encontrado"}), 404

        update_stock_quantity(barcode, quantity, logged_in_drt, reason_id)

    except StockNotFoundError:
        return jsonify({"mensagem": "produto sem registro no estoque"}), 404
    except ValueError:
        # Os motivos permitidos já foram validados; a ausência na tabela indica
        # um erro de configuração.
        logger.exception("motivo aceito não existe na tabela motivos")
        return jsonify({"mensagem": "erro inesperado, tente novamente mais tarde"}), 500
    except sqlite3.Error:
        logger.exception("erro ao atualizar estoque")
        return jsonify({"mensagem": "erro inesperado, tente novamente mais tarde"}), 500

    return jsonify({"mensagem": "ok, quantidade ajustada"}), 200
