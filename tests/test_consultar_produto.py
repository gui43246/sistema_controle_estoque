def test_consultar_produto_exige_autenticacao(client):
    from conftest import record_result
    response = record_result("POST /consultar", lambda: client.post("/consultar", json={}))
    assert response.status_code == 401
