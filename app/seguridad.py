"""Protección CSRF mínima, hecha a mano para poder explicarla en clase.

CSRF (Cross-Site Request Forgery): una web maliciosa podría hacer que tu
navegador envíe un formulario a esta aplicación usando tu sesión abierta.
Para evitarlo, cada formulario lleva un token secreto guardado en la sesión;
si el token no coincide, rechazamos la petición.

(En proyectos reales se usaría una librería como Flask-WTF.)
"""
import hmac
import secrets
from functools import wraps

from flask import abort, request, session
from flask_login import current_user


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def comprobar_csrf():
    """Se ejecuta antes de cada petición POST."""
    if request.method != "POST":
        return
    enviado = request.form.get("_csrf") or request.headers.get("X-CSRF-Token", "")
    if not hmac.compare_digest(enviado, session.get("_csrf", "")):
        abort(400, "Token CSRF no válido. Recarga la página.")


def solo_admin(vista):
    """Decorador: la ruta solo es accesible para el profesorado (admin)."""
    @wraps(vista)
    def envoltorio(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_admin:
            abort(403)
        return vista(*args, **kwargs)
    return envoltorio
