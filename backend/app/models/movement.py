"""Representa e registra uma movimentação de estoque."""


class StockNotFoundError(LookupError):
    """O item informado não existe na tabela de estoque."""


class StockMovement:
    """Agrupa operações de persistência de movimentações de estoque.

    Nenhum método abre conexão nem confirma a transação. Todos recebem
    ``conn`` e deixam as exceções subirem; quem abriu a transação decide
    confirmá-la ou revertê-la.
    """

    @staticmethod
    def find_reason(conn, reason_id):
        """Retorna a descrição do motivo ou ``None`` se o ID não existir.

        Args:
            conn: Conexão SQLite da transação atual.
            reason_id: ID do motivo registrado na tabela ``motivos``.

        Returns:
            A descrição do motivo ou ``None`` quando não existe.
        """
        result = conn.execute(
            "SELECT descricao FROM motivos WHERE id = ?", (reason_id,)
        ).fetchone()
        return None if result is None else result["descricao"]

    @staticmethod
    def record(
        conn,
        barcode,
        status,
        reason,
        user_drt,
        quantity=0,
        old_price=0,
        new_price=0,
    ):
        """Registra uma movimentação com a descrição cadastrada do motivo.

        Args:
            conn: Conexão SQLite da transação atual.
            barcode: Código de barras associado à movimentação.
            status: Tipo de movimentação.
            reason: ID do motivo cadastrado.
            user_drt: DRT do usuário responsável.
            quantity: Quantidade movimentada; o padrão é ``0``.
            old_price: Preço anterior, usado em alterações de preço.
            new_price: Preço novo, usado em alterações de preço.

        Returns:
            ID da movimentação inserida.

        Raises:
            ValueError: Se o motivo informado não existir.
        """
        description = StockMovement.find_reason(conn, reason)
        if description is None:
            raise ValueError("Motivo não encontrado")

        cursor = conn.execute(
            """INSERT INTO movimentacoes
                    (codigo_barras, quantidade, old_valor, new_valor,
                    status, motivo, usuario_drt)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (barcode, quantity, old_price, new_price,
            status, description, user_drt),
        )
        return cursor.lastrowid
