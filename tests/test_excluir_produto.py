def test_excluir_produto_exige_admin(client):
    from conftest import record_result
    response = record_result("DELETE /produto/codigo", lambda: client.delete("/produto/codigo"))
    assert response.status_code == 401
