"""Persiste alterações de setor de um produto."""

from app.core.database import get_db
from app.models.product import ProdutoNaoEncontradoError


def update_product_sector(barcode, sector_id):
    """Atualiza o setor de um produto ativo.

    Raises:
        ProdutoNaoEncontradoError: Se o produto não existe ou foi excluído.
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
            raise ProdutoNaoEncontradoError("produto nao encontrado")