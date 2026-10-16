"""Persiste alterações de setor de um produto."""

import sqlite3

from app.core.database import get_db


def update_product_sector(barcode, sector_id):
    """Atualiza o setor associado ao código de barras informado."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE Produtos_cadastrados
                SET setor_id = ?
                WHERE codigo_barras = ?
                """,
                (sector_id, barcode),
            )
            if cursor.rowcount == 0:
                return False
            conn.commit()
        return True
    except sqlite3.Error:
        return False
