def test_update_sector_requires_admin(client):
    from conftest import record_result
    response = record_result("POST /ajuste_setor_produto", lambda: client.post("/ajuste_setor_produto", json={}))
    assert response.status_code == 401
