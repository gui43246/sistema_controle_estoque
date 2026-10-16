def test_cadastrar_produto_exige_admin(client):
    from conftest import record_result
    response = record_result("POST /cadastrar", lambda: client.post("/cadastrar", json={}))
    assert response.status_code == 401
