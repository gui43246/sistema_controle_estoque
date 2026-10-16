def test_listar_estoque_exige_autenticacao(client):
    from conftest import record_result
    response = record_result("GET /estoque", lambda: client.get("/estoque"))
    assert response.status_code == 401
