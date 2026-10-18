"""Consulta o nome de um setor pelo identificador."""

from app.core.database import get_db


def buscar_setor(id: int) -> str | None:
    """Retorna o nome do setor ou None quando o identificador não existe."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
                       SELECT nome_setor from setor
                       Where id=?""",
            (id,),
        )
        resultado = cursor.fetchone()
        return resultado["nome_setor"] if resultado is not None else None
