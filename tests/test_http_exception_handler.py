"""HTTP exceptions keep their status and receive a JSON response."""

import logging


def test_not_found_stays_404_json_without_global_error_log(client, caplog):
    with caplog.at_level(logging.ERROR, logger="app"):
        response = client.get("/route-that-does-not-exist")

    assert response.status_code == 404
    assert response.is_json
    assert response.get_json() == {"mensagem": "Not Found"}
    assert "erro inesperado não tratado" not in caplog.text


def test_method_not_allowed_stays_405_json_without_global_error_log(client, caplog):
    with caplog.at_level(logging.ERROR, logger="app"):
        response = client.get("/login")

    assert response.status_code == 405
    assert response.is_json
    assert response.get_json() == {"mensagem": "Method Not Allowed"}
    assert response.headers["Allow"]
    assert "erro inesperado não tratado" not in caplog.text
