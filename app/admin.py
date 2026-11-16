"""Panel del profesorado (admin).

El admin decide qué libros forman la biblioteca: puede añadirlos a mano
o importarlos desde la API de Open Library. Solo los libros ACTIVOS se
muestran al alumnado.
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from . import openlibrary, sinopsis
from .extensions import db
from .matching import todas_las_conexiones
from .models import Libro, Usuario, Voto
from .seguridad import solo_admin

bp = Blueprint("admin", __name__)


@bp.route("/")
@login_required
@solo_admin
def panel():
    total_votos = Voto.query.count()
    me_gusta = Voto.query.filter_by(me_gusta=True).count()

    # Libros más valorados: consulta con GROUP BY (buen ejemplo de SQL)
    ranking = (db.session.query(Libro, db.func.count(Voto.id).label("likes"))
               .join(Voto).filter(Voto.me_gusta.is_(True))
               .group_by(Libro.id).order_by(db.desc("likes")).limit(5).all())

    return render_template(
        "admin/panel.html",
        n_alumnos=Usuario.query.filter_by(es_admin=False).count(),
        n_libros=Libro.query.filter_by(activo=True).count(),
        total_votos=total_votos,
        pct_gusta=round(100 * me_gusta / total_votos) if total_votos else 0,
        ranking=ranking,
        conexiones=todas_las_conexiones(),
        libros={l.id: l for l in Libro.query.all()},
    )


@bp.route("/libros", methods=["GET", "POST"])
@login_required
@solo_admin
def libros():
    if request.method == "POST":  # alta manual
        titulo = request.form.get("titulo", "").strip()
        if not titulo:
            flash("El título es obligatorio.", "error")
        else:
            anio = request.form.get("anio", "").strip()
            db.session.add(Libro(
                titulo=titulo,
                autor=request.form.get("autor", "").strip(),
                anio=int(anio) if anio.isdigit() else None,
                portada_url=request.form.get("portada_url", "").strip(),
                sinopsis=request.form.get("sinopsis", "").strip(),
            ))
            db.session.commit()
            flash(f"Libro «{titulo}» añadido.", "ok")
        return redirect(url_for("admin.libros"))

    lista = Libro.query.order_by(Libro.activo.desc(), Libro.titulo).all()
    return render_template("admin/libros.html", libros=lista)


@bp.post("/libros/<int:libro_id>/activar")
@login_required
@solo_admin
def activar(libro_id):
    libro = db.get_or_404(Libro, libro_id)
    libro.activo = not libro.activo
    db.session.commit()
    return redirect(url_for("admin.libros"))


@bp.post("/libros/<int:libro_id>/borrar")
@login_required
@solo_admin
def borrar(libro_id):
    libro = db.get_or_404(Libro, libro_id)
    db.session.delete(libro)  # borra también sus votos (cascade)
    db.session.commit()
    flash(f"Libro «{libro.titulo}» eliminado.", "ok")
    return redirect(url_for("admin.libros"))


@bp.route("/buscar")
@login_required
@solo_admin
def buscar():
    q = request.args.get("q", "").strip()
    resultados, error = [], None
    if q:
        try:
            resultados = openlibrary.buscar(q)
        except Exception as exc:  # sin conexión, API caída...
            error = f"No se pudo consultar Open Library ({exc})."
    ya_importados = {l.openlibrary_id for l in Libro.query.filter(Libro.openlibrary_id.isnot(None))}
    return render_template("admin/buscar.html", q=q, resultados=resultados,
                           error=error, ya_importados=ya_importados)


@bp.post("/importar")
@login_required
@solo_admin
def importar():
    ol_id = request.form.get("openlibrary_id", "").strip()
    if ol_id and not Libro.query.filter_by(openlibrary_id=ol_id).first():
        anio = request.form.get("anio", "")
        libro = Libro(
            openlibrary_id=ol_id,
            titulo=request.form.get("titulo", "Sin título"),
            autor=request.form.get("autor", ""),
            anio=int(anio) if anio.isdigit() else None,
            portada_url=request.form.get("portada_url", ""),
        )
        fuente = sinopsis.completar(libro)      # consulta Google Books / Open Library
        db.session.add(libro)
        db.session.commit()
        detalle = f"con sinopsis de {fuente}" if fuente else "sin sinopsis (puedes escribirla en «Editar»)"
        flash(f"Importado: «{libro.titulo}», {detalle}.", "ok")
    return redirect(url_for("admin.buscar", q=request.form.get("q", "")))


@bp.route("/libros/<int:libro_id>/editar", methods=["GET", "POST"])
@login_required
@solo_admin
def editar(libro_id):
    libro = db.get_or_404(Libro, libro_id)
    if request.method == "POST":
        libro.titulo = request.form.get("titulo", libro.titulo).strip() or libro.titulo
        libro.autor = request.form.get("autor", "").strip()
        anio = request.form.get("anio", "").strip()
        libro.anio = int(anio) if anio.isdigit() else None
        libro.portada_url = request.form.get("portada_url", "").strip()
        libro.sinopsis = request.form.get("sinopsis", "").strip()
        db.session.commit()
        flash("Cambios guardados.", "ok")
        return redirect(url_for("admin.libros"))
    return render_template("admin/editar.html", libro=libro)


@bp.post("/libros/<int:libro_id>/sinopsis")
@login_required
@solo_admin
def buscar_sinopsis(libro_id):
    """Busca la sinopsis en las APIs externas y la guarda (sustituye la que hubiera)."""
    libro = db.get_or_404(Libro, libro_id)
    temas = [l for l in (libro.sinopsis or "").split("\n") if l.startswith("Temas:")]
    libro.sinopsis = temas[0] if temas else ""          # conservamos solo los «Temas» de Séneca
    fuente = sinopsis.completar(libro)
    db.session.commit()
    if fuente:
        flash(f"Sinopsis encontrada en {fuente}. Revísala: puede estar en inglés.", "ok")
    else:
        flash("No he encontrado sinopsis para este libro. Puedes escribirla a mano.", "error")
    return redirect(url_for("admin.editar", libro_id=libro.id))


@bp.route("/usuarios")
@login_required
@solo_admin
def usuarios():
    alumnos = (db.session.query(Usuario, db.func.count(Voto.id))
               .outerjoin(Voto).filter(Usuario.es_admin.is_(False))
               .group_by(Usuario.id).order_by(Usuario.grupo, Usuario.alias).all())
    return render_template("admin/usuarios.html", alumnos=alumnos)


@bp.post("/usuarios/<int:usuario_id>/borrar")
@login_required
@solo_admin
def borrar_usuario(usuario_id):
    usuario = db.get_or_404(Usuario, usuario_id)
    if usuario.es_admin:
        flash("No se puede borrar una cuenta de administración desde aquí.", "error")
    else:
        db.session.delete(usuario)
        db.session.commit()
        flash(f"Usuario «{usuario.alias}» eliminado.", "ok")
    return redirect(url_for("admin.usuarios"))
