"""Compara uma senha informada com seu hash bcrypt armazenado."""

import bcrypt

def verifique_hash(senha_digitada=str,hash_armazenado=bytes)->bool:
    
    """Retorna se a senha informada corresponde ao hash bcrypt fornecido."""
    return bcrypt.checkpw(senha_digitada.encode("utf-8"),hash_armazenado)
