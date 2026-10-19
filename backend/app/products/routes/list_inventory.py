"""Lista os produtos e as quantidades disponíveis no estoque."""

from flask import Flask,request,jsonify
import sqlite3
from app.core.database import get_db
from app.products import products_bp
from flask_jwt_extended import jwt_required
from app import limiter

@products_bp.route("/estoque",methods=["GET"])
@limiter.limit("30 per minute")
@jwt_required()
def  list_inventory_route():
    
    """Retorna uma lista JSON dos produtos com saldo de estoque."""
    try:
        with get_db() as conn:
            conn.row_factory= sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT
                           p.codigo_barras,
                           p.nome_produto,
                           p.valor_prod,
                           p.setor_id,
                           e.quantidade
                           FROM Produtos_cadastrados p 
                           JOIN estoque e ON p.codigo_barras = e.codigo_barras
                           WHERE p.status = 'ativo'
                           """)
            products = cursor.fetchall()
            items =[]
            for p in products:
                items.append({
                   "codigo_barras":p["codigo_barras"],
                   "nome_produto": p["nome_produto"],
                   "valor_prod": p["valor_prod"],
                   "setor_id": p["setor_id"],
                    "quantidade": p["quantidade"]
                })
            return jsonify(items)
    except Exception as e:
        return  jsonify({"mensagem":f"erro: {e}"}),500
