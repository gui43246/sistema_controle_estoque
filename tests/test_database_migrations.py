"""Tests for additive SQLite schema migrations."""

import sqlite3

import pytest
from flask_jwt_extended import create_access_token

from app import app
from app.core import database
from app.products.services.update_product_price import update_product_price


def test_init_db_migrates_legacy_movements_without_losing_data(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.sqlite"
    monkeypatch.setattr(database, "DB_PATH", str(db_path))
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """CREATE TABLE movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL,
                codigo_barras TEXT NOT NULL,
                quantidade INTEGER DEFAULT 0,
                motivo TEXT NOT NULL,
                data_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                usuario_drt TEXT NOT NULL
            )"""
        )
        conn.execute(
            "INSERT INTO movimentacoes (status, codigo_barras, quantidade, motivo, usuario_drt) "
            "VALUES ('ajuste', 'historico-antigo', 4, 'motivo antigo', 'antigo')"
        )

    database.init_db()
    database.init_db()  # migration must be idempotent

    with database.get_db() as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(movimentacoes)")}
        assert {"old_valor", "new_valor"}.issubset(columns)
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        historic = conn.execute(
            "SELECT status, codigo_barras, quantidade, motivo, usuario_drt "
            "FROM movimentacoes WHERE id = 1"
        ).fetchone()
        assert tuple(historic) == ("ajuste", "historico-antigo", 4, "motivo antigo", "antigo")
        conn.execute(
            "INSERT INTO users (drt, name, email, numero_telefone, senha) VALUES (?, ?, ?, ?, ?)",
            ("123456789", "Usuário teste", "migracao@example.com", "11912345678", "hash"),
        )
        conn.execute(
            "INSERT INTO Produtos_cadastrados (codigo_barras, nome_produto, valor_prod, setor_id) "
            "VALUES (?, ?, ?, 1)",
            ("789000000001", "Produto teste", 10.0),
        )

    update_product_price("789000000001", 15.5, "123456789")

    with database.get_db() as conn:
        price = conn.execute(
            "SELECT old_valor, new_valor FROM movimentacoes "
            "WHERE codigo_barras = '789000000001'"
        ).fetchone()
        assert tuple(price) == (10.0, 15.5)


def test_migration_rolls_back_all_schema_changes_on_failure(tmp_path, monkeypatch):
    db_path = tmp_path / "migration-rollback.sqlite"
    original_connect = sqlite3.connect
    with original_connect(db_path) as conn:
        conn.execute(
            """CREATE TABLE movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL,
                codigo_barras TEXT NOT NULL,
                quantidade INTEGER DEFAULT 0,
                motivo TEXT NOT NULL,
                data_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                usuario_drt TEXT NOT NULL
            )"""
        )
        conn.execute(
            "INSERT INTO movimentacoes (status, codigo_barras, quantidade, motivo, usuario_drt) "
            "VALUES ('ajuste', 'legado', 3, 'ajuste', 'usuario-legado')"
        )

    monkeypatch.setattr(database, "DB_PATH", str(db_path))

    class FailOnNewValueColumn(sqlite3.Connection):
        def execute(self, sql, parameters=()):
            if "ADD COLUMN new_valor" in sql:
                raise sqlite3.OperationalError("falha simulada na migração")
            return super().execute(sql, parameters)

    def connect_with_failure(*args, **kwargs):
        kwargs["factory"] = FailOnNewValueColumn
        return original_connect(*args, **kwargs)

    monkeypatch.setattr(database.sqlite3, "connect", connect_with_failure)
    with pytest.raises(sqlite3.OperationalError, match="falha simulada"):
        database.init_db()

    with original_connect(db_path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(movimentacoes)")}
        assert "old_valor" not in columns
        assert "new_valor" not in columns
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM movimentacoes").fetchone()[0] == 1


def test_migrated_null_price_values_remain_listable_through_pagination(
    tmp_path, monkeypatch, client
):
    db_path = tmp_path / "legacy-null-prices.sqlite"
    monkeypatch.setattr(database, "DB_PATH", str(db_path))
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """CREATE TABLE movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL,
                codigo_barras TEXT NOT NULL,
                quantidade INTEGER DEFAULT 0,
                old_valor FLOAT,
                new_valor FLOAT,
                motivo TEXT NOT NULL,
                data_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                usuario_drt TEXT NOT NULL
            )"""
        )
        conn.execute(
            """INSERT INTO movimentacoes
                (status, codigo_barras, quantidade, old_valor, new_valor, motivo, usuario_drt)
                VALUES ('ajuste', 'historico-nulo', 3, NULL, NULL, 'legado', 'usuario-legado')"""
        )

    database.init_db()

    with database.get_db() as conn:
        values = conn.execute(
            "SELECT old_valor, new_valor FROM movimentacoes WHERE codigo_barras = ?",
            ("historico-nulo",),
        ).fetchone()
        assert tuple(values) == (None, None)

    with app.app_context():
        token = create_access_token(identity="usuario-legado")
    response = client.get(
        "/movimentacoes?page=1&per_page=10",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["total"] == 1
    assert response.get_json()["items"][0]["codigo_barras"] == "historico-nulo"
