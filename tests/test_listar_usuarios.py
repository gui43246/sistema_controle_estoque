def test_listar_usuarios_exige_autenticacao(client):
    from conftest import record_result
    response = record_result("GET /usuarios", lambda: client.get("/usuarios"))
    assert response.status_code == 401
