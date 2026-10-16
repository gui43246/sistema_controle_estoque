def test_ajustar_quantidade_exige_admin(client):
    from conftest import record_result
    response = record_result("POST /EditarQuantidade", lambda: client.post("/EditarQuantidade", json={}))
    assert response.status_code == 401
