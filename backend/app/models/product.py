"""Define o modelo de dados de um produto."""

import math
import sqlite3

from app.core.database import get_db


class Product:
    """Representa os dados e as regras de criação de um produto do estoque.

    Attributes:
        barcode: Identificador único do produto.
        name: Nome ou descrição do produto.
        price: Preço unitário normalizado como ``float``.
        sector_id: Identificador numérico do setor associado ao produto.
        quantity: Quantidade inicial ou atual em estoque; começa em zero
            quando não é informada.

    Use :meth:`from_values` para criar um produto a partir de valores externos.
    Esse método valida e normaliza os campos antes de instanciar a classe.
    :meth:`insert` persiste o produto e seu registro inicial de estoque.
    """

    @classmethod
    def from_values(cls, barcode, name, price, sector_id):
        """Valida e normaliza os dados recebidos antes de criar um produto.

        Args:
            barcode: Código de barras não vazio.
            name: Nome não vazio.
            price: Valor convertido para ``float``; deve ser finito e
                maior ou igual a zero. Valores booleanos não são aceitos.
            sector_id: Identificador convertido para ``int`` dentro do intervalo
                permitido pelo SQLite. Valores booleanos não são aceitos.

        Returns:
            Uma instância de ``Product`` com preço e setor normalizados.

        Raises:
            ValueError: Quando um campo é inválido. A mensagem é devolvida em
                português e pode ser usada diretamente na resposta da API.
        """
        if not isinstance(barcode, str) or not barcode.strip():
            raise ValueError("código de barras inválido")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("nome do produto inválido")
        if isinstance(price, bool) or isinstance(sector_id, bool):
            raise ValueError("Campo inválido: valor_prod ou setor_id")
        if isinstance(sector_id, float) and not sector_id.is_integer():
            raise ValueError("setor_id inválido")

        try:
            price = float(price)
            sector_id = int(sector_id)
        except (ValueError, TypeError, OverflowError) as error:
            raise ValueError("Campo inválido: valor_prod ou setor_id") from error

        if sector_id < 1 or sector_id > 9_223_372_036_854_775_807:
            raise ValueError("setor_id inválido")
        if not math.isfinite(price) or price < 0:
            raise ValueError("valor do produto inválido")

        return cls(barcode, name, price, sector_id)

    def __init__(self, barcode, name, price, sector_id, quantity=0):
        """Armazena os campos de uma instância de produto.

        Args:
            barcode: Identificador do produto.
            name: Nome ou descrição do produto.
            price: Preço unitário.
            sector_id: Identificador do setor.
            quantity: Quantidade em estoque, padrão ``0``.

        Note:
            Este inicializador apenas armazena os valores. Para validar e
            normalizar dados externos, use ``Product.from_values``.
        """
        self.barcode = barcode
        self.name = name
        self.price = price
        self.sector_id = sector_id
        self.quantity = quantity

    def insert(self, conn):
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
            (self.barcode, self.name, self.price, self.sector_id),
        )
        conn.execute(
            "INSERT INTO estoque(codigo_barras) VALUES (?)",
            (self.barcode,),
        )
        
        
class ProductNotFoundError(LookupError):
    """O código de barras informado não existe ou não está ativo."""
