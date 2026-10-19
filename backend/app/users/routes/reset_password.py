"""Valida e redefine a senha de uma conta existente."""

import logging
from app.users import users_bp
from app.core.database import get_db
from flask import request, jsonify
from app.users.services import validate_password
from app.core.security.password_hash import hash_password
from app.core.security.authorization import admin_required
from app import limiter

logger = logging.getLogger(__name__)


@users_bp.route("/reset_senha", methods=["POST"])
@limiter.limit("10 per minute")
@admin_required
def reset_password_route():
    """Confere a nova senha e atualiza o hash da conta indicada."""
    request_data = request.get_json(silent=True)
    required_fields = ["drt", "nova_senha", "confirmar_senha"]

    if not isinstance(request_data, dict) or any(
        field not in request_data for field in required_fields
    ):
        return jsonify({"mensagem": "Verifique os campos enviados"}), 400

    drt = request_data["drt"]
    new_password = request_data["nova_senha"]
    confirm_password = request_data["confirmar_senha"]

    if any(not isinstance(value, str) for value in (drt, new_password, confirm_password)):
        return jsonify({"mensagem": "todos os campos devem ser textos"}), 400

    password_is_valid, message = validate_password(new_password)
    if not password_is_valid:
        return jsonify({"mensagem": message}), 400

    if confirm_password != new_password:
        return jsonify({"mensagem": "As senhas devem corresponder"}), 400

    try:
        with get_db() as conn:
            cursor = conn.execute(
                """
                UPDATE users
                SET senha = ?
                WHERE drt = ?
                """,
                (hash_password(new_password), drt),
            )

            if cursor.rowcount == 0:
                return jsonify({"mensagem": "Usuário não encontrado"}), 404

        return jsonify({"mensagem": "Senha alterada com sucesso"}), 200

    except Exception:
        logger.exception("erro ao alterar senha")
        return jsonify({"mensagem": "erro interno, tente novamente mais tarde"}), 500
