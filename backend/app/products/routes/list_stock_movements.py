"""Lista o histórico de movimentações de estoque."""

import sqlite3

from flask import jsonify, request
from flask_jwt_extended import jwt_required

from app.core.database import get_db
from app.products import products_bp
from app import limiter
from app.utils.pagination import parse_pagination


@products_bp.route("/movimentacoes", methods=["GET"])
@limiter.limit("30 per minute")
@jwt_required()
def list_stock_movements_route():
    """Retorna o histórico de movimentações com produto e usuário associados."""
    try:
        page, per_page = parse_pagination(request.args)
        with get_db() as conn:
            total = conn.execute("SELECT COUNT(*) FROM movimentacoes").fetchone()[0]
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
                LIMIT ? OFFSET ?
                """
                , (per_page, (page - 1) * per_page)
            ).fetchall()

        return jsonify({
            "items": [dict(movement) for movement in movements],
            "page": page,
            "per_page": per_page,
            "total": total,
        }), 200
    except ValueError as error:
        return jsonify({"mensagem": str(error)}), 400
    except sqlite3.Error:
        return jsonify({"mensagem": "erro ao consultar movimentações"}), 500
