"""Algoritmo de afinidad lectora.

IDEA: dos personas son afines si les gustan los mismos libros.

Usamos el ÍNDICE DE JACCARD, una medida clásica de similitud entre conjuntos:

                 |A ∩ B|        libros que nos gustan a los dos
    J(A, B) = ------------- = ------------------------------------
                 |A ∪ B|        libros que le gustan a alguno de los dos

    · J = 1   -> nos gustan exactamente los mismos libros
    · J = 0   -> no coincidimos en ninguno

Ejemplo:
    A = {Dune, 1984, Momo}        B = {1984, Momo, Matilda, Coraline}
    A ∩ B = {1984, Momo}                              -> 2 elementos
    A ∪ B = {Dune, 1984, Momo, Matilda, Coraline}     -> 5 elementos
    J = 2 / 5 = 0.40  -> 40 % de afinidad

Hay "conexión" si la afinidad supera un umbral Y además hay un mínimo de
libros en común (para que coincidir en un único libro no dé un 100 %).

ACTIVIDAD: ¿cómo cambiarías la fórmula para tener en cuenta también
los "no me gusta"? ¿Y para penalizar los desacuerdos?
"""
from collections import defaultdict

from flask import current_app

from .models import Usuario, Voto


def jaccard(a: set, b: set) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _gustos_por_usuario():
    """Devuelve {usuario_id: {ids de libros que le gustan}} con una sola consulta."""
    gustos = defaultdict(set)
    filas = Voto.query.filter_by(me_gusta=True).with_entities(Voto.usuario_id, Voto.libro_id)
    for usuario_id, libro_id in filas:
        gustos[usuario_id].add(libro_id)
    return gustos


def _es_conexion(afinidad, comunes):
    return (afinidad >= current_app.config["UMBRAL_AFINIDAD"]
            and len(comunes) >= current_app.config["MIN_LIBROS_COMUNES"])


def calcular_afinidades(usuario):
    """Afinidad del usuario con el resto del alumnado, de mayor a menor."""
    gustos = _gustos_por_usuario()
    mios = gustos.get(usuario.id, set())

    resultados = []
    otros = Usuario.query.filter(Usuario.id != usuario.id, Usuario.es_admin.is_(False))
    for otro in otros:
        suyos = gustos.get(otro.id, set())
        comunes = mios & suyos
        afinidad = jaccard(mios, suyos)
        resultados.append({
            "usuario": otro,
            "afinidad": afinidad,
            "comunes": comunes,
            "es_conexion": _es_conexion(afinidad, comunes),
        })

    resultados.sort(key=lambda r: r["afinidad"], reverse=True)
    return resultados


def todas_las_conexiones():
    """Todas las parejas con conexión (para el panel del profesorado)."""
    gustos = _gustos_por_usuario()
    alumnos = Usuario.query.filter_by(es_admin=False).order_by(Usuario.alias).all()

    parejas = []
    for i, a in enumerate(alumnos):
        for b in alumnos[i + 1:]:          # cada pareja se compara una sola vez
            ga, gb = gustos.get(a.id, set()), gustos.get(b.id, set())
            afinidad = jaccard(ga, gb)
            comunes = ga & gb
            if _es_conexion(afinidad, comunes):
                parejas.append({"a": a, "b": b, "afinidad": afinidad, "comunes": comunes})
    parejas.sort(key=lambda p: p["afinidad"], reverse=True)
    return parejas
