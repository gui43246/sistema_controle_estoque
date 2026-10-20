"""Run the Flask development server or the production WSGI server."""

import os

from app import app


DEBUG_TRUE_VALUES = {"1", "true", "yes", "on"}


def resolve_debug_mode(environment, debug_value):
    """Return whether debug is enabled and forbid it in production."""
    debug_enabled = (debug_value or "").strip().casefold() in DEBUG_TRUE_VALUES
    if environment.strip().casefold() == "production" and debug_enabled:
        raise RuntimeError("FLASK_DEBUG não pode ser habilitado em produção")
    return debug_enabled


def main():
    environment = os.getenv("FLASK_ENV", "development")
    debug_enabled = resolve_debug_mode(environment, os.getenv("FLASK_DEBUG", "0"))
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))

    if environment.strip().casefold() == "production":
        from waitress import serve

        serve(app, host=os.getenv("HOST", "0.0.0.0"), port=port)
        return

    app.run(host=host, port=port, debug=debug_enabled)


if __name__ == "__main__":
    main()
