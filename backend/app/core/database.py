"""Inicializa o esquema SQLite e fornece conexões ao banco configurado."""

import sqlite3
import os
import bcrypt

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, os.getenv("CAMINHO_BANCO"))




def init_db():
    """Cria as tabelas necessárias e insere os setores e motivos padrão."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode =WAL")

        cursor.execute("""CREATE TABLE IF NOT EXISTS setor(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            nome_setor TEXT NOT NULL UNIQUE)""")

        sectors = [
        ("Perfumaria",),
        ("Drogaria",),
        ("Mercearia seca",),
        ("Mercearia líquida",),
        ("DPH - Departamento de Higiene Pessoal",),
        ("Hortifruti",),
        ("Padaria",),
        ("Açougue",),
        ]
        # Também evita duplicatas em bancos antigos, cuja tabela ainda não tem UNIQUE.
        for (sector_name,) in sectors:
            cursor.execute(
                "SELECT 1 FROM setor WHERE nome_setor = ? LIMIT 1",
                (sector_name,),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO setor (nome_setor) VALUES (?)",
                    (sector_name,),
                    
        # Cria a tabela que armazena os produtos cadastrados.
                )
        cursor.execute("""CREATE TABLE IF NOT EXISTS Produtos_cadastrados(
            codigo_barras TEXT PRIMARY KEY NOT NULL,
            nome_produto TEXT NOT NULL,
            valor_prod REAL NOT NULL,
            setor_id INTEGER NOT NULL,
            status TEST NOT NULL DEFAULT "ativo" CHECK(status IN ("ativo","excluido")),
            FOREIGN KEY (setor_id) REFERENCES setor(id))""")

        # Cria a tabela que armazena as quantidades em estoque.
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS estoque(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            codigo_barras TEXT UNIQUE NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (codigo_barras) REFERENCES Produtos_cadastrados(codigo_barras))"""
        )

        # Cria a tabela de usuários e seus dados de acesso.
    
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS users(
                           id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                           drt TEXT UNIQUE NOT NULL,
                           name TEXT NOT NULL,
                           email TEXT UNIQUE NOT NULL,
                           numero_telefone TEXT UNIQUE NOT NULL,
                           senha TEXT NOT NULL,
                           tipo_user TEXT DEFAULT "user_comum"
                           )
                       """)
       
        # Cria a tabela de motivos usados no histórico de movimentações.
        cursor.execute("""
    CREATE TABLE IF NOT EXISTS motivos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL UNIQUE
    )
""")
        
        # Insere os motivos padrão.

        cursor.executemany(
            "INSERT OR IGNORE INTO motivos (descricao) VALUES (?)",
          [
        ("cadastro de item",),
        ("Compra de produto",),
        ("Devolução",),
        ("Ajuste de estoque",),
        ("valor ajustado",),
        ("Produto danificado",),
        ("Produto vencido",),
        ("Recepção",),
        ("Ruptura",),
        ("exclusão",),
        ("Venda",),
    ],
        )
        
        # Cria a tabela que registra o histórico de ações.
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL CHECK (status IN ('entrada','ajuste','exclusão', 'saida')),
            codigo_barras TEXT NOT NULL,
            quantidade INTEGER DEFAULT 0,
            old_valor FLOAT DEFAULT 0,
            new_valor FLOAT DEFAULT 0,
            motivo TEXT NOT NULL,
            data_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            usuario_drt TEXT NOT NULL,

            FOREIGN KEY (codigo_barras)
                REFERENCES Produtos_cadastrados(codigo_barras),
            FOREIGN KEY (usuario_drt)
                REFERENCES users(drt)
        )
    """)


def get_db():
    """Abre uma conexão SQLite com os resultados configurados como linhas nomeadas."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_test_admin(
    drt="900000000",
    name="adm",
    email="adm@text.com",
    phone_number="11991901212",
    password="Admteste123",
):
    """Cria a conta de administrador usada nos testes, se ainda não existir."""
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
    with get_db() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO users
               (drt, name, email, numero_telefone, senha, tipo_user)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (drt, name, email, phone_number, password_hash, "adm"),
        )
    return "ok, tudo pronto pra testes"


if __name__ == "__main__":
    init_db()
    print("Banco de dados inicializado com sucesso!")
    print(create_test_admin())
