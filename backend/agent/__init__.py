"""Blueprint agent (traitement des declarations, paiements, arrieres)."""

from flask import Blueprint

agent_bp = Blueprint("agent", __name__, url_prefix="/agent")

from . import routes  # noqa: E402,F401
