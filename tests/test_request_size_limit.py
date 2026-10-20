"""Request body size limit behavior."""

from app import app


def test_oversized_request_returns_generic_json_413(client, monkeypatch):
    monkeypatch.setitem(app.config, "MAX_CONTENT_LENGTH", 32)

    response = client.post(
        "/login",
        data=b"x" * 33,
        content_type="application/json",
    )

    assert response.status_code == 413
    assert response.is_json
    assert response.get_json() == {
        "mensagem": "corpo da requisição excede o limite permitido"
    }


def test_normal_sized_request_still_reaches_login_validation(client, monkeypatch):
    monkeypatch.setitem(app.config, "MAX_CONTENT_LENGTH", 32)

    response = client.post(
        "/login",
        json={},
    )

    assert response.status_code == 400
    assert response.is_json
