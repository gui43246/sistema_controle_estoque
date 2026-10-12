"""Recebe um codigo de barras na requisição consulta o estoque e retorna o produto ."""

from flask import jsonify, request
from flask_jwt_extended.utils import get_jwt_identity
from flask_jwt_extended import jwt_required
from app.services import registrar_movimentacao
from app.routes.product import produtos_bp
from app.services.buscar import buscar
from app import limiter


@produtos_bp.route("/consultar", methods=["POST"])
@limiter.limit("30 per minute")
@jwt_required()
def consultar_produto_por_codigo():
    """Valida o JSON e retorna os dados do produto encontrado pelo serviço de busca."""
    usuario = get_jwt_identity()
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({"mensagem": "envie um objeto JSON valido"}), 400

    codigo_barras = dados.get("codigo_barras")
    if not isinstance(codigo_barras, str) or not codigo_barras.strip():
        return jsonify({"mensagem": "codigo de barras invalido"}), 422

    produto = buscar(codigo_barras, config="dados")
    if produto is None:
        produto_existe = buscar(codigo_barras, config="status")
        if produto_existe is False:
            return jsonify({"mensagem": "produto nao encontrado"}), 404
        return jsonify({"mensagem": "erro ao consultar produto"}), 500

    return jsonify(produto), 200
