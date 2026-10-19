def test_login_rejects_invalid_payload(client):
    from conftest import record_result
    response = record_result("POST /login", lambda: client.post("/login", json={}))
    assert response.status_code == 400
