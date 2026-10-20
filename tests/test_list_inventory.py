import sqlite3

from flask_jwt_extended import create_access_token

from app import app


def test_list_inventory_requires_authentication(client):
    from conftest import record_result
    response = record_result("GET /estoque", lambda: client.get("/estoque"))
    assert response.status_code == 401


def test_list_inventory_hides_database_error(client, monkeypatch):
    import app.products.routes.list_inventory as inventory_route

    def fail_database_connection():
        raise sqlite3.OperationalError("private database path")

    monkeypatch.setattr(inventory_route, "get_db", fail_database_connection)
    app.config["JWT_SECRET_KEY"] = "list-inventory-test-secret-at-least-32-bytes"
    with app.app_context():
        token = create_access_token(identity="123456789")

    response = client.get("/estoque", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 500
    assert "private database path" not in response.get_data(as_text=True)
