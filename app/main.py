"""Rutas del alumnado.

Hay dos tipos de rutas:
  · Páginas HTML (render_template): /descubrir, /mis-libros, /afinidades
  · API JSON (las usa el JavaScript del navegador): /api/siguiente, /api/votar

Así se ve claramente la separación FRONT (navegador) / BACK (servidor).
"""
from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .extensions import db
from .matching import calcular_afinidades
from .models import Libro, Voto

bp = Blueprint("main", __name__)


def libro_a_dict(libro):
    return {
        "id": libro.id,
        "titulo": libro.titulo,
        "autor": libro.autor,
        "anio": libro.anio,
        "portada_url": libro.portada_url,
        "sinopsis": libro.sinopsis,
    }


def siguiente_libro(usuario):
    """Primer libro activo que el usuario todavía no ha valorado."""
    votados = db.session.query(Voto.libro_id).filter(Voto.usuario_id == usuario.id)
    return (Libro.query.filter(Libro.activo.is_(True), Libro.id.not_in(votados))
            .order_by(db.func.random()).first())


def pendientes(usuario):
    votados = db.session.query(Voto.libro_id).filter(Voto.usuario_id == usuario.id)
    return Libro.query.filter(Libro.activo.is_(True), Libro.id.not_in(votados)).count()


@bp.route("/")
def inicio():
    if current_user.is_authenticated:
        return redirect(url_for("admin.panel" if current_user.es_admin else "main.descubrir"))
    return render_template("inicio.html")


@bp.route("/descubrir")
@login_required
def descubrir():
    return render_template("descubrir.html")


# ---------------------------------------------------------------- API JSON

@bp.get("/api/siguiente")
@login_required
def api_siguiente():
    libro = siguiente_libro(current_user)
    return jsonify({
        "libro": libro_a_dict(libro) if libro else None,
        "pendientes": pendientes(current_user),
    })


@bp.post("/api/votar")
@login_required
def api_votar():
    datos = request.get_json(silent=True) or {}
    libro = db.session.get(Libro, datos.get("libro_id"))
    if libro is None or not libro.activo or not isinstance(datos.get("me_gusta"), bool):
        return jsonify({"error": "Datos no válidos"}), 400

    voto = Voto.query.filter_by(usuario_id=current_user.id, libro_id=libro.id).first()
    if voto is None:
        voto = Voto(usuario_id=current_user.id, libro_id=libro.id)
        db.session.add(voto)
    voto.me_gusta = datos["me_gusta"]
    db.session.commit()
    return api_siguiente()


# ---------------------------------------------------------------- Páginas

@bp.route("/mis-libros")
@login_required
def mis_libros():
    votos = (Voto.query.filter_by(usuario_id=current_user.id)
             .join(Libro).order_by(Libro.titulo).all())
    return render_template("mis_libros.html",
                           gustan=[v.libro for v in votos if v.me_gusta],
                           no_gustan=[v.libro for v in votos if not v.me_gusta])


@bp.post("/mis-libros/<int:libro_id>/cambiar")
@login_required
def cambiar_voto(libro_id):
    voto = Voto.query.filter_by(usuario_id=current_user.id, libro_id=libro_id).first_or_404()
    voto.me_gusta = not voto.me_gusta
    db.session.commit()
    return redirect(url_for("main.mis_libros"))


@bp.route("/afinidades")
@login_required
def afinidades():
    if current_user.es_admin:
        abort(404)
    resultados = calcular_afinidades(current_user)
    libros = {l.id: l for l in Libro.query.all()}
    return render_template("afinidades.html",
                           conexiones=[r for r in resultados if r["es_conexion"]],
                           resto=[r for r in resultados if not r["es_conexion"]],
                           libros=libros)
