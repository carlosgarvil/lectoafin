"""Lectura del catálogo de la biblioteca exportado desde Séneca (Biblioweb).

Séneca exporta un .xls con UNA FILA POR EJEMPLAR (si la biblioteca tiene 6 copias
de un libro, aparecen 6 filas). Aquí lo convertimos en UNA ENTRADA POR LIBRO:

    1. Leemos la hoja y localizamos la fila de cabecera (la que contiene "ISBN" y "Título").
    2. Descartamos los ejemplares dados de baja.
    3. Agrupamos: mismo ISBN  ->  mismo libro.  Sin ISBN: mismo título + autor.
    4. Limpiamos los textos (autor "APELLIDO, NOMBRE ; ;" -> "Nombre Apellido", etc.).

Es un buen ejemplo de "limpieza de datos" (data cleaning): los datos reales casi nunca
vienen como los necesitamos.
"""
import re
import unicodedata

import xlrd

COLUMNAS_OBLIGATORIAS = ("ISBN", "Título", "Autor")


def normalizar_isbn(isbn):
    """'978-84-1342-144-5' -> '9788413421445'. Devuelve '' si no parece un ISBN."""
    limpio = re.sub(r"[^0-9Xx]", "", str(isbn)).upper()
    return limpio if len(limpio) in (10, 13) else ""


def clave_texto(texto):
    """Minúsculas, sin tildes ni signos: sirve para comparar títulos y autores."""
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", texto.lower()).strip()


def _capitalizar(texto):
    """Pone en formato título los textos que vienen TODO EN MAYÚSCULAS."""
    return texto.title() if texto.isupper() else texto


def limpiar_autor(autor):
    """'YOSHIZUMI, WATARU ; ;' -> 'Wataru Yoshizumi'.  '-, -' -> ''.

    Si hay varios autores separados por ';' se juntan con ' y '.
    """
    nombres = []
    for parte in str(autor).split(";"):
        parte = re.sub(r"[\s,-]+$", "", parte.strip())        # quita comas y guiones sueltos al final
        if not parte or parte.strip(" ,.-") == "":
            continue
        if parte.count(",") == 1:                       # "Apellidos, Nombre"
            apellidos, nombre = (p.strip(" -") for p in parte.split(","))
            parte = f"{nombre} {apellidos}".strip(" -")
        if parte:
            nombres.append(_capitalizar(parte))
    return " y ".join(nombres)


def limpiar_titulo(titulo):
    titulo = re.sub(r"\s+", " ", str(titulo)).strip().rstrip(".").strip()
    return _capitalizar(titulo) if len(titulo) > 4 else titulo


def leer_catalogo(ruta):
    """Devuelve una lista de libros (dict) a partir del .xls de Séneca.

    Cada libro: titulo, autor, isbn, ejemplares, temas (descriptores de Séneca).
    """
    hoja = xlrd.open_workbook(ruta).sheet_by_index(0)

    # La cabecera no está en la primera fila: Séneca pone antes título, autor y fecha.
    fila_cabecera = None
    for r in range(min(hoja.nrows, 20)):
        valores = [str(c.value).strip() for c in hoja.row(r)]
        if all(col in valores for col in COLUMNAS_OBLIGATORIAS):
            fila_cabecera, cabecera = r, valores
            break
    if fila_cabecera is None:
        raise ValueError("No encuentro la fila de cabecera (ISBN, Título, Autor). "
                         "¿Es una exportación del catálogo de Séneca?")

    libros = {}   # clave de agrupación -> libro
    for r in range(fila_cabecera + 1, hoja.nrows):
        fila = dict(zip(cabecera, (str(c.value).strip() for c in hoja.row(r))))
        titulo = limpiar_titulo(fila.get("Título", ""))
        if not titulo or fila.get("Fecha baja"):
            continue                                    # fila vacía o ejemplar dado de baja
        autor = limpiar_autor(fila.get("Autor", ""))
        isbn = normalizar_isbn(fila.get("ISBN", ""))
        clave = isbn or (clave_texto(titulo), clave_texto(autor))

        libro = libros.setdefault(clave, {
            "titulo": titulo, "autor": autor, "isbn": isbn, "ejemplares": 0, "temas": set(),
        })
        libro["ejemplares"] += 1
        for tema in fila.get("Descriptor", "").split(","):
            if tema.strip():
                libro["temas"].add(tema.strip())

    for libro in libros.values():
        libro["temas"] = sorted(libro["temas"])
    return list(libros.values())
