"""Verifica o tamanho e os tipos de caracteres exigidos para uma senha."""

import re

def validate_password(password: str) -> tuple[bool, str]:
    """Retorna se a senha atende aos requisitos e a mensagem correspondente."""
    if not isinstance(password, str):
        return False, "senha inválida"

    if len(password) <8:
        return False ,"senha curta"
        
    if len(password) > 64 or len(password.encode("utf-8")) > 72:
        return False, "senha comprida"
    if not re.search(r"[A-Z]",password):
        return False, "falta letra maiúscula"
    
    if not re.search(r"[a-z]",password):
        return False, "faltam letras minúsculas"
    
    if not re.search(r"[0-9]",password):
        return False, "faltam números"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "falta caractere especial"
    
    return True, "senha válida"
