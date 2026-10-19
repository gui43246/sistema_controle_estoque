"""Pagination behavior for the API list endpoints."""

import pytest
from flask_jwt_extended import create_access_token

from app import app
from app.core import database


LIST_ENDPOINTS = ("/estoque", "/movimentacoes", "/usuarios")


@pytest.fixture
def paged_api(tmp_path, monkeypatch):
    db_path = tmp_path / "pagination.sqlite"
    monkeypatch.setattr(database, "DB_PATH", str(db_path))
    database.init_db()

    with database.get_db() as conn:
        for index in range(3):
            drt = f"90000000{index}"
            conn.execute(
                "INSERT INTO users (drt, name, email, numero_telefone, senha, tipo_user) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (drt, f"Pessoa {index}", f"pessoa{index}@example.com", f"1190000000{index}", "hash", "adm" if index == 0 else "user_comum"),
            )
            barcode = f"78900000000{index}"
            conn.execute(
                "INSERT INTO Produtos_cadastrados (codigo_barras, nome_produto, valor_prod, setor_id) "
                "VALUES (?, ?, ?, 1)",
                (barcode, f"Produto {index}", 10 + index),
            )
            conn.execute(
                "INSERT INTO estoque (codigo_barras, quantidade) VALUES (?, ?)",
                (barcode, index + 1),
            )
            conn.execute(
                "INSERT INTO movimentacoes (status, codigo_barras, quantidade, motivo, usuario_drt) "
                "VALUES ('ajuste', ?, ?, 'Ajuste', ?)",
                (barcode, index + 1, "900000000"),
            )

    app.config.update(TESTING=True, JWT_SECRET_KEY="pagination-test-secret-key-with-at-least-32-bytes")
    with app.app_context():
        token = create_access_token(identity="900000000")
    with app.test_client() as client:
        yield client, {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("endpoint", LIST_ENDPOINTS)
def test_list_endpoint_returns_page_one_and_two(paged_api, endpoint):
    client, headers = paged_api
    first = client.get(f"{endpoint}?page=1&per_page=1", headers=headers)
    second = client.get(f"{endpoint}?page=2&per_page=1", headers=headers)

    assert first.status_code == second.status_code == 200
    first_data, second_data = first.get_json(), second.get_json()
    assert first_data["page"] == 1 and second_data["page"] == 2
    assert first_data["per_page"] == second_data["per_page"] == 1
    assert first_data["total"] == second_data["total"] == 3
    assert len(first_data["items"]) == len(second_data["items"]) == 1
    assert first_data["items"] != second_data["items"]


@pytest.mark.parametrize("endpoint", LIST_ENDPOINTS)
def test_list_endpoint_caps_per_page_and_uses_default(paged_api, endpoint):
    client, headers = paged_api
    capped = client.get(f"{endpoint}?per_page=999", headers=headers)
    default = client.get(endpoint, headers=headers)

    assert capped.status_code == default.status_code == 200
    assert capped.get_json()["per_page"] == 200
    assert default.get_json()["page"] == 1
    assert default.get_json()["per_page"] == 50


@pytest.mark.parametrize("endpoint", LIST_ENDPOINTS)
@pytest.mark.parametrize("page", ["0", "-1", "not-a-number"])
def test_list_endpoint_rejects_invalid_page(paged_api, endpoint, page):
    client, headers = paged_api
    response = client.get(f"{endpoint}?page={page}", headers=headers)
    assert response.status_code == 400
    assert response.get_json()["mensagem"]
