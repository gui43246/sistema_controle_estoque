"""Exclui logicamente um produto, zera seu estoque e registra a movimentação."""

from app.core.database import get_db
from app.models.product import ProductNotFoundError
from app.models.movement import StockMovement


def delete_product(barcode: str, reason_id: int, user_drt: str) -> None:
    """Marca o produto como excluído e registra a movimentação na mesma transação.

    Raises:
        ProductNotFoundError: Se o produto não existe ou já foi excluído.
        ValueError: Se o motivo não existir.
        sqlite3.Error: Para qualquer falha do banco.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """UPDATE Produtos_cadastrados
               SET status = 'excluido'
               WHERE codigo_barras = ? AND status = 'ativo'""",
            (barcode,),
        )
        if cursor.rowcount == 0:
            raise ProductNotFoundError("produto não encontrado")

        conn.execute(
            "UPDATE estoque SET quantidade = 0 WHERE codigo_barras = ?",
            (barcode,),
        )
        StockMovement.record(
            conn,
            barcode=barcode,
            status="exclusão",
            reason=reason_id,
            user_drt=user_drt,
        )
