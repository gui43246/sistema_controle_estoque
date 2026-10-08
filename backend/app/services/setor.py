"""Consulta o nome de um setor pelo identificador."""

from app.DATABASE import get_db


def buscar_setor(id: int) -> str:
    """Retorna a linha do setor encontrado ou a indicação textual de setor desconhecido."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
                       SELECT nome_setor from setor
                       Where id=?""",
            (id,),
        )
        resultado = cursor.fetchone()
        if resultado is None:
            return "nao indentificado"
        return resultado
