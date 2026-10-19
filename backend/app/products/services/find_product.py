"""Consulta o status ou os dados completos de um produto pelo código de barras."""

from app.core.database import get_db


def find_product(barcode, config="status") -> bool | dict | None:
    """Consulta um produto pelo código de barras.

    Args:
        barcode: Código de barras do produto.
        config: ``"status"`` (padrão) ou ``"data"``.

    Returns:
        - ``config="status"``: ``True`` se o produto existe e está ativo;
          ``False`` se não existe ou se foi excluído.
        - ``config="data"``: ``dict`` com as colunas do produto ativo, ou
          ``None`` se não for encontrado.

    Raises:
        ValueError: Se ``config`` for diferente de ``"status"`` e ``"data"``.
        sqlite3.Error: Para falhas do banco.
    """
    if config not in ("status", "data"):
        raise ValueError("config deve ser 'status' ou 'data'")

    with get_db() as conn:
        if config == "status":
            result = conn.execute(
                "SELECT status FROM Produtos_cadastrados WHERE codigo_barras = ?",
                (barcode,),
            ).fetchone()
            return result is not None and result["status"] == "ativo"

        product = conn.execute(
            """
            SELECT
                p.codigo_barras,
                p.nome_produto,
                p.valor_prod,
                p.setor_id,
                s.nome_setor,
                COALESCE(e.quantidade, 0) AS quantidade
            FROM Produtos_cadastrados p
            LEFT JOIN setor s ON s.id = p.setor_id
            LEFT JOIN estoque e ON e.codigo_barras = p.codigo_barras
            WHERE p.codigo_barras = ? AND p.status = 'ativo'
            """,
            (barcode,),
        ).fetchone()
        return dict(product) if product is not None else None
