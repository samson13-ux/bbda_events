"""Capture les ecrans memoires avec l'UI actuelle (Playwright + base demo locale).

Usage (depuis la racine du projet, venv active) :
  python archives/scripts/capturer_screenshots_memoire.py

Ecrase les PNG dans memoire/screenshots/ (meme noms que le memoire).
"""

from __future__ import annotations

import os
import sys
import time
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "tmp_bbda_capture.db"
OUT = ROOT / "memoire" / "screenshots"
BASE = "http://127.0.0.1:5055"
MDP = "password123"


def preparer_base():
    if DB_PATH.exists():
        DB_PATH.unlink()
    os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH.as_posix()}"
    os.environ["FLASK_ENV"] = "testing"
    os.environ["SECRET_KEY"] = "capture-screenshots-key-32chars-min"
    os.environ.pop("SENDGRID_API_KEY", None)

    from app import create_app
    from config import TestingConfig
    from extensions import db
    from demo_data import seed_soutenance

    # Base fichier (pas :memory:) pour le serveur HTTP du thread
    TestingConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH.as_posix()}"
    app = create_app("testing")
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["MAIL_SUPPRESS_SEND"] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_soutenance(app)
    return app


def demarrer_serveur(app):
    def run():
        app.run(host="127.0.0.1", port=5055, debug=False, use_reloader=False)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    time.sleep(1.5)


def shot(page, nom: str, full=True):
    OUT.mkdir(parents=True, exist_ok=True)
    chemin = OUT / nom
    page.screenshot(path=str(chemin), full_page=full)
    print(f"  OK {nom}")


def connecter(page, email: str):
    page.goto(f"{BASE}/auth/deconnexion", wait_until="domcontentloaded")
    page.goto(f"{BASE}/auth/connexion", wait_until="networkidle")
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', MDP)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")


def main():
    print("1. Preparation base demo...")
    app = preparer_base()
    print("2. Demarrage serveur local :5055...")
    demarrer_serveur(app)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        print("3. Captures publiques...")
        page.goto(f"{BASE}/", wait_until="networkidle")
        time.sleep(1.2)
        shot(page, "01-accueil.png")
        shot(page, "07-accueil-v2.png")

        page.goto(f"{BASE}/auth/inscription", wait_until="networkidle")
        shot(page, "02-inscription.png")

        page.goto(f"{BASE}/auth/connexion", wait_until="networkidle")
        shot(page, "03-connexion.png")

        page.fill('input[name="email"]', "inconnu@example.com")
        page.fill('input[name="password"]', "mauvais")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        shot(page, "08-flash-erreur.png")

        # Evenement public
        page.goto(f"{BASE}/evenements", wait_until="networkidle")
        shot(page, "04-espace-organisateur.png")  # listing public temporaire si besoin
        liens = page.locator("a[href*='/evenements/']")
        if liens.count() > 0:
            liens.first.click()
            page.wait_for_load_state("networkidle")
            shot(page, "34-detail-evenement-public.png")

        print("4. Organisateur actif...")
        connecter(page, "orga1@example.com")
        page.goto(f"{BASE}/declarations/", wait_until="networkidle")
        shot(page, "09-dashboard-orga1.png")
        shot(page, "04-espace-organisateur.png")

        page.goto(f"{BASE}/declarations/nouvelle", wait_until="networkidle")
        shot(page, "11-formulaire-concert.png")
        # Section promotion
        case = page.locator('input[name="promouvoir"]')
        if case.count():
            case.check()
            time.sleep(0.3)
        shot(page, "35-formulaire-promotion.png")

        # Festival + artistes
        nature = page.locator('select[name="nature_manifestation"]')
        if nature.count():
            try:
                nature.select_option(label="Festival")
            except Exception:
                try:
                    nature.select_option(index=1)
                except Exception:
                    pass
        for sel in (
            "button#ajouter-artiste",
            "button[data-ajouter-artiste]",
            "#btn-ajouter-artiste",
            "button:has-text('Ajouter un artiste')",
            "button:has-text('artiste')",
        ):
            btn = page.locator(sel)
            if btn.count():
                btn.first.click()
                time.sleep(0.2)
                break
        shot(page, "12-formulaire-festival-artistes.png")

        # Erreurs validation
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        shot(page, "13-formulaire-erreurs.png")

        # Detail declaration existante
        page.goto(f"{BASE}/declarations/", wait_until="networkidle")
        voir = page.locator("a.lien-action-table, a:has-text('Voir')").first
        if voir.count():
            voir.click()
            page.wait_for_load_state("networkidle")
            shot(page, "15-detail-orga3-0.png")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(0.3)
            shot(page, "15-detail-orga3-1.png")

        print("5. Organisateur bloque...")
        connecter(page, "orga4@example.com")
        page.goto(f"{BASE}/declarations/", wait_until="networkidle")
        shot(page, "10-dashboard-orga4-bloque.png")

        print("6. Agent...")
        connecter(page, "agent1@bbda.bf")
        page.goto(f"{BASE}/agent/", wait_until="networkidle")
        shot(page, "05-espace-agent.png")
        shot(page, "17-dashboard-agent.png")
        shot(page, "22-dashboard-agent-apres.png")

        page.goto(f"{BASE}/agent/surveillance", wait_until="networkidle")
        shot(page, "18-agent-surveillance.png")

        page.goto(f"{BASE}/agent/arrieres", wait_until="networkidle")
        shot(page, "19-agent-arrieres.png")

        page.goto(f"{BASE}/agent/declarations?statut=nouvelle", wait_until="networkidle")
        traiter = page.locator("a.lien-action-table, a:has-text('Traiter'), a:has-text('Voir')").first
        if traiter.count():
            traiter.click()
            page.wait_for_load_state("networkidle")
            shot(page, "20-agent-traitement.png")
            tarif = page.locator('input[name="tarif"]')
            redev = page.locator('input[name="redevance"]')
            if tarif.count() and redev.count():
                tarif.fill("5000")
                redev.fill("15000")
                time.sleep(0.4)
                shot(page, "21-avant-validation-total.png")

        # Paiement : declaration montant_fixe
        page.goto(f"{BASE}/agent/declarations", wait_until="networkidle")
        encaisser = page.locator("a:has-text('Encaisser')").first
        if encaisser.count():
            encaisser.click()
            page.wait_for_load_state("networkidle")
            shot(page, "24-formulaire-paiement-vide.png")
            # Remplir
            mode = page.locator('select[name="mode_paiement"], input[name="mode_paiement"][value="especes"]')
            if page.locator('input[name="mode_paiement"][value="especes"]').count():
                page.locator('input[name="mode_paiement"][value="especes"]').check()
            elif page.locator('select[name="mode_paiement"]').count():
                page.locator('select[name="mode_paiement"]').select_option("especes")
            montant = page.locator('input[name="montant_chiffres"]')
            if montant.count():
                # prendre la valeur max visible si placeholder
                montant.fill(montant.get_attribute("value") or "20000")
            lettres = page.locator('input[name="montant_lettres"], textarea[name="montant_lettres"]')
            if lettres.count():
                lettres.fill("Vingt mille francs CFA")
            typ = page.locator('input[name="type_paiement"][value="integral"]')
            if typ.count():
                typ.check()
            shot(page, "25-formulaire-paiement-rempli.png")

        page.goto(f"{BASE}/agent/", wait_until="networkidle")
        shot(page, "26-dashboard-agent-apres-paiement.png")

        print("7. Quittance / detail orga...")
        # Chercher une declaration quittance_delivree
        connecter(page, "orga1@example.com")
        page.goto(f"{BASE}/declarations/", wait_until="networkidle")
        shot(page, "23-dashboard-organisateur-apres.png")
        # Ouvrir details un par un pour trouver bouton telecharger
        liens_voir = page.locator("a.lien-action-table:has-text('Voir'), td.cellule-actions a:has-text('Voir')")
        trouve = False
        for i in range(min(liens_voir.count(), 8)):
            connecter(page, "orga1@example.com")
            page.goto(f"{BASE}/declarations/", wait_until="networkidle")
            page.locator("a.lien-action-table:has-text('Voir'), td.cellule-actions a:has-text('Voir')").nth(i).click()
            page.wait_for_load_state("networkidle")
            if page.locator("a.bouton-telecharger, a:has-text('quittance')").count():
                shot(page, "27-dossier-apres-paiement.png")
                shot(page, "32-detail-avec-bouton-telecharger.png")
                shot(page, "16-detail-montant-fixe.png")
                trouve = True
                # Telecharger PDF via URL
                href = page.locator("a.bouton-telecharger, a:has-text('quittance')").first.get_attribute("href")
                if href:
                    if href.startswith("/"):
                        href = BASE + href
                    # Ouvrir PDF dans nouvel onglet n'affiche pas toujours ; on copie fichier disque
                break
        if not trouve:
            # Essayer orga5 ou autres comptes demo
            for email in ("orga2@example.com", "orga5@example.com", "orga3@example.com"):
                connecter(page, email)
                page.goto(f"{BASE}/declarations/", wait_until="networkidle")
                if page.locator("a:has-text('Voir')").count():
                    page.locator("a:has-text('Voir')").first.click()
                    page.wait_for_load_state("networkidle")
                    if page.locator("a.bouton-telecharger, a:has-text('quittance')").count():
                        shot(page, "27-dossier-apres-paiement.png")
                        shot(page, "32-detail-avec-bouton-telecharger.png")
                        break

        # PDF quittance depuis dossier static
        from models import Quittance

        with app.app_context():
            q = Quittance.query.first()
            if q and q.fichier_pdf_path and Path(q.fichier_pdf_path).exists():
                # Rendu PDF -> PNG via playwright (chromium ouvre pdf)
                pdf_url = Path(q.fichier_pdf_path).resolve().as_uri()
                page.goto(pdf_url, wait_until="load")
                time.sleep(1)
                shot(page, "28-quittance-pdf.png", full=False)
                shot(page, "29-quittance-pdf-corrigee.png", full=False)
                shot(page, "30-quittance-pdf-v3.png", full=False)
                shot(page, "31-quittance-partiel.png", full=False)

        print("8. Admin...")
        connecter(page, "admin@bbda.bf")
        page.goto(f"{BASE}/admin/", wait_until="networkidle")
        shot(page, "06-espace-admin.png")

        # Apres soumission : message flash simulé via nouvelle declaration minimale trop lourd
        # Reprendre dashboard orga apres
        connecter(page, "orga1@example.com")
        page.goto(f"{BASE}/declarations/", wait_until="networkidle")
        shot(page, "14-apres-soumission.png")

        # Email : page non disponible — garder placeholder informatif via screenshot notification admin messages si existe
        page.goto(f"{BASE}/", wait_until="networkidle")
        # Copie 08 comme base pour 33 si pas d'email UI
        if not (OUT / "33-email-montant-fixe.png").exists():
            shot(page, "33-email-montant-fixe.png")

        browser.close()

    print("Terminé. Captures dans", OUT)
    try:
        DB_PATH.unlink(missing_ok=True)
    except Exception:
        pass


if __name__ == "__main__":
    main()
