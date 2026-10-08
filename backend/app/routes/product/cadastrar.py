"""Valida e cadastra um produto novo com estoque inicial zerado."""
from flask import  request, jsonify
from app.DATABASE import get_db
import sqlite3
from app.models.produto import Produto
from app.routes.product import produtos_bp
from app.services.buscar import buscar
from app import limiter
from app.security.authorization import admin_required
import math


@produtos_bp.route('/cadastrar', methods=["POST"])
@limiter.limit("30 per minute")
@admin_required
def cadastrar_produto():
    """Valida os campos e cadastra o produto e seu registro de estoque."""
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        dados = request.get_json(silent=True)
        if not isinstance(dados, dict):
            return jsonify({"mensagem": "envie um objeto JSON valido"}), 400

        campos_obrigatorios = ["codigo_barras","nome_produto","valor_prod","setor_id"]
        faltando = [campo for campo in campos_obrigatorios if not campo in dados]
        if faltando:
            return jsonify({"mensagem": f"faltando o campo {','.join(faltando)}"}),400
        
        if not isinstance(dados["codigo_barras"], str) or not dados["codigo_barras"].strip():
            return jsonify({"mensagem": "codigo de barras invalido"}), 422
        if not isinstance(dados["nome_produto"], str) or not dados["nome_produto"].strip():
            return jsonify({"mensagem": "nome do produto invalido"}), 422
        if isinstance(dados["valor_prod"], bool) or isinstance(dados["setor_id"], bool):
            return jsonify({"mensagem": "Campo invalido: valor_prod ou setor_id"}), 422

        try:
            dados["valor_prod"] = float(dados["valor_prod"])
            dados["setor_id"] = int(dados["setor_id"])
        except (ValueError, TypeError, OverflowError):
            return jsonify({"mensagem": "Campo invalido: valor_prod ou setor_id"}), 422

        if dados["setor_id"] < 1 or dados["setor_id"] > 9_223_372_036_854_775_807:
            return jsonify({"mensagem": "setor_id invalido"}), 422
        if not math.isfinite(dados["valor_prod"]) or dados["valor_prod"] < 0:
            return jsonify({"mensagem": "valor do produto invalido"}), 422

        setor_existe = cursor.execute(
            "SELECT 1 FROM setor WHERE id = ?",
            (dados["setor_id"],),
        ).fetchone()
        if setor_existe is None:
            return jsonify({"mensagem": "setor nao encontrado"}), 404
        
        produto_existe = buscar(dados["codigo_barras"], config="status")
        if produto_existe is None:
            return jsonify({"mensagem": "erro ao consultar produto"}), 500
        if produto_existe is False:
            
            NOVO_PRODUTO = Produto(codigo_barras=dados["codigo_barras"],nome_produto=dados["nome_produto"],valor_produto=dados["valor_prod"],setor=dados["setor_id"])
            
            cursor.execute("""
                INSERT INTO Produtos_cadastrados(
                    codigo_barras,
                    nome_produto,
                    valor_prod,
                    setor_id
                ) VALUES (?, ?, ?, ?)
            """, (
                NOVO_PRODUTO.codigo_barras,
                NOVO_PRODUTO.nome_produto,
                NOVO_PRODUTO.valor_produto,
                NOVO_PRODUTO.setor
            ))
            cursor.execute("""INSERT INTO estoque(
                codigo_barras
                )VALUES(?)""", 
                (NOVO_PRODUTO.codigo_barras,))
                                   
            conn.commit()
            
            
            return jsonify({"mensagem": "Sucesso ao cadastrar item"}), 201
        else:
            return jsonify({"mensagem":"produto ja cadastrado com esse codigo de barras"}),409
            
    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro inespeado tenta novamente mais tarde: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"mensagem": "Erro inesperado, verifique os campos e tente novamnete "}), 500
    finally:
        if conn:
            conn.close()

        
