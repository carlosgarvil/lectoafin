"""Generador de alias para el alumnado (p. ej. «KatnissExploradora07», «FrodoHolmes42»).

Las palabras salen de los ficheros de la carpeta listas_alias/ (en la raíz del proyecto),
que el profesorado puede editar con el Bloc de notas:

    personajes_femeninos.txt   un nombre por línea
    personajes_masculinos.txt  un nombre por línea
    apellidos.txt              un apellido por línea
    adjetivos.txt              "masculino / femenino" (explorador / exploradora)
                               o una sola palabra si no cambia (veloz)

En todos se ignoran las líneas vacías y las que empiezan por #.
Las listas se leen UNA vez, al arrancar la app: para aplicar cambios hay que reiniciarla.

¿Por qué alias generados? Protegen la identidad del alumnado (nadie usa su nombre real)
y evitan alias ofensivos.
"""
import logging
import random
import re
from pathlib import Path

log = logging.getLogger(__name__)

LONGITUD_MAXIMA = 40          # límite del campo alias en el formulario y en la BD
INTENTOS = 20

# Una palabra válida: letras (con tildes, ñ, ü...) y, como mucho, espacios entre ellas.
PALABRA = re.compile(r"^[^\W\d_]+(?: [^\W\d_]+)*$")

# Apellido "propio" de cada personaje, para no generar su nombre real (HarryPotter).
# Los ficheros no dicen qué apellido va con qué nombre, así que lo indicamos aquí.
APELLIDO_PROPIO = {
    "Harry": "Potter", "Hermione": "Granger", "Ron": "Weasley", "Ginny": "Weasley",
    "Luna": "Lovegood", "Neville": "Longbottom", "Sherlock": "Holmes", "Watson": "Watson",
    "Sancho": "Panza", "Quijote": "Quijano", "Katniss": "Everdeen", "Frodo": "Bolsón",
    "Bilbo": "Bolsón", "Percy": "Jackson", "Annabeth": "Chase", "Elizabeth": "Bennet",
    "Jane": "Eyre", "Jo": "March", "Pippi": "Calzaslargas", "Wendy": "Darling",
    "Robinson": "Crusoe", "Tom": "Sawyer", "Huck": "Finn", "Manolito": "Gafotas",
    "Peter": "Pan", "Lyra": "Belacqua", "Matilda": "Wormwood", "Oliver": "Twist",
    "Lazarillo": "Tormes", "Gulliver": "Gulliver", "Drácula": "VanHelsing",
}


# ---------------------------------------------------------------- Lectura de los ficheros

def lineas_utiles(ruta):
    """Devuelve las líneas con contenido (sin vacías ni comentarios), con su número de línea."""
    try:
        texto = ruta.read_text(encoding="utf-8-sig")      # -sig: tolera el BOM del Bloc de notas
    except FileNotFoundError:
        log.warning("Listas: no existe el fichero %s; se usará una lista vacía.", ruta)
        return []
    except (OSError, UnicodeDecodeError) as exc:
        log.warning("Listas: no se pudo leer %s (%s); se usará una lista vacía.", ruta, exc)
        return []
    return [(n, l.strip()) for n, l in enumerate(texto.splitlines(), 1)
            if l.strip() and not l.strip().startswith("#")]


def _camel(palabra):
    """'dormilón' -> 'Dormilón';  'van helsing' -> 'VanHelsing';  'VanHelsing' se queda igual."""
    return "".join(p[0].upper() + p[1:] for p in palabra.split())


def _leer_palabras(ruta):
    palabras = []
    for n, linea in lineas_utiles(ruta):
        if PALABRA.match(linea):
            palabras.append(_camel(linea))
        else:
            log.warning("Alias: %s, línea %d ignorada (solo se admiten letras): %r", ruta.name, n, linea)
    return palabras


def _leer_adjetivos(ruta):
    """Devuelve dos listas: formas masculinas y femeninas (las invariables van en ambas)."""
    masculinos, femeninos = [], []
    for n, linea in lineas_utiles(ruta):
        partes = [p.strip() for p in linea.split("/")]
        if len(partes) == 1 and PALABRA.match(partes[0]):
            masculinos.append(_camel(partes[0]))
            femeninos.append(_camel(partes[0]))
        elif len(partes) == 2 and all(PALABRA.match(p) for p in partes):
            masculinos.append(_camel(partes[0]))
            femeninos.append(_camel(partes[1]))
        else:
            log.warning("Alias: adjetivos.txt, línea %d ignorada (formato «masculino / femenino» "
                        "o una sola palabra): %r", n, linea)
    return masculinos, femeninos


class Listas:
    """Las palabras disponibles, ya limpias y en formato CamelCase."""

    def __init__(self, carpeta):
        carpeta = Path(carpeta)
        self.femeninos = _leer_palabras(carpeta / "personajes_femeninos.txt")
        self.masculinos = _leer_palabras(carpeta / "personajes_masculinos.txt")
        self.apellidos = _leer_palabras(carpeta / "apellidos.txt")
        self.adj_masc, self.adj_fem = _leer_adjetivos(carpeta / "adjetivos.txt")
        if not self.disponible:
            log.warning("Alias: las listas de %s no bastan para generar alias "
                        "(hacen falta nombres y adjetivos o apellidos). El alias será libre.", carpeta)

    @property
    def disponible(self):
        hay_nombres = self.femeninos or self.masculinos
        return bool(hay_nombres and (self.adj_masc or self.adj_fem or self.apellidos))

    # ------------------------------------------------------------ Generar

    def _combinaciones_apellido(self, nombre):
        propio = APELLIDO_PROPIO.get(nombre)
        return [a for a in self.apellidos if a != nombre and a != propio]

    def generar(self):
        """Un alias al azar (sin comprobar la BD). None si las listas no lo permiten."""
        if not self.disponible:
            return None
        personajes = ([(n, self.adj_fem) for n in self.femeninos] +
                      [(n, self.adj_masc) for n in self.masculinos])
        for _ in range(INTENTOS):
            nombre, adjetivos = random.choice(personajes)
            apellidos = self._combinaciones_apellido(nombre)
            # Fórmula 1 (nombre + adjetivo) o 2 (nombre + apellido de otro personaje), 50/50
            if adjetivos and (not apellidos or random.random() < 0.5):
                segunda = random.choice(adjetivos)
            elif apellidos:
                segunda = random.choice(apellidos)
            else:
                continue
            alias = f"{nombre}{segunda}{random.randint(0, 99):02d}"
            if len(alias) <= LONGITUD_MAXIMA:
                return alias
        return None

    # ------------------------------------------------------------ Validar

    def es_valido(self, alias):
        """True si el alias encaja con las listas: nombre + (adjetivo o apellido) + 2 cifras."""
        if not alias or len(alias) > LONGITUD_MAXIMA or not re.fullmatch(r".+\d\d", alias):
            return False
        cuerpo = alias[:-2]
        for nombres, adjetivos in ((self.femeninos, self.adj_fem), (self.masculinos, self.adj_masc)):
            for nombre in nombres:
                if cuerpo.startswith(nombre):
                    resto = cuerpo[len(nombre):]
                    if resto in adjetivos or resto in self._combinaciones_apellido(nombre):
                        return True
        return False


# ---------------------------------------------------------------- Integración con Flask

def iniciar(app):
    """Carga las listas al arrancar. Se guardan en app.extensions["alias"]."""
    carpeta = Path(app.root_path).parent / "listas_alias"      # raíz del proyecto, sin rutas de Windows
    app.extensions["alias"] = Listas(carpeta)
    listas = app.extensions["alias"]
    app.logger.info("Alias: %d personajes, %d adjetivos, %d apellidos.",
                    len(listas.femeninos) + len(listas.masculinos), len(listas.adj_masc), len(listas.apellidos))


def listas_actuales():
    from flask import current_app
    return current_app.extensions["alias"]


def alias_libre_disponible():
    """Busca un alias generado que no exista aún en la base de datos (hasta INTENTOS veces)."""
    from .models import Usuario
    listas = listas_actuales()
    for _ in range(INTENTOS):
        alias = listas.generar()
        if alias is None:
            return None
        if not Usuario.query.filter_by(alias=alias).first():
            return alias
    return None
