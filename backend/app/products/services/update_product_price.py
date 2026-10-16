"""Persiste alterações de preço de um produto."""

import sqlite3

from app.core.database import get_db


def update_product_price(barcode, price):
    """Atualiza o preço do produto identificado pelo código de barras."""
    if price <= 0:
        return False

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE Produtos_cadastrados
                SET valor_prod = ?
                WHERE codigo_barras = ?
                """,
                (price, barcode),
            )
            if cursor.rowcount == 0:
                return False
            conn.commit()
        return True
    except sqlite3.Error:
        return False
