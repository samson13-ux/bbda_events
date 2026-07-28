"""Notifications automatiques envoyees aux utilisateurs.

Flux :
1. Journalisation en base (`notification`, statut `en_attente`) — RM-100
2. Envoi :
   - SendGrid API HTTPS si `SENDGRID_API_KEY` (Render free)
   - sinon SMTP Gmail si `MAIL_USERNAME` + `MAIL_PASSWORD` (local)
3. Mise a jour du statut `envoyee` ou `echouee` — RM-101, RM-102

Configuration :
- Local : MAIL_USERNAME + MAIL_PASSWORD (SMTP Gmail)
- Render : SENDGRID_API_KEY + MAIL_USERNAME (= email Single Sender verifie)
"""

import base64
import json
import os
import socket
import urllib.error
import urllib.request

from flask import current_app, url_for
from flask_mail import Message

from extensions import db, mail
from models import Notification, Utilisateur

SMTP_TIMEOUT_SECONDES = 15
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"

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
    db.session.flush()
    return notification


def _gabarit_html(sujet, paragraphes):
    """Enveloppe le corps d'un email dans le gabarit HTML BBDA Events."""
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


def _expediteur():
    """Adresse From : MAIL_DEFAULT_SENDER, sinon MAIL_USERNAME."""
    return current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")


def _sendgrid_configure():
    return bool((current_app.config.get("SENDGRID_API_KEY") or "").strip())


def _smtp_configure():
    return bool(current_app.config.get("MAIL_USERNAME") and current_app.config.get("MAIL_PASSWORD"))


def _canal_actif():
    """'sendgrid', 'smtp' ou None."""
    if _sendgrid_configure():
        return "sendgrid"
    if _smtp_configure():
        return "smtp"
    return None


def _normaliser_pieces_jointes(pieces_jointes):
    """Liste de dicts {filename, content_type, data} (data = bytes)."""
    return list(pieces_jointes or [])


def _envoyer_via_sendgrid(notification, destinataire_email, corps_html, reply_to=None, pieces_jointes=None):
    """Envoi via API HTTPS SendGrid (Render free)."""
    expediteur = _expediteur()
    if not expediteur:
        raise RuntimeError(
            "MAIL_USERNAME manquant : mets l'email Single Sender vérifié chez SendGrid."
        )

    payload = {
        "personalizations": [{"to": [{"email": destinataire_email}]}],
        "from": {"email": expediteur, "name": "BBDA Events"},
        "subject": notification.sujet,
        "content": [{"type": "text/html", "value": corps_html}],
    }
    if reply_to:
        payload["reply_to"] = {"email": reply_to}

    pieces = _normaliser_pieces_jointes(pieces_jointes)
    if pieces:
        payload["attachments"] = [
            {
                "content": base64.b64encode(piece["data"]).decode("ascii"),
                "type": piece.get("content_type") or "application/octet-stream",
                "filename": piece["filename"],
                "disposition": "attachment",
            }
            for piece in pieces
        ]

    requete = urllib.request.Request(
        SENDGRID_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {current_app.config['SENDGRID_API_KEY'].strip()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(requete, timeout=30) as reponse:
            if reponse.status not in (200, 201, 202):
                corps = reponse.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"SendGrid HTTP {reponse.status}: {corps}")
    except urllib.error.HTTPError as erreur_http:
        detail = erreur_http.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"SendGrid HTTP {erreur_http.code}: {detail}") from erreur_http


def _envoyer_via_smtp(notification, destinataire_email, corps_html, reply_to=None, pieces_jointes=None):
    """Envoi SMTP Gmail via Flask-Mail (chemin local, inchange)."""
    if not _smtp_configure():
        raise RuntimeError(
            "SMTP non configure : definis MAIL_USERNAME et MAIL_PASSWORD "
            "(mot de passe d'application Gmail) dans .env."
        )
    timeout_avant = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(SMTP_TIMEOUT_SECONDES)
        message = Message(
            subject=notification.sujet,
            recipients=[destinataire_email],
            html=corps_html,
            sender=_expediteur(),
        )
        if reply_to:
            message.reply_to = reply_to
        for piece in _normaliser_pieces_jointes(pieces_jointes):
            message.attach(
                piece["filename"],
                piece.get("content_type") or "application/octet-stream",
                piece["data"],
            )
        mail.send(message)
    finally:
        socket.setdefaulttimeout(timeout_avant)


def _dispatch_envoi(notification, destinataire_email, corps_html, reply_to=None, pieces_jointes=None):
    """Choisit SendGrid (prioritaire) ou SMTP."""
    canal = _canal_actif()
    if canal == "sendgrid":
        _envoyer_via_sendgrid(
            notification,
            destinataire_email,
            corps_html,
            reply_to=reply_to,
            pieces_jointes=pieces_jointes,
        )
    elif canal == "smtp":
        _envoyer_via_smtp(
            notification,
            destinataire_email,
            corps_html,
            reply_to=reply_to,
            pieces_jointes=pieces_jointes,
        )
    else:
        raise RuntimeError(
            "Aucun canal email : definis SENDGRID_API_KEY + MAIL_USERNAME (Render) "
            "ou MAIL_USERNAME + MAIL_PASSWORD (SMTP local)."
        )
    return canal


def _envoyer(notification, destinataire_email, corps_html, reply_to=None, pieces_jointes=None):
    """Envoie l'email puis met a jour le statut (RM-101, RM-102)."""
    if current_app.config.get("MAIL_SUPPRESS_SEND"):
        notification.statut = "envoyee"
        return notification

    try:
        _dispatch_envoi(
            notification,
            destinataire_email,
            corps_html,
            reply_to=reply_to,
            pieces_jointes=pieces_jointes,
        )
        notification.statut = "envoyee"
    except Exception as erreur:  # noqa: BLE001
        notification.statut = "echouee"
        current_app.logger.error(
            "Echec d'envoi de l'email '%s' (notification #%s) : %s",
            notification.sujet,
            notification.id,
            erreur,
        )
    return notification


def _piece_jointe_pdf(chemin, nom_fichier):
    """Lit un PDF disque pour piece jointe email, ou None si absent."""
    if not chemin or not os.path.exists(chemin):
        return None
    with open(chemin, "rb") as fichier:
        return {
            "filename": nom_fichier,
            "content_type": "application/pdf",
            "data": fichier.read(),
        }


def _boite_dediee_et_admin():
    """Retourne (email_boite_dediee, admin) ou (None, None) si non configurable."""
    boite = _expediteur()
    admin = Utilisateur.query.filter_by(role="admin").order_by(Utilisateur.id.asc()).first()
    if not boite or admin is None:
        return None, None
    return boite, admin


def notifier_confirmation_declaration(declaration):
    """Confirme a l'organisateur la reception de sa declaration (RM-014)."""
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
    """Informe l'organisateur du montant a payer une fois fixe par l'agent (RM-033)."""
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
    """Informe l'organisateur que sa quittance est prete, avec le PDF en
    piece jointe et un lien vers l'espace (apres connexion) (RM-054)."""
    from backend.exports.pdf_generator import assurer_fichier_pdf

    utilisateur = declaration.organisateur.utilisateur
    quittance = declaration.quittance
    sujet = "BBDA Events : Votre quittance est disponible"
    try:
        lien_detail = _lien_externe("declarations.detail", declaration_id=declaration.id)
    except RuntimeError:
        lien_detail = "votre espace organisateur BBDA Events"
    try:
        lien_pdf = _lien_externe("exports.quittance", declaration_id=declaration.id)
    except RuntimeError:
        lien_pdf = lien_detail

    paragraphes = [
        f"Bonjour {declaration.prenom_demandeur} {declaration.nom_demandeur},",
        f"Votre paiement pour l'événement « {declaration.nom_artiste_evenement} » a bien été enregistré.",
        f"Votre quittance n° {quittance.numero_quittance} est jointe à cet email (PDF).",
        f"Vous pouvez aussi la télécharger depuis votre espace : "
        f"<a href='{lien_pdf}'>télécharger ma quittance</a> "
        f"(connectez-vous d'abord si besoin) ou ouvrir "
        f"<a href='{lien_detail}'>le détail de votre déclaration</a>.",
        "Cordialement,<br>Le Bureau Burkinabè du Droit d'Auteur.",
    ]
    message = (
        f"Bonjour {declaration.prenom_demandeur},\n\n"
        f"Votre paiement pour l'evenement « {declaration.nom_artiste_evenement} » a bien ete enregistre.\n"
        f"Votre quittance (n° {quittance.numero_quittance}) est jointe a cet email.\n\n"
        "Cordialement,\nLe Bureau Burkinabe du Droit d'Auteur."
    )
    notification = _enregistrer_notification(
        destinataire_id=utilisateur.id,
        type_notification="quittance_disponible",
        sujet=sujet,
        message=message,
    )

    pieces = []
    try:
        chemin = assurer_fichier_pdf(quittance)
        piece = _piece_jointe_pdf(
            chemin,
            f"quittance_BBDA_{quittance.numero_quittance}.pdf",
        )
        if piece:
            pieces.append(piece)
    except Exception as erreur:  # noqa: BLE001
        current_app.logger.error(
            "Impossible de joindre la quittance #%s : %s",
            quittance.id if quittance else "?",
            erreur,
        )

    return _envoyer(
        notification,
        utilisateur.email,
        _gabarit_html(sujet, paragraphes),
        pieces_jointes=pieces,
    )


def notifier_rappel_arriere(arriere):
    """Rappelle a l'organisateur qu'un arriere de paiement est en attente
    et qu'il bloque toute nouvelle declaration (RM-06x)."""
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
    """Alerte tous les agents/administrateurs quand un compte organisateur
    sous surveillance se reconnecte (RM-081)."""
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
    """Informe l'organisateur que son compte est bloque et l'empeche de
    soumettre une nouvelle declaration (RM-010, RM-074)."""
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
    publique BBDA Events (apres delivrance de la quittance)."""
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


def notifier_reinitialisation_mot_de_passe(utilisateur, lien_reset):
    """Envoie le lien de reinitialisation de mot de passe (Partie 3)."""
    sujet = "BBDA Events : Réinitialisation de votre mot de passe"
    paragraphes = [
        f"Bonjour {utilisateur.prenom},",
        "Une demande de réinitialisation de mot de passe a été faite pour votre compte BBDA Events.",
        f'<a href="{lien_reset}" style="color:{COULEUR_BBDA};">Cliquez ici pour choisir un nouveau mot de passe</a>',
        "Ce lien expire dans une heure. Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.",
    ]
    texte = (
        f"Réinitialisation de mot de passe\n\n"
        f"Bonjour {utilisateur.prenom},\n"
        f"Ouvrez ce lien (valable 1 h) : {lien_reset}\n"
    )
    notification = _enregistrer_notification(
        destinataire_id=utilisateur.id,
        type_notification="reset_mot_de_passe",
        sujet=sujet,
        message=texte,
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
