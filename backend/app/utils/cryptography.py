from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

class Cryptography:
    """Criptografa e descriptografa textos usando o algoritmo simétrico Fernet.

    A chave de criptografia deve ser definida na variável de ambiente
    `CRYPTO_KEY` dentro do arquivo `.env`.

    Attributes:
        encryption_key: Chave usada para inicializar o objeto Fernet.
        fernet: Instância do algoritmo Fernet.
    """

    def __init__(self):
        """Carrega a chave de criptografia da variável `CRYPTO_KEY`.

        Raises:
            ValueError: Se a chave não estiver definida no arquivo `.env`.
        """
        self.encryption_key = os.getenv("CRYPTO_KEY")
        if not self.encryption_key:
            raise ValueError("Chave de criptografia não encontrada. Defina CRYPTO_KEY no .env")
        self.fernet = Fernet(self.encryption_key.encode())

    def encrypt(self, value: str):
        """Criptografa um texto usando Fernet.

        Args:
            value: Texto simples que será criptografado.

        Returns:
            Texto criptografado ou ``None`` se o texto estiver vazio.
        """
        if not value:
            return None
        return self.fernet.encrypt(value.encode()).decode()

    def decrypt(self, value: str):
        """Descriptografa um texto usando Fernet.

        Args:
            value: Texto criptografado que será convertido ao original.

        Returns:
            Texto original ou ``None`` se o texto estiver vazio.

        Raises:
            cryptography.fernet.InvalidToken: Se o texto estiver corrompido
                ou tiver sido criptografado com outra chave.
        """
        if not value:
            return None
        return self.fernet.decrypt(value.encode()).decode()
