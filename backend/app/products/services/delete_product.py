"""Exclui logicamente um produto, zera seu estoque e registra a movimentação."""

from app.core.database import get_db
from app.models.product import ProdutoNaoEncontradoError
from app.models.movimentacao import Movimentacao


def excluir_produto(codigo_barras: str, motivo_id: int, usuario_drt: str) -> None:
    """Marca o produto como excluído e registra a movimentação na mesma transação.

    Raises:
        ProdutoNaoEncontradoError: Se o produto não existe ou já foi excluído.
        ValueError: Se o motivo não existir.
        sqlite3.Error: Para qualquer falha do banco.
    """
    with get_db() as conn:
        cursor = conn.execute(
            """UPDATE Produtos_cadastrados
               SET status = 'excluido'
               WHERE codigo_barras = ? AND status = 'ativo'""",
            (codigo_barras,),
        )
        if cursor.rowcount == 0:
            raise ProdutoNaoEncontradoError("produto nao encontrado")

        conn.execute(
            "UPDATE estoque SET quantidade = 0 WHERE codigo_barras = ?",
            (codigo_barras,),
        )
        Movimentacao.registrar(
            conn,
            codigo_barras=codigo_barras,
            status="exclusão",
            motivo=motivo_id,
            usuario_drt=usuario_drt,
        )