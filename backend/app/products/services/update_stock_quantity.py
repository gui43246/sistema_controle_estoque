"""Persiste alterações simples de quantidade em estoque."""

import sqlite3

from app.core.database import get_db


def update_stock_quantity(barcode, quantity):
    """Atualiza a quantidade em estoque para o produto informado."""
    if quantity < 0:
        return False

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE estoque
                SET quantidade = ?
                WHERE codigo_barras = ?
                """,
                (quantity, barcode),
            )
            if cursor.rowcount == 0:
                return False
            conn.commit()
        return True
    except sqlite3.Error:
        return False
