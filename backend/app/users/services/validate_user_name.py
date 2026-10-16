"""Valida nomes formados por letras e espaços."""

import re

def validar_name(name: str) -> bool:
    """Retorna se o nome contém somente letras ASCII e espaços."""
    if not isinstance(name, str):
        return False
    return bool(re.match(r"^[A-Za-z ]+$", name))
