"""Valida a solicitação administrativa para alterar o setor de um produto."""

from flask import request, jsonify
from app.products import products_bp
from app.products.services.find_product import find_product
from app.products.services.find_sector import find_sector
from app.products.services.update_product_sector import update_product_sector
from app.core.security.authorization import admin_required
from app import limiter


@products_bp.route("/ajuste_setor_produto", methods=["POST"])
@limiter.limit("30 per minute")
@admin_required
def update_sector_route():
    """Valida o produto e o setor antes de aplicar a alteração administrativa."""
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"mensagem": "envie um objeto JSON válido"}), 400
    if not payload.get("codigo_barras") or "novo_setor" not in payload:
        return jsonify({"mensagem": "erro: verifique os campos e tente novamente"}), 400

    barcode = payload["codigo_barras"]
    if not isinstance(barcode, str) or not barcode.strip():
        return jsonify({"mensagem": "código de barras inválido"}), 422
    if isinstance(payload["novo_setor"], bool):
        return jsonify({"mensagem": "setor inválido"}), 422
    try:
        original_sector = payload["novo_setor"]
        sector_id = int(original_sector)
        if isinstance(original_sector, float) and not original_sector.is_integer():
            raise ValueError
    except (ValueError, TypeError, OverflowError):
        return jsonify({"mensagem": "setor inválido"}), 422
    if sector_id < 1 or sector_id > 9_223_372_036_854_775_807:
        return jsonify({"mensagem": "setor inválido"}), 422

    product_exists = find_product(barcode, config="status")
    if product_exists is None:
        return jsonify({"mensagem": "erro ao consultar produto"}), 500
    if product_exists is False:
        return jsonify({"mensagem": "erro: produto não encontrado"}), 404

    sector_exists = find_sector(sector_id)

    if sector_exists is None:
        return jsonify({"mensagem": "setor não encontrado"}), 404

    success = update_product_sector(barcode, sector_id)

    if not success:
        return jsonify({"mensagem": "erro: verifique e tente novamente"}), 500

    return jsonify({"mensagem": "sucesso: setor ajustado"}), 200
