"""Persiste alterações de preço de um produto."""

import math

from app.core.database import get_db
from app.models.movement import StockMovement
from app.models.product import ProductNotFoundError

REASON_PRICE_CHANGE = 5 # ID do motivo na tabela ``motivos``.

def update_product_price(barcode, price, user_drt):
    """Atualiza o preço do produto e registra a alteração na mesma transação.

    Raises:
        ValueError: Se o preço for inválido ou o motivo não existir.
        ProductNotFoundError: Se o produto não existir.
        sqlite3.Error: Para qualquer falha do banco.
    """
    if (
        isinstance(price, bool)
        or not isinstance(price, (int, float))
        or not math.isfinite(price)
        or price < 0
    ):
        raise ValueError("valor do produto inválido")

    with get_db() as conn:
        row = conn.execute(
            "SELECT valor_prod FROM Produtos_cadastrados WHERE codigo_barras = ?",
            (barcode,),
        ).fetchone()
        if row is None:
            raise ProductNotFoundError("produto não encontrado")

        conn.execute(
            "UPDATE Produtos_cadastrados SET valor_prod = ? WHERE codigo_barras = ?",
            (price, barcode),
        )
        StockMovement.record(
            conn,
            barcode=barcode,
            status="ajuste",
            reason=REASON_PRICE_CHANGE,
            user_drt=user_drt,
            old_price=row["valor_prod"],
            new_price=price,
        )
