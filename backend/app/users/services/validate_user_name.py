"""Valida nomes formados por letras e espaços."""

def validar_name(name: str) -> bool:
    """Retorna se cada parte do nome contém apenas letras Unicode."""
    if not isinstance(name, str):
        return False
    partes = name.split()
    return bool(partes) and all(parte.isalpha() for parte in partes)
