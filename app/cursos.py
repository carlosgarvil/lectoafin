"""Lista de cursos del desplegable de registro, leída del fichero cursos.txt (raíz del proyecto).

Formato (igual que las listas de alias): un curso por línea; se ignoran las líneas vacías
y las que empiezan por #. Se lee una sola vez, al arrancar la app.
Si el fichero falta o queda vacío, el registro vuelve a mostrar un campo de texto libre.
"""
import logging
from pathlib import Path

from .alias import lineas_utiles

log = logging.getLogger(__name__)

LONGITUD_MAXIMA = 20      # tamaño de la columna "grupo" en la base de datos


def leer_cursos(ruta):
    cursos = []
    for n, linea in lineas_utiles(Path(ruta)):
        linea = " ".join(linea.split())                  # espacios dobles -> uno
        if len(linea) > LONGITUD_MAXIMA:
            log.warning("Cursos: %s, línea %d ignorada (más de %d caracteres): %r",
                        Path(ruta).name, n, LONGITUD_MAXIMA, linea)
        elif linea not in cursos:                         # sin duplicados, en el orden del fichero
            cursos.append(linea)
    if not cursos:
        log.warning("Cursos: no hay cursos en %s; el registro usará un campo de texto libre.", ruta)
    return cursos


def iniciar(app):
    ruta = Path(app.root_path).parent / "cursos.txt"     # raíz del proyecto, sin rutas de Windows
    app.extensions["cursos"] = leer_cursos(ruta)
    # Disponible en todas las plantillas como {{ lista_cursos }}
    app.context_processor(lambda: {"lista_cursos": app.extensions["cursos"]})
    app.logger.info("Cursos: %d cargados.", len(app.extensions["cursos"]))


def cursos_actuales():
    from flask import current_app
    return current_app.extensions["cursos"]
