"""Point d'entree WSGI pour PythonAnywhere.

Sur le dashboard PythonAnywhere : Web → WSGI configuration file
→ remplacer le contenu par un import de ce fichier, ou pointer vers lui.
"""

import os
import sys

# Dossier du projet sur PythonAnywhere (a adapter si besoin) :
# /home/<ton_user>/bbda_events
PROJET = os.path.dirname(os.path.abspath(__file__))
if PROJET not in sys.path:
    sys.path.insert(0, PROJET)

os.environ.setdefault("FLASK_ENV", "production")

from app import create_app

application = create_app("production")
