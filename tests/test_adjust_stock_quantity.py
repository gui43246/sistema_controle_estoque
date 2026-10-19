def test_adjust_stock_quantity_requires_admin(client):
    from conftest import record_result
    response = record_result("POST /EditarQuantidade", lambda: client.post("/EditarQuantidade", json={}))
    assert response.status_code == 401
