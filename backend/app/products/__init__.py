"""Define e registra as rotas de produtos e estoque."""

from flask import Blueprint

produtos_bp = Blueprint("produtos", __name__)

from .routes import (
    adjust_sector,
    adjust_stock_quantity,
    create_product,
    delete_product,
    list_inventory,
    list_stock_movements,
    search_product,
    update_product_price,
)
