def test_excluir_produto_exige_admin(client):
    from conftest import record_result
    response = record_result("PUT /ExcluirProduto", lambda: client.put("/ExcluirProduto", json={}))
    assert response.status_code == 401
