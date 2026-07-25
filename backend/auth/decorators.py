"""Decorateurs de controle d'acces par role, utilises par tous les blueprints
proteges (declarations, agent, admin) — cf. docs/ARCHITECTURE.md §6 et
docs/REGLES_METIER.md RM-002 a RM-005."""

from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def role_required(*roles):
    """Restreint une route aux utilisateurs connectes ayant un des roles donnes.

    Renvoie 401 (via Flask-Login) si l'utilisateur n'est pas connecte, ou 403
    si son role ne fait pas partie de `roles` (RM-005 : un organisateur ne
    peut pas acceder aux routes /agent/ ou /admin/, et reciproquement).

    :param roles: roles autorises, ex. role_required("agent", "admin")
    """

    def decorateur(vue):
        @wraps(vue)
        @login_required
        def vue_protegee(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return vue(*args, **kwargs)

        return vue_protegee

    return decorateur
