"""Remove um produto e seu estoque quando não há movimentações vinculadas."""

from app.core.database import get_db


def excluir_produto(codigo_barras: str) -> str:
    """atualiza o status do produto pra excluido."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM Produtos_cadastrados WHERE codigo_barras = ?",
            (codigo_barras,),
        )
        if cursor.fetchone() is None:
            return "nao_encontrado"

        cursor.execute(
            "UPDATE estoque SET quantidade = ? WHERE codigo_barras = ?",
            (0,codigo_barras,),
        )
        cursor.execute(
            """UPDATE Produtos_cadastrados 
            SET status = ?  WHERE codigo_barras = ?""",
            (
                "excluido",
                codigo_barras,
            ),
        )
        return "excluido"
