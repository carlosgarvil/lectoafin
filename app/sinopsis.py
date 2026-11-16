"""Búsqueda automática de sinopsis en APIs externas.

Orden de preferencia:
    1. Google Books, en español. Solo si existe la variable de entorno GOOGLE_BOOKS_API_KEY
       (sin clave, Google rechaza casi todas las peticiones con "429 Too Many Requests").
    2. Open Library. No necesita clave, pero las descripciones suelen estar en inglés.

Los textos de estas APIs vienen "sucios" (HTML, Markdown, notas de Wikipedia como [2]...),
así que los limpiamos antes de guardarlos. Otro ejemplo de limpieza de datos.
"""
import html
import json
import os
import re
import urllib.parse
import urllib.request

CABECERAS = {"User-Agent": "Bookcrush-educativo/1.0"}
LONGITUD_MAXIMA = 700   # caracteres: la tarjeta del móvil no da para más


def _pedir_json(url):
    peticion = urllib.request.Request(url, headers=CABECERAS)
    with urllib.request.urlopen(peticion, timeout=10) as respuesta:
        return json.load(respuesta)


# ---------------------------------------------------------------- Limpieza

def limpiar(texto):
    """Quita HTML, Markdown y notas al pie; recorta a LONGITUD_MAXIMA sin cortar frases.

    Devuelve '' si el texto no está escrito en alfabeto latino (p. ej., japonés).
    """
    if not texto:
        return ""
    texto = html.unescape(re.sub(r"<[^>]+>", " ", texto))            # etiquetas HTML
    texto = re.split(r"\n\s*-{3,}", texto)[0]                         # Open Library: "----" y anexos
    texto = re.sub(r"^\s*\[\d+\]:\s*\S+.*$", "", texto, flags=re.M)   # [1]: https://...
    texto = re.sub(r"\(\s*\[[^\]]*\]\[\d+\]\s*\)", "", texto)         # ([fuente][1])
    texto = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", texto)            # [texto](url) -> texto
    texto = re.sub(r"\[\d+\]", "", texto)                             # notas tipo Wikipedia [2]
    texto = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", texto)       # **negrita**, *cursiva*
    texto = re.sub(r"\s+", " ", texto).strip()

    letras = [c for c in texto if c.isalpha()]
    latinas = [c for c in letras if c.isascii() or "À" <= c <= "ɏ"]
    if not letras or len(latinas) / len(letras) < 0.8:
        return ""

    if len(texto) > LONGITUD_MAXIMA:
        corte = texto[:LONGITUD_MAXIMA]
        fin_frase = max(corte.rfind(". "), corte.rfind("! "), corte.rfind("? "))
        texto = corte[:fin_frase + 1] if fin_frase > 200 else corte.rsplit(" ", 1)[0] + "…"
    return texto


# ---------------------------------------------------------------- Fuentes

def desde_google_books(titulo, autor="", isbn=""):
    clave = os.environ.get("GOOGLE_BOOKS_API_KEY", "").strip()
    if not clave:
        return ""
    consulta = f"isbn:{isbn}" if isbn else f'intitle:"{titulo}"' + (f' inauthor:"{autor}"' if autor else "")
    params = urllib.parse.urlencode({"q": consulta, "langRestrict": "es", "maxResults": 5,
                                     "printType": "books", "key": clave})
    datos = _pedir_json(f"https://www.googleapis.com/books/v1/volumes?{params}")
    for item in datos.get("items", []):
        info = item.get("volumeInfo", {})
        if info.get("language") == "es" and info.get("description"):
            return limpiar(info["description"])
    return ""


def desde_open_library(titulo, autor="", isbn="", openlibrary_id=""):
    if not openlibrary_id:
        # Sin identificador: buscamos la obra por ISBN o por título + autor
        consulta = f"isbn:{isbn}" if isbn else f"{titulo} {autor}".strip()
        params = urllib.parse.urlencode({"q": consulta, "limit": 1, "fields": "key"})
        docs = _pedir_json(f"https://openlibrary.org/search.json?{params}").get("docs", [])
        if not docs:
            return ""
        openlibrary_id = docs[0]["key"].replace("/works/", "")
    obra = _pedir_json(f"https://openlibrary.org/works/{openlibrary_id}.json")
    descripcion = obra.get("description", "")
    if isinstance(descripcion, dict):          # a veces viene como {"type": ..., "value": "..."}
        descripcion = descripcion.get("value", "")
    return limpiar(descripcion)


def buscar_sinopsis(titulo, autor="", isbn="", openlibrary_id=""):
    """Devuelve (texto, fuente). Si no encuentra nada o las APIs fallan: ('', '')."""
    for fuente, funcion, args in (
        ("Google Books", desde_google_books, (titulo, autor, isbn)),
        ("Open Library", desde_open_library, (titulo, autor, isbn, openlibrary_id)),
    ):
        try:
            texto = funcion(*args)
        except Exception:      # sin conexión, cupo agotado, respuesta rara... probamos la siguiente
            texto = ""
        if texto:
            return texto, fuente
    return "", ""


def sin_sinopsis_real(libro):
    """True si el libro no tiene sinopsis o solo tiene los «Temas» del catálogo de Séneca."""
    return not libro.sinopsis or libro.sinopsis.startswith("Temas:")


def completar(libro):
    """Rellena la sinopsis de un libro (conservando sus «Temas»). Devuelve la fuente o ''."""
    texto, fuente = buscar_sinopsis(libro.titulo, libro.autor, openlibrary_id=libro.openlibrary_id or "")
    if texto:
        temas = libro.sinopsis if (libro.sinopsis or "").startswith("Temas:") else ""
        libro.sinopsis = texto + (f"\n\n{temas}" if temas else "")
    return fuente
