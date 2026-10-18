"""Configuração compartilhada dos testes da API."""
import pytest
from app import app


@pytest.fixture
def client():
    app.config.update(TESTING=True, JWT_SECRET_KEY="pytest-secret")
    with app.test_client() as test_client:
        yield test_client


def record_result(name, call):
    """Executa a chamada; mantido para compatibilidade com testes existentes."""
    return call()
