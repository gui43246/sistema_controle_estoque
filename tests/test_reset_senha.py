def test_reset_senha_exige_admin(client):
    from conftest import record_result
    response = record_result("POST /reset_senha", lambda: client.post("/reset_senha", json={}))
    assert response.status_code == 401
