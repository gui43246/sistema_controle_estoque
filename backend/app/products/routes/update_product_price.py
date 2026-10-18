"""Valida e altera o preço de um produto existente."""

import logging
import math

from flask import jsonify, request
from flask_jwt_extended.utils import get_jwt_identity

from app import limiter
from app.core.security.authorization import admin_required
from app.products import produtos_bp
from app.products.services.find_product import buscar
from app.products.services.update_product_price import (
    ProdutoNaoEncontradoError,
    update_product_price,
)

logger = logging.getLogger(__name__)


@produtos_bp.route("/EditarValor", methods=["POST"])
@limiter.limit("30 per minute")
@admin_required
def ajustar_valor_produto():
    """Valida o novo preço e atualiza o produto por código de barras."""
    usuario_logado = get_jwt_identity()
    requisicao = request.get_json(silent=True)

    if not isinstance(requisicao, dict):
        return jsonify({"mensagem": "envie um objeto JSON valido"}), 400
    if not requisicao.get("codigo_barras") or "novo_valor" not in requisicao:
        return jsonify({"mensagem": "verifique os campos e tente novamente"}), 400

    codigo_barras = requisicao["codigo_barras"]
    if not isinstance(codigo_barras, str) or not codigo_barras.strip():
        return jsonify({"mensagem": "codigo de barras invalido"}), 422

    novo_valor = requisicao["novo_valor"]
    if isinstance(novo_valor, bool):
        return jsonify({"mensagem": "novo valor invalido"}), 422
    try:
        valor = float(novo_valor)
    except (TypeError, ValueError, OverflowError):
        return jsonify({"mensagem": "novo valor invalido"}), 422
    if not math.isfinite(valor) or valor < 0:
        return jsonify({"mensagem": "novo valor invalido"}), 422

    try:
        # Produto excluído conta como não encontrado.
        if not buscar(codigo_barras):
            return jsonify({"mensagem": "produto nao encontrado"}), 404

        update_product_price(codigo_barras, valor, usuario_logado)

    except ProdutoNaoEncontradoError:
        return jsonify({"mensagem": "produto nao encontrado"}), 404
    except Exception:
        logger.exception("erro ao atualizar preco")
        return jsonify({"mensagem": "erro inesperado, tente novamente mais tarde"}), 500

    return jsonify({"mensagem": "ok valor inserido com sucesso"}), 200