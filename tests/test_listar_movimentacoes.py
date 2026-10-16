def test_listar_movimentacoes_exige_autenticacao(client):
    from conftest import record_result
    response = record_result("GET /movimentacoes", lambda: client.get("/movimentacoes"))
    assert response.status_code == 401
