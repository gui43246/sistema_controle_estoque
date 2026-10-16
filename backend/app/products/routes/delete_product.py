"""Processa a exclusão administrativa de um produto sem histórico de movimentações."""

import sqlite3

from flask import jsonify, request
from app.products import produtos_bp
from app.models.movimentacao import Movimentacao
from app.products.services.delete_product import excluir_produto
from app.core.security.authorization import admin_required
from app import limiter
from flask_jwt_extended.utils import get_jwt_identity


@produtos_bp.route("/ExcluirProduto", methods=["PUT"])
@limiter.limit("30 per minute")
@admin_required
def excluir_produto_rota():
    usuario_logado = get_jwt_identity()
    """Converte o resultado do serviço de exclusão em uma resposta HTTP."""
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or not {"codigo_barras", "motivo"}.issubset(dados):
        return jsonify({"mensagem": "Dados inválidos ou incompletos"}), 400

    codigo_barras = dados["codigo_barras"]
    try:
        motivo = int(dados["motivo"])
    except (ValueError, TypeError, OverflowError):
        return jsonify({"mensagem": "o campo motivo é invalido"}), 400

    if Movimentacao.buscar_motivo(motivo) is None:
        return jsonify({"mensagem": "motivo nao encontrado"}), 404

    try:
        resultado = excluir_produto(codigo_barras)
    except sqlite3.Error:
        return jsonify({"mensagem": "erro ao excluir produto; tente novamente"}), 500

    if resultado == "nao_encontrado":
        return jsonify({"mensagem": "produto nao encontrado"}), 404

    if resultado == "excluido":
        Movimentacao.registrar(
            codigo_barras=codigo_barras,
            quantidade=0,
            status="exclusão",
            motivo=motivo,
            usuario_drt=usuario_logado
            )
        return jsonify({"mensagem": "produto e registro de estoque excluidos"}), 200
