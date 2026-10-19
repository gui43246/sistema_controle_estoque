"""Valida as credenciais e emite um token de acesso."""

import logging

from flask import jsonify, request

from app import limiter
from app.core.database import get_db
from app.core.security.jwt_authentication import generate_access_token
from app.core.security.password_hash import hash_password
from app.core.security.password_hash_verification import verify_password
from app.users import users_bp

logger = logging.getLogger(__name__)

DUMMY_PASSWORD_HASH = hash_password("Descartavel1!")


@users_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    """Valida credenciais e retorna um JWT quando a senha está correta."""
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict) or any(
        field not in payload for field in ("drt", "senha_digitada")
    ):
        return jsonify({"mensagem": "Verifique os dados e tente novamente"}), 400

    drt = payload["drt"]
    password = payload["senha_digitada"]
    if (
        not isinstance(drt, str)
        or not isinstance(password, str)
        or not drt.strip()
        or not password
    ):
        return jsonify({"mensagem": "DRT e senha devem ser textos válidos"}), 400

    try:
        with get_db() as conn:
            user = conn.execute(
                "SELECT drt, senha FROM users WHERE drt = ?", (drt,)
            ).fetchone()
    except Exception:
        logger.exception("erro ao consultar usuário no login")
        return jsonify({"mensagem": "erro interno, tente novamente mais tarde"}), 500

    stored_password_hash = user["senha"] if user is not None else DUMMY_PASSWORD_HASH
    password_matches = verify_password(password, stored_password_hash)

    if user is None or not password_matches:
        return jsonify({"mensagem": "DRT ou senha incorretos"}), 401

    token = generate_access_token(identity=drt)
    return jsonify({"mensagem": "login realizado", "token": token}), 200
