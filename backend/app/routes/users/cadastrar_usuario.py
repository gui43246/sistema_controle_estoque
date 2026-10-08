"""Valida e cadastra uma conta de usuário comum."""

from flask import request,jsonify
import sqlite3
from app.routes.users import users_bp
from app.DATABASE import get_db
from app.services import (
    validar_name,
    validar_email,
    validar_telefone,
    validar_senha,
    validar_DRT,
)
from app.security.hash import criar_hash
from app.security.authorization import admin_required
from app import limiter
@users_bp.route("/Cadastro_usuario", methods=["POST"])
@limiter.limit("10 per minute")
@admin_required
def cadastrar_usuario():
    
    """Valida os dados, gera o hash da senha e cria um usuário comum."""
    dados = request.get_json(silent=True)
    obrigatorio = ["DRT", "name", "Email", "numero_tel", "senha"]
    
    if not isinstance(dados, dict) or any(campo not in dados for campo in obrigatorio):
        return jsonify({"mensagem": "sem resultado, verifique os dados"}), 400
    
    DRT = dados["DRT"]
    name = dados["name"]
    Email = dados["Email"]
    numero_tel = dados["numero_tel"]
    senha = dados["senha"]

    if any(not isinstance(valor, str) for valor in (DRT, name, Email, numero_tel, senha)):
        return jsonify({"mensagem": "todos os campos devem ser textos"}), 400
    
    drt_ok, mensagem = validar_DRT(DRT)
    if not drt_ok:
        return jsonify({"mensagem": mensagem}), 409
    
    if not validar_name(name):
        return jsonify({"mensagem": "verifique o nome"}), 400
    
    if not validar_email(Email):
        return jsonify({"mensagem": "email invalido"}), 400
    
    senha_ok, mensagem = validar_senha(senha)
    if not senha_ok:
        return jsonify({"mensagem": mensagem}), 400
    
    senha=criar_hash(senha)
    
    if not validar_telefone(numero_tel):
        return jsonify({"mensagem": "verifique o numero de telefone"}), 400
    
    with get_db() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users(drt, name, email, numero_telefone, senha)
                VALUES (?, ?, ?, ?, ?)
            """, (DRT, name, Email, numero_tel, senha))
            conn.commit()
            return jsonify({"mensagem": "ok usuario cadastrado"}), 201
        except sqlite3.IntegrityError:
            return jsonify({"mensagem": "DRT ou email ja cadastrados"}), 409
        except sqlite3.Error:
            return jsonify({"mensagem": "erro interno, tente mais tarde"}), 500
