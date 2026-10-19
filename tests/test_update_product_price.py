def test_update_product_price_requires_admin(client):
    from conftest import record_result
    response = record_result("POST /EditarValor", lambda: client.post("/EditarValor", json={}))
    assert response.status_code == 401
