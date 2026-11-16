"""Registro, inicio y cierre de sesión."""
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from .extensions import db
from .models import Usuario

bp = Blueprint("auth", __name__)


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
        if len(password) < 6:
            errores.append("La contraseña debe tener al menos 6 caracteres.")
        if password != password2:
            errores.append("Las contraseñas no coinciden.")
        if Usuario.query.filter_by(alias=alias).first():
            errores.append("Ese alias ya está en uso.")

        if errores:
            for e in errores:
                flash(e, "error")
            return render_template("registro.html", alias=alias, grupo=grupo)

        usuario = Usuario(alias=alias, grupo=grupo)
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()
        login_user(usuario)
        flash(f"¡Bienvenido/a, {alias}! Empieza a valorar libros.", "ok")
        return redirect(url_for("main.descubrir"))

    return render_template("registro.html")


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
