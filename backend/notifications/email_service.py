"""Notifications automatiques envoyees aux utilisateurs (Prompt 13).

Chaque notification est d'abord journalisee en base (table `notification`,
statut `en_attente`) AVANT toute tentative d'envoi, puis son statut est mis a
jour a `envoyee` ou `echouee` APRES la tentative d'envoi SMTP reel via
Flask-Mail. Toute exception d'envoi est interceptee et journalisee : elle ne
doit jamais faire planter l'application (RM-101, RM-102).
"""

import socket

from flask import current_app, url_for
from flask_mail import Message

from extensions import db, mail
from models import Notification, Utilisateur

# Sur Render, SMTP Gmail peut rester bloque longtemps : on coupe apres 10 s
# pour ne pas faire tomber le formulaire (timeout worker / erreur 500).
SMTP_TIMEOUT_SECONDES = 10

COULEUR_BBDA = "#1F4E79"
ADRESSE_BBDA = "01 BP 3926 Ouagadougou 01 : Tél. 25 32 47 50"


def _lien_externe(endpoint, **valeurs):
    """Construit une URL absolue pour les emails.

    Priorite a PUBLIC_BASE_URL (tunnel / hebergement) pour eviter les liens
    en 127.0.0.1 inutilisables hors de la machine de developpement.
    """
    base = (current_app.config.get("PUBLIC_BASE_URL") or "").rstrip("/")
    chemin = url_for(endpoint, **valeurs)
    if base:
        return f"{base}{chemin}"
    try:
        return url_for(endpoint, _external=True, **valeurs)
    except RuntimeError:
        return chemin


def _enregistrer_notification(destinataire_id, type_notification, sujet, message):
    """Cree et journalise une notification en base, sans l'envoyer (RM-100)."""
    notification = Notification(
        destinataire_id=destinataire_id,
        type_notification=type_notification,
        sujet=sujet,
        message=message,
        canal="email",
        statut="en_attente",
    )
    db.session.add(notification)
    db.session.flush()  # obtenir notification.id pour les logs eventuels
    return notification


def _gabarit_html(sujet, paragraphes):
    """Enveloppe le corps d'un email (liste de paragraphes en texte simple)
    dans un gabarit HTML avec en-tete BBDA Events et pied de page."""
    corps = "".join(f"<p style='margin:0 0 12px 0;'>{p}</p>" for p in paragraphes)
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background-color: {COULEUR_BBDA}; color: #ffffff; padding: 20px; text-align: center;">
        <h1 style="margin: 0; font-size: 20px;">BBDA Events</h1>
        <p style="margin: 4px 0 0 0; font-size: 13px;">Bureau Burkinabè du Droit d'Auteur</p>
      </div>
      <div style="padding: 20px; color: #222222; font-size: 14px; line-height: 1.5;">
        {corps}
      </div>
      <div style="background-color: #f2f2f2; color: #666666; padding: 14px 20px; font-size: 12px; text-align: center;">
        {ADRESSE_BBDA}<br>Cet email est envoyé automatiquement, merci de ne pas y répondre directement.
      </div>
    </div>
    """


def _envoyer(notification, destinataire_email, corps_html, reply_to=None):
    """Tente l'envoi SMTP reel d'une notification deja journalisee, puis met a
    jour son statut selon le resultat (RM-101, RM-102)."""
    timeout_avant = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(SMTP_TIMEOUT_SECONDES)
        message = Message(subject=notification.sujet, recipients=[destinataire_email], html=corps_html)
        if reply_to:
            message.reply_to = reply_to
        mail.send(message)
        notification.statut = "envoyee"
    except Exception as erreur:  # noqa: BLE001 — un echec d'envoi ne doit jamais planter l'appli
        notification.statut = "echouee"
        current_app.logger.error(
            "Echec d'envoi de l'email '%s' (notification #%s) : %s",
            notification.sujet,
            notification.id,
            erreur,
        )
    finally:
        socket.setdefaulttimeout(timeout_avant)
    return notification


def _boite_dediee_et_admin():
    """Retourne (email_boite_dediee, admin) ou (None, None) si non configurable."""
    boite = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")
    admin = Utilisateur.query.filter_by(role="admin").order_by(Utilisateur.id.asc()).first()
    if not boite or admin is None:
        return None, None
    return boite, admin


def notifier_confirmation_declaration(declaration):
    """FONCTION 1 (RM-014) : confirme a l'organisateur la reception de sa
    declaration."""
    utilisateur = declaration.organisateur.utilisateur
    sujet = f"BBDA Events : Déclaration #{declaration.id} reçue avec succès"
    paragraphes = [
        f"Bonjour {declaration.prenom_demandeur} {declaration.nom_demandeur},",
        f"Votre déclaration pour l'événement « {declaration.nom_artiste_evenement} » "
        f"({declaration.nature_manifestation}, le {declaration.date_evenement.strftime('%d/%m/%Y')} "
        f"à {declaration.nom_salle}) a bien été reçue par le BBDA.",
        "Elle sera examinée par un agent dans un délai de 72 heures. Vous serez informé par email "
        "dès que le montant de votre redevance sera fixé.",
        f"Coordonnées du BBDA : {ADRESSE_BBDA}",
        "Cordialement,<br>Le Bureau Burkinabè du Droit d'Auteur.",
    ]
    message = (
        f"Bonjour {declaration.prenom_demandeur},\n\n"
        f"Votre declaration pour l'evenement « {declaration.nom_artiste_evenement} » "
        "a bien ete recue par le BBDA. Elle sera examinee par un agent dans les "
        "prochains jours et vous serez informe du montant a payer.\n\n"
        "Cordialement,\nLe Bureau Burkinabe du Droit d'Auteur."
    )
    notification = _enregistrer_notification(
        destinataire_id=utilisateur.id,
        type_notification="confirmation_declaration",
        sujet=sujet,
        message=message,
    )
    return _envoyer(notification, utilisateur.email, _gabarit_html(sujet, paragraphes))


def notifier_nouvelle_declaration_bbda(declaration):
    """Informe la boite mail dediee (admin) qu'une nouvelle declaration
    vient d'etre soumise et attend un traitement agent."""
    boite, admin = _boite_dediee_et_admin()
    if not boite:
        current_app.logger.warning(
            "Boite dediee ou admin absent : alerte nouvelle declaration #%s non envoyee.",
            declaration.id,
        )
        return None

    try:
        lien = _lien_externe("agent.traiter_declaration", declaration_id=declaration.id)
    except Exception:
        lien = f"/agent/declarations/{declaration.id}"

    organisateur = declaration.organisateur.utilisateur
    sujet = f"BBDA Events : Nouvelle déclaration #{declaration.id} à traiter"
    paragraphes = [
        "Une nouvelle déclaration d'événement a été soumise et attend un traitement.",
        f"<strong>Déclaration :</strong> #{declaration.id} - {declaration.nature_manifestation}",
        f"<strong>Événement :</strong> {declaration.nom_artiste_evenement}",
        f"<strong>Date :</strong> {declaration.date_evenement.strftime('%d/%m/%Y à %Hh%M')}",
        f"<strong>Lieu :</strong> {declaration.nom_salle}, {declaration.ville}",
        f"<strong>Organisateur :</strong> {organisateur.prenom} {organisateur.nom} ({declaration.email})",
        f'<a href="{lien}">Ouvrir le dossier dans l\'espace agent</a>',
    ]
    texte = (
        f"Nouvelle declaration #{declaration.id}\n"
        f"Evenement : {declaration.nom_artiste_evenement}\n"
        f"Organisateur : {organisateur.prenom} {organisateur.nom} ({declaration.email})\n"
        f"Lien : {lien}\n"
    )
    notification = _enregistrer_notification(
        destinataire_id=admin.id,
        type_notification="nouvelle_declaration",
        sujet=sujet,
        message=texte,
    )
    return _envoyer(notification, boite, _gabarit_html(sujet, paragraphes))


def notifier_montant_fixe(declaration):
    """FONCTION 2 (RM-033) : informe l'organisateur du montant a payer une
    fois fixe par l'agent."""
    utilisateur = declaration.organisateur.utilisateur
    evaluation = declaration.evaluation
    sujet = "BBDA Events : Montant de votre redevance fixé"
    paragraphes = [
        f"Bonjour {declaration.prenom_demandeur} {declaration.nom_demandeur},",
        f"Le montant de la redevance pour votre événement « {declaration.nom_artiste_evenement} » a été fixé par nos services :",
        f"Tarif : {evaluation.tarif:,.0f} FCFA<br>Redevance : {evaluation.redevance:,.0f} FCFA<br>"
        f"<strong>Total à payer : {evaluation.montant_total:,.0f} FCFA</strong>".replace(",", " "),
        f"Merci de vous présenter au bureau du BBDA pour effectuer votre paiement. {ADRESSE_BBDA}",
        "Cordialement,<br>Le Bureau Burkinabè du Droit d'Auteur.",
    ]
    message = (
        f"Bonjour {declaration.prenom_demandeur},\n\n"
        f"Le montant a payer pour votre evenement « {declaration.nom_artiste_evenement} » a ete fixe :\n"
        f"Tarif : {evaluation.tarif:.0f} FCFA\nRedevance : {evaluation.redevance:.0f} FCFA\n"
        f"Total : {evaluation.montant_total:.0f} FCFA\n\n"
        f"Presentez-vous au bureau du BBDA ({ADRESSE_BBDA}) pour effectuer "
        "votre paiement.\n\nCordialement,\nLe Bureau Burkinabe du Droit d'Auteur."
    )
    notification = _enregistrer_notification(
        destinataire_id=utilisateur.id,
        type_notification="montant_fixe",
        sujet=sujet,
        message=message,
    )
    return _envoyer(notification, utilisateur.email, _gabarit_html(sujet, paragraphes))


def notifier_quittance_disponible(declaration):
    """FONCTION 3 (RM-054) : informe l'organisateur que sa quittance est
    prete a etre telechargee depuis son espace."""
    utilisateur = declaration.organisateur.utilisateur
    quittance = declaration.quittance
    sujet = "BBDA Events : Votre quittance est disponible"
    try:
        lien = _lien_externe("exports.quittance", declaration_id=declaration.id)
    except RuntimeError:
        lien = "votre espace organisateur BBDA Events"
    paragraphes = [
        f"Bonjour {declaration.prenom_demandeur} {declaration.nom_demandeur},",
        f"Votre paiement pour l'événement « {declaration.nom_artiste_evenement} » a bien été enregistré.",
        f"Votre quittance n° {quittance.numero_quittance} est désormais disponible au téléchargement : "
        f"<a href='{lien}'>télécharger ma quittance</a>.",
        "Cordialement,<br>Le Bureau Burkinabè du Droit d'Auteur.",
    ]
    message = (
        f"Bonjour {declaration.prenom_demandeur},\n\n"
        f"Votre paiement pour l'evenement « {declaration.nom_artiste_evenement} » a bien ete enregistre.\n"
        f"Votre quittance (n° {quittance.numero_quittance}) est desormais disponible au telechargement "
        "depuis votre espace organisateur.\n\nCordialement,\nLe Bureau Burkinabe du Droit d'Auteur."
    )
    notification = _enregistrer_notification(
        destinataire_id=utilisateur.id,
        type_notification="quittance_disponible",
        sujet=sujet,
        message=message,
    )
    return _envoyer(notification, utilisateur.email, _gabarit_html(sujet, paragraphes))


def notifier_rappel_arriere(arriere):
    """FONCTION 4 (RM-06x) : rappelle a l'organisateur qu'un arriere de
    paiement est en attente et qu'il bloque toute nouvelle declaration."""
    utilisateur = arriere.organisateur.utilisateur
    sujet = "BBDA Events : Rappel d'arriéré de paiement en attente"
    paragraphes = [
        f"Bonjour {utilisateur.prenom} {utilisateur.nom},",
        f"Un arriéré de <strong>{arriere.montant_du:,.0f} FCFA</strong>".replace(",", " ")
        + f" reste dû sur votre compte, avec une échéance dépassée depuis le {arriere.date_echeance.strftime('%d/%m/%Y')}.",
        "Tant que cet arriéré n'est pas régularisé, vous ne pouvez pas soumettre de nouvelle déclaration d'événement.",
        f"Merci de vous présenter au bureau du BBDA pour régulariser votre situation. {ADRESSE_BBDA}",
        "Cordialement,<br>Le Bureau Burkinabè du Droit d'Auteur.",
    ]
    message = (
        f"Bonjour {utilisateur.prenom},\n\n"
        f"Un arriere de {arriere.montant_du:.0f} FCFA reste du sur votre compte "
        f"(echeance depassee depuis le {arriere.date_echeance.strftime('%d/%m/%Y')}).\n"
        "Tant que cet arriere n'est pas regularise, toute nouvelle declaration sera bloquee.\n\n"
        f"Merci de vous presenter au bureau du BBDA ({ADRESSE_BBDA}) pour regulariser.\n\n"
        "Cordialement,\nLe Bureau Burkinabe du Droit d'Auteur."
    )
    notification = _enregistrer_notification(
        destinataire_id=utilisateur.id,
        type_notification="rappel_arriere",
        sujet=sujet,
        message=message,
    )
    return _envoyer(notification, utilisateur.email, _gabarit_html(sujet, paragraphes))


def notifier_alerte_surveillance(organisateur):
    """FONCTION 5 (RM-081) : alerte tous les agents/administrateurs quand un
    compte organisateur sous surveillance se reconnecte."""
    from datetime import datetime

    utilisateur_organisateur = organisateur.utilisateur
    horodatage = datetime.utcnow().strftime("%d/%m/%Y à %H:%M")
    sujet = "⚠ BBDA Events : ALERTE - Compte sous surveillance reconnecté"
    paragraphes = [
        "Bonjour,",
        f"Le compte organisateur <strong>{utilisateur_organisateur.prenom} {utilisateur_organisateur.nom}</strong> "
        f"(sous surveillance) vient de se reconnecter le {horodatage}.",
        "Merci de consulter en urgence le tableau de bord agent (rubrique « Comptes sous surveillance ») "
        "pour évaluer la situation.",
        "Cordialement,<br>BBDA Events.",
    ]
    message = (
        f"Le compte organisateur {utilisateur_organisateur.prenom} {utilisateur_organisateur.nom} "
        f"(sous surveillance) s'est reconnecte le {horodatage}.\n"
        "Merci de consulter le tableau de bord agent."
    )

    destinataires = Utilisateur.query.filter(Utilisateur.role.in_(["agent", "admin"]), Utilisateur.statut == "actif").all()
    notifications = []
    for agent in destinataires:
        notification = _enregistrer_notification(
            destinataire_id=agent.id,
            type_notification="alerte_surveillance",
            sujet=sujet,
            message=message,
        )
        notifications.append(_envoyer(notification, agent.email, _gabarit_html(sujet, paragraphes)))
    return notifications


def notifier_declaration_bloquee(organisateur):
    """FONCTION 6 : informe l'organisateur que son compte est bloque et
    l'empeche de soumettre une nouvelle declaration (RM-010, RM-074)."""
    utilisateur = organisateur.utilisateur
    total_du = sum(a.montant_du for a in organisateur.arrieres if a.statut == "en_attente")
    sujet = "BBDA Events : Déclaration bloquée"
    paragraphes = [
        f"Bonjour {utilisateur.prenom} {utilisateur.nom},",
        "Votre tentative de déclaration d'un nouvel événement a été bloquée car votre compte présente "
        f"un arriéré de <strong>{total_du:,.0f} FCFA</strong>".replace(",", " ") + ".",
        "Tant que cet arriéré n'est pas régularisé, vous ne pouvez pas soumettre de nouvelle déclaration.",
        f"Merci de vous présenter au bureau du BBDA pour régulariser votre situation. {ADRESSE_BBDA}",
        "Cordialement,<br>Le Bureau Burkinabè du Droit d'Auteur.",
    ]
    message = (
        f"Bonjour {utilisateur.prenom},\n\n"
        f"Votre tentative de declaration a ete bloquee car votre compte presente un arriere de {total_du:.0f} FCFA.\n"
        "Tant que cet arriere n'est pas regularise, toute nouvelle declaration sera bloquee.\n\n"
        f"Merci de vous presenter au bureau du BBDA ({ADRESSE_BBDA}) pour regulariser.\n\n"
        "Cordialement,\nLe Bureau Burkinabe du Droit d'Auteur."
    )
    notification = _enregistrer_notification(
        destinataire_id=utilisateur.id,
        type_notification="declaration_bloquee",
        sujet=sujet,
        message=message,
    )
    return _envoyer(notification, utilisateur.email, _gabarit_html(sujet, paragraphes))


def notifier_evenement_publie(declaration):
    """Informe l'organisateur que son evenement est visible sur la page
    publique BBDA Events (apres delivrance de la quittance, Prompt 19)."""
    utilisateur = declaration.organisateur.utilisateur
    sujet = f"BBDA Events : Votre événement est en ligne : {declaration.nom_artiste_evenement}"
    try:
        url_publique = _lien_externe("public.detail_evenement", declaration_id=declaration.id)
    except RuntimeError:
        url_publique = f"/evenements/{declaration.id}"

    paragraphes = [
        f"Bonjour {utilisateur.prenom} {utilisateur.nom},",
        f"Bonne nouvelle ! Votre événement <strong>{declaration.nom_artiste_evenement}</strong> "
        "est maintenant visible sur la page publique BBDA Events.",
        f'<a href="{url_publique}">Voir la page de votre événement</a>',
        "Les internautes peuvent désormais consulter les informations de votre événement "
        "et être informés de sa tenue.",
        "Cordialement,<br>Le Bureau Burkinabè du Droit d'Auteur.",
    ]
    message = (
        f"Bonjour {utilisateur.prenom},\n\n"
        f"Votre evenement {declaration.nom_artiste_evenement} est maintenant visible "
        f"sur la page publique BBDA Events : {url_publique}\n\n"
        "Cordialement,\nLe Bureau Burkinabe du Droit d'Auteur."
    )
    notification = _enregistrer_notification(
        destinataire_id=utilisateur.id,
        type_notification="evenement_publie",
        sujet=sujet,
        message=message,
    )
    return _envoyer(notification, utilisateur.email, _gabarit_html(sujet, paragraphes))


def notifier_message_contact(message_contact):
    """Transmet un message du formulaire Contact a la boite mail dediee
    de l'application (MAIL_DEFAULT_SENDER / MAIL_USERNAME), afin que le
    BBDA puisse traiter la preoccupation de l'utilisateur."""
    boite, admin = _boite_dediee_et_admin()
    if not boite:
        current_app.logger.warning(
            "MAIL_USERNAME ou admin absent : message contact #%s non envoye.", message_contact.id
        )
        return None

    sujet = f"BBDA Events : Contact - {message_contact.sujet}"
    paragraphes = [
        "Un nouveau message a été envoyé via le formulaire de contact public.",
        f"<strong>De :</strong> {message_contact.nom} ({message_contact.email})",
        f"<strong>Sujet :</strong> {message_contact.sujet}",
        f"<strong>Message :</strong><br>{message_contact.message.replace(chr(10), '<br>')}",
        "Vous pouvez répondre directement à cet email (réponse adressée à l'expéditeur), "
        "ou traiter le message depuis l'espace administrateur.",
    ]
    texte = (
        f"Nouveau message de contact\n\n"
        f"De : {message_contact.nom} ({message_contact.email})\n"
        f"Sujet : {message_contact.sujet}\n\n"
        f"{message_contact.message}\n"
    )
    notification = _enregistrer_notification(
        destinataire_id=admin.id,
        type_notification="message_contact",
        sujet=sujet,
        message=texte,
    )
    return _envoyer(
        notification,
        boite,
        _gabarit_html(sujet, paragraphes),
        reply_to=message_contact.email,
    )
