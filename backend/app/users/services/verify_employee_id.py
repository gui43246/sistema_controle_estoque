"""Valida o formato da identificação DRT de um usuário."""

import re


def validate_drt(drt: str) -> tuple[bool, str]:
    """Verifica se a DRT contém exatamente nove dígitos ASCII."""
    if not isinstance(drt,str):
        return False, "campo inválido"

    if not re.fullmatch(r"[0-9]{9}", drt):
        return False, "Verifique a DRT"
    return True, "ok"
