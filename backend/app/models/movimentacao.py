"""Representa e registra uma movimentação de estoque."""

from app.core.database import get_db


class Movimentacao:
    """
    Operações de persistência de uma movimentação de estoque.

    Essa classe fornece métodos para registrar movimentações e ajustes
    de quantidade no estoque, garantindo que o histórico seja mantido
    na tabela de movimentações.

    Methods
    -------
    registrar(codigo_barras, quantidade, status, motivo, usuario_drt) -> int
        Registra uma movimentação de estoque com base em um motivo existente.
        Retorna o ID da movimentação inserida.
        Lança ValueError se o motivo não existir.

    ajustar_quantidade_e_registrar(codigo_barras, quantidade, motivo_id, usuario_drt) -> str
        Atualiza a quantidade de um item no estoque e registra a movimentação
        correspondente. Retorna "ok" em caso de sucesso, ou mensagens de erro
        específicas ("quantidade_invalida", "estoque_nao_encontrado").
    """

    @staticmethod
    def registrar(codigo_barras, quantidade, status, motivo, usuario_drt):
        """
        Registra a movimentação usando a descrição cadastrada do motivo.

        Parameters
        ----------
        codigo_barras : str
            Código de barras do item movimentado.
        quantidade : int
            Quantidade movimentada.
        status : str
            Status da movimentação (ex.: 'entrada', 'saida').
        motivo : int
            Identificador do motivo cadastrado.
        usuario_drt : str
            Identificação do usuário responsável pela movimentação.

        Returns
        -------
        int
            O ID da movimentação inserida.

        Raises
        ------
        ValueError
            Se o motivo informado não existir.
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT descricao FROM motivos WHERE id = ?", (motivo,))
            resultado = cursor.fetchone()
            if resultado is None:
                raise ValueError("Motivo não encontrado")

            cursor.execute(
                """INSERT INTO movimentacoes
                       (codigo_barras, quantidade, status, motivo, usuario_drt)
                   VALUES (?, ?, ?, ?, ?)""",
                (codigo_barras, quantidade, status, resultado["descricao"], usuario_drt),
            )
            return cursor.lastrowid

    @staticmethod
    def ajustar_quantidade_e_registrar(
        codigo_barras,
        quantidade,
        motivo_id,
        usuario_drt,
    ):
        """
        Atualiza o estoque e registra o histórico na mesma transação.

        Parameters
        ----------
        codigo_barras : str
            Código de barras do item a ser ajustado.
        quantidade : int
            Nova quantidade a ser registrada no estoque.
        motivo_id : int
            Identificador do motivo do ajuste.
        usuario_drt : str
            Identificação do usuário responsável pelo ajuste.

        Returns
        -------
        str
            "ok" se o ajuste foi realizado com sucesso.
            "quantidade_invalida" se a quantidade for negativa.
            "estoque_nao_encontrado" se o item não existir no estoque.
        """
        if quantidade < 0:
            return "quantidade_invalida"

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE estoque SET quantidade = ? WHERE codigo_barras = ?",
                (quantidade, codigo_barras),
            )
            if cursor.rowcount == 0:
                return "estoque_nao_encontrado"

            cursor.execute(
                """
                INSERT INTO movimentacoes
                    (codigo_barras, quantidade, status, motivo, usuario_drt)
                VALUES (?, ?, 'ajuste', ?, ?)
                """,
                (codigo_barras, quantidade, Movimentacao.buscar_motivo(motivo_id), usuario_drt),
            )
            return True

    @staticmethod
    def buscar_motivo(id: int) -> str | None:
        """
        Retorna a descrição do motivo ou None quando o identificador não existe.

        Parameters
        ----------
        id : int
            Identificador do motivo.

        Returns
        -------
        str | None
            Descrição do motivo se encontrado, ou None caso contrário.
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT descricao FROM motivos WHERE id = ?",
                (id,),
            )
            resultado = cursor.fetchone()

            if resultado is None:
                return None

            return resultado["descricao"]
