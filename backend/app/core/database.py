"""SQLite schema initialization, migrations, and connection helpers."""

import os
import sqlite3

import bcrypt
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, os.getenv("CAMINHO_BANCO"))
CURRENT_SCHEMA_VERSION = 1

DEFAULT_SECTORS = (
    "Perfumaria",
    "Drogaria",
    "Mercearia seca",
    "Mercearia líquida",
    "DPH - Departamento de Higiene Pessoal",
    "Hortifruti",
    "Padaria",
    "Açougue",
)

DEFAULT_REASONS = (
    "cadastro de item",
    "Compra de produto",
    "Devolução",
    "Ajuste de estoque",
    "valor ajustado",
    "Produto danificado",
    "Produto vencido",
    "Recepção",
    "Ruptura",
    "exclusão",
    "Venda",
)

CREATE_TABLES_SQL = (
    """CREATE TABLE IF NOT EXISTS setor (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        nome_setor TEXT NOT NULL UNIQUE
    )""",
    """CREATE TABLE IF NOT EXISTS Produtos_cadastrados (
        codigo_barras TEXT PRIMARY KEY NOT NULL,
        nome_produto TEXT NOT NULL,
        valor_prod REAL NOT NULL,
        setor_id INTEGER NOT NULL,
        status TEST NOT NULL DEFAULT 'ativo'
            CHECK (status IN ('ativo', 'excluido')),
        FOREIGN KEY (setor_id) REFERENCES setor(id)
    )""",
    """CREATE TABLE IF NOT EXISTS estoque (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        codigo_barras TEXT UNIQUE NOT NULL,
        quantidade INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (codigo_barras)
            REFERENCES Produtos_cadastrados(codigo_barras)
    )""",
    """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        drt TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        numero_telefone TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        tipo_user TEXT DEFAULT 'user_comum'
    )""",
    """CREATE TABLE IF NOT EXISTS motivos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL UNIQUE
    )""",
    """CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status TEXT NOT NULL
            CHECK (status IN ('entrada', 'ajuste', 'exclusão', 'saida')),
        codigo_barras TEXT NOT NULL,
        quantidade INTEGER DEFAULT 0,
        old_valor FLOAT DEFAULT 0,
        new_valor FLOAT DEFAULT 0,
        motivo TEXT NOT NULL,
        data_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        usuario_drt TEXT NOT NULL,
        FOREIGN KEY (codigo_barras)
            REFERENCES Produtos_cadastrados(codigo_barras),
        FOREIGN KEY (usuario_drt) REFERENCES users(drt)
    )""",
)


def _create_tables(conn):
    """Create all application tables if they do not already exist."""
    for statement in CREATE_TABLES_SQL:
        conn.execute(statement)


def _seed_reference_data(conn):
    """Insert default sectors and movement reasons without duplicating them."""
    for sector_name in DEFAULT_SECTORS:
        sector_exists = conn.execute(
            "SELECT 1 FROM setor WHERE nome_setor = ? LIMIT 1",
            (sector_name,),
        ).fetchone()
        if sector_exists is None:
            conn.execute(
                "INSERT INTO setor (nome_setor) VALUES (?)",
                (sector_name,),
            )

    conn.executemany(
        "INSERT OR IGNORE INTO motivos (descricao) VALUES (?)",
        ((reason,) for reason in DEFAULT_REASONS),
    )


def _apply_migrations(conn):
    """Apply additive schema migrations and record the current version."""
    schema_version = conn.execute("PRAGMA user_version").fetchone()[0]
    if schema_version >= CURRENT_SCHEMA_VERSION:
        return

    movement_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(movimentacoes)")
    }
    for column in ("old_valor", "new_valor"):
        if column not in movement_columns:
            conn.execute(
                f"ALTER TABLE movimentacoes ADD COLUMN {column} FLOAT DEFAULT 0"
            )

    conn.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")


def init_db():
    """Create the schema, seed reference rows, and migrate older databases."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        # DDL and the schema version update must commit or roll back together.
        conn.execute("BEGIN IMMEDIATE")
        _create_tables(conn)
        _seed_reference_data(conn)
        _apply_migrations(conn)


def get_db():
    """Open a named-row SQLite connection with foreign-key checks enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def create_test_admin(
    drt="900000000",
    name="adm",
    email="adm@text.com",
    phone_number="11991901212",
    password="Admteste123",
):
    """Create the local development admin account if it does not exist."""
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
