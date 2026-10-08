"""Define a verificação de permissões administrativas baseada no usuário do token."""

from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.DATABASE import get_db


def admin_required(view_function):
    """Protege uma rota e permite sua execução apenas para usuários administradores."""

    @wraps(view_function)
    def wrapped(*args, **kwargs):
        """Valida o JWT e consulta o perfil atual do usuário antes de chamar a rota."""
        verify_jwt_in_request()
        drt = get_jwt_identity()

        with get_db() as conn:
            usuario = conn.execute(
                "SELECT tipo_user FROM users WHERE drt = ?",
                (drt,),
            ).fetchone()

        if usuario is None:
            return jsonify({"mensagem": "usuário do token não existe"}), 401
        tipo_usuario = (usuario["tipo_user"] or "").strip().lower()
        if tipo_usuario not in {"adm", "admin", "user_adm", "user_admin"}:
            return (
                jsonify(
                    {"mensagem": "usuario sem permicao "}
                ),
                403,
            )

        return view_function(*args, **kwargs)

    return wrapped
