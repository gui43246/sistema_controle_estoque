def test_create_product_requires_admin(client):
    from conftest import record_result
    response = record_result("POST /cadastrar", lambda: client.post("/cadastrar", json={}))
    assert response.status_code == 401
