"""Valida as credenciais e emite um token de acesso."""

import logging

from flask import jsonify, request

from app import limiter
from app.core.database import get_db
from app.core.security.jwt_authentication import GerarTokenAcesso
from app.core.security.password_hash import criar_hash
from app.core.security.password_hash_verification import verifique_hash
from app.users import users_bp

logger = logging.getLogger(__name__)

HASH_FALSO = criar_hash("Descartavel1!")


@users_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    """Valida credenciais e retorna um JWT quando a senha está correta."""
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict) or any(
        campo not in dados for campo in ("drt", "senha_digitada")
    ):
        return jsonify({"mensagem": "Verifique os dados e tente novamente"}), 400

    drt = dados["drt"]
    senha_digitada = dados["senha_digitada"]
    if (
        not isinstance(drt, str)
        or not isinstance(senha_digitada, str)
        or not drt.strip()
        or not senha_digitada
    ):
        return jsonify({"mensagem": "DRT e senha devem ser textos validos"}), 400

    try:
        with get_db() as conn:
            usuario = conn.execute(
                "SELECT drt, senha FROM users WHERE drt = ?", (drt,)
            ).fetchone()
    except Exception:
        logger.exception("erro ao consultar usuario no login")
        return jsonify({"mensagem": "erro interno, tente novamente mais tarde"}), 500

    senha_armazenada = usuario["senha"] if usuario else HASH_FALSO
    senha_confere = verifique_hash(senha_digitada, senha_armazenada)

    if usuario is None or not senha_confere:
        return jsonify({"mensagem": "DRT ou senha incorretos"}), 401

    token = GerarTokenAcesso(identidade=drt)
    return jsonify({"mensagem": "login realizado", "token": token}), 200