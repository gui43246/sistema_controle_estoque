"""Cria tokens de acesso JWT para usuários autenticados."""

from flask_jwt_extended import create_access_token
from datetime import timedelta

def GerarTokenAcesso(identidade:str,validade:int=5)->str:
    """Gera um token JWT de acesso com identidade e validade em minutos."""
    token=create_access_token(
        identity=identidade,
        expires_delta=timedelta(minutes=validade)
    )
    return token





