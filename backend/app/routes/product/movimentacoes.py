"""Lista o histórico de movimentações de estoque."""

import sqlite3

from flask import jsonify
from flask_jwt_extended import jwt_required

from app.DATABASE import get_db
from app.routes.product import produtos_bp
from app import limiter


@produtos_bp.route("/movimentacoes", methods=["GET"])
@limiter.limit("30 per minute")
@jwt_required()
def listar_movimentacoes():
    """Retorna o histórico de movimentações com produto e usuário associados."""
    try:
        with get_db() as conn:
            movimentacoes = conn.execute(
                """
                SELECT
                    m.id,
                    m.codigo_barras,
                    p.nome_produto,
                    m.quantidade,
                    m.status,
                    m.motivo,
                    m.data_hora,
                    m.usuario_drt,
                    u.name AS nome_usuario
                FROM movimentacoes m
                LEFT JOIN Produtos_cadastrados p
                    ON p.codigo_barras = m.codigo_barras
                LEFT JOIN users u
                    ON u.drt = m.usuario_drt
                ORDER BY m.data_hora DESC, m.id DESC
                """
            ).fetchall()

        return jsonify([dict(movimentacao) for movimentacao in movimentacoes]), 200
    except sqlite3.Error:
        return jsonify({"mensagem": "erro ao consultar movimentacoes"}), 500
