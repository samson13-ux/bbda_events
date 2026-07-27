"""Routes et generation des quittances.

`generer_quittance()` cree l'enregistrement `Quittance` en base a partir
du tarif + redevance fixes par l'agent, puis genere le fichier PDF via
`pdf_generator.generer_pdf_quittance()` et enregistre son chemin dans
`fichier_pdf_path`. Elle integre aussi les arrieres pre-existants de
l'organisateur (`droit_arriere`) via le moteur d'arrieres. Le
telechargement cote organisateur sert ce fichier avec `send_file`.

Sur Render le disque est ephemere : si le PDF a disparu apres un redeploy,
`assurer_fichier_pdf()` le regenere a la volee depuis les donnees en base.
"""

import os

from flask import abort, send_file
from flask_login import current_user

from backend.arrieres.moteur import integrer_arrieres_dans_quittance
from backend.auth.decorators import role_required
from extensions import db
from models import Declaration, Quittance

from . import exports_bp
from .pdf_generator import assurer_fichier_pdf, generer_pdf_quittance


def generer_quittance(declaration, agent):
    """Cree l'enregistrement Quittance d'une declaration soldee (RM-050 a
    RM-054) et genere son fichier PDF.

    `droit_annuel` porte le montant du de CETTE declaration (tarif +
    redevance) ; `droit_arriere` porte les arrieres PRE-EXISTANTS de
    l'organisateur (`integrer_arrieres_dans_quittance`) ; `droit_exigible`
    est la somme des deux, c'est-a-dire le montant total que l'organisateur
    doit regulariser au guichet du BBDA.

    Si une quittance existe deja pour cette declaration (nouvel essai apres
    un echec partiel), elle est reutilisee au lieu d'en creer une seconde
    (evite l'IntegrityError sur declaration_id NOT NULL / UNIQUE).
    """
    evaluation = declaration.evaluation
    dernier_paiement = declaration.paiements[-1] if declaration.paiements else None

    # Preferer declaration_id / agent_id (pas les objets relationship) pour
    # eviter que SQLAlchemy "detache" une ancienne quittance en mettant
    # declaration_id a NULL (interdit par la FK MySQL).
    existante = Quittance.query.filter_by(declaration_id=declaration.id).first()
    if existante is not None:
        quittance = existante
        quittance.agent_id = agent.id
        quittance.droit_annuel = evaluation.montant_total
        quittance.droit_arriere = 0
        quittance.droit_exigible = evaluation.montant_total
        quittance.droits_type = declaration.nature_manifestation
        quittance.droits_montant = evaluation.montant_total
        quittance.somme_totale_chiffres = evaluation.montant_total
        quittance.somme_totale_lettres = (
            dernier_paiement.montant_lettres if dernier_paiement else quittance.somme_totale_lettres
        )
    else:
        numero_quittance = f"{Quittance.query.count() + 1:07d}"
        quittance = Quittance(
            declaration_id=declaration.id,
            agent_id=agent.id,
            numero_quittance=numero_quittance,
            droit_annuel=evaluation.montant_total,
            droit_arriere=0,
            droit_exigible=evaluation.montant_total,
            droits_type=declaration.nature_manifestation,
            droits_montant=evaluation.montant_total,
            etiquettes_nombre=0,
            etiquettes_montant=0,
            penalites_montant=0,
            somme_totale_chiffres=evaluation.montant_total,
            somme_totale_lettres=dernier_paiement.montant_lettres if dernier_paiement else "",
        )
        db.session.add(quittance)

    db.session.flush()

    integrer_arrieres_dans_quittance(quittance)

    quittance.fichier_pdf_path = generer_pdf_quittance(quittance)
    return quittance


@exports_bp.route("/quittance/<int:declaration_id>")
@role_required("organisateur")
def quittance(declaration_id):
    """Telechargement de la quittance PDF d'une declaration (RM-050 a RM-054).

    Regenere le PDF si le fichier a disparu (disque ephemere Render).
    """
    declaration = Declaration.query.get_or_404(declaration_id)
    if declaration.organisateur_id != current_user.organisateur.id:
        abort(404)
    if declaration.quittance is None:
        abort(404)

    try:
        chemin = assurer_fichier_pdf(declaration.quittance)
        db.session.commit()
    except Exception:
        db.session.rollback()
        abort(404)

    if not chemin or not os.path.exists(chemin):
        abort(404)

    nom_telechargement = f"quittance_BBDA_{declaration.quittance.numero_quittance}.pdf"
    return send_file(chemin, as_attachment=True, download_name=nom_telechargement)
