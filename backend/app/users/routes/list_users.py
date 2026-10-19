"""Lista os usuários sem expor os hashes de senha."""

import logging
import sqlite3

from flask import jsonify, request

from app.core.database import get_db
from app.users import users_bp
from app import limiter
from app.core.security.authorization import admin_required
from app.utils.pagination import parse_pagination

logger = logging.getLogger(__name__)


@users_bp.route("/usuarios", methods=["GET"])
@limiter.limit("30 per minute")
@admin_required
def list_users_route():
    """Retorna os dados públicos dos usuários autenticados."""
    try:
        page, per_page = parse_pagination(request.args)
        with get_db() as conn:
            total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            users = conn.execute(
                """
                SELECT id, drt, name, email, numero_telefone, tipo_user
                FROM users
                ORDER BY name COLLATE NOCASE, id
                LIMIT ? OFFSET ?
                """, (per_page, (page - 1) * per_page)
            ).fetchall()

        return jsonify({
            "items": [dict(user) for user in users],
            "page": page,
            "per_page": per_page,
            "total": total,
        }), 200
    except ValueError as error:
        return jsonify({"mensagem": str(error)}), 400
    except sqlite3.Error:
        logger.exception("erro ao consultar usuários")
        return jsonify({"mensagem": "erro interno, tente novamente mais tarde"}), 500
