"""Consulta o nome de um setor pelo identificador."""

from app.core.database import get_db


def find_sector(sector_id: int) -> str | None:
    """Retorna o nome do setor ou None quando o identificador não existe."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
                       SELECT nome_setor from setor
                       Where id=?""",
            (sector_id,),
        )
        result = cursor.fetchone()
        return result["nome_setor"] if result is not None else None
