"""Instances des extensions Flask, separees pour eviter les imports circulaires
entre app.py, models.py et les blueprints de backend/."""

from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
