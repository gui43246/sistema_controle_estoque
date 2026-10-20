"""
Cria a aplicação Flask e registra as rotas e a autenticação JWT.
"""
import os
from datetime import timedelta
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()


ENV = os.getenv("FLASK_ENV", "development")
JWT_SECRET = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET_KEY não configurada. Crie no .env")

# Bloqueia chaves fracas / de dev em produção
WEAK_SECRETS = {
    "dev-secret", "123456", "secret", "teste", "change-me",
    "troque-esta-chave-em-producao",
    "coloque-uma-chave-longa-e-aleatoria-aqui",
}
WEAK_SECRET_TERMS = (
    "coloque-uma-chave",
    "chave-longa-e-aleatoria-aqui",
    "your-secret-key",
    "change-me",
    "example-key",
    "senha-aqui",
)


def validate_production_secret(secret):
    """Reject placeholders, known weak values, and short production keys."""
    normalized_secret = secret.casefold()
    if (
        secret in WEAK_SECRETS
        or len(secret) < 32
        or any(term in normalized_secret for term in WEAK_SECRET_TERMS)
    ):
        raise RuntimeError(
            "JWT_SECRET_KEY insegura para produção. "
            "Use uma chave aleatória com no mínimo 32 caracteres."
        )


if ENV == "production":
    validate_production_secret(JWT_SECRET)

try:
    MAX_REQUEST_BODY_BYTES = int(os.getenv("MAX_CONTENT_LENGTH_BYTES", str(1024 * 1024)))
except ValueError as error:
    raise RuntimeError("MAX_CONTENT_LENGTH_BYTES deve ser um inteiro positivo") from error

if MAX_REQUEST_BODY_BYTES < 1:
    raise RuntimeError("MAX_CONTENT_LENGTH_BYTES deve ser um inteiro positivo")

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = JWT_SECRET
app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BODY_BYTES
# Define expiração explícita para poder testar token expirado
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
    minutes=int(os.getenv("JWT_ACCESS_MINUTES", "60"))
)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)


@app.errorhandler(Exception)
def handle_unexpected_exception(error):
    """Log unexpected failures and return a generic response to clients."""
    if isinstance(error, HTTPException):
        response = error.get_response()
        response.set_data(app.json.dumps({"mensagem": error.name}))
        response.content_type = "application/json"
        return response
    app.logger.error(
        "erro inesperado não tratado",
        exc_info=(type(error), error, error.__traceback__),
    )
    return jsonify({"mensagem": "erro interno, tente novamente mais tarde"}), 500


@app.errorhandler(413)
def handle_request_too_large(error):
    """Return a generic JSON response when a request exceeds the body limit."""
    return jsonify({"mensagem": "corpo da requisição excede o limite permitido"}), 413

jwt = JWTManager(app)

# Tratamento uniforme de erro de JWT (Item 5)
@jwt.expired_token_loader
def expired_token(jwt_header, jwt_payload):
    return jsonify({"error": "Token expirado"}), 401

@jwt.invalid_token_loader
def invalid_token(reason):
    return jsonify({"error": "Token inválido"}), 401

@jwt.unauthorized_loader
def missing_token(reason):
    return jsonify({"error": "Token ausente"}), 401

# Limiter
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
)

from .products import products_bp
from .users import users_bp

app.register_blueprint(products_bp)
app.register_blueprint(users_bp)
