"""Define o modelo de dados de um produto."""

import math
import sqlite3

from app.core.database import get_db


class Produto:
    """Representa os dados e as regras de criação de um produto do estoque.

    Attributes:
        codigo_barras: Identificador único do produto.
        nome_produto: Nome ou descrição do produto.
        valor_produto: Preço unitário normalizado como ``float``.
        setor: Identificador numérico do setor associado ao produto.
        quantidade: Quantidade inicial ou atual em estoque; começa em zero
            quando não é informada.

    Use :meth:`from_values` para criar um produto a partir de valores externos.
    Esse método valida e normaliza os campos antes de instanciar a classe.
    :meth:`commit` persiste o produto e seu registro inicial de estoque.
    """

    @classmethod
    def from_values(cls, codigo_barras, nome_produto, valor_produto, setor):
        """Valida e normaliza os dados recebidos antes de criar um produto.

        Args:
            codigo_barras: Código de barras não vazio.
            nome_produto: Nome não vazio.
            valor_produto: Valor convertido para ``float``; deve ser finito e
                maior ou igual a zero. Valores booleanos não são aceitos.
            setor: Identificador convertido para ``int`` dentro do intervalo
                permitido pelo SQLite. Valores booleanos não são aceitos.

        Returns:
            Uma instância de ``Produto`` com preço e setor normalizados.

        Raises:
            ValueError: Quando um campo é inválido. A mensagem é devolvida em
                português e pode ser usada diretamente na resposta da API.
        """
        if not isinstance(codigo_barras, str) or not codigo_barras.strip():
            raise ValueError("codigo de barras invalido")
        if not isinstance(nome_produto, str) or not nome_produto.strip():
            raise ValueError("nome do produto invalido")
        if isinstance(valor_produto, bool) or isinstance(setor, bool):
            raise ValueError("Campo invalido: valor_prod ou setor_id")
        if isinstance(setor, float) and not setor.is_integer():
            raise ValueError("setor_id invalido")

        try:
            valor_produto = float(valor_produto)
            setor = int(setor)
        except (ValueError, TypeError, OverflowError) as error:
            raise ValueError("Campo invalido: valor_prod ou setor_id") from error

        if setor < 1 or setor > 9_223_372_036_854_775_807:
            raise ValueError("setor_id invalido")
        if not math.isfinite(valor_produto) or valor_produto < 0:
            raise ValueError("valor do produto invalido")

        return cls(codigo_barras, nome_produto, valor_produto, setor)

    def __init__(self, codigo_barras, nome_produto, valor_produto, setor, quantidade=0):
        """Armazena os campos de uma instância de produto.

        Args:
            codigo_barras: Identificador do produto.
            nome_produto: Nome ou descrição do produto.
            valor_produto: Preço unitário.
            setor: Identificador do setor.
            quantidade: Quantidade em estoque, padrão ``0``.

        Note:
            Este inicializador apenas armazena os valores. Para validar e
            normalizar dados externos, use ``Produto.from_values``.
        """
        self.codigo_barras = codigo_barras
        self.nome_produto = nome_produto
        self.valor_produto = valor_produto
        self.setor = setor
        self.quantidade = quantidade

    def inserir(self, conn):
        """Insere o produto e seu registro de estoque inicial.

        Não faz commit: quem abriu a transação é responsável por isso.

        Raises:
            sqlite3.IntegrityError: Se o código de barras já existe.
            sqlite3.Error: Para qualquer outra falha do banco.
        """
        conn.execute(
            """INSERT INTO Produtos_cadastrados(
                    codigo_barras, nome_produto, valor_prod, setor_id
                ) VALUES (?, ?, ?, ?)""",
            (self.codigo_barras, self.nome_produto, self.valor_produto, self.setor),
        )
        conn.execute(
            "INSERT INTO estoque(codigo_barras) VALUES (?)",
            (self.codigo_barras,),
        )
        
        
class ProdutoNaoEncontradoError(LookupError):
    """O código de barras informado não existe ou não está ativo."""