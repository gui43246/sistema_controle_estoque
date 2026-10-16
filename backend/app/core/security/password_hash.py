"""Gera hashes bcrypt para armazenar senhas com segurança."""

import bcrypt

def criar_hash(senha_original=str)->bytes:
    """Cria e retorna o hash bcrypt de uma senha em formato de bytes."""
    salt =bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(senha_original.encode("utf-8"),salt)