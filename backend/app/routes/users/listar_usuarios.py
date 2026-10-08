"""Lista os usuários sem expor os hashes de senha."""

import sqlite3

from flask import jsonify
from flask_jwt_extended import jwt_required

from app.DATABASE import get_db
from app.routes.users import users_bp
from app import limiter


@users_bp.route("/usuarios", methods=["GET"])
@limiter.limit("30 per minute")
@jwt_required()
def listar_usuarios():
    """Retorna os dados públicos dos usuários autenticados."""
    try:
        with get_db() as conn:
            usuarios = conn.execute(
                """
                SELECT id, drt, name, email, numero_telefone, tipo_user
                FROM users
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()

        return jsonify([dict(usuario) for usuario in usuarios]), 200
    except sqlite3.Error:
        return jsonify({"mensagem": "erro ao consultar usuários"}), 500
