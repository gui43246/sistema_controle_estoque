"""Configuração compartilhada dos testes da API."""
import os
import tempfile

# Defina a configuração dos testes antes de importar a aplicação. Desabilitar
# python-dotenv impede que valores do .env local afetem a coleta da suíte.
os.environ["PYTHON_DOTENV_DISABLED"] = "1"
os.environ.setdefault("FLASK_ENV", "development")
os.environ.setdefault(
    "JWT_SECRET_KEY", "pytest-only-fake-secret-key-32-characters-minimum"
)
os.environ.setdefault("JWT_ACCESS_MINUTES", "60")
os.environ.setdefault("RATELIMIT_STORAGE_URI", "memory://")
os.environ.setdefault(
    "CAMINHO_BANCO",
    os.path.join(tempfile.gettempdir(), "estoque-pytest-unused.sqlite"),
)

import pytest
from app import app, limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter_storage():
    """Keep in-memory request counters independent between tests."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def client():
    app.config.update(
        TESTING=True,
        JWT_SECRET_KEY="pytest-only-fake-secret-key-32-characters-minimum",
    )
    with app.test_client() as test_client:
        yield test_client


def record_result(name, call):
    """Executa a chamada; mantido para compatibilidade com testes existentes."""
    return call()
