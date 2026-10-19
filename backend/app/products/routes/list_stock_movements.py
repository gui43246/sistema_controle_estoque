"""Lista o histórico de movimentações de estoque."""

import sqlite3

from flask import jsonify
from flask_jwt_extended import jwt_required

from app.core.database import get_db
from app.products import products_bp
from app import limiter


@products_bp.route("/movimentacoes", methods=["GET"])
@limiter.limit("30 per minute")
@jwt_required()
def list_stock_movements_route():
    """Retorna o histórico de movimentações com produto e usuário associados."""
    try:
        with get_db() as conn:
            movements = conn.execute(
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

        return jsonify([dict(movement) for movement in movements]), 200
    except sqlite3.Error:
        return jsonify({"mensagem": "erro ao consultar movimentações"}), 500
