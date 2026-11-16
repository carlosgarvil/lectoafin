"""Modelo de datos (capa de BASE DE DATOS).

Tres tablas:

    usuario (1) ──< voto >── (1) libro

Un VOTO relaciona a un usuario con un libro e indica si le gusta (True)
o no (False). Es una relación muchos-a-muchos con un dato extra.
"""
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


def ahora():
    return datetime.now(timezone.utc)


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(40), unique=True, nullable=False)   # nombre visible (no el nombre real)
    grupo = db.Column(db.String(20), nullable=False, default="")    # p. ej. "1º BACH A"
    password_hash = db.Column(db.String(256), nullable=False)
    es_admin = db.Column(db.Boolean, default=False, nullable=False)
    creado = db.Column(db.DateTime, default=ahora)

    votos = db.relationship("Voto", back_populates="usuario", cascade="all, delete-orphan")

    # Nunca guardamos la contraseña en claro: solo su "hash".
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Libro(db.Model):
    __tablename__ = "libro"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(200), nullable=False, default="")
    anio = db.Column(db.Integer)
    portada_url = db.Column(db.String(500), default="")
    sinopsis = db.Column(db.Text, default="")
    openlibrary_id = db.Column(db.String(40), unique=True)       # si se importó desde la API
    activo = db.Column(db.Boolean, default=True, nullable=False)  # visible en la biblioteca
    creado = db.Column(db.DateTime, default=ahora)

    votos = db.relationship("Voto", back_populates="libro", cascade="all, delete-orphan")


class Voto(db.Model):
    __tablename__ = "voto"
    # Un usuario solo puede votar una vez cada libro
    __table_args__ = (db.UniqueConstraint("usuario_id", "libro_id"),)

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey("libro.id"), nullable=False)
    me_gusta = db.Column(db.Boolean, nullable=False)
    fecha = db.Column(db.DateTime, default=ahora)

    usuario = db.relationship("Usuario", back_populates="votos")
    libro = db.relationship("Libro", back_populates="votos")


@login_manager.user_loader
def cargar_usuario(user_id):
    return db.session.get(Usuario, int(user_id))
