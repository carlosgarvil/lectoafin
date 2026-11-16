"""Extensiones compartidas (se crean aquí para evitar importaciones circulares)."""
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
