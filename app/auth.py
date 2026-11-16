"""Registro, inicio y cierre de sesión."""
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from . import alias as generador
from .cursos import cursos_actuales
from .extensions import db
from .models import Usuario

bp = Blueprint("auth", __name__)


def alias_generado_obligatorio():
    """True si el alias debe salir del generador (ALIAS_LIBRE desactivado y listas cargadas)."""
    return not current_app.config["ALIAS_LIBRE"] and generador.listas_actuales().disponible


@bp.get("/api/alias-aleatorio")
def api_alias_aleatorio():
    """Devuelve un alias nuevo que no está en uso:  {"alias": "SherlockDormilón07"}."""
    alias = generador.alias_libre_disponible()
    if alias is None:
        return jsonify({"alias": None, "error": "No se pudo generar un alias."}), 503
    return jsonify({"alias": alias})


@bp.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        alias = request.form.get("alias", "").strip()
        grupo = request.form.get("grupo", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        codigo = request.form.get("codigo", "").strip()

        # Validación en el SERVIDOR (nunca hay que fiarse solo de la del navegador)
        errores = []
        codigo_clase = current_app.config.get("CODIGO_REGISTRO", "")
        if codigo_clase and codigo != codigo_clase:
            errores.append("El código de clase no es correcto. Pídeselo a tu profesor/a.")
        if not 3 <= len(alias) <= 40:
            errores.append("El alias debe tener entre 3 y 40 caracteres.")
        elif alias_generado_obligatorio() and not generador.listas_actuales().es_valido(alias):
            # Alguien ha manipulado el formulario: solo valen alias del generador
            errores.append("Usa el botón 🎲 para elegir un alias generado.")
            alias = ""
        if len(password) < 6:
            errores.append("La contraseña debe tener al menos 6 caracteres.")
        if cursos_actuales() and grupo not in cursos_actuales():
            errores.append("Elige tu curso en la lista.")
            grupo = ""
        if password != password2:
            errores.append("Las contraseñas no coinciden.")
        if Usuario.query.filter_by(alias=alias).first():
            errores.append("Ese alias ya está en uso.")
            if alias_generado_obligatorio():
                alias = ""          # se propondrá otro alias generado

        if errores:
            for e in errores:
                flash(e, "error")
            return render_template("registro.html", grupo=grupo,
                                   alias=alias or generador.alias_libre_disponible(),
                                   generado=alias_generado_obligatorio())

        usuario = Usuario(alias=alias, grupo=grupo)
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()
        login_user(usuario)
        flash(f"¡Bienvenido/a, {alias}! Apunta tu alias: lo necesitarás para entrar.", "ok")
        return redirect(url_for("main.descubrir"))

    generado = alias_generado_obligatorio()
    return render_template("registro.html", generado=generado,
                           alias=generador.alias_libre_disponible() if generado else "")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = Usuario.query.filter_by(alias=request.form.get("alias", "").strip()).first()
        if usuario and usuario.check_password(request.form.get("password", "")):
            login_user(usuario)
            return redirect(url_for("admin.panel" if usuario.es_admin else "main.descubrir"))
        # Mensaje genérico: no revelamos si el alias existe o no
        flash("Alias o contraseña incorrectos.", "error")
    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.inicio"))
