"""Recebe um codigo de barras na requisição consulta o estoque e retorna o produto ."""

from flask import jsonify, request
from flask_jwt_extended import jwt_required

from app.products import products_bp
from app.products.services.find_product import find_product
from app import limiter


@products_bp.route("/consultar", methods=["POST"])
@limiter.limit("30 per minute")
@jwt_required()
def find_product_route():
    """Valida o JSON e retorna os dados do produto encontrado pelo serviço de busca."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"mensagem": "envie um objeto JSON válido"}), 400

    barcode = payload.get("codigo_barras")
    if not isinstance(barcode, str) or not barcode.strip():
        return jsonify({"mensagem": "código de barras inválido"}), 422

    product = find_product(barcode, config="data")
    if product is None:
        product_exists = find_product(barcode, config="status")
        if product_exists is False:
            return jsonify({"mensagem": "produto não encontrado"}), 404
        if product_exists is None:
            return jsonify({"mensagem": "erro ao consultar produto"}), 500
        return jsonify({"mensagem": "erro ao consultar produto"}), 500

    return jsonify(product), 200
