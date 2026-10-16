"""Configuração compartilhada dos testes da API."""
import pytest
from app import app
from app.utils.logger import log_message


@pytest.fixture
def client():
    app.config.update(TESTING=True, JWT_SECRET_KEY="pytest-secret")
    with app.test_client() as test_client:
        yield test_client


def record_result(name, call):
    """Executa a chamada e registra sucesso, rejeição esperada ou exceção."""
    try:
        result = call()
        status = getattr(result, "status_code", None)
        if status is not None and status >= 400:
            log_message(
                "WARNING",
                f"{name}: resposta HTTP {status}",
                logger_name="estoque.tests",
            )
        else:
            log_message(
                "INFO",
                f"{name}: teste concluído com sucesso",
                logger_name="estoque.tests",
            )
        return result
    except Exception:
        log_message("ERROR", f"{name}: teste falhou com exceção", logger_name="estoque.tests")
        raise
