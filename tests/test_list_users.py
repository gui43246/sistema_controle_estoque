def test_list_users_requires_authentication(client):
    from conftest import record_result
    response = record_result("GET /usuarios", lambda: client.get("/usuarios"))
    assert response.status_code == 401
