"""Consulta a existência ou os dados completos de um produto pelo código de barras."""

from app.DATABASE import get_db


def buscar(codigo_barras, config="status") -> bool | dict | None:
    """Retorna existência como booleano, dados do produto como dicionário ou None em falha/ausência de dados."""
    try:
        with get_db() as conn:
            if config == "status":
                resultado = conn.execute(
                    "SELECT 1 FROM Produtos_cadastrados WHERE codigo_barras = ?",
                    (codigo_barras,),
                ).fetchone()
                return resultado is not None

            if config == "dados":
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
                    WHERE p.codigo_barras = ?
                    """,
                    (codigo_barras,),
                ).fetchone()
                return dict(produto) if produto is not None else None

            raise ValueError("config deve ser 'status' ou 'dados'")
    except Exception:
        return None
