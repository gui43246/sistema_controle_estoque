"""Production configuration safety tests."""

import secrets

import pytest

from app import validate_production_secret


@pytest.mark.parametrize(
    "secret",
    [
        "coloque-uma-chave-longa-e-aleatoria-aqui",
        "dev-secret",
        "change-me",
        "esta-chave-contem-EXAMPLE-e-é-longa-o-suficiente",
        "senha-muito-longa-mas-ainda-insegura",
    ],
)
def test_production_rejects_example_and_weak_secrets(secret):
    with pytest.raises(RuntimeError):
        validate_production_secret(secret)


def test_production_accepts_generated_strong_secret():
    validate_production_secret(secrets.token_urlsafe(48))
