"""Testes isolados da autenticação e do cadastro de usuários."""

import sqlite3
from contextlib import contextmanager

import pytest
from flask_jwt_extended import create_access_token

from app import app
from app.core.security.password_hash import criar_hash
from app.users.services.validate_email import validar_email
from app.users.services.validate_password import validar_senha
from app.users.services.validate_phone_number import validar_telefone
from app.users.services.validate_user_name import validar_name
from app.users.services.verify_employee_id import validar_DRT


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
            ("123456789", "Pessoa Comum", "comum@gmail.com", "11912345678", criar_hash("Senha123!"), "user_comum"),
        )
        conn.execute(
            "INSERT INTO users (drt, name, email, numero_telefone, senha, tipo_user) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("987654321", "Administradora", "admin@gmail.com", "11987654321", criar_hash("Admin123!"), "adm"),
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


def test_login_nao_revela_se_drt_existe_e_autentica(auth_client):
    inexistente = auth_client.post("/login", json={"drt": "000000000", "senha_digitada": "Senha123!"})
    senha_errada = auth_client.post("/login", json={"drt": "123456789", "senha_digitada": "Errada123!"})
    assert inexistente.status_code == senha_errada.status_code == 401
    assert inexistente.get_json() == senha_errada.get_json() == {"mensagem": "DRT ou senha incorretos"}

    correto = auth_client.post("/login", json={"drt": "123456789", "senha_digitada": "Senha123!"})
    assert correto.status_code == 200
    assert correto.get_json()["mensagem"] == "login realizado"
    assert "token" in correto.get_json()


def test_listagem_de_usuarios_exige_admin_e_nao_expoe_hash(auth_client):
    assert auth_client.get("/usuarios").status_code == 401
    comum = auth_client.get("/usuarios", headers={"Authorization": f"Bearer {token_for('123456789')}"})
    assert comum.status_code == 403
    admin = auth_client.get("/usuarios", headers={"Authorization": f"Bearer {token_for('987654321')}"})
    assert admin.status_code == 200
    assert all("senha" not in usuario for usuario in admin.get_json())


@pytest.mark.parametrize("nome", ["José da Silva", "Conceição"])
def test_validar_name_aceita_acentos(nome):
    assert validar_name(nome)


@pytest.mark.parametrize("nome", ["   ", "", "Ana123"])
def test_validar_name_rejeita_vazio_espacos_ou_numeros(nome):
    assert not validar_name(nome)


def test_validar_drt_so_confere_formato():
    assert validar_DRT("123456789")[0]
    for valor in ("12345678", "1234567890", "12345678a", 123456789, None):
        assert not validar_DRT(valor)[0]


@pytest.mark.parametrize("valor", [123, None])
def test_validadores_rejeitam_tipos_errados(valor):
    assert not validar_senha(valor)[0]
    assert not validar_email(valor)
    assert not validar_telefone(valor)


def test_validar_senha_respeita_limite_de_caracteres_e_bytes():
    assert validar_senha("Abcdef1!" + "x" * 56)[0]
    assert not validar_senha("Abcdef1!" + "x" * 57)[0]
    assert not validar_senha("Á" * 37 + "aA1!")[0]


def dados_cadastro(**alteracoes):
    dados = {
        "drt": "111222333",
        "name": "José da Silva",
        "email": "NOVO@GMAIL.COM",
        "numero_tel": "11922223333",
        "senha": "SenhaNova1!",
    }
    dados.update(alteracoes)
    return dados


def test_cadastro_valida_formato_unicidade_e_minimiza_email(auth_client):
    malformado = auth_client.post("/Cadastro_usuario", json=dados_cadastro(drt="12"), headers={"Authorization": f"Bearer {token_for('987654321')}"})
    assert malformado.status_code == 400

    headers = {"Authorization": f"Bearer {token_for('987654321')}"}
    primeiro = auth_client.post("/Cadastro_usuario", json=dados_cadastro(), headers=headers)
    assert primeiro.status_code == 201
    mesmo_drt = auth_client.post("/Cadastro_usuario", json=dados_cadastro(email="outro@gmail.com", numero_tel="11922223334"), headers=headers)
    assert mesmo_drt.status_code == 409
    mesmo_email = auth_client.post("/Cadastro_usuario", json=dados_cadastro(drt="111222334", numero_tel="11922223335"), headers=headers)
    assert mesmo_email.status_code == 409

    import app.users.routes.create_user as create_user
    with create_user.get_db() as conn:
        salvo = conn.execute("SELECT email FROM users WHERE drt = ?", ("111222333",)).fetchone()
    assert salvo["email"] == "novo@gmail.com"


def test_cadastro_rejeita_usuario_comum(auth_client):
    response = auth_client.post(
        "/Cadastro_usuario",
        json=dados_cadastro(),
        headers={"Authorization": f"Bearer {token_for('123456789')}"},
    )
    assert response.status_code == 403
