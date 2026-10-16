"""Define e valida os dados necessários para cadastrar um usuário."""

import sqlite3

from app.core.security.password_hash import criar_hash
from app.core.database import get_db
from app.users.services import (
    validar_DRT,
    validar_email,
    validar_name,
    validar_senha,
    validar_telefone,
)


class UserValidationError(ValueError):
    """Representa um erro de validação com mensagem e status da API."""

    def __init__(self, message, status_code):
        super().__init__(message)
        self.status_code = status_code


class CreateUser:
    """Representa os dados validados para criar uma conta de usuário.

    A classe aplica as validações existentes na mesma ordem do cadastro,
    gera o hash da senha e mantém os dados prontos para persistência. Ela não
    persiste os dados no banco por meio de ``commit``.

    Attributes:
        drt: Identificação única do funcionário.
        name: Nome validado do usuário.
        email: Endereço de e-mail validado.
        phone_number: Telefone validado.
        password_hash: Hash da senha, nunca a senha em texto puro.
    """

    def __init__(self, drt, name, email, phone_number, password_hash):
        self.drt = drt
        self.name = name
        self.email = email
        self.phone_number = phone_number
        self.password_hash = password_hash

    @classmethod
    def from_payload(cls, payload):
        """Valida o corpo recebido pela API e cria uma instância de usuário.

        Raises:
            UserValidationError: Se o corpo não for um objeto com todos os
                campos necessários ou se algum campo for inválido.
        """
        required_fields = ("DRT", "name", "Email", "numero_tel", "senha")
        if not isinstance(payload, dict) or any(
            field not in payload for field in required_fields
        ):
            raise UserValidationError("sem resultado, verifique os dados", 400)

        return cls.from_values(
            drt=payload["DRT"],
            name=payload["name"],
            email=payload["Email"],
            phone_number=payload["numero_tel"],
            password=payload["senha"],
        )

    @classmethod
    def from_values(cls, drt, name, email, phone_number, password):
        """Valida os dados, gera o hash e cria uma instância de ``CreateUser``.

        Raises:
            UserValidationError: Se algum campo não passar pela validação.
                A exceção contém a mensagem em português e o status HTTP usado
                atualmente pela rota de cadastro.
        """
        values = (drt, name, email, phone_number, password)
        if any(not isinstance(value, str) for value in values):
            raise UserValidationError("todos os campos devem ser textos", 400)

        drt_valid, message = validar_DRT(drt)
        if not drt_valid:
            raise UserValidationError(message, 409)

        if not validar_name(name):
            raise UserValidationError("verifique o nome", 400)

        if not validar_email(email):
            raise UserValidationError("email invalido", 400)

        password_valid, message = validar_senha(password)
        if not password_valid:
            raise UserValidationError(message, 400)

        password_hash = criar_hash(password)

        if not validar_telefone(phone_number):
            raise UserValidationError("verifique o numero de telefone", 400)

        return cls(drt, name, email, phone_number, password_hash)

    def to_database_values(self):
        """Retorna os campos na ordem esperada pelo INSERT da tabela ``users``."""
        return (
            self.drt,
            self.name,
            self.email,
            self.phone_number,
            self.password_hash,
        )

    def commit(self):
        """Insere este usuário no banco e informa se a operação funcionou."""
        try:
            with get_db() as conn:
                conn.execute(
                    """INSERT INTO users(drt, name, email, numero_telefone, senha)
                       VALUES (?, ?, ?, ?, ?)""",
                    self.to_database_values(),
                )
                conn.commit()
            return True
        except sqlite3.Error:
            return False
