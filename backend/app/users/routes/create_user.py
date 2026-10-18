"""Valida e cadastra uma conta de usuário comum."""

import logging
import sqlite3
from flask import request, jsonify
from app.users import users_bp
from app.models.create_user import CreateUser, UserValidationError
from app.core.security.authorization import admin_required
from app import limiter
from app.core.database import get_db

logger = logging.getLogger(__name__)
@users_bp.route("/Cadastro_usuario", methods=["POST"])
@limiter.limit("10 per minute")
@admin_required
def cadastrar_usuario():
    """Cria a conta a partir dos dados preparados pela classe de domínio."""
    dados = request.get_json(silent=True)
    try:
        new_user = CreateUser.from_payload(dados)
    except UserValidationError as error:
        return jsonify({"mensagem": str(error)}), error.status_code
    
    try:
        with get_db() as conn:
            new_user.inserir(conn)
    except sqlite3.IntegrityError:
        return jsonify({"mensagem": "DRT, email ou telefone ja cadastrados"}), 409
    except Exception:
        logger.exception("erro ao cadastrar usuario")
        return jsonify({"mensagem": "erro interno, tente novamente mais tarde"}), 500

    return jsonify({"mensagem": "ok usuario cadastrado"}), 201


