"""Lista os usuários sem expor os hashes de senha."""

import logging

from flask import jsonify

from app.core.database import get_db
from app.users import users_bp
from app import limiter
from app.core.security.authorization import admin_required

logger = logging.getLogger(__name__)


@users_bp.route("/usuarios", methods=["GET"])
@limiter.limit("30 per minute")
@admin_required
def list_users_route():
    """Retorna os dados públicos dos usuários autenticados."""
    try:
        with get_db() as conn:
            users = conn.execute(
                """
                SELECT id, drt, name, email, numero_telefone, tipo_user
                FROM users
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()

        return jsonify([dict(user) for user in users]), 200
    except Exception:
        logger.exception("erro ao consultar usuários")
        return jsonify({"mensagem": "erro interno, tente novamente mais tarde"}), 500
