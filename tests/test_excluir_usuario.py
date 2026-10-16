def test_excluir_usuario_exige_admin(client):
    from conftest import record_result
    response = record_result("DELETE /usuarios/000", lambda: client.delete("/usuarios/000"))
    assert response.status_code == 401
