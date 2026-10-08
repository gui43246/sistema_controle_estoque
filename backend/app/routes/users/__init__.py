"""Define e registra as rotas de usuários e autenticação."""

from flask import Blueprint
users_bp = Blueprint("users", __name__)

from . import cadastrar_usuario, reset_senha, login, listar_usuarios, excluir_usuario



