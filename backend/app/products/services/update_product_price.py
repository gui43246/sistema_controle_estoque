"""Persiste alterações de preço de um produto."""

import math

from app.core.database import get_db
from app.models.movimentacao import Movimentacao

MOTIVO_ALTERACAO_PRECO = 4  # id do motivo na tabela motivos


class ProdutoNaoEncontradoError(LookupError):
    """O código de barras informado não existe em Produtos_cadastrados."""


def update_product_price(barcode, price, user_drt):
    """Atualiza o preço do produto e registra a alteração na mesma transação.

    Raises:
        ValueError: Se o preço for inválido ou o motivo não existir.
        ProdutoNaoEncontradoError: Se o produto não existir.
        sqlite3.Error: Para qualquer falha do banco.
    """
    if (
        isinstance(price, bool)
        or not isinstance(price, (int, float))
        or not math.isfinite(price)
        or price < 0
    ):
        raise ValueError("valor do produto invalido")

    with get_db() as conn:
        linha = conn.execute(
            "SELECT valor_prod FROM Produtos_cadastrados WHERE codigo_barras = ?",
            (barcode,),
        ).fetchone()
        if linha is None:
            raise ProdutoNaoEncontradoError("produto nao encontrado")

        conn.execute(
            "UPDATE Produtos_cadastrados SET valor_prod = ? WHERE codigo_barras = ?",
            (price, barcode),
        )
        Movimentacao.registrar(
            conn,
            codigo_barras=barcode,
            status="ajuste",
            motivo=MOTIVO_ALTERACAO_PRECO,
            usuario_drt=user_drt,
            old_valor=linha["valor_prod"],
            new_valor=price,
        )