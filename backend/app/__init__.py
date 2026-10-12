"""Configura Flask, JWT, limite de requisições e rotas.

O limiter é configurado antes das rotas, que usam seus decoradores.
"""

import os
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

jwt = JWTManager(app)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
)

from .routes.product import produtos_bp
from .routes.users import users_bp

app.register_blueprint(produtos_bp)
app.register_blueprint(users_bp)
