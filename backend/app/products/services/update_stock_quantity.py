"""Persiste alterações simples de quantidade em estoque."""

from app.core.database import get_db
from app.models.movement import StockNotFoundError, StockMovement


def update_stock_quantity(barcode, quantity, user_drt, reason):
    """Atualiza a quantidade em estoque e registra o ajuste na mesma transação.

    Args:
        barcode: Código de barras do produto.
        quantity: Nova quantidade total em estoque (inteiro, zero ou mais).
        user_drt: DRT do usuário responsável.
        reason: ID do motivo na tabela ``motivos``.

    Raises:
        ValueError: Se a quantidade for inválida ou o motivo não existir.
        StockNotFoundError: Se o item não existir no estoque.
        sqlite3.Error: Para qualquer falha do banco.
    """
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
        raise ValueError("quantidade inválida")

    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE estoque SET quantidade = ? WHERE codigo_barras = ?",
            (quantity, barcode),
        )
        if cursor.rowcount == 0:
            raise StockNotFoundError("estoque não encontrado")

        StockMovement.record(
            conn,
            barcode=barcode,
            status="ajuste",
            reason=reason,
            user_drt=user_drt,
            quantity=quantity,
        )
