def test_cadastrar_usuario_exige_admin(client):
    from conftest import record_result
    response = record_result("POST /Cadastro_usuario", lambda: client.post("/Cadastro_usuario", json={}))
    assert response.status_code == 401
