"""Remove um produto e seu estoque quando não há movimentações vinculadas."""

from app.DATABASE import get_db


def excluir_produto(codigo_barras: str) -> str:
    """Remove o produto e seu estoque somente se não houver histórico."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM Produtos_cadastrados WHERE codigo_barras = ?",
            (codigo_barras,),
        )
        if cursor.fetchone() is None:
            return "nao_encontrado"

        cursor.execute(
            "SELECT 1 FROM movimentacoes WHERE codigo_barras = ? LIMIT 1",
            (codigo_barras,),
        )
        if cursor.fetchone() is not None:
            return "tem_movimentacoes"

        cursor.execute(
            "DELETE FROM estoque WHERE codigo_barras = ?",
            (codigo_barras,),
        )
        cursor.execute(
            "DELETE FROM Produtos_cadastrados WHERE codigo_barras = ?",
            (codigo_barras,),
        )
        return "excluido"
