"""Valida nomes formados por letras e espaços."""

def validate_name(name: str) -> bool:
    """Retorna se cada parte do nome contém apenas letras Unicode."""
    if not isinstance(name, str):
        return False
    parts = name.split()
    return bool(parts) and all(part.isalpha() for part in parts)
