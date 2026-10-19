def test_list_stock_movements_requires_authentication(client):
    from conftest import record_result
    response = record_result("GET /movimentacoes", lambda: client.get("/movimentacoes"))
    assert response.status_code == 401
