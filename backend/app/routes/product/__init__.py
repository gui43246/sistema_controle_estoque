"""Define e registra as rotas de produtos e estoque."""

from flask import Blueprint

produtos_bp = Blueprint("produtos", __name__)

from . import (
    cadastrar,
    editar_quantidade,
    estoque,
    editar_valor,
    ajuste_setor,
    excluir,
    movimentacoes,
    buscar_produto,
)
