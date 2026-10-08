"""Valida a solicitação administrativa para alterar o setor de um produto."""

from flask import request, jsonify
from app.routes.product import produtos_bp
from app.services.buscar import buscar
from app.models.produto import Produto
from app.security.authorization import admin_required
from app.DATABASE import get_db
from app import limiter


@produtos_bp.route("/ajuste_setor_produto", methods=["POST"])
@limiter.limit("30 per minute")
@admin_required
def ajuste_setor():
    """Valida o produto e o setor antes de aplicar a alteração administrativa."""
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({"mensagem": "envie um objeto JSON valido"}), 400
    if not dados.get("codigo_barras") or "novo_setor" not in dados:
        return jsonify({"mensagem": "erro: verifique os campos e tente novamente"}), 400

    codigo_barras = dados["codigo_barras"]
    if not isinstance(codigo_barras, str) or not codigo_barras.strip():
        return jsonify({"mensagem": "codigo de barras invalido"}), 422
    if isinstance(dados["novo_setor"], bool):
        return jsonify({"mensagem": "setor invalido"}), 422
    try:
        setor = int(dados["novo_setor"])
    except (ValueError, TypeError, OverflowError):
        return jsonify({"mensagem": "setor invalido"}), 422
    if setor < 0 or setor > 9_223_372_036_854_775_807:
        return jsonify({"mensagem": "setor invalido"}), 422

    produto_existe = buscar(codigo_barras, config="status")
    if produto_existe is None:
        return jsonify({"mensagem": "erro ao consultar produto"}), 500
    if produto_existe is False:
        return jsonify({"mensagem": "erro: produto nao encontrado"}), 404

    with get_db() as conn:
        setor_existe = conn.execute(
            "SELECT 1 FROM setor WHERE id = ?",
            (setor,),
        ).fetchone()
    if setor_existe is None:
        return jsonify({"mensagem": "setor nao encontrado"}), 404

    sucesso = Produto.setor_ajustar(codigo_barras, setor)

    if not sucesso:
        return jsonify({"mensagem": "erro: verifique e tente novamente"}), 500

    return jsonify({"mensagem": "sucesso: setor ajustado"}), 200
