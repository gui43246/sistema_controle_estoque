"""Gera hashes bcrypt para armazenar senhas com segurança."""

import bcrypt

def hash_password(password: str) -> bytes:
    """Cria e retorna o hash bcrypt de uma senha em formato de bytes."""
    salt =bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"),salt)
