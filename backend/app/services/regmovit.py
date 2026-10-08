"""Registra movimentações e atualiza o estoque dentro de transações SQLite."""

from app.DATABASE import get_db


def registrar_movimentacao(
    codigo_barras,
    quantidade,
    status,
    motivo,
    usuario_drt,
):
    """Insere uma movimentação usando a descrição do motivo cadastrada."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT descricao FROM motivos WHERE id = ?", (motivo,))
        resultado = cursor.fetchone()
        if resultado is None:
            raise ValueError("Motivo não encontrado")

        cursor.execute(
            """
            INSERT INTO movimentacoes
                (codigo_barras, quantidade, status, motivo, usuario_drt)
            VALUES (?, ?, ?, ?, ?)
            """,
            (codigo_barras, quantidade, status, resultado["descricao"], usuario_drt),
        )
        return cursor.lastrowid


def ajustar_quantidade_e_registrar(
    codigo_barras,
    quantidade,
    motivo_id,
    usuario_drt,
):
    """Atualiza o estoque e registra o histórico na mesma transação."""
    if quantidade < 0:
        return "quantidade_invalida"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT descricao FROM motivos WHERE id = ?", (motivo_id,))
        motivo = cursor.fetchone()
        if motivo is None:
            return "motivo_invalido"

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
            (codigo_barras, quantidade, motivo["descricao"], usuario_drt),
        )
        return "ok"
