"""Define e registra as rotas de usuários e autenticação."""

from flask import Blueprint
users_bp = Blueprint("users", __name__)

from .routes import (
    authenticate_user,
    create_user,
    delete_user,
    list_users,
    reset_password,
)



