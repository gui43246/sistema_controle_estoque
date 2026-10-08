"""Inicializa o esquema SQLite e fornece conexões ao banco configurado."""

import sqlite3
import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, os.getenv("CAMINHO_BANCO"))


def init_db():
    """Cria as tabelas necessárias e insere os setores e motivos padrão."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""CREATE TABLE IF NOT EXISTS setor(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            nome_setor TEXT NOT NULL UNIQUE)""")

        setores = [
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
        for (nome_setor,) in setores:
            cursor.execute(
                "SELECT 1 FROM setor WHERE nome_setor = ? LIMIT 1",
                (nome_setor,),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO setor (nome_setor) VALUES (?)",
                    (nome_setor,),
                )
        cursor.execute("""CREATE TABLE IF NOT EXISTS Produtos_cadastrados(
            codigo_barras TEXT PRIMARY KEY NOT NULL,
            nome_produto TEXT NOT NULL,
            valor_prod REAL NOT NULL,
            setor_id INTEGER NOT NULL,
            FOREIGN KEY (setor_id) REFERENCES setor(id))""")

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS estoque(
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            codigo_barras TEXT UNIQUE NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (codigo_barras) REFERENCES Produtos_cadastrados(codigo_barras))"""
        )

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
       
        
        cursor.execute("""
    CREATE TABLE IF NOT EXISTS motivos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL UNIQUE
    )
""")

        cursor.executemany(
            "INSERT OR IGNORE INTO motivos (descricao) VALUES (?)",
            [
                ("cadastro de item",),
                ("Compra de produto",),
                ("Devolução",),
                ("Ajuste de estoque",),
                ("Produto danificado",),
                ("Produto vencido",),
                ("Recepção",),
                ("Ruptura",),
                ("exclusão",)
            ],
        )
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_barras TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('entrada','ajuste','exclusão', 'saida')),
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


if __name__ == "__main__":
    init_db()
    print("Banco de dados inicializado com sucesso!")
