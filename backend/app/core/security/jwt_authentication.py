"""Cria tokens de acesso JWT para usuários autenticados."""

from flask_jwt_extended import create_access_token
from datetime import timedelta

def generate_access_token(identity:str,expiration_minutes:int=5)->str:
    """Gera um token JWT de acesso com identidade e validade em minutos."""
    token=create_access_token(
        identity=identity,
        expires_delta=timedelta(minutes=expiration_minutes)
    )
    return token





