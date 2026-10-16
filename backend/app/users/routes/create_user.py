"""Valida e cadastra uma conta de usuário comum."""

from flask import request, jsonify
from app.users import users_bp
from app.models.create_user import CreateUser, UserValidationError
from app.core.security.authorization import admin_required
from app import limiter
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
    
    if new_user.commit():
        return jsonify({"mensagem": "ok usuario cadastrado"}), 201
    return jsonify({"mensagem": "DRT, email ou telefone ja cadastrados"}), 409


