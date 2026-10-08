"""
Cria a aplicação Flask e registra as rotas e a autenticação JWT.
"""

import os
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
from .routes.product import produtos_bp
from .routes.users import users_bp

# Registrar blueprints.
app.register_blueprint(produtos_bp)
app.register_blueprint(users_bp)
