"""Compara uma senha informada com seu hash bcrypt armazenado."""

import bcrypt

def verify_password(password: str, stored_hash: bytes) -> bool:
    
    """Retorna se a senha informada corresponde ao hash bcrypt fornecido."""
    return bcrypt.checkpw(password.encode("utf-8"),stored_hash)
