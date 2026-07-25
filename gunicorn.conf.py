"""Configuration Gunicorn pour Render (Postgres SSL)."""

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
# 1 worker sur plan free : plus stable avec Postgres SSL Render.
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
timeout = 120
accesslog = "-"
errorlog = "-"
capture_output = True


def post_fork(server, worker):
    """Apres fork : jeter le pool herite pour recreer des connexions SSL propres."""
    try:
        from extensions import db

        db.session.remove()
        db.engine.dispose()
    except Exception:
        # Au tout premier demarrage l'engine peut ne pas etre pret.
        pass
