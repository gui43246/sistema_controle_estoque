from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

class criptografia:
    """
    Classe responsável por realizar operações de criptografia e
    descriptografia utilizando o algoritmo Fernet (simétrico).

    A chave de criptografia deve ser definida na variável de ambiente
    `CRYPTO_KEY` dentro do arquivo `.env`.

    Attributes
    ----------
    chave_criptografia : str
        Chave usada para inicializar o objeto Fernet.
    fernet : Fernet
        Instância do algoritmo Fernet para criptografia e descriptografia.

    Methods
    -------
    criptografar(dado: str) -> str | None
        Criptografa uma string e retorna o texto criptografado.
        Retorna None se o dado for vazio.

    descriptografar(dado: str) -> str | None
        Descriptografa uma string criptografada e retorna o texto original.
        Retorna None se o dado for vazio.
        Pode lançar exceção se o dado estiver corrompido ou a chave for inválida.
    """

    def __init__(self):
        """
        Inicializa a classe carregando a chave de criptografia
        da variável de ambiente `CRYPTO_KEY`.

        Raises
        ------
        ValueError
            Se a chave não estiver definida no arquivo `.env`.
        """
        self.chave_criptografia = os.getenv("CRYPTO_KEY")
        if not self.chave_criptografia:
            raise ValueError("Chave de criptografia não encontrada. Defina CRYPTO_KEY no .env")
        self.fernet = Fernet(self.chave_criptografia.encode())

    def criptografar(self, dado: str):
        """
        Criptografa uma string utilizando Fernet.

        Parameters
        ----------
        dado : str
            Texto simples que será criptografado.

        Returns
        -------
        str | None
            Texto criptografado em formato string.
            Retorna None se o dado for vazio.
        """
        if not dado:
            return None
        return self.fernet.encrypt(dado.encode()).decode()

    def descriptografar(self, dado: str):
        """
        Descriptografa uma string criptografada utilizando Fernet.

        Parameters
        ----------
        dado : str
            Texto criptografado que será convertido de volta ao original.

        Returns
        -------
        str | None
            Texto original descriptografado.
            Retorna None se o dado for vazio.

        Raises
        ------
        Exception
            Se o dado não puder ser descriptografado (corrompido ou chave incorreta).
        """
        if not dado:
            return None
        return self.fernet.decrypt(dado.encode()).decode()
