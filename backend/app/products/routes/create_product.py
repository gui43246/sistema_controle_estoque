"""Valida e cadastra um produto novo com estoque inicial zerado."""

from flask import request, jsonify
import sqlite3
from app.models.product import Produto
from app.models.movimentacao import Movimentacao
from app.products import produtos_bp
from app.products.services.find_product import buscar
from app import limiter
from app.core.security.authorization import admin_required
from flask_jwt_extended.utils import get_jwt_identity


@produtos_bp.route("/cadastrar", methods=["POST"])
@limiter.limit("30 per minute")
@admin_required
def cadastrar_produto():
    usuario_logado = get_jwt_identity()
    """Valida os campos e cadastra o produto e seu registro de estoque."""
    try:
        dados = request.get_json(silent=True)
        if not isinstance(dados, dict):
            return jsonify({"mensagem": "envie um objeto JSON valido"}), 400

        campos_obrigatorios = [
            "codigo_barras",
            "nome_produto",
            "valor_prod",
            "setor_id",
        ]
        faltando = [campo for campo in campos_obrigatorios if not campo in dados]
        if faltando:
            return jsonify({"mensagem": f"faltando o campo {','.join(faltando)}"}), 400

        try:
            novo_produto = Produto.from_values(
                codigo_barras=dados["codigo_barras"],
                nome_produto=dados["nome_produto"],
                valor_produto=dados["valor_prod"],
                setor=dados["setor_id"],
            )
        except ValueError as error:
            return jsonify({"mensagem": str(error)}), 422

        produto_existe = buscar(dados["codigo_barras"], config="status")
        if produto_existe is None:
            return jsonify({"mensagem": "erro ao consultar produto"}), 500
        if produto_existe is False:
            if novo_produto.commit():
                Movimentacao.registrar(
                    codigo_barras=novo_produto.codigo_barras,
                    quantidade=0,
                    status="entrada",
                    motivo=1,
                    usuario_drt=usuario_logado)
                
                return jsonify({"mensagem": "Sucesso ao cadastrar item"}), 201
            return jsonify({"mensagem": "erro ao cadastrar produto; tente novamente"}), 500

        return jsonify({"mensagem": "produto ja cadastrado"}), 409

    except sqlite3.Error as e:
        return jsonify({"mensagem": f"Erro inesperado, tente novamente mais tarde: {str(e)}"}), 500

    except Exception:
        return jsonify({"mensagem": "Erro inesperado, verifique os campos e tente novamente"}), 500

