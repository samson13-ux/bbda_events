"""Blueprint des declarations (formulaire et suivi cote organisateur)."""

from flask import Blueprint

declarations_bp = Blueprint("declarations", __name__, url_prefix="/declarations")

from . import routes  # noqa: E402,F401
