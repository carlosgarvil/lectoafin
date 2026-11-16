"""Comandos de terminal para el profesorado.

    flask --app run crear-admin           -> crea una cuenta de administración
    flask --app run datos-ejemplo         -> carga libros y alumnado ficticio para probar
"""
import random

import click

from .extensions import db
from .models import Libro, Usuario, Voto

LIBROS_EJEMPLO = [
    ("El principito", "Antoine de Saint-Exupéry", 1943),
    ("Momo", "Michael Ende", 1973),
    ("La historia interminable", "Michael Ende", 1979),
    ("1984", "George Orwell", 1949),
    ("Rebelión en la granja", "George Orwell", 1945),
    ("Fahrenheit 451", "Ray Bradbury", 1953),
    ("Harry Potter y la piedra filosofal", "J. K. Rowling", 1997),
    ("El hobbit", "J. R. R. Tolkien", 1937),
    ("Los juegos del hambre", "Suzanne Collins", 2008),
    ("Matilda", "Roald Dahl", 1988),
    ("Marina", "Carlos Ruiz Zafón", 1999),
    ("Frankenstein", "Mary Shelley", 1818),
    ("Don Quijote de la Mancha", "Miguel de Cervantes", 1605),
    ("La casa de los espíritus", "Isabel Allende", 1982),
    ("Cien años de soledad", "Gabriel García Márquez", 1967),
    ("El curioso incidente del perro a medianoche", "Mark Haddon", 2003),
    ("Wonder", "R. J. Palacio", 2012),
    ("Percy Jackson y el ladrón del rayo", "Rick Riordan", 2005),
    ("Persépolis", "Marjane Satrapi", 2000),
    ("El diario de Ana Frank", "Ana Frank", 1947),
]


def register_cli(app):

    @app.cli.command("crear-admin")
    @click.option("--alias", prompt="Alias del admin")
    @click.password_option(prompt="Contraseña")
    def crear_admin(alias, password):
        """Crea (o convierte en) una cuenta de administración."""
        usuario = Usuario.query.filter_by(alias=alias).first()
        if usuario is None:
            usuario = Usuario(alias=alias, grupo="Profesorado")
            db.session.add(usuario)
        usuario.es_admin = True
        usuario.set_password(password)
        db.session.commit()
        click.echo(f"Admin «{alias}» listo.")

    @app.cli.command("datos-ejemplo")
    @click.option("--alumnos", default=12, help="Nº de alumnos ficticios")
    def datos_ejemplo(alumnos):
        """Carga libros de ejemplo y alumnado ficticio con votos aleatorios."""
        for titulo, autor, anio in LIBROS_EJEMPLO:
            if not Libro.query.filter_by(titulo=titulo).first():
                db.session.add(Libro(titulo=titulo, autor=autor, anio=anio))
        db.session.commit()

        libros = Libro.query.filter_by(activo=True).all()
        random.seed(42)  # resultados reproducibles
        for i in range(1, alumnos + 1):
            alias = f"lector{i:02d}"
            if Usuario.query.filter_by(alias=alias).first():
                continue
            u = Usuario(alias=alias, grupo=random.choice(["1º BACH A", "1º BACH B", "4º ESO A"]))
            u.set_password("prueba123")
            db.session.add(u)
            db.session.flush()  # para obtener u.id
            # Cada alumno ficticio tiene un "género favorito" para que salgan afinidades
            preferidos = set(random.sample(range(len(libros)), k=len(libros) // 3))
            for idx in random.sample(range(len(libros)), k=random.randint(8, len(libros))):
                prob = 0.85 if idx in preferidos else 0.25
                db.session.add(Voto(usuario_id=u.id, libro_id=libros[idx].id,
                                    me_gusta=random.random() < prob))
        db.session.commit()
        click.echo(f"{len(libros)} libros y {alumnos} alumnos de prueba "
                   f"(contraseña: prueba123).")
