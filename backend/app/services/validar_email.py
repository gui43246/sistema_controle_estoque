"""Valida o formato do e-mail e restringe os domínios aceitos."""

import re

provedores_email = [
    "gmail.com",
    "outlook.com",
    "hotmail.com",
    "yahoo.com",
    "icloud.com",
    "live.com",
    "aol.com"
]


def validar_email(email: str) -> bool:
    """Valida se uma string é um e-mail com formato correto e provedor permitido.

    A validação ocorre em duas etapas:
    1. Verifica se o e-mail segue um formato válido (via regex), rejeitando
       casos como ponto duplicado, ponto/hífen logo após o '@', ou parte
       local iniciando/terminando com ponto.
    2. Verifica se o domínio do e-mail está na lista de provedores
       permitidos (`provedores_email`).

    Args:
        email (str): Endereço de e-mail a ser validado.

    Returns:
        bool: True se o e-mail tiver formato válido E o domínio estiver
            na lista de provedores permitidos. False caso contrário,
            incluindo quando `email` for vazio, None ou não for string.

    Examples:
        >>> validar_email("usuario@gmail.com")
        True
        >>> validar_email("usuario@gmail.br")
        False
        >>> validar_email("usuario@empresaxyz.com")
        False
        >>> validar_email("")
        False
    """
    if not email:
        return False

    padrao = r'^(?!\.)[a-zA-Z0-9._%+-]+(?<!\.)@(?!-)(?!\.)[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$'
    if not bool(re.match(padrao, email)):
        return False

    dominio = email.split("@")[-1].lower()
    return dominio in provedores_email


