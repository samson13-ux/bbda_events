"""Modeles SQLAlchemy de BBDA Events — cf. docs/DATABASE_SCHEMA.md pour le detail
des colonnes et docs/REGLES_METIER.md pour les regles metier associees."""

from datetime import datetime

from flask_login import UserMixin

from extensions import db, login_manager


def _enum(*valeurs, name):
    """Enum portable MySQL/Postgres (stocke en VARCHAR, evite les types ENUM natifs)."""
    return db.Enum(*valeurs, name=name, native_enum=False, length=50)


class Utilisateur(db.Model, UserMixin):
    """Compte de connexion (organisateur, agent ou administrateur)."""

    __tablename__ = "utilisateur"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    role = db.Column(_enum("organisateur", "agent", "admin", name="role_enum"), nullable=False)
    statut = db.Column(_enum("actif", "inactif", name="statut_utilisateur_enum"), default="actif")
    date_inscription = db.Column(db.DateTime, default=datetime.utcnow)

    organisateur = db.relationship("Organisateur", back_populates="utilisateur", uselist=False)
    notifications = db.relationship("Notification", back_populates="destinataire")

    @property
    def is_active(self):
        """Surcharge UserMixin : un compte 'inactif' ne peut pas rester connecte
        (verifie par Flask-Login a chaque requete, en plus du controle explicite
        fait a la connexion dans backend/auth/routes.py)."""
        return self.statut == "actif"


@login_manager.user_loader
def charger_utilisateur(utilisateur_id):
    """Callback Flask-Login : recharge l'utilisateur depuis son id de session."""
    return Utilisateur.query.get(int(utilisateur_id))


class Organisateur(db.Model):
    """Profil organisateur, lie 1-1 a un compte Utilisateur (role=organisateur)."""

    __tablename__ = "organisateur"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), unique=True, nullable=False, index=True)
    qualite = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    statut_compte = db.Column(
        _enum("actif", "arriere", "bloque", "surveillance", name="statut_compte_enum"),
        default="actif",
    )

    utilisateur = db.relationship("Utilisateur", back_populates="organisateur")
    declarations = db.relationship("Declaration", back_populates="organisateur")
    arrieres = db.relationship("Arriere", back_populates="organisateur")
    alertes_surveillance = db.relationship("AlerteSurveillance", back_populates="organisateur")


class Declaration(db.Model):
    """Declaration d'un evenement culturel occasionnel par un organisateur."""

    __tablename__ = "declaration"

    id = db.Column(db.Integer, primary_key=True)
    organisateur_id = db.Column(db.Integer, db.ForeignKey("organisateur.id"), nullable=False, index=True)
    nom_demandeur = db.Column(db.String(100), nullable=False)
    prenom_demandeur = db.Column(db.String(100), nullable=False)
    qualite_demandeur = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    nature_manifestation = db.Column(db.String(100), nullable=False)
    nom_artiste_evenement = db.Column(db.String(200), nullable=False)
    nom_salle = db.Column(db.String(200), nullable=False)
    adresse = db.Column(db.String(200), nullable=False)
    ville = db.Column(db.String(100), nullable=False)
    date_evenement = db.Column(db.DateTime, nullable=False)
    duree_heures = db.Column(db.Float, nullable=False)
    capacite_accueil = db.Column(db.Integer, nullable=False)
    entree_payante = db.Column(db.Boolean, default=False)
    nature_diffusion = db.Column(db.String(200), nullable=False)
    autres_details = db.Column(db.Text, nullable=True)
    promouvoir = db.Column(db.Boolean, default=False, index=True)
    description_publique = db.Column(db.Text, nullable=True)
    affiche_path = db.Column(db.String(300), nullable=True)
    contact_public = db.Column(db.Boolean, default=False)
    statut = db.Column(
        _enum(
            "nouvelle",
            "en_evaluation",
            "montant_fixe",
            "paiement_en_attente",
            "payee",
            "quittance_delivree",
            "en_attente",
            name="statut_declaration_enum",
        ),
        default="nouvelle",
        index=True,
    )
    date_soumission = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    commentaire_agent = db.Column(db.Text, nullable=True)

    organisateur = db.relationship("Organisateur", back_populates="declarations")
    artistes = db.relationship("ListeArtiste", back_populates="declaration", cascade="all, delete-orphan")
    evaluation = db.relationship("EvaluationAgent", back_populates="declaration", uselist=False)
    paiements = db.relationship("Paiement", back_populates="declaration")
    quittance = db.relationship("Quittance", back_populates="declaration", uselist=False)
    arrieres = db.relationship("Arriere", back_populates="declaration")


class ListeArtiste(db.Model):
    """Artiste associe a une declaration (une declaration peut en lister plusieurs)."""

    __tablename__ = "liste_artiste"

    id = db.Column(db.Integer, primary_key=True)
    declaration_id = db.Column(db.Integer, db.ForeignKey("declaration.id"), nullable=False, index=True)
    nom_artiste = db.Column(db.String(200), nullable=False)
    discipline = db.Column(db.String(100), nullable=True)

    declaration = db.relationship("Declaration", back_populates="artistes")


class EvaluationAgent(db.Model):
    """Evaluation d'une declaration par un agent : Tarif + Redevance (RM-030 a RM-035)."""

    __tablename__ = "evaluation_agent"

    id = db.Column(db.Integer, primary_key=True)
    declaration_id = db.Column(db.Integer, db.ForeignKey("declaration.id"), unique=True, nullable=False, index=True)
    agent_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False, index=True)
    tarif = db.Column(db.Float, nullable=False)
    redevance = db.Column(db.Float, nullable=False)
    date_evaluation = db.Column(db.DateTime, default=datetime.utcnow)
    commentaire = db.Column(db.Text, nullable=True)

    declaration = db.relationship("Declaration", back_populates="evaluation")
    agent = db.relationship("Utilisateur", foreign_keys=[agent_id])

    @property
    def montant_total(self):
        """Montant total a payer pour la declaration (RM-032)."""
        return self.tarif + self.redevance


class Paiement(db.Model):
    """Versement effectue sur une declaration. Une declaration peut recevoir
    plusieurs versements successifs (RM-047, RM-048) jusqu'a solde nul."""

    __tablename__ = "paiement"

    id = db.Column(db.Integer, primary_key=True)
    declaration_id = db.Column(db.Integer, db.ForeignKey("declaration.id"), nullable=False, index=True)
    mode_paiement = db.Column(
        _enum("especes", "cheque", "orange_money", name="mode_paiement_enum"), nullable=False
    )
    numero_cheque = db.Column(db.String(50), nullable=True)
    montant_chiffres = db.Column(db.Float, nullable=False)
    montant_lettres = db.Column(db.String(300), nullable=False)
    type_paiement = db.Column(_enum("integral", "partiel", name="type_paiement_enum"), default="integral")
    solde_apres = db.Column(db.Float, default=0)
    date_paiement = db.Column(db.DateTime, default=datetime.utcnow)
    confirme_par = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)

    declaration = db.relationship("Declaration", back_populates="paiements")
    agent_confirmateur = db.relationship("Utilisateur", foreign_keys=[confirme_par])


class Quittance(db.Model):
    """Quittance PDF delivree une fois le solde d'une declaration a zero (RM-050 a RM-054)."""

    __tablename__ = "quittance"

    id = db.Column(db.Integer, primary_key=True)
    declaration_id = db.Column(db.Integer, db.ForeignKey("declaration.id"), unique=True, nullable=False, index=True)
    numero_quittance = db.Column(db.String(20), unique=True, nullable=False)
    droit_annuel = db.Column(db.Float, default=0)
    droit_arriere = db.Column(db.Float, default=0)
    droit_exigible = db.Column(db.Float, default=0)
    droits_type = db.Column(db.String(100), nullable=True)
    droits_montant = db.Column(db.Float, default=0)
    etiquettes_nombre = db.Column(db.Integer, default=0)
    etiquettes_montant = db.Column(db.Float, default=0)
    penalites_type = db.Column(db.String(100), nullable=True)
    penalites_montant = db.Column(db.Float, default=0)
    somme_totale_chiffres = db.Column(db.Float, nullable=False)
    somme_totale_lettres = db.Column(db.String(300), nullable=False)
    date_delivrance = db.Column(db.DateTime, default=datetime.utcnow)
    agent_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)
    fichier_pdf_path = db.Column(db.String(300), nullable=True)

    declaration = db.relationship("Declaration", back_populates="quittance")
    agent = db.relationship("Utilisateur", foreign_keys=[agent_id])


class Arriere(db.Model):
    """Montant du non regle par un organisateur (RM-060 a RM-076)."""

    __tablename__ = "arriere"

    id = db.Column(db.Integer, primary_key=True)
    organisateur_id = db.Column(db.Integer, db.ForeignKey("organisateur.id"), nullable=False, index=True)
    declaration_id = db.Column(db.Integer, db.ForeignKey("declaration.id"), nullable=True)
    montant_du = db.Column(db.Float, nullable=False)
    date_echeance = db.Column(db.DateTime, nullable=False)
    statut = db.Column(
        _enum("en_attente", "regle", name="statut_arriere_enum"), default="en_attente", index=True
    )
    date_reglement = db.Column(db.DateTime, nullable=True)
    derniere_notification = db.Column(db.DateTime, nullable=True)

    organisateur = db.relationship("Organisateur", back_populates="arrieres")
    declaration = db.relationship("Declaration", back_populates="arrieres")


class Notification(db.Model):
    """Email automatique envoye a un utilisateur, journalise en base (RM-100 a RM-103)."""

    __tablename__ = "notification"

    id = db.Column(db.Integer, primary_key=True)
    destinataire_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False, index=True)
    type_notification = db.Column(db.String(50), nullable=False)
    sujet = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    canal = db.Column(db.String(20), default="email")
    date_envoi = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(
        _enum("en_attente", "envoyee", "echouee", name="statut_notification_enum"),
        default="en_attente",
        index=True,
    )

    destinataire = db.relationship("Utilisateur", back_populates="notifications")


class AlerteSurveillance(db.Model):
    """Alerte declenchee quand un compte 'sous surveillance' se reconnecte (RM-080 a RM-084)."""

    __tablename__ = "alerte_surveillance"

    id = db.Column(db.Integer, primary_key=True)
    organisateur_id = db.Column(db.Integer, db.ForeignKey("organisateur.id"), nullable=False, index=True)
    date_marquage = db.Column(db.DateTime, default=datetime.utcnow)
    marque_par = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=True)
    traitee = db.Column(db.Boolean, default=False, index=True)
    date_traitement = db.Column(db.DateTime, nullable=True)
    traite_par = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=True)
    commentaire = db.Column(db.Text, nullable=True)

    organisateur = db.relationship("Organisateur", back_populates="alertes_surveillance")
    agent_marqueur = db.relationship("Utilisateur", foreign_keys=[marque_par])
    agent_traiteur = db.relationship("Utilisateur", foreign_keys=[traite_par])


class MessageContact(db.Model):
    """Message envoye via le formulaire de contact de la face publique."""

    __tablename__ = "message_contact"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    sujet = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_envoi = db.Column(db.DateTime, default=datetime.utcnow)
    traite = db.Column(db.Boolean, default=False)


class ParametresSysteme(db.Model):
    """Valeurs configurables par l'administrateur (seuil arriere, delai rappel...).

    Voir docs/REGLES_METIER.md §9. Cles seedees par init_db.py :
    SEUIL_ARRIERE (defaut 1000), DELAI_NOTIFICATION (defaut 7).
    """

    __tablename__ = "parametres_systeme"

    id = db.Column(db.Integer, primary_key=True)
    cle = db.Column(db.String(100), unique=True, nullable=False)
    valeur = db.Column(db.String(300), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    modifie_par = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=True)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
