"""Persiste alterações simples de quantidade em estoque."""

from app.core.database import get_db
from app.models.movimentacao import EstoqueNaoEncontradoError, Movimentacao


def update_stock_quantity(barcode, quantity, usuario_drt, motivo):
    """Atualiza a quantidade em estoque e registra o ajuste na mesma transação.

    Args:
        barcode: Código de barras do produto.
        quantity: Nova quantidade total em estoque (inteiro, zero ou mais).
        usuario_drt: DRT do usuário responsável.
        motivo: Id do motivo na tabela ``motivos``.

    Raises:
        ValueError: Se a quantidade for inválida ou o motivo não existir.
        EstoqueNaoEncontradoError: Se o item não existir no estoque.
        sqlite3.Error: Para qualquer falha do banco.
    """
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
        raise ValueError("quantidade invalida")

    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE estoque SET quantidade = ? WHERE codigo_barras = ?",
            (quantity, barcode),
        )
        if cursor.rowcount == 0:
            raise EstoqueNaoEncontradoError("estoque nao encontrado")

        Movimentacao.registrar(
            conn,
            codigo_barras=barcode,
            status="ajuste",
            motivo=motivo,
            usuario_drt=usuario_drt,
            quantidade=quantity,
        )