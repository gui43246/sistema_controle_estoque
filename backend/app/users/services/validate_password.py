"""Verifica o tamanho e os tipos de caracteres exigidos para uma senha."""

import re

def validar_senha(senha: str) -> tuple[bool, str]:
    """Retorna se a senha atende aos requisitos e a mensagem correspondente."""
    if not isinstance(senha, str):
        return False, "senha invalida"

    if len(senha) <8:
        return False ,"senha curta"
        
    if len(senha) > 64 or len(senha.encode("utf-8")) > 72:
        return False, "senha comprida"
    if not re.search(r"[A-Z]",senha):
        return False, "falta letra maiúscula"
    
    if not re.search(r"[a-z]",senha):
        return False, "faltam letras minúsculas"
    
    if not re.search(r"[0-9]",senha):
        return False, "faltam números"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):
        return False, "falta caractere especial"
    
    return True, "senha valida"
