"""Cliente mínimo de la API pública de Open Library (https://openlibrary.org).

No necesita clave. Es un buen ejemplo de cómo consumir una API REST que
devuelve JSON. Pruébala directamente en el navegador:
    https://openlibrary.org/search.json?q=el+principito&limit=5
"""
import json
import urllib.parse
import urllib.request

URL_BUSQUEDA = "https://openlibrary.org/search.json"
URL_PORTADA = "https://covers.openlibrary.org/b/id/{}-M.jpg"


def buscar(texto, limite=12):
    params = urllib.parse.urlencode({
        "q": texto,
        "limit": limite,
        "fields": "key,title,author_name,first_publish_year,cover_i",
    })
    peticion = urllib.request.Request(
        f"{URL_BUSQUEDA}?{params}", headers={"User-Agent": "Bookcrush-educativo/1.0"}
    )
    with urllib.request.urlopen(peticion, timeout=10) as respuesta:
        datos = json.load(respuesta)

    libros = []
    for doc in datos.get("docs", []):
        libros.append({
            "openlibrary_id": doc.get("key", "").replace("/works/", ""),
            "titulo": doc.get("title", "Sin título"),
            "autor": ", ".join(doc.get("author_name", [])[:2]),
            "anio": doc.get("first_publish_year"),
            "portada_url": URL_PORTADA.format(doc["cover_i"]) if doc.get("cover_i") else "",
        })
    return libros


def buscar_por_isbn(isbn):
    """Busca un libro por ISBN. Devuelve un dict como los de buscar() o None si no está."""
    resultados = buscar(f"isbn:{isbn}", limite=1)
    return resultados[0] if resultados else None
