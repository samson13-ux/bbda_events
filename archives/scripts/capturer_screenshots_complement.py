"""Complement de captures : quittance, PDF, accueil viewport."""
import os
import sys
import time
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
DB = ROOT / "tmp_bbda_capture.db"
OUT = ROOT / "memoire" / "screenshots"
BASE = "http://127.0.0.1:5056"
MDP = "password123"

if DB.exists():
    DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{DB.as_posix()}"
os.environ["FLASK_ENV"] = "testing"
os.environ["SECRET_KEY"] = "capture-screenshots-key-32chars-min"

from config import TestingConfig

TestingConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB.as_posix()}"

from app import create_app
from demo_data import seed_soutenance
from extensions import db
from models import Declaration, Quittance

app = create_app("testing")
app.config["WTF_CSRF_ENABLED"] = False
app.config["MAIL_SUPPRESS_SEND"] = True
with app.app_context():
    db.drop_all()
    db.create_all()
    seed_soutenance(app)
    # Generer les PDF manquants pour les captures
    from backend.exports.pdf_generator import generer_pdf_quittance

    for q in Quittance.query.all():
        if not q.fichier_pdf_path or not Path(q.fichier_pdf_path).exists():
            q.fichier_pdf_path = generer_pdf_quittance(q)
    db.session.commit()
    print("quittances:", Quittance.query.count())

    targets = []
    for q in Quittance.query.all():
        d = db.session.get(Declaration, q.declaration_id)
        targets.append(
            (
                d.organisateur.utilisateur.email,
                d.id,
                q.fichier_pdf_path,
            )
        )
    mf = Declaration.query.filter_by(statut="montant_fixe").first()
    mf_info = None
    if mf:
        mf_info = (mf.organisateur.utilisateur.email, mf.id)


def run():
    app.run(host="127.0.0.1", port=5056, debug=False, use_reloader=False)


threading.Thread(target=run, daemon=True).start()
time.sleep(1.2)

from playwright.sync_api import sync_playwright


def shot(page, nom, full=False):
    data = page.screenshot(full_page=full)
    cible = OUT / nom
    tmp = OUT / f".tmp-{nom}"
    tmp.write_bytes(data)
    for _ in range(5):
        try:
            if cible.exists():
                cible.unlink()
            tmp.rename(cible)
            print("OK", nom)
            return
        except OSError:
            time.sleep(0.4)
    # Dernier recours : garder le .tmp sous le nom final alternatif
    alt = OUT / f"NEW-{nom}"
    if alt.exists():
        alt.unlink()
    tmp.rename(alt)
    print("OK (alt)", alt.name)


def login(page, email):
    page.goto(f"{BASE}/auth/connexion", wait_until="networkidle")
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', MDP)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")


def pdf_vers_png(chemin_pdf, chemin_png):
    import fitz

    doc = fitz.open(chemin_pdf)
    page0 = doc[0]
    pix = page0.get_pixmap(matrix=fitz.Matrix(2, 2))
    tmp = Path(str(chemin_png)).with_suffix(".tmp.png")
    pix.save(str(tmp))
    doc.close()
    cible = Path(chemin_png)
    for _ in range(5):
        try:
            if cible.exists():
                cible.unlink()
            tmp.replace(cible)
            print("OK", cible.name)
            return
        except OSError:
            time.sleep(0.4)
    alt = cible.with_name("NEW-" + cible.name)
    if alt.exists():
        try:
            alt.unlink()
        except OSError:
            pass
    tmp.replace(alt)
    print("OK (alt)", alt.name)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_context(viewport={"width": 1280, "height": 800}).new_page()

    page.goto(f"{BASE}/", wait_until="networkidle")
    time.sleep(1.5)
    shot(page, "01-accueil.png")
    shot(page, "07-accueil-v2.png")

    if targets:
        email, did, pdf = targets[0]
        login(page, email)
        page.goto(f"{BASE}/declarations/{did}", wait_until="networkidle")
        shot(page, "27-dossier-apres-paiement.png", full=True)
        shot(page, "32-detail-avec-bouton-telecharger.png", full=True)
        if pdf and Path(pdf).exists():
            pdf_vers_png(pdf, OUT / "28-quittance-pdf.png")
            pdf_vers_png(pdf, OUT / "29-quittance-pdf-corrigee.png")
            pdf_vers_png(pdf, OUT / "30-quittance-pdf-v3.png")
            if len(targets) > 1 and targets[1][2] and Path(targets[1][2]).exists():
                pdf_vers_png(targets[1][2], OUT / "31-quittance-partiel.png")
            else:
                pdf_vers_png(pdf, OUT / "31-quittance-partiel.png")

    if mf_info:
        login(page, mf_info[0])
        page.goto(f"{BASE}/declarations/{mf_info[1]}", wait_until="networkidle")
        shot(page, "16-detail-montant-fixe.png", full=True)

    login(page, "agent1@bbda.bf")
    page.goto(f"{BASE}/agent/declarations?statut=nouvelle", wait_until="networkidle")
    lien = page.locator("a:has-text('Traiter'), a:has-text('Voir')")
    if lien.count():
        lien.first.click()
        page.wait_for_load_state("networkidle")
        if page.locator('input[name="tarif"]').count():
            page.fill('input[name="tarif"]', "5000")
            page.fill('input[name="redevance"]', "15000")
            time.sleep(0.5)
            shot(page, "21-avant-validation-total.png", full=True)
            shot(page, "20-agent-traitement.png", full=True)

    browser.close()

print("done")
try:
    DB.unlink(missing_ok=True)
except Exception:
    pass
