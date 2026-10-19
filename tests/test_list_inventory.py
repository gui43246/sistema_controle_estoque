def test_list_inventory_requires_authentication(client):
    from conftest import record_result
    response = record_result("GET /estoque", lambda: client.get("/estoque"))
    assert response.status_code == 401
