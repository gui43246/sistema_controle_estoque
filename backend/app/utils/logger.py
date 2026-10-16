"""Logging centralizado da aplicação e dos testes."""

import logging
import os
from pathlib import Path
from threading import Lock

_LOGGER_NAME = "estoque"
_CONFIG_LOCK = Lock()


def get_logger(name: str = _LOGGER_NAME) -> logging.Logger:
    """Retorna logger reutilizável com saída para arquivo e console.

    O arquivo padrão é <raiz do projeto>/logs/app.log. A variável
    ESTOQUE_LOG_FILE pode apontar para outro caminho, útil em testes.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    with _CONFIG_LOCK:
        if not logger.handlers:
            file_path = Path(os.getenv("ESTOQUE_LOG_FILE", Path(__file__).resolve().parents[3] / "logs" / "app.log"))
            file_path.parent.mkdir(parents=True, exist_ok=True)
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler = logging.FileHandler(file_path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
    return logger


def log_message(level: str, message: str, *, logger_name: str = _LOGGER_NAME) -> None:
    """Registra mensagem nos níveis INFO, WARNING ou ERROR."""
    normalized_level = level.upper()
    levels = {"INFO": logging.INFO, "WARNING": logging.WARNING, "ERROR": logging.ERROR}
    if normalized_level not in levels:
        raise ValueError("Nível inválido. Use INFO, WARNING ou ERROR.")
    get_logger(logger_name).log(levels[normalized_level], message)
