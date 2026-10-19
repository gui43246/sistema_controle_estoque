"""Testes isolados da autenticação e do cadastro de usuários."""

import sqlite3
from contextlib import contextmanager

import pytest
from flask_jwt_extended import create_access_token

from app import app
from app.core.security.password_hash import hash_password
from app.users.services.validate_email import validate_email
from app.users.services.validate_password import validate_password
from app.users.services.validate_phone_number import validate_phone_number
from app.users.services.validate_user_name import validate_name
from app.users.services.verify_employee_id import validate_drt


@pytest.fixture
def auth_client(tmp_path, monkeypatch):
    db_path = tmp_path / "auth-test.sqlite"

    def get_db():
        @contextmanager
        def connection_scope():
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

        return connection_scope()

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drt TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                numero_telefone TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                tipo_user TEXT DEFAULT 'user_comum'
            )"""
        )
        conn.execute(
            """CREATE TABLE movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_drt TEXT NOT NULL REFERENCES users(drt)
            )"""
        )
        conn.execute(
            "INSERT INTO users (drt, name, email, numero_telefone, senha, tipo_user) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("123456789", "Pessoa Comum", "comum@gmail.com", "11912345678", hash_password("Senha123!"), "user_comum"),
        )
        conn.execute(
            "INSERT INTO users (drt, name, email, numero_telefone, senha, tipo_user) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("987654321", "Administradora", "admin@gmail.com", "11987654321", hash_password("Admin123!"), "adm"),
        )

    import app.core.security.authorization as authorization
    import app.users.routes.authenticate_user as authenticate_user
    import app.users.routes.create_user as create_user
    import app.users.routes.delete_user as delete_user
    import app.users.routes.list_users as list_users
    import app.users.routes.reset_password as reset_password

    for module in (authorization, authenticate_user, create_user, delete_user, list_users, reset_password):
        monkeypatch.setattr(module, "get_db", get_db)

    app.config.update(TESTING=True, JWT_SECRET_KEY="pytest-secret-key-at-least-32-bytes")
    with app.test_client() as client:
        yield client


def token_for(identity):
    with app.app_context():
        return create_access_token(identity=identity)


def test_login_masks_unknown_drt_and_authenticates(auth_client):
    nonexistent = auth_client.post("/login", json={"drt": "000000000", "senha_digitada": "Senha123!"})
    wrong_password = auth_client.post("/login", json={"drt": "123456789", "senha_digitada": "Errada123!"})
    assert nonexistent.status_code == wrong_password.status_code == 401
    assert nonexistent.get_json() == wrong_password.get_json() == {"mensagem": "DRT ou senha incorretos"}

    correct = auth_client.post("/login", json={"drt": "123456789", "senha_digitada": "Senha123!"})
    assert correct.status_code == 200
    assert correct.get_json()["mensagem"] == "login realizado"
    assert "token" in correct.get_json()


def test_list_users_requires_admin_and_hides_hash(auth_client):
    assert auth_client.get("/usuarios").status_code == 401
    regular_user = auth_client.get("/usuarios", headers={"Authorization": f"Bearer {token_for('123456789')}"})
    assert regular_user.status_code == 403
    admin = auth_client.get("/usuarios", headers={"Authorization": f"Bearer {token_for('987654321')}"})
    assert admin.status_code == 200
    assert all("senha" not in user for user in admin.get_json())


@pytest.mark.parametrize("name", ["José da Silva", "Conceição"])
def test_validate_name_accepts_accents(name):
    assert validate_name(name)


@pytest.mark.parametrize("name", ["   ", "", "Ana123"])
def test_validate_name_rejects_empty_spaces_or_digits(name):
    assert not validate_name(name)


def test_validate_drt_checks_format_only():
    assert validate_drt("123456789")[0]
    for value in ("12345678", "1234567890", "12345678a", 123456789, None):
        assert not validate_drt(value)[0]


@pytest.mark.parametrize("value", [123, None])
def test_validators_reject_wrong_types(value):
    assert not validate_password(value)[0]
    assert not validate_email(value)
    assert not validate_phone_number(value)


def test_validate_password_respects_character_and_byte_limits():
    assert validate_password("Abcdef1!" + "x" * 56)[0]
    assert not validate_password("Abcdef1!" + "x" * 57)[0]
    assert not validate_password("Á" * 37 + "aA1!")[0]


def registration_payload(**overrides):
    payload = {
        "drt": "111222333",
        "name": "José da Silva",
        "email": "NOVO@GMAIL.COM",
        "numero_tel": "11922223333",
        "senha": "SenhaNova1!",
    }
    payload.update(overrides)
    return payload


def test_registration_validates_format_uniqueness_and_lowercases_email(auth_client):
    malformed = auth_client.post("/Cadastro_usuario", json=registration_payload(drt="12"), headers={"Authorization": f"Bearer {token_for('987654321')}"})
    assert malformed.status_code == 400

    headers = {"Authorization": f"Bearer {token_for('987654321')}"}
    first = auth_client.post("/Cadastro_usuario", json=registration_payload(), headers=headers)
    assert first.status_code == 201
    duplicate_drt = auth_client.post("/Cadastro_usuario", json=registration_payload(email="outro@gmail.com", numero_tel="11922223334"), headers=headers)
    assert duplicate_drt.status_code == 409
    duplicate_email = auth_client.post("/Cadastro_usuario", json=registration_payload(drt="111222334", numero_tel="11922223335"), headers=headers)
    assert duplicate_email.status_code == 409

    import app.users.routes.create_user as create_user
    with create_user.get_db() as conn:
        saved_user = conn.execute("SELECT email FROM users WHERE drt = ?", ("111222333",)).fetchone()
    assert saved_user["email"] == "novo@gmail.com"


def test_registration_rejects_regular_user(auth_client):
    response = auth_client.post(
        "/Cadastro_usuario",
        json=registration_payload(),
        headers={"Authorization": f"Bearer {token_for('123456789')}"},
    )
    assert response.status_code == 403
