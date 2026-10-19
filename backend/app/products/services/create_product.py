"""Cadastra um produto e registra a movimentação de entrada na mesma transação."""

from app.core.database import get_db
from app.models.movement import StockMovement

# ID do motivo de cadastro do produto na tabela ``motivos``.
REASON_CREATION = 1


def create_product(user_drt, product):
    """Insere o produto e registra sua entrada de forma atômica.

    Args:
        user_drt: DRT do usuário responsável.
        product: Instância validada de ``Product``.

    Raises:
        ValueError: Se o motivo não existir.
        sqlite3.IntegrityError: Se o código de barras já estiver cadastrado.
        sqlite3.Error: Para qualquer outra falha do banco.
    """
    with get_db() as conn:
        product.insert(conn)
        StockMovement.record(
            conn,
            barcode=product.barcode,
            quantity=product.quantity,
            status="entrada",
            reason=REASON_CREATION,
            user_drt=user_drt,
        )
