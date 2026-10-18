"""Consulta o status ou os dados completos de um produto pelo código de barras."""

from app.core.database import get_db


def buscar(codigo_barras, config="status") -> bool | dict | None:
    """Consulta um produto pelo código de barras.

    Args:
        codigo_barras: Código de barras do produto.
        config: ``"status"`` (padrão) ou ``"dados"``.

    Returns:
        - ``config="status"``: ``True`` se o produto existe e está ativo;
          ``False`` se não existe ou se foi excluído.
        - ``config="dados"``: ``dict`` com as colunas do produto ativo, ou
          ``None`` se não for encontrado.

    Raises:
        ValueError: Se ``config`` for diferente de ``"status"`` e ``"dados"``.
        sqlite3.Error: Para falhas do banco.
    """
    if config not in ("status", "dados"):
        raise ValueError("config deve ser 'status' ou 'dados'")

    with get_db() as conn:
        if config == "status":
            resultado = conn.execute(
                "SELECT status FROM Produtos_cadastrados WHERE codigo_barras = ?",
                (codigo_barras,),
            ).fetchone()
            return resultado is not None and resultado["status"] == "ativo"

        produto = conn.execute(
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
            (codigo_barras,),
        ).fetchone()
        return dict(produto) if produto is not None else None