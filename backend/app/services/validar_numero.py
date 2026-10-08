"""Valida números telefônicos usando os metadados da biblioteca phonenumbers."""

import phonenumbers
import re

def validar_telefone(numero: str, default_region: str = "BR") -> bool:
    """
    Valida um número de telefone a partir de uma string contendo apenas dígitos
    (sem símbolos como +, -, (), espaços etc.).

    Etapas:
    1. Remove todos os caracteres que não sejam dígitos.
    2. Se o número já começar com um código de país (ex.: 55 para Brasil, 1 para EUA, 44 para Reino Unido),
       adiciona automaticamente o prefixo '+' e interpreta como número internacional.
    3. Caso contrário, assume a região padrão informada (default_region).
    4. Usa a biblioteca 'phonenumbers' para verificar se o número é válido.

    Parâmetros:
    ----------
    numero : str
        String contendo o número de telefone (pode ter símbolos ou apenas dígitos).
    default_region : str, opcional
        Região padrão a ser usada caso o número não inclua código de país.
        O valor padrão é "BR" (Brasil).

    Retorno:
    --------
    bool
        True se o número for válido de acordo com o padrão E.164 e regras da região,
        False caso contrário.

    Exemplos:
    ---------
    >>> validar_telefone("11912345678")
    True   # Número válido no Brasil

    >>> validar_telefone("2025550125", "US")
    True   # Número válido nos EUA

    >>> validar_telefone("4479460958", "GB")
    True   # Número válido no Reino Unido

    >>> validar_telefone("12345")
    False  # Número inválido
    """
    apenas_digitos = re.sub(r"\D", "", numero)

    try:
        # Números brasileiros locais com DDD têm 10 ou 11 dígitos e podem
        # começar por "1" (por exemplo, DDD 11). Não os confunda com +1.
        numero_local_br = default_region == "BR" and len(apenas_digitos) in (10, 11)
        if apenas_digitos.startswith("55") or (
            not numero_local_br and apenas_digitos.startswith(("1", "44"))
        ):
            telefone = phonenumbers.parse("+" + apenas_digitos, None)
        else:
            telefone = phonenumbers.parse(apenas_digitos, default_region)

        return phonenumbers.is_valid_number(telefone)
    except phonenumbers.NumberParseException:
        return False
