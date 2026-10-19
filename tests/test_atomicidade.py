"""Testes de atomicidade dos serviços de produtos e estoque."""

import sqlite3

import pytest

from app.core import database
from app.models.product import Product, ProductNotFoundError
from app.models.movement import StockNotFoundError
from app.products.services import create_product as create_product_module
from app.products.services import delete_product as delete_product_module
from app.products.services import update_product_price as price_module
from app.products.services import update_product_sector as sector_module
from app.products.services import update_stock_quantity as stock_module


USER_DRT = "123456789"
BARCODE = "789000000001"


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Prepara um banco temporário com o esquema e os dados mínimos."""
    db_path = tmp_path / "atomicidade.sqlite"
    monkeypatch.setattr(database, "DB_PATH", str(db_path))
    database.init_db()

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO users (drt, name, email, numero_telefone, senha) VALUES (?, ?, ?, ?, ?)",
            (USER_DRT, "Usuário teste", "teste@example.com", "11912345678", "hash"),
        )
        conn.execute(
            "INSERT INTO Produtos_cadastrados (codigo_barras, nome_produto, valor_prod, setor_id) VALUES (?, ?, ?, 1)",
            (BARCODE, "Produto teste", 10.0),
        )
        conn.execute(
            "INSERT INTO estoque (codigo_barras, quantidade) VALUES (?, 7)", (BARCODE,)
        )

    return db_path


def rows(db_path, query, parameters=()):
    """Reads rows from the isolated database without touching production data."""
    with database.get_db() as conn:
        return conn.execute(query, parameters).fetchall()


def make_product(barcode, quantity=3):
    """Builds a valid product for service-level tests."""
    product = Product.from_values(barcode, "Produto novo", 12.5, 1)
    product.quantity = quantity
    return product


def test_create_product_rolls_back_when_reason_is_missing(isolated_db, monkeypatch):
    """Rolls back product and stock inserts when movement reason lookup fails."""
    monkeypatch.setattr(create_product_module, "REASON_CREATION", 999)
    with pytest.raises(ValueError, match="Motivo não encontrado"):
        create_product_module.create_product(USER_DRT, make_product("789000000002"))
    assert rows(isolated_db, "SELECT 1 FROM Produtos_cadastrados WHERE codigo_barras = ?", ("789000000002",)) == []
    assert rows(isolated_db, "SELECT 1 FROM estoque WHERE codigo_barras = ?", ("789000000002",)) == []
    assert rows(isolated_db, "SELECT 1 FROM movimentacoes WHERE codigo_barras = ?", ("789000000002",)) == []


def test_create_product_duplicate_barcode_adds_no_movement(isolated_db):
    """Rejects a duplicate barcode without adding a movement."""
    with pytest.raises(sqlite3.IntegrityError):
        create_product_module.create_product(USER_DRT, make_product(BARCODE))
    assert rows(isolated_db, "SELECT id FROM movimentacoes") == []


def test_price_update_rolls_back_when_reason_is_missing(isolated_db, monkeypatch):
    """Restores the original price when movement reason lookup fails."""
    monkeypatch.setattr(price_module, "REASON_PRICE_CHANGE", 999)
    with pytest.raises(ValueError, match="Motivo não encontrado"):
        price_module.update_product_price(BARCODE, 20.0, USER_DRT)
    assert rows(isolated_db, "SELECT valor_prod FROM Produtos_cadastrados WHERE codigo_barras = ?", (BARCODE,))[0]["valor_prod"] == 10.0


def test_stock_update_rolls_back_when_reason_is_missing(isolated_db):
    """Restores the original quantity when movement reason lookup fails."""
    with pytest.raises(ValueError, match="Motivo não encontrado"):
        stock_module.update_stock_quantity(BARCODE, 20, USER_DRT, 999)
    assert rows(isolated_db, "SELECT quantidade FROM estoque WHERE codigo_barras = ?", (BARCODE,))[0]["quantidade"] == 7


def test_delete_rolls_back_when_reason_is_missing(isolated_db):
    """Restores product status and quantity when movement reason lookup fails."""
    with pytest.raises(ValueError, match="Motivo não encontrado"):
        delete_product_module.delete_product(BARCODE, 999, USER_DRT)
    assert rows(isolated_db, "SELECT status FROM Produtos_cadastrados WHERE codigo_barras = ?", (BARCODE,))[0]["status"] == "ativo"
    assert rows(isolated_db, "SELECT quantidade FROM estoque WHERE codigo_barras = ?", (BARCODE,))[0]["quantidade"] == 7


def test_create_product_saves_product_stock_and_movement(isolated_db):
    """Persists a new product, its initial stock row, and its entry movement."""
    create_product_module.create_product(USER_DRT, make_product("789000000003"))
    assert len(rows(isolated_db, "SELECT 1 FROM Produtos_cadastrados WHERE codigo_barras = ?", ("789000000003",))) == 1
    assert len(rows(isolated_db, "SELECT 1 FROM estoque WHERE codigo_barras = ?", ("789000000003",))) == 1
    movement = rows(isolated_db, "SELECT status FROM movimentacoes WHERE codigo_barras = ?", ("789000000003",))
    assert len(movement) == 1 and movement[0]["status"] == "entrada"


def test_price_update_saves_new_price_and_movement(isolated_db):
    """Persists the new price and both price values in the movement."""
    price_module.update_product_price(BARCODE, 18.75, USER_DRT)
    assert rows(isolated_db, "SELECT valor_prod FROM Produtos_cadastrados WHERE codigo_barras = ?", (BARCODE,))[0]["valor_prod"] == 18.75
    movement = rows(isolated_db, "SELECT status, old_valor, new_valor FROM movimentacoes WHERE codigo_barras = ?", (BARCODE,))[0]
    assert (movement["status"], movement["old_valor"], movement["new_valor"]) == ("ajuste", 10.0, 18.75)


def test_stock_update_saves_quantity_and_adjustment(isolated_db):
    """Persists the new stock quantity and its adjustment movement."""
    stock_module.update_stock_quantity(BARCODE, 15, USER_DRT, 4)
    assert rows(isolated_db, "SELECT quantidade FROM estoque WHERE codigo_barras = ?", (BARCODE,))[0]["quantidade"] == 15
    movement = rows(isolated_db, "SELECT status, quantidade FROM movimentacoes WHERE codigo_barras = ?", (BARCODE,))[0]
    assert (movement["status"], movement["quantidade"]) == ("ajuste", 15)


def test_delete_saves_status_zero_stock_and_movement(isolated_db):
    """Persists logical deletion, zero stock, and a deletion movement."""
    delete_product_module.delete_product(BARCODE, 10, USER_DRT)
    assert rows(isolated_db, "SELECT status FROM Produtos_cadastrados WHERE codigo_barras = ?", (BARCODE,))[0]["status"] == "excluido"
    assert rows(isolated_db, "SELECT quantidade FROM estoque WHERE codigo_barras = ?", (BARCODE,))[0]["quantidade"] == 0
    movement = rows(isolated_db, "SELECT status FROM movimentacoes WHERE codigo_barras = ?", (BARCODE,))[0]
    assert movement["status"] == "exclusão"


@pytest.mark.parametrize("service", ["price", "delete", "sector"])
def test_services_reject_unknown_product_without_changes(isolated_db, service):
    """Rejects an unknown barcode in each product update or deletion service."""
    operation = {
        "price": lambda: price_module.update_product_price("missing", 20, USER_DRT),
        "delete": lambda: delete_product_module.delete_product("missing", 10, USER_DRT),
        "sector": lambda: sector_module.update_product_sector("missing", 1),
    }[service]
    with pytest.raises(ProductNotFoundError):
        operation()
    assert rows(isolated_db, "SELECT id FROM movimentacoes") == []


def test_delete_rejects_already_deleted_product(isolated_db):
    """Rejects a product that has already been logically deleted."""
    with sqlite3.connect(isolated_db) as conn:
        conn.execute("UPDATE Produtos_cadastrados SET status = 'excluido' WHERE codigo_barras = ?", (BARCODE,))
    with pytest.raises(ProductNotFoundError):
        delete_product_module.delete_product(BARCODE, 10, USER_DRT)
    assert rows(isolated_db, "SELECT quantidade FROM estoque WHERE codigo_barras = ?", (BARCODE,))[0]["quantidade"] == 7


def test_stock_update_rejects_product_without_stock_row(isolated_db):
    """Raises the stock-specific error when the product has no stock row."""
    with sqlite3.connect(isolated_db) as conn:
        conn.execute("DELETE FROM estoque WHERE codigo_barras = ?", (BARCODE,))
    with pytest.raises(StockNotFoundError):
        stock_module.update_stock_quantity(BARCODE, 2, USER_DRT, 4)
    assert rows(isolated_db, "SELECT id FROM movimentacoes") == []


@pytest.mark.parametrize("quantity", [-1, True, 1.5, "2"])
def test_stock_update_rejects_invalid_quantities(isolated_db, quantity):
    """Rejects negative, boolean, non-integer, and string quantities."""
    with pytest.raises(ValueError, match="quantidade inválida"):
        stock_module.update_stock_quantity(BARCODE, quantity, USER_DRT, 4)
    assert rows(isolated_db, "SELECT quantidade FROM estoque WHERE codigo_barras = ?", (BARCODE,))[0]["quantidade"] == 7
    assert rows(isolated_db, "SELECT id FROM movimentacoes") == []


def test_get_db_enables_foreign_keys(isolated_db):
    """Application connections should enable FK enforcement by default."""
    with database.get_db() as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_get_db_rejects_movement_for_unknown_product(isolated_db):
    """A movement cannot reference a product absent from the catalog."""
    with database.get_db() as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """INSERT INTO movimentacoes
                   (status, codigo_barras, motivo, usuario_drt)
                   VALUES ('ajuste', 'produto-inexistente', 'teste', ?)""",
                (USER_DRT,),
            )
