"""Valida o ajuste de estoque e registra a movimentação associada."""

import logging

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity

from app import limiter
from app.core.security.authorization import admin_required
from app.models.movimentacao import EstoqueNaoEncontradoError
from app.products import produtos_bp
from app.products.services.find_product import buscar
from app.products.services.update_stock_quantity import update_stock_quantity

logger = logging.getLogger(__name__)

LIMITE_SQLITE = 9_223_372_036_854_775_807
MOTIVO_AJUSTE_ESTOQUE = 4  # padrão quando nenhum motivo é informado

# Ids da tabela motivos aceitos neste endpoint.
MOTIVOS_ACEITOS = (
    3,  # Devolução
    4,  # Ajuste de estoque
    6,  # Produto danificado
    7,  # Produto vencido
    9,  # Ruptura
)


@produtos_bp.route("/EditarQuantidade", methods=["POST"])
@limiter.limit("30 per minute")
@admin_required
def editar_produtos():
    """Valida a quantidade e o motivo e delega a atualização transacional do estoque."""
    usuario_logado = get_jwt_identity()
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({"mensagem": "JSON invalido"}), 400

    campos_obrigatorios = ("codigo_barras", "quantidade")
    if any(campo not in dados for campo in campos_obrigatorios):
        return jsonify({"mensagem": "campo obrigatorio ausente"}), 400

    codigo_barras = dados["codigo_barras"]
    if not isinstance(codigo_barras, str) or not codigo_barras.strip():
        return jsonify({"mensagem": "codigo de barras invalido"}), 422

    try:
        quantidade_original = dados["quantidade"]
        motivo_original = dados.get("motivo")
        if motivo_original is None:
            motivo_original = MOTIVO_AJUSTE_ESTOQUE

        if isinstance(quantidade_original, bool) or isinstance(motivo_original, bool):
            raise ValueError
        if isinstance(quantidade_original, float) and not quantidade_original.is_integer():
            raise ValueError
        if isinstance(motivo_original, float) and not motivo_original.is_integer():
            raise ValueError

        quantidade = int(quantidade_original)
        motivo_id = int(motivo_original)
    except (ValueError, TypeError, OverflowError):
        return jsonify({"mensagem": "quantidade ou motivo invalido"}), 422

    if quantidade < 0:
        return jsonify({"mensagem": "quantidade nao pode ser negativa"}), 422
    if quantidade > LIMITE_SQLITE:
        return jsonify({"mensagem": "quantidade invalida"}), 422
    if motivo_id not in MOTIVOS_ACEITOS:
        return jsonify({"mensagem": "motivo nao aceito para este ajuste"}), 422

    try:
        # Produto excluído conta como não encontrado.
        if not buscar(codigo_barras):
            return jsonify({"mensagem": "produto nao encontrado"}), 404

        update_stock_quantity(codigo_barras, quantidade, usuario_logado, motivo_id)

    except EstoqueNaoEncontradoError:
        return jsonify({"mensagem": "produto sem registro no estoque"}), 404
    except ValueError:
        # Quantidade e motivo já foram validados acima. Se chegou aqui, um id de
        # MOTIVOS_ACEITOS não existe na tabela motivos: erro de configuração.
        logger.exception("motivo de MOTIVOS_ACEITOS nao existe na tabela motivos")
        return jsonify({"mensagem": "erro inesperado, tente novamente mais tarde"}), 500
    except Exception:
        logger.exception("erro ao atualizar estoque")
        return jsonify({"mensagem": "erro inesperado, tente novamente mais tarde"}), 500

    return jsonify({"mensagem": "ok, quantidade ajustada"}), 200