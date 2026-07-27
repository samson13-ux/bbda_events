"""Generation du PDF de la quittance BBDA (Prompt 12, RM-050 a RM-054).

Reproduit la structure du formulaire papier physique du BBDA (en-tete
3 colonnes, corps avec champs a lignes de points, tableau des droits et
mode de paiement, pied avec somme en lettres et signature de l'agent),
a partir des donnees deja enregistrees en base par `generer_quittance()`
(backend/exports/routes.py, Prompt 11).
"""

import os

from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

CHEMIN_LOGO = os.path.join("frontend", "static", "img", "bbda_logo.jpg")

LARGEUR_PAGE_MM, HAUTEUR_PAGE_MM = A4[0] / mm, A4[1] / mm
MARGE = 15


def _y(depuis_haut):
    """Convertit une position 'depuis le haut de la page' (en mm) en
    coordonnee ReportLab (origine en bas a gauche, en points)."""
    return (HAUTEUR_PAGE_MM - depuis_haut) * mm


def _x(depuis_gauche):
    """Convertit une position horizontale en mm en points."""
    return depuis_gauche * mm


def _ligne_pointillee(c, x_debut, x_fin, depuis_haut):
    c.saveState()
    c.setDash(1, 2)
    c.setLineWidth(0.5)
    c.line(_x(x_debut), _y(depuis_haut), _x(x_fin), _y(depuis_haut))
    c.restoreState()


def _champ(c, label, valeur, depuis_haut, x_label=MARGE, x_valeur_debut=70, x_fin=125):
    """Une ligne de formulaire : 'Label :' suivi d'une ligne de points et
    de la valeur ecrite juste au-dessus."""
    c.setFont("Helvetica", 9)
    c.drawString(_x(x_label), _y(depuis_haut), label)
    _ligne_pointillee(c, x_valeur_debut, x_fin, depuis_haut)
    if valeur:
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(_x(x_valeur_debut) + 2, _y(depuis_haut) + 2, str(valeur))


def _case(c, depuis_gauche, depuis_haut_baseline, cochee, taille=3.2):
    """Case a cocher carree, alignee sur la ligne de base d'un texte voisin
    (son bord bas touche la ligne de base, comme la lettre qui la
    precede), avec un X si `cochee` est vrai."""
    x = _x(depuis_gauche)
    y_bas = _y(depuis_haut_baseline)
    cote = taille * mm
    c.rect(x, y_bas, cote, cote)
    if cochee:
        c.line(x, y_bas, x + cote, y_bas + cote)
        c.line(x, y_bas + cote, x + cote, y_bas)


def _fmt(montant):
    """Formate un montant avec des espaces comme separateurs de milliers
    (convention francaise), ex: 25000 -> '25 000'."""
    return f"{montant:,.0f}".replace(",", " ")


def _en_tete(c, quittance):
    """EN-TETE 3 colonnes : coordonnees BBDA, logo, encadre 'QUITTANCE'."""
    c.setFont("Helvetica-Bold", 10)
    c.drawString(_x(MARGE), _y(15), "BUREAU BURKINABÈ")
    c.drawString(_x(MARGE), _y(20), "DU DROIT D'AUTEUR")
    c.setFont("Helvetica", 7.5)
    c.drawString(_x(MARGE), _y(27), "01 B.P. 3926 Ouagadougou 01")
    c.drawString(_x(MARGE), _y(32), "Tél : (+226) 25 32 47 50 / 25 30 22 23")
    c.drawString(_x(MARGE), _y(37), "Fax : +226 25 30 06 82")

    if os.path.exists(CHEMIN_LOGO):
        largeur_logo, hauteur_logo = 46, 33
        x_logo = LARGEUR_PAGE_MM / 2 - largeur_logo / 2
        c.drawImage(
            CHEMIN_LOGO,
            _x(x_logo),
            _y(42),
            width=largeur_logo * mm,
            height=hauteur_logo * mm,
            preserveAspectRatio=True,
            mask="auto",
        )

    largeur_encadre, hauteur_encadre = 48, 26
    x_encadre = LARGEUR_PAGE_MM - MARGE - largeur_encadre
    c.setLineWidth(0.8)
    c.rect(_x(x_encadre), _y(13 + hauteur_encadre), largeur_encadre * mm, hauteur_encadre * mm)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(_x(x_encadre + largeur_encadre / 2), _y(19), "QUITTANCE N° 1")
    c.setFont("Helvetica", 9)
    c.drawCentredString(_x(x_encadre + largeur_encadre / 2), _y(25), "OUAGADOUGOU")
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(_x(x_encadre + largeur_encadre / 2), _y(34), f"N° {quittance.numero_quittance}")


def _corps(c, quittance, declaration):
    """Champs 'Delivree a', adresse, telephone... avec lignes de points."""
    depuis_haut = 55
    c.setFont("Helvetica", 9)

    _champ(c, "Délivrée à M/Mme :", f"{declaration.prenom_demandeur} {declaration.nom_demandeur}", depuis_haut)
    depuis_haut += 7
    _champ(c, "Adresse/Secteur :", f"{declaration.adresse}, {declaration.ville}", depuis_haut)
    depuis_haut += 7
    _champ(c, "Téléphone :", declaration.telephone, depuis_haut)
    depuis_haut += 7
    _champ(c, "Etablissement :", f"{declaration.nature_manifestation} - {declaration.nom_artiste_evenement}", depuis_haut)
    depuis_haut += 7
    _champ(c, "N° : Contrat / Autorisation :", "", depuis_haut)
    depuis_haut += 7
    _champ(c, "Période Exercice :", declaration.date_evenement.year, depuis_haut)
    depuis_haut += 7

    c.setFont("Helvetica-Bold", 9)
    c.drawString(_x(MARGE), _y(depuis_haut), "Objet : REDEVANCE DE DROIT D'AUTEUR")
    depuis_haut += 8

    _champ(c, "Droit Annuel :", f"{_fmt(quittance.droit_annuel)} F" if quittance.droit_annuel else "", depuis_haut)
    depuis_haut += 7
    _champ(c, "Droit Arriéré :", f"{_fmt(quittance.droit_arriere)} F" if quittance.droit_arriere else "", depuis_haut)
    depuis_haut += 7
    _champ(c, "Droit Exigible :", f"{_fmt(quittance.droit_exigible)} F", depuis_haut)
    depuis_haut += 10
    return depuis_haut


def _tableau(c, quittance, paiement, depuis_haut):
    """Tableau des droits/etiquettes/penalites + mode et type de paiement.

    Les 3 premieres lignes ont 3 colonnes (libelle, valeur 1, valeur 2) ;
    la derniere ligne (Intégral/Partiel/Reste à payer) est fusionnee sur
    toute la largeur des colonnes de valeurs, faute de place pour 3
    colonnes distinctes sur cette ligne precise."""
    x_debut, x_fin = MARGE, LARGEUR_PAGE_MM - MARGE
    x_col1, x_col2 = 115, 160
    hauteur_ligne = 8
    lignes = 6
    hauteur_totale = hauteur_ligne * lignes

    c.setLineWidth(0.8)
    c.rect(_x(x_debut), _y(depuis_haut + hauteur_totale), _x(x_fin) - _x(x_debut), hauteur_totale * mm)
    for i in range(1, lignes):
        y = depuis_haut + i * hauteur_ligne
        c.line(_x(x_debut), _y(y), _x(x_fin), _y(y))
    # Les colonnes de valeurs ne sont separees que sur les 3 premieres lignes
    # (Droits / Etiquettes / Penalites) ; la ligne "mode de paiement" a
    # besoin de toute la largeur.
    for x in (x_col1, x_col2):
        c.line(_x(x), _y(depuis_haut), _x(x), _y(depuis_haut + 3 * hauteur_ligne))

    c.setFont("Helvetica", 8)

    def texte_ligne(numero, libelle, val_col1, val_col2):
        y_texte = depuis_haut + numero * hauteur_ligne - 3
        c.drawString(_x(x_debut + 2), _y(y_texte), libelle)
        c.drawString(_x(x_col1 + 2), _y(y_texte), str(val_col1) if val_col1 not in (None, "") else "")
        c.drawString(_x(x_col2 + 2), _y(y_texte), str(val_col2) if val_col2 not in (None, "") else "")

    texte_ligne(
        1,
        "Droits : type (1) montant (2)",
        quittance.droits_type or "",
        _fmt(quittance.droits_montant) if quittance.droits_montant else "",
    )
    texte_ligne(
        2,
        "Etiquettes : nombre (1) montant (2)",
        quittance.etiquettes_nombre or "",
        _fmt(quittance.etiquettes_montant) if quittance.etiquettes_montant else "",
    )
    texte_ligne(
        3,
        "Pénalités : types (1) montant (2)",
        quittance.penalites_type or "",
        _fmt(quittance.penalites_montant) if quittance.penalites_montant else "",
    )

    mode = paiement.mode_paiement if paiement else None
    type_paiement = paiement.type_paiement if paiement else None

    y4 = depuis_haut + 4 * hauteur_ligne - 3
    c.drawString(_x(x_debut + 2), _y(y4), "Mode de paiement")
    c.drawString(_x(x_col1 + 8), _y(y4), "Espèces")
    _case(c, x_col1 + 30, y4 - 2.2, mode == "especes")

    y5 = depuis_haut + 5 * hauteur_ligne - 3
    c.drawString(_x(x_col1 + 8), _y(y5), "Chèque N°")
    _case(c, x_col1 + 30, y5 - 2.2, mode == "cheque")
    if mode == "cheque" and paiement.numero_cheque:
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(_x(x_col1 + 38), _y(y5), paiement.numero_cheque)
    elif mode == "orange_money":
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(_x(x_col1 + 38), _y(y5), "(reglement par Orange Money)")
    c.setFont("Helvetica", 8)

    y6 = depuis_haut + 6 * hauteur_ligne - 3
    c.drawString(_x(x_col1 + 4), _y(y6), "Intégral")
    _case(c, x_col1 + 18, y6 - 2, type_paiement == "integral")
    c.drawString(_x(x_col1 + 24), _y(y6), "Partiel")
    _case(c, x_col1 + 38, y6 - 2, type_paiement == "partiel")
    c.setFont("Helvetica", 7)
    reste = paiement.solde_apres if paiement and paiement.solde_apres else 0
    texte_reste = f"Reste à payer : {_fmt(reste)} F" if reste else "Reste à payer : -"
    c.drawString(_x(x_col1 + 44), _y(y6), texte_reste)
    c.setFont("Helvetica", 8)

    return depuis_haut + hauteur_totale + 8


def _pied(c, quittance, declaration, depuis_haut):
    """Somme totale en lettres/chiffres, date, signature de l'agent."""
    c.setFont("Helvetica", 9)
    c.drawString(_x(MARGE), _y(depuis_haut), "Somme totale payée (en chiffre et en lettre) :")
    depuis_haut += 6
    _ligne_pointillee(c, MARGE, LARGEUR_PAGE_MM - MARGE, depuis_haut)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(_x(MARGE) + 2, _y(depuis_haut) + 2, f"{quittance.somme_totale_lettres} ({_fmt(quittance.somme_totale_chiffres)} F)")
    depuis_haut += 12

    c.setFont("Helvetica", 9)
    date_txt = quittance.date_delivrance.strftime("%d/%m/%Y") if quittance.date_delivrance else ""
    c.drawString(_x(MARGE), _y(depuis_haut), f"A Ouagadougou, le {date_txt}")
    depuis_haut += 16

    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(_x(LARGEUR_PAGE_MM - MARGE - 30), _y(depuis_haut), "L'Agent du BBDA")
    depuis_haut += 20
    c.setFont("Helvetica-Oblique", 8)
    nom_agent = f"{quittance.agent.prenom} {quittance.agent.nom}" if quittance.agent else ""
    c.drawCentredString(_x(LARGEUR_PAGE_MM - MARGE - 30), _y(depuis_haut), nom_agent)


def _candidats_chemin(chemin_stocke):
    """Chemins possibles pour un PDF deja enregistre (relatif, absolu, basename)."""
    if not chemin_stocke:
        return []
    candidats = [chemin_stocke, os.path.abspath(chemin_stocke)]
    dossier = current_app.config["QUITTANCE_FOLDER"]
    candidats.append(os.path.join(dossier, os.path.basename(chemin_stocke)))
    # Deduplique en conservant l'ordre
    vus = set()
    uniques = []
    for candidat in candidats:
        if candidat not in vus:
            vus.add(candidat)
            uniques.append(candidat)
    return uniques


def resoudre_chemin_pdf(quittance):
    """Retourne un chemin existant vers le PDF, ou None s'il a disparu."""
    for candidat in _candidats_chemin(quittance.fichier_pdf_path):
        if candidat and os.path.exists(candidat):
            return os.path.abspath(candidat)
    # Fichier regenerate ailleurs sous le nom attendu
    attendu = os.path.join(
        current_app.config["QUITTANCE_FOLDER"],
        f"quittance_{quittance.numero_quittance}.pdf",
    )
    if os.path.exists(attendu):
        return os.path.abspath(attendu)
    return None


def generer_pdf_quittance(quittance):
    """Genere le PDF d'une quittance et retourne le chemin absolu du fichier."""
    declaration = quittance.declaration
    paiement = declaration.paiements[-1] if declaration.paiements else None

    dossier_quittances = current_app.config["QUITTANCE_FOLDER"]
    os.makedirs(dossier_quittances, exist_ok=True)
    nom_fichier = f"quittance_{quittance.numero_quittance}.pdf"
    chemin_fichier = os.path.abspath(os.path.join(dossier_quittances, nom_fichier))

    c = canvas.Canvas(chemin_fichier, pagesize=A4)
    c.setTitle(f"Quittance BBDA n° {quittance.numero_quittance}")

    _en_tete(c, quittance)
    depuis_haut = _corps(c, quittance, declaration)
    depuis_haut = _tableau(c, quittance, paiement, depuis_haut)
    _pied(c, quittance, declaration, depuis_haut)

    c.showPage()
    c.save()
    return chemin_fichier


def assurer_fichier_pdf(quittance):
    """Garantit un PDF sur disque (regenere si absent — disque ephemere Render).

    Met a jour `fichier_pdf_path` si regeneration. Ne commit pas : le caller
    decide (flush pendant paiement, commit pendant telechargement).
    """
    existant = resoudre_chemin_pdf(quittance)
    if existant:
        if quittance.fichier_pdf_path != existant:
            quittance.fichier_pdf_path = existant
        return existant

    chemin = generer_pdf_quittance(quittance)
    quittance.fichier_pdf_path = chemin
    return chemin
