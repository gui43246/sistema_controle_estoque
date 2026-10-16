"""Verifica o tamanho e os tipos de caracteres exigidos para uma senha."""

import re

def validar_senha(senha=str)->tuple[bool,str]:
    """Retorna se a senha atende aos requisitos e a mensagem correspondente."""
    if not isinstance(senha, str):
        return False, "senha invalida"

    if len(senha) <8:
        return False ,"senha curta"
        
    if len(senha) >20:
        return False,"senha comprida"
    if not re.search(r"[A-Z]",senha):
        return False, "falta letras maiuscula"
    
    if not re.search(r"[a-z]",senha):
        return False,"falta letras minusculas"
    
    if not re.search(r"[0-9]",senha):
        return False, "falta numeros"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):
        return False, "falta caractere especial"
    
    return True, "senha valida"
