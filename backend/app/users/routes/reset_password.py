"""Valida e redefine a senha de uma conta existente."""

import logging
from app.users import users_bp
from app.core.database import get_db
from flask import request, jsonify
from app.users.services import validar_senha
from app.core.security.password_hash import criar_hash
from app.core.security.authorization import admin_required
from app import limiter

logger = logging.getLogger(__name__)


@users_bp.route("/reset_senha", methods=["POST"])
@limiter.limit("10 per minute")
@admin_required
def resetar_senha():
    """Confere a nova senha e atualiza o hash da conta indicada."""
    requisicao = request.get_json(silent=True)
    campos_obrigatorios = ["drt", "nova_senha", "confirmar_senha"]

    if not isinstance(requisicao, dict) or any(
        campo not in requisicao for campo in campos_obrigatorios
    ):
        return jsonify({"mensagem": "Verifique os campos enviados"}), 400

    drt = requisicao["drt"]
    nova_senha = requisicao["nova_senha"]
    confirmar_senha = requisicao["confirmar_senha"]

    if any(not isinstance(valor, str) for valor in (drt, nova_senha, confirmar_senha)):
        return jsonify({"mensagem": "todos os campos devem ser textos"}), 400

    senha_valida, mensagem = validar_senha(nova_senha)
    if not senha_valida:
        return jsonify({"mensagem": mensagem}), 400

    if confirmar_senha != nova_senha:
        return jsonify({"mensagem": "As senhas devem corresponder"}), 400

    try:
        with get_db() as conn:
            cursor = conn.execute(
                """
                UPDATE users
                SET senha = ?
                WHERE drt = ?
                """,
                (criar_hash(nova_senha), drt),
            )

            if cursor.rowcount == 0:
                return jsonify({"mensagem": "Usuario nao encontrado"}), 404

        return jsonify({"mensagem": "Senha alterada com sucesso"}), 200

    except Exception:
        logger.exception("erro ao alterar senha")
        return jsonify({"mensagem": "erro interno, tente novamente mais tarde"}), 500
