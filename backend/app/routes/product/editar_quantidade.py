"""Valida o ajuste de estoque e registra a movimentação associada."""

from flask import request, jsonify
from app.routes.product import produtos_bp
from app.services.regmovit import ajustar_quantidade_e_registrar
from flask_jwt_extended import get_jwt_identity
from app.security.authorization import admin_required
from app import limiter
import sqlite3


@produtos_bp.route("/EditarQuantidade", methods=["POST"])
@limiter.limit("30 per minute")
@admin_required
def editar_produtos():
    """Valida a quantidade e o motivo e delega a atualização transacional do estoque."""
    usuario_logado = get_jwt_identity()
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({"mensagem": "JSON inválido"}), 400

    campos_obrigatorios = ("codigo_barras", "quantidade", "motivo")
    if any(campo not in dados for campo in campos_obrigatorios):
        return jsonify({"mensagem": "não autorizado, campo incorreto"}), 400

    codigo_barras = dados["codigo_barras"]
    if not isinstance(codigo_barras, str) or not codigo_barras.strip():
        return jsonify({"mensagem": "código de barras inválido"}), 422
    try:
        quantidade_original = dados["quantidade"]
        motivo_original = dados["motivo"]
        if isinstance(quantidade_original, bool) or isinstance(motivo_original, bool):
            raise ValueError
        quantidade = int(quantidade_original)
        motivo_id = int(motivo_original)
        if isinstance(quantidade_original, float) and not quantidade_original.is_integer():
            raise ValueError
        if isinstance(motivo_original, float) and not motivo_original.is_integer():
            raise ValueError
    except (ValueError, TypeError, OverflowError):
        return jsonify({"mensagem": "quantidade ou motivo inválido"}), 422

    limite_sqlite = 9_223_372_036_854_775_807
    if quantidade > limite_sqlite or motivo_id > limite_sqlite or motivo_id < 0:
        return jsonify({"mensagem": "quantidade ou motivo inválido"}), 422

    try:
        resultado = ajustar_quantidade_e_registrar(
            codigo_barras=codigo_barras,
            quantidade=quantidade,
            motivo_id=motivo_id,
            usuario_drt=usuario_logado,
        )
    except sqlite3.Error:
        return jsonify({"mensagem": "erro inesperado, tente novamente"}), 500

    if resultado == "quantidade_invalida":
        return jsonify({"mensagem": "quantidade não pode ser negativa"}), 422
    if resultado == "motivo_invalido":
        return jsonify({"mensagem": "motivo não encontrado"}), 404
    if resultado == "estoque_nao_encontrado":
        return jsonify({"mensagem": "produto sem registro no estoque"}), 404

    return jsonify({"mensagem": "ok, quantidade ajustada"}), 200
