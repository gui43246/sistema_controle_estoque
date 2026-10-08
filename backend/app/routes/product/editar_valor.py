"""Valida e altera o preço de um produto existente."""

from flask import blueprints ,request, jsonify
from app.models.produto import Produto
from app.services.buscar import buscar
from app.routes.product import produtos_bp
from app.security.authorization import admin_required
from app import limiter
import math



@produtos_bp.route("/EditarValor", methods=["POST"])
@limiter.limit("30 per minute")
@admin_required
def ajustar_valor_produto():
    """Valida o novo preço e atualiza o produto por codigo de barras."""
    requisicao = request.get_json(silent=True)

    if not isinstance(requisicao, dict):
        return jsonify({"mensagem": "envie um objeto JSON valido"}), 400
    if not requisicao.get("codigo_barras") or "novo_valor" not in requisicao:
        return jsonify({"mensagem": "verifique os campos e tente novamente"}), 400

    codigo_barras = requisicao["codigo_barras"]
    if not isinstance(codigo_barras, str) or not codigo_barras.strip():
        return jsonify({"mensagem": "codigo de barras invalido"}), 422

    try:
        if isinstance(requisicao["novo_valor"], bool):
            raise ValueError
        valor = float(requisicao["novo_valor"])
        if not math.isfinite(valor) or valor < 0:
            return jsonify({"mensagem": "novo valor invalido"}), 422

        produto_existe = buscar(codigo_barras, config="status")
        if produto_existe is None:
            return jsonify({"mensagem": "erro ao consultar produto"}), 500
        if produto_existe is False:
            return jsonify({"mensagem": "produto nao encontrado"}), 404

    except (TypeError, ValueError, OverflowError):
        return jsonify({"mensagem": "novo valor invalido"}), 422

    ajuste_devalor = Produto.editar_valor_produto(codigo_barras, valor)

    if not ajuste_devalor:
        return jsonify({"mensagem": "produto nao encontrado ou erro no banco"}), 404
    else:
        return jsonify({"mensagem": "ok valor inserido com sucesso"}), 200
