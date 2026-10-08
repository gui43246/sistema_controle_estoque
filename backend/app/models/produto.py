"""Define o modelo Produto e suas operações de atualização no banco."""

from app.DATABASE import get_db
import sqlite3


class Produto:
    """Representa um produto cadastrado no sistema de estoque.

    Além de armazenar os dados de um produto, esta classe agrupa métodos
    estáticos utilitários para atualizar informações do produto diretamente
    no banco de dados (setor, quantidade em estoque e valor), sem
    necessidade de instanciar um objeto.

    Attributes:
        codigo_barras (str): Código de barras do produto (identificador único).
        nome_produto (str): Nome/descrição do produto.
        valor_produto (float): Valor unitário do produto.
        setor (int): ID do setor ao qual o produto pertence.
        quantidade (int): Quantidade em estoque. Padrão: 0.
    """

    def __init__(self, codigo_barras, nome_produto, valor_produto, setor, quantidade=0):
        """Inicializa uma instância de Produto.

        Args:
            codigo_barras (str): Código de barras do produto.
            nome_produto (str): Nome/descrição do produto.
            valor_produto (float): Valor unitário do produto.
            setor (int): ID do setor ao qual o produto pertence.
            quantidade (int, optional): Quantidade inicial em estoque. Padrão: 0.
        """
        self.codigo_barras = codigo_barras
        self.nome_produto = nome_produto
        self.valor_produto = valor_produto
        self.setor = setor
        self.quantidade = quantidade

    @staticmethod
    def setor_ajustar(codigo_barras, novo_setor):
        """Atualiza o setor de um produto no banco de dados.

        Args:
            codigo_barras (str): Código de barras do produto a ser atualizado.
            novo_setor (int): ID do novo setor.

        Returns:
            tuple[bool, int]: (sucesso, código do resultado)
                - (True, 0): atualização feita com sucesso.
                - (False, 3): erro inesperado no banco de dados.
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE Produtos_cadastrados
                    SET setor_id = ?
                    WHERE codigo_barras = ?
                """, (novo_setor, codigo_barras))
                if cursor.rowcount == 0:
                    return False
                conn.commit()
            return True
        except sqlite3.Error:
            return False

    @staticmethod
    def ajustar_quantidade(codigo_barras, quantidade):
        """Atualiza a quantidade em estoque de um produto.

        Args:
            codigo_barras (str): Código de barras do produto a ser atualizado.
            quantidade (int): Nova quantidade em estoque. Deve ser >= 0.

        Returns:
            tuple[bool, int]: (sucesso, código do resultado)
                - (True, 0): atualização feita com sucesso.
                - (False, 1): quantidade inválida (menor que zero).
                - (False, 3): erro inesperado no banco de dados.
        """
        if quantidade < 0:
            return False 

        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE estoque
                    SET quantidade = ?
                    WHERE codigo_barras = ?
                """, (quantidade, codigo_barras))
                if cursor.rowcount == 0:
                    return False
                conn.commit()
            return True 
        except sqlite3.Error:
            return False

    @staticmethod
    def editar_valor_produto(codigo_barras, valor):
        """Atualiza o valor de venda de um produto.

        Args:
            codigo_barras (str): Código de barras do produto a ser atualizado.
            valor (float): Novo valor do produto. Deve ser maior que zero.

        Returns:
            tuple[bool, int]: (sucesso, código do resultado)
                - (True, 0): atualização feita com sucesso.
                - (False, 1): valor inválido (menor ou igual a zero).
                - (False, 3): erro inesperado no banco de dados.
        """
        if valor <= 0:
            return False 

        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE Produtos_cadastrados
                    SET valor_prod = ?
                    WHERE codigo_barras = ?
                """, (valor, codigo_barras))
                if cursor.rowcount == 0:
                    return False
                conn.commit()
            return True  
        except sqlite3.Error:
            return False  



