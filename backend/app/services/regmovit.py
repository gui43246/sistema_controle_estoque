"""Registra movimentações e atualiza o estoque dentro de transações SQLite."""

from app.DATABASE import get_db
from .motivos import buscar_motivo


def registrar_movimentacao(
    codigo_barras: str,
    quantidade: int,
    status: str,
    motivo: int,
    usuario_drt: str,
):
    """Insere uma movimentação usando a descrição do motivo cadastrada."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO movimentacoes
                (codigo_barras, quantidade, status, motivo, usuario_drt)
            VALUES (?, ?, ?, ?, ?)
            """,
            (codigo_barras, quantidade, status, buscar_motivo(motivo), usuario_drt),
        )
        return cursor.lastrowid
