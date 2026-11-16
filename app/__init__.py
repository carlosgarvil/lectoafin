"""Bookcrush · fábrica de la aplicación Flask (patrón "application factory").

Aquí se juntan las piezas: configuración, base de datos, login y los
"blueprints" (módulos de rutas): auth, main (alumnado) y admin.

La configuración sensible se lee de VARIABLES DE ENTORNO, así el mismo
código funciona en local (SQLite) y en un servidor como Render (PostgreSQL).
"""
import mimetypes
import os

from flask import Flask

from .extensions import db, login_manager

# Tipo MIME correcto para el manifest de la web instalable (Python no lo trae de serie)
mimetypes.add_type("application/manifest+json", ".webmanifest")


def url_base_de_datos(instance_path):
    """En local usamos SQLite; si existe DATABASE_URL (Render), PostgreSQL."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        return "sqlite:///" + os.path.join(instance_path, "bookcrush.db")
    # SQLAlchemy necesita saber qué "driver" usar para hablar con PostgreSQL
    for prefijo in ("postgres://", "postgresql://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url[len(prefijo):]
    return url


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    app.config.update(
        # En producción esta clave debe ser secreta y aleatoria (Render la genera).
        SECRET_KEY=os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion"),
        SQLALCHEMY_DATABASE_URI=url_base_de_datos(app.instance_path),
        # Comprueba que la conexión sigue viva antes de usarla (útil en la nube)
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        # En Render (HTTPS) la cookie de sesión solo viaja cifrada
        SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")),
        # Parámetros del algoritmo de afinidad (ver app/matching.py)
        UMBRAL_AFINIDAD=0.30,   # afinidad mínima (0..1) para considerar que hay "conexión"
        MIN_LIBROS_COMUNES=2,   # nº mínimo de libros que gustan a ambos
        # Si se define, el alumnado necesita este código para registrarse
        CODIGO_REGISTRO=os.environ.get("CODIGO_REGISTRO", ""),
        # False: el alias SOLO puede salir del generador (listas_alias/). True: alias libre.
        ALIAS_LIBRE=os.environ.get("ALIAS_LIBRE", "").lower() in ("1", "true", "si", "sí"),
    )

    from . import alias
    alias.iniciar(app)      # lee las listas de listas_alias/ una sola vez, al arrancar

    from .seguridad import comprobar_csrf, csrf_token
    app.before_request(comprobar_csrf)
    app.jinja_env.globals["csrf_token"] = csrf_token

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Inicia sesión para continuar."

    from . import models  # noqa: F401  (registra los modelos en SQLAlchemy)
    from .admin import bp as admin_bp
    from .auth import bp as auth_bp
    from .cli import register_cli
    from .main import bp as main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    register_cli(app)

    with app.app_context():
        db.create_all()
        crear_admin_desde_entorno()

    return app


def crear_admin_desde_entorno():
    """Si existen ADMIN_ALIAS y ADMIN_PASSWORD, garantiza que esa cuenta admin existe.

    Sirve para servidores sin terminal (como el plan gratuito de Render).
    La contraseña se sincroniza en cada arranque: para cambiarla, basta con
    cambiar la variable de entorno y reiniciar.
    """
    from .models import Usuario

    alias = os.environ.get("ADMIN_ALIAS", "").strip()
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not alias or not password:
        return
    usuario = Usuario.query.filter_by(alias=alias).first()
    if usuario is None:
        usuario = Usuario(alias=alias, grupo="Profesorado")
        db.session.add(usuario)
    usuario.es_admin = True
    if not usuario.password_hash or not usuario.check_password(password):
        usuario.set_password(password)
    db.session.commit()
