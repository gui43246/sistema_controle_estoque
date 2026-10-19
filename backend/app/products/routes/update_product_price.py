"""Valida e altera o preço de um produto existente."""

import logging
import math

from flask import jsonify, request
from flask_jwt_extended.utils import get_jwt_identity

from app import limiter
from app.core.security.authorization import admin_required
from app.models.product import ProductNotFoundError
from app.products import products_bp
from app.products.services.find_product import find_product
from app.products.services.update_product_price import update_product_price

logger = logging.getLogger(__name__)


@products_bp.route("/EditarValor", methods=["POST"])
@limiter.limit("30 per minute")
@admin_required
def update_product_price_route():
    """Valida o novo preço e atualiza o produto por código de barras."""
    logged_in_drt = get_jwt_identity()
    request_data = request.get_json(silent=True)

    if not isinstance(request_data, dict):
        return jsonify({"mensagem": "envie um objeto JSON válido"}), 400
    if not request_data.get("codigo_barras") or "novo_valor" not in request_data:
        return jsonify({"mensagem": "verifique os campos e tente novamente"}), 400

    barcode = request_data["codigo_barras"]
    if not isinstance(barcode, str) or not barcode.strip():
        return jsonify({"mensagem": "código de barras inválido"}), 422

    new_price = request_data["novo_valor"]
    if isinstance(new_price, bool):
        return jsonify({"mensagem": "novo valor inválido"}), 422
    try:
        value = float(new_price)
    except (TypeError, ValueError, OverflowError):
        return jsonify({"mensagem": "novo valor inválido"}), 422
    if not math.isfinite(value) or value < 0:
        return jsonify({"mensagem": "novo valor inválido"}), 422

    try:
        # Produto excluído conta como não encontrado.
        if not find_product(barcode):
            return jsonify({"mensagem": "produto não encontrado"}), 404

        update_product_price(barcode, value, logged_in_drt)

    except ProductNotFoundError:
        return jsonify({"mensagem": "produto não encontrado"}), 404
    except Exception:
        logger.exception("erro ao atualizar preço")
        return jsonify({"mensagem": "erro inesperado, tente novamente mais tarde"}), 500

    return jsonify({"mensagem": "ok valor inserido com sucesso"}), 200
