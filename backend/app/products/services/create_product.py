"""Cadastra um produto e registra a movimentação de entrada na mesma transação."""

from app.core.database import get_db
from app.models.movimentacao import Movimentacao

# id do motivo "cadastro de produto" na tabela motivos
MOTIVO_CADASTRO = 1  


def cria_produto(usuario_drt, novo_produto):
    """Insere o produto e registra sua entrada de forma atômica.

    Args:
        usuario_drt: Identificação do usuário responsável.
        novo_produto: Instância de ``Produto`` já validada (via ``from_values``).

    Raises:
        ValueError: Se o motivo não existir.
        sqlite3.IntegrityError: Se o código de barras já estiver cadastrado.
        sqlite3.Error: Para qualquer outra falha do banco.
    """
    with get_db() as conn:
        novo_produto.inserir(conn)
        Movimentacao.registrar(
            conn,
            codigo_barras=novo_produto.codigo_barras,
            quantidade=novo_produto.quantidade,
            status="entrada",
            motivo=MOTIVO_CADASTRO,
            usuario_drt=usuario_drt,
        )