"""Persiste alterações de setor de um produto."""

from app.core.database import get_db
from app.models.product import ProductNotFoundError


def update_product_sector(barcode, sector_id) -> bool:
    """Atualiza o setor de um produto ativo.

    Returns:
        ``True`` quando um produto ativo é atualizado.

    Raises:
        ProductNotFoundError: Se o produto não existe ou foi excluído.
        sqlite3.Error: Para qualquer falha do banco.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """
            UPDATE Produtos_cadastrados
            SET setor_id = ?
            WHERE codigo_barras = ? AND status = 'ativo'
            """,
            (sector_id, barcode),
        )
        if cursor.rowcount == 0:
            raise ProductNotFoundError("produto não encontrado")
        return True
