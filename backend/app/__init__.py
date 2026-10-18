"""
Cria a aplicação Flask e registra as rotas e a autenticação JWT.
"""

import os
import unicodedata
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar aplicação Flask
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")


@app.after_request
def remover_acentos_das_respostas_json(response):
    """Remove diacríticos de textos nas respostas JSON da API."""
    if not response.is_json:
        return response

    payload = response.get_json(silent=True)
    if payload is None:
        return response

    def normalizar(valor):
        if isinstance(valor, str):
            decomposed = unicodedata.normalize("NFKD", valor)
            return "".join(char for char in decomposed if not unicodedata.combining(char))
        if isinstance(valor, list):
            return [normalizar(item) for item in valor]
        if isinstance(valor, dict):
            return {normalizar(chave): normalizar(item) for chave, item in valor.items()}
        return valor

    response.set_data(app.json.dumps(normalizar(payload)))
    return response

# Configurar JWT
jwt = JWTManager(app)

# Configurar Limiter (rate limiting)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
)

# Importar as rotas depois de criar o limiter, pois elas o usam nos decorators.
from .products import produtos_bp
from .users import users_bp

# Registrar blueprints.
app.register_blueprint(produtos_bp)
app.register_blueprint(users_bp)
