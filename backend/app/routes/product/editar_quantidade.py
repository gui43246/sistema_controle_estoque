"""Valida o ajuste de estoque e registra a movimentação associada."""

from flask import request, jsonify
from app.routes.product import produtos_bp
from app.models.produto import Produto
from app.services import registrar_movimentacao, buscar_motivo
from app.services.buscar import buscar
from flask_jwt_extended import get_jwt_identity
from app.security.authorization import admin_required
from app import limiter
import sqlite3

SQLITE_INT_MAX = 9_223_372_036_854_775_807


@produtos_bp.route("/EditarQuantidade", methods=["POST"])
@limiter.limit("30 per minute")
@admin_required
def editar_produtos():
    """Valida os dados recebidos e atualiza a quantidade em estoque."""
    usuario_logado = get_jwt_identity()
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({"mensagem": "JSON inválido"}), 400
    if not all(campo in dados for campo in ("codigo_barras", "quantidade", "motivo")):
        return jsonify({"mensagem": "campo obrigatório ausente"}), 400

    codigo_barras = dados["codigo_barras"]
    if not isinstance(codigo_barras, str) or not codigo_barras.strip():
        return jsonify({"mensagem": "código de barras inválido"}), 422

    if not buscar(codigo_barras):
        return jsonify({"mensagem": "produto não existe"}), 422

    try:
        quantidade_original = dados["quantidade"]
        motivo_original = dados["motivo"]
        if isinstance(quantidade_original, bool) or isinstance(motivo_original, bool):
            raise ValueError
        quantidade = int(quantidade_original)
        motivo_id = int(motivo_original)
        if (
            isinstance(quantidade_original, float)
            and not quantidade_original.is_integer()
        ):
            raise ValueError
        if isinstance(motivo_original, float) and not motivo_original.is_integer():
            raise ValueError
    except (ValueError, TypeError, OverflowError):
        return jsonify({"mensagem": "quantidade ou motivo inválido"}), 422

    if quantidade < 0 or motivo_id < 0:
        return jsonify({"mensagem": "quantidade ou motivo inválido"}), 422
    if quantidade > SQLITE_INT_MAX or motivo_id > SQLITE_INT_MAX:
        return jsonify({"mensagem": "quantidade ou motivo inválido"}), 422

    if buscar_motivo(motivo_id) is None:
        return jsonify({"mensagem": "motivo não encontrado"}), 404

    if not Produto.ajustar_quantidade(
        codigo_barras=codigo_barras, quantidade=quantidade
    ):
        return jsonify({"mensagem": "erro inesperado, tente novamente"}), 500

    try:
        registrar_movimentacao(
            codigo_barras=codigo_barras,
            quantidade=quantidade,
            status="ajuste",
            motivo=motivo_id,
            usuario_drt=usuario_logado,
        )
    except sqlite3.Error:
        return jsonify({"mensagem": "erro inesperado, tente novamente"}), 500

    return jsonify({"mensagem": "ok, quantidade ajustada"}), 200
