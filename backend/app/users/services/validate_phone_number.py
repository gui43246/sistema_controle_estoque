"""Valida números telefônicos usando os metadados da biblioteca phonenumbers."""

import phonenumbers
import re

def validate_phone_number(phone_number: str, default_region: str = "BR") -> bool:
    """Valida um telefone com os metadados da biblioteca ``phonenumbers``.

    Remove caracteres que não sejam dígitos. Números com código de país
    recebem o prefixo ``+``; os demais são interpretados na região indicada.

    Args:
        phone_number: Telefone informado, com ou sem símbolos de formatação.
        default_region: Região usada quando o telefone não inclui código de país.
            O padrão é ``"BR"``.

    Returns:
        ``True`` se o número for válido para a região; caso contrário, ``False``.

    Examples:
        >>> validate_phone_number("11912345678")
        True
        >>> validate_phone_number("12345")
        False
    """
    if not isinstance(phone_number, str):
        return False

    digits_only = re.sub(r"\D", "", phone_number)

    try:
        # Números brasileiros locais com DDD têm 10 ou 11 dígitos e podem
        # começar por "1" (por exemplo, DDD 11). Não os confunda com +1.
        brazilian_local_number = default_region == "BR" and len(digits_only) in (10, 11)
        if digits_only.startswith("55") or (
            not brazilian_local_number and digits_only.startswith(("1", "44"))
        ):
            phone_number = phonenumbers.parse("+" + digits_only, None)
        else:
            phone_number = phonenumbers.parse(digits_only, default_region)

        return phonenumbers.is_valid_number(phone_number)
    except phonenumbers.NumberParseException:
        return False
