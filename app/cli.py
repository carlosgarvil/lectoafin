"""Bookcrush · comandos de terminal para el profesorado.

    flask --app run crear-admin           -> crea una cuenta de administración
    flask --app run datos-ejemplo         -> carga libros y alumnado ficticio para probar
    flask --app run datos-ejemplo --catalogo RegEjemplares.xls
                                          -> igual, pero con los libros del catálogo de Séneca
    flask --app run importar-seneca RegEjemplares.xls [--ocultos] [--open-library]
                                          -> importa el catálogo real de la biblioteca
"""
import random

import click

from . import openlibrary, sinopsis
from .catalogo_seneca import clave_texto, leer_catalogo
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


def importar_catalogo(ruta, activos=True, usar_open_library=False):
    """Añade a la BD los libros del .xls de Séneca que aún no estén. Devuelve (nuevos, repetidos)."""
    existentes = {(clave_texto(l.titulo), clave_texto(l.autor)) for l in Libro.query.all()}
    ids_ol = {l.openlibrary_id for l in Libro.query.filter(Libro.openlibrary_id.isnot(None))}
    nuevos = repetidos = 0

    for datos in leer_catalogo(ruta):
        if (clave_texto(datos["titulo"]), clave_texto(datos["autor"])) in existentes:
            repetidos += 1
            continue
        temas = "Temas: " + ", ".join(datos["temas"]) + "." if datos["temas"] else ""
        libro = Libro(titulo=datos["titulo"][:200], autor=datos["autor"][:200],
                      sinopsis=temas, activo=activos)

        # Opcional: completar portada y año preguntando a Open Library por el ISBN
        if usar_open_library and datos["isbn"]:
            try:
                info = openlibrary.buscar_por_isbn(datos["isbn"])
            except Exception as exc:          # sin conexión, API caída...
                click.echo(f"  ! Open Library no responde ({exc}); sigo sin portadas.")
                usar_open_library = False
                info = None
            if info:
                libro.portada_url = info["portada_url"]
                libro.anio = info["anio"]
                if info["openlibrary_id"] and info["openlibrary_id"] not in ids_ol:
                    libro.openlibrary_id = info["openlibrary_id"]
                    ids_ol.add(libro.openlibrary_id)
            texto, _ = sinopsis.buscar_sinopsis(libro.titulo, libro.autor, datos["isbn"],
                                                libro.openlibrary_id or "")
            if texto:
                libro.sinopsis = texto + ("\n\n" + temas if temas else "")
            marcas = ("P" if libro.portada_url else "·") + ("S" if texto else "·")
            click.echo(f"  {marcas} {libro.titulo}")

        db.session.add(libro)
        existentes.add((clave_texto(libro.titulo), clave_texto(libro.autor)))
        nuevos += 1
    db.session.commit()
    return nuevos, repetidos


def register_cli(app):

    @app.cli.command("importar-seneca")
    @click.argument("ruta", type=click.Path(exists=True, dir_okay=False))
    @click.option("--ocultos", is_flag=True,
                  help="Importa los libros ocultos, para activarlos uno a uno desde el panel.")
    @click.option("--open-library", "usar_ol", is_flag=True,
                  help="Busca portada y año por ISBN en Open Library (tarda ~1 s por libro).")
    def importar_seneca(ruta, ocultos, usar_ol):
        """Importa el catálogo exportado de Séneca (.xls, una fila por ejemplar)."""
        nuevos, repetidos = importar_catalogo(ruta, activos=not ocultos, usar_open_library=usar_ol)
        click.echo(f"{nuevos} libros nuevos ({'ocultos' if ocultos else 'activos'}); "
                   f"{repetidos} omitidos por repetidos (mismo título y autor).")

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

    @app.cli.command("completar-sinopsis")
    @click.option("--limite", default=0, help="Máximo de libros a consultar (0 = todos).")
    def completar_sinopsis(limite):
        """Busca sinopsis en Google Books / Open Library para los libros que no la tienen."""
        pendientes = [l for l in Libro.query.order_by(Libro.id) if sinopsis.sin_sinopsis_real(l)]
        if limite:
            pendientes = pendientes[:limite]
        encontradas = 0
        for libro in pendientes:
            fuente = sinopsis.completar(libro)
            encontradas += bool(fuente)
            click.echo(f"  {'✓ ' + fuente if fuente else '· sin resultado':16} {libro.titulo}")
            db.session.commit()          # guardamos libro a libro: si se corta, no se pierde lo hecho
        click.echo(f"{encontradas} de {len(pendientes)} libros con sinopsis nueva.")

    @app.cli.command("datos-ejemplo")
    @click.option("--alumnos", default=12, help="Nº de alumnos ficticios")
    @click.option("--catalogo", type=click.Path(exists=True, dir_okay=False),
                  help="Usa los libros de un .xls de Séneca en vez de los 20 de ejemplo.")
    @click.option("--open-library", "usar_ol", is_flag=True,
                  help="Con --catalogo: busca portadas y año por ISBN en Open Library.")
    def datos_ejemplo(alumnos, catalogo, usar_ol):
        """Carga libros de ejemplo y alumnado ficticio con votos aleatorios."""
        if catalogo:
            nuevos, repetidos = importar_catalogo(catalogo, usar_open_library=usar_ol)
            click.echo(f"Catálogo: {nuevos} libros nuevos, {repetidos} omitidos por repetidos.")
        else:
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
