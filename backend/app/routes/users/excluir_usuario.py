"""Exclui usuários sem movimentações associadas, preservando o histórico."""

import sqlite3

from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from app import limiter
from app.DATABASE import get_db
from app.routes.users import users_bp
from app.security.authorization import admin_required


@users_bp.route("/usuarios/<string:drt>", methods=["DELETE"])
@limiter.limit("30 per minute")
@admin_required
def excluir_usuario(drt):
    """Exclui um usuário sem histórico e impede autoexclusão administrativa."""
    drt_logado = get_jwt_identity()
    if drt == drt_logado:
        return jsonify({"mensagem": "não é permitido excluir o próprio usuário"}), 409

    try:
        with get_db() as conn:
            usuario = conn.execute(
                "SELECT drt FROM users WHERE drt = ?",
                (drt,),
            ).fetchone()
            if usuario is None:
                return jsonify({"mensagem": "usuário não encontrado"}), 404

            possui_movimentacoes = conn.execute(
                "SELECT 1 FROM movimentacoes WHERE usuario_drt = ? LIMIT 1",
                (drt,),
            ).fetchone()
            if possui_movimentacoes is not None:
                return jsonify({
                    "mensagem": (
                        "usuário possui movimentações no histórico e não pode ser excluído"
                    )
                }), 409

            conn.execute("DELETE FROM users WHERE drt = ?", (drt,))

        return jsonify({"mensagem": "usuário excluído com sucesso"}), 200
    except sqlite3.Error:
        return jsonify({"mensagem": "erro ao excluir usuário"}), 500
