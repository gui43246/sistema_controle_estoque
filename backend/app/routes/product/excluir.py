"""Processa a exclusão administrativa de um produto sem histórico de movimentações."""

import sqlite3

from flask import jsonify
from app.routes.product import produtos_bp
from app.services.excluir_produto import excluir_produto
from app.security.authorization import admin_required
from app import limiter


@produtos_bp.route("/produto/<string:codigo_barras>", methods=["DELETE"])
@limiter.limit("30 per minute")
@admin_required
def excluir_produto_rota(codigo_barras):
    """Converte o resultado do serviço de exclusão em uma resposta HTTP."""
    try:
        resultado = excluir_produto(codigo_barras)
    except sqlite3.Error:
        return jsonify({"mensagem": "erro ao excluir produto; tente novamente"}), 500

    if resultado == "nao_encontrado":
        return jsonify({"mensagem": "produto nao encontrado"}), 404
    if resultado == "tem_movimentacoes":
        return jsonify({
            "mensagem": (
                "produto possui movimentacoes no historico e nao pode ser excluido; "
                "mantenha o registro para preservar o historico"
            )
        }), 409

    return jsonify({"mensagem": "produto e registro de estoque excluidos"}), 200
