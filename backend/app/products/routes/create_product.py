"""Valida e cadastra um produto novo com estoque inicial zerado."""

import sqlite3

from flask import current_app, jsonify, request
from flask_jwt_extended.utils import get_jwt_identity
from app import limiter
from app.core.security.authorization import admin_required
from app.models.product import Product
from app.products import products_bp
from app.products.services.create_product import create_product
from app.products.services.find_product import find_product
from app.products.services.find_sector import find_sector

REQUIRED_FIELDS = ("codigo_barras", "nome_produto", "valor_prod", "setor_id")


@products_bp.route("/cadastrar", methods=["POST"])
@limiter.limit("30 per minute")
@admin_required
def create_product_route():
    """Valida os campos e cadastra o produto, seu estoque e a movimentação."""
    logged_in_drt = get_jwt_identity()

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"mensagem": "envie um objeto JSON válido"}), 400

    missing_fields = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing_fields:
        return jsonify({"mensagem": f"faltando o campo {', '.join(missing_fields)}"}), 400

    try:
        product = Product.from_values(
            barcode=payload["codigo_barras"],
            name=payload["nome_produto"],
            price=payload["valor_prod"],
            sector_id=payload["setor_id"],
        )
    except ValueError as error:
        return jsonify({"mensagem": str(error)}), 422

    try:
        if find_sector(product.sector_id) is None:
            return jsonify({"mensagem": "setor não encontrado"}), 404

        if find_product(product.barcode):
            return jsonify({"mensagem": "produto já cadastrado"}), 409

        create_product(logged_in_drt, product)

    except sqlite3.IntegrityError:
        return jsonify({"mensagem": "produto já cadastrado"}), 409
    except Exception:
        current_app.logger.exception("erro ao cadastrar produto")
        return jsonify({"mensagem": "erro inesperado, tente novamente mais tarde"}), 500

    return jsonify({"mensagem": "Sucesso ao cadastrar item"}), 201
