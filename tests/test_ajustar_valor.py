def test_ajustar_valor_exige_admin(client):
    from conftest import record_result
    response = record_result("POST /EditarValor", lambda: client.post("/EditarValor", json={}))
    assert response.status_code == 401
