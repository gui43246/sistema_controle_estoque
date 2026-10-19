"""Valida o formato do e-mail e restringe os domínios aceitos."""

import re

allowed_email_providers = [
    "gmail.com",
    "outlook.com",
    "hotmail.com",
    "yahoo.com",
    "icloud.com",
    "live.com",
    "aol.com"
]


def validate_email(email: str) -> bool:
    """Valida se uma string é um e-mail com formato correto e provedor permitido.

    A validação ocorre em duas etapas:
    1. Verifica se o e-mail segue um formato válido (via regex), rejeitando
       casos como ponto duplicado, ponto/hífen logo após o '@', ou parte
       local iniciando/terminando com ponto.
    2. Verifica se o domínio do e-mail está na lista de provedores
       permitidos (`allowed_email_providers`).

    Args:
        email: Endereço de e-mail a ser validado.

    Returns:
        ``True`` se o e-mail tiver formato válido e o domínio estiver
            na lista de provedores permitidos; caso contrário, ``False``,
            incluindo quando `email` for vazio, None ou não for string.

    Examples:
        >>> validate_email("usuario@gmail.com")
        True
        >>> validate_email("usuario@gmail.br")
        False
        >>> validate_email("usuario@empresaxyz.com")
        False
        >>> validate_email("")
        False
    """
    if not isinstance(email, str) or not email:
        return False

    pattern = r'^(?!\.)[a-zA-Z0-9._%+-]+(?<!\.)@(?!-)(?!\.)[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$'
    if not bool(re.match(pattern, email)):
        return False

    domain = email.split("@")[-1].lower()
    return domain in allowed_email_providers


