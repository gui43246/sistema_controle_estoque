"""Valida e cadastra um produto novo com estoque inicial zerado."""

import sqlite3

from flask import current_app, jsonify, request
from flask_jwt_extended.utils import get_jwt_identity
from app import limiter
from app.core.security.authorization import admin_required
from app.models.product import Produto
from app.products import produtos_bp
from app.products.services.create_product import cria_produto  # ajuste o caminho
from app.products.services.find_product import buscar
from app.products.services.sector_service import buscar_setor

CAMPOS_OBRIGATORIOS = ("codigo_barras", "nome_produto", "valor_prod", "setor_id")


@produtos_bp.route("/cadastrar", methods=["POST"])
@limiter.limit("30 per minute")
@admin_required
def cadastrar_produto():
    """Valida os campos e cadastra o produto, seu estoque e a movimentação."""
    usuario_logado = get_jwt_identity()

    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({"mensagem": "envie um objeto JSON valido"}), 400

    faltando = [campo for campo in CAMPOS_OBRIGATORIOS if campo not in dados]
    if faltando:
        return jsonify({"mensagem": f"faltando o campo {', '.join(faltando)}"}), 400

    try:
        novo_produto = Produto.from_values(
            codigo_barras=dados["codigo_barras"],
            nome_produto=dados["nome_produto"],
            valor_produto=dados["valor_prod"],
            setor=dados["setor_id"],
        )
    except ValueError as error:
        return jsonify({"mensagem": str(error)}), 422

    try:
        if buscar_setor(novo_produto.setor) is None:
            return jsonify({"mensagem": "setor nao encontrado"}), 404

        if buscar(novo_produto.codigo_barras):
            return jsonify({"mensagem": "produto ja cadastrado"}), 409

        cria_produto(usuario_logado, novo_produto)

    except sqlite3.IntegrityError:
        return jsonify({"mensagem": "produto ja cadastrado"}), 409
    except Exception:
        current_app.logger.exception("erro ao cadastrar produto")
        return jsonify({"mensagem": "erro inesperado, tente novamente mais tarde"}), 500

    return jsonify({"mensagem": "Sucesso ao cadastrar item"}), 201