"""Consulta a descrição de um motivo de movimentação pelo identificador."""

from app.DATABASE import get_db


def buscar_motivo(id: int) -> str | None:
    """Retorna a descrição do motivo ou None quando o identificador não existe."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT descricao FROM motivos WHERE id = ?",
            (id,),
        )
        resultado = cursor.fetchone()

        if resultado is None:
            return None

        return resultado["descricao"]