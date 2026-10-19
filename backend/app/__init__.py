"""
Cria a aplicação Flask e registra as rotas e a autenticação JWT.
"""
import os
from datetime import timedelta
from flask import Flask, jsonify
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
WEAK_SECRETS = {"dev-secret", "123456", "secret", "teste", "change-me", "troque-esta-chave-em-producao"}
if ENV == "production":
    if JWT_SECRET in WEAK_SECRETS or len(JWT_SECRET) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY insegura para produção. "
            "Use uma chave aleatória com no mínimo 32 caracteres."
        )

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = JWT_SECRET
# Define expiração explícita para poder testar token expirado
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
    minutes=int(os.getenv("JWT_ACCESS_MINUTES", "60"))
)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)

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