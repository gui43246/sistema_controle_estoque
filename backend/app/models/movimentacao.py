"""Representa e registra uma movimentação de estoque."""


class EstoqueNaoEncontradoError(LookupError):
    """O item informado não existe na tabela de estoque."""


class Movimentacao:
    """
    Operações de persistência de uma movimentação de estoque.

    Nenhum método abre conexão nem faz commit: todos recebem ``conn`` e
    deixam os erros subirem. Quem abriu a transação decide o commit/rollback.

    Methods
    -------
    buscar_motivo(conn, motivo_id) -> str | None
    registrar(conn, codigo_barras, quantidade, status, motivo, usuario_drt) -> int
    ajustar_quantidade_e_registrar(conn, codigo_barras, quantidade, motivo_id, usuario_drt) -> int
    """

    @staticmethod
    def buscar_motivo(conn, motivo_id):
        """Retorna a descrição do motivo ou None se o id não existir."""
        resultado = conn.execute(
            "SELECT descricao FROM motivos WHERE id = ?", (motivo_id,)
        ).fetchone()
        return None if resultado is None else resultado["descricao"]

    @staticmethod
    def registrar(
        conn,
        codigo_barras,
        status,
        motivo,
        usuario_drt,
        quantidade=0,
        old_valor=0,
        new_valor=0,
    ):
        """Registra a movimentação usando a descrição cadastrada do motivo.

        ``quantidade``, ``old_valor`` e ``new_valor`` são opcionais e valem ``0``
        quando não informados. ``old_valor`` e ``new_valor`` só são usados em
        alterações de preço.

        Returns
        -------
        int
            ID da movimentação inserida.

        Raises
        ------
        ValueError
            Se o motivo informado não existir.
        """
        descricao = Movimentacao.buscar_motivo(conn, motivo)
        if descricao is None:
            raise ValueError("Motivo não encontrado")

        cursor = conn.execute(
            """INSERT INTO movimentacoes
                    (codigo_barras, quantidade, old_valor, new_valor,
                    status, motivo, usuario_drt)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (codigo_barras, quantidade, old_valor, new_valor,
            status, descricao, usuario_drt),
        )
        return cursor.lastrowid
        