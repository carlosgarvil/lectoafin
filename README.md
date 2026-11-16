# Bookcrush · encuentra tu flechazo lector

<img src="app/static/logo.svg" alt="Logo de Bookcrush" width="120">

Aplicación web educativa para la biblioteca del instituto. El alumnado valora los libros con
**me gusta / no me gusta** y la aplicación calcula su **afinidad lectora** con el resto de
compañeros y compañeras. Con esas conexiones el profesorado puede formar clubes de lectura,
parejas de debate, tertulias dialógicas…

> El objetivo es encontrar **compañeros de lectura**, no otra cosa. La app no tiene chat ni
> fotos, y solo pide un alias. El contacto se produce en clase.

---

## 1. Arquitectura (las tres capas)

```
┌──────────── FRONT-END (navegador) ────────────┐
│ HTML (plantillas Jinja) + CSS + JavaScript    │
│ descubrir.js habla con el servidor en JSON    │
└──────────────────────┬────────────────────────┘
                       │  HTTP  (GET /api/siguiente, POST /api/votar …)
┌──────────────────────▼────────────────────────┐
│ BACK-END: Python + Flask                      │
│ rutas · validación · login · algoritmo        │──► API externa: Open Library
└──────────────────────┬────────────────────────┘
                       │  SQLAlchemy (ORM)
┌──────────────────────▼────────────────────────┐
│ BASE DE DATOS: SQLite (instance/bookcrush.db) │
└───────────────────────────────────────────────┘
```

| Capa | Tecnología | Por qué |
|---|---|---|
| Front | HTML + CSS + JS sin frameworks | Se entiende sin herramientas de compilación |
| Back | Flask 3 | Microframework: poco código y fácil de leer |
| BD | SQLite + SQLAlchemy | No hay que instalar un servidor de BD; el ORM traduce clases ↔ tablas |
| API externa | Open Library | Gratuita, sin clave, devuelve JSON |

### Estructura de carpetas

```
lectoafin/
├── run.py                 ← punto de entrada
├── requirements.txt       ← dependencias
├── listas_alias/          ← palabras para generar alias (editables)
└── app/
    ├── __init__.py        ← crea la app y configura (umbral de afinidad, etc.)
    ├── models.py          ← tablas: Usuario, Libro, Voto
    ├── auth.py            ← registro / login / logout
    ├── alias.py           ← generador de alias a partir de listas_alias/
    ├── main.py            ← páginas y API del alumnado
    ├── admin.py           ← panel del profesorado
    ├── matching.py        ← ⭐ algoritmo de afinidad (índice de Jaccard)
    ├── openlibrary.py     ← cliente de la API de Open Library
    ├── seguridad.py       ← protección CSRF y control de acceso
    ├── cli.py             ← comandos: crear-admin, datos-ejemplo
    ├── templates/         ← HTML (Jinja2)
    └── static/            ← style.css, descubrir.js, confeti.js, logo e iconos
```

### Modelo de datos

```
USUARIO                 VOTO                       LIBRO
──────────              ──────────────             ──────────────
id (PK)        1 ──< N  id (PK)          N >── 1   id (PK)
alias (único)           usuario_id (FK)            titulo
grupo                   libro_id (FK)              autor, anio
password_hash           me_gusta (bool)            portada_url, sinopsis
es_admin                fecha                      openlibrary_id
                        UNIQUE(usuario, libro)     activo (bool)
```

---

## 2. Puesta en marcha

Requisitos: Python 3.10 o superior.

```bash
cd lectoafin
python -m venv .venv
# Windows:           .venv\Scripts\activate
# Linux / macOS:     source .venv/bin/activate
pip install -r requirements.txt

flask --app run crear-admin          # crea la cuenta del profesorado
flask --app run datos-ejemplo        # (opcional) 20 libros + 12 alumnos ficticios
flask --app run run --debug          # abre http://127.0.0.1:5000
```

* Los alumnos ficticios son `lector01` … `lector12`, con la contraseña `prueba123`.
* **Catálogo real de la biblioteca (Séneca):** en Séneca, exporta el catálogo de ejemplares a Excel
  (`RegEjemplares.xls`) y cárgalo:
  ```bash
  flask --app run importar-seneca RegEjemplares.xls --ocultos --open-library
  # o, para pruebas, con alumnado ficticio:  flask --app run datos-ejemplo --catalogo RegEjemplares.xls
  ```
  Séneca da una fila por **ejemplar**; el script agrupa por ISBN (o por título + autor), limpia
  los nombres de autor y guarda los descriptores como «Temas». `--ocultos` los deja ocultos para
  activar desde el panel solo los que interesen; `--open-library` busca portada y año por ISBN.
  Ejecutarlo dos veces no duplica libros. Código en `app/catalogo_seneca.py`.
* **Sinopsis automáticas:** al importar un libro desde Open Library se busca su sinopsis
  (código en `app/sinopsis.py`). Primero en **Google Books en español**, si existe la variable
  `GOOGLE_BOOKS_API_KEY` (clave gratuita de Google Cloud → API «Books»); si no, en **Open Library**,
  que no necesita clave pero suele darla en inglés. En «Editar libro» hay un botón para buscarla
  de nuevo, y para los libros que ya tengas: `flask --app run completar-sinopsis`.
* Para empezar de cero, borra `instance/bookcrush.db`.
* Para que puedan entrar otros equipos del aula, ejecuta `flask --app run run --host 0.0.0.0`
  y accede con la IP del ordenador del profesor.
* **Código de clase (opcional):** si defines la variable de entorno `CODIGO_REGISTRO`
  (por ejemplo `set CODIGO_REGISTRO=LIBROS24` en Windows), solo podrá registrarse quien lo sepa.

### Despliegue en Render

El repositorio incluye un [render.yaml](render.yaml) que crea la web y una base de datos
PostgreSQL. En Render el disco se borra en cada reinicio, así que allí no se usa SQLite.

1. Sube el proyecto a un repositorio de GitHub.
2. En [dashboard.render.com](https://dashboard.render.com): **New → Blueprint**, elige el repositorio.
3. Render pedirá `ADMIN_PASSWORD` (contraseña del admin `profe`) y `CODIGO_REGISTRO` (opcional).
4. Cuando termine, la app estará en `https://lectoafin-XXXX.onrender.com`.

| Variable | Para qué sirve |
|---|---|
| `DATABASE_URL` | Conexión a PostgreSQL (la rellena Render). Si no existe, se usa SQLite |
| `SECRET_KEY` | Firma las cookies de sesión (la genera Render) |
| `ADMIN_ALIAS` / `ADMIN_PASSWORD` | Crea o actualiza la cuenta admin en cada arranque |
| `CODIGO_REGISTRO` | Código de clase opcional para registrarse |
| `GOOGLE_BOOKS_API_KEY` | Opcional: sinopsis en español desde Google Books |
| `ALIAS_LIBRE` | Opcional: `1` permite escribir el alias a mano en el registro |

Limitaciones del plan gratuito: la web se «duerme» tras 15 minutos sin visitas (la primera
carga tarda en torno a un minuto) y la base de datos gratuita caduca a los 30 días.

### Personalizar los alias

Al registrarse, cada alumno o alumna recibe un **alias generado** que mezcla un personaje
literario con un adjetivo o con el apellido de otro personaje: `KatnissExploradora07`,
`FrodoHolmes42`, `SherlockDormilón15`… Si no le gusta, pulsa 🎲 **Generar otro**. Así nadie
usa su nombre real y no aparecen alias ofensivos.

Las palabras están en la carpeta **`listas_alias/`** y se pueden cambiar sin saber programar:

| Fichero | Qué contiene | Ejemplo de línea |
|---|---|---|
| `personajes_femeninos.txt` | Nombres de personajes femeninos | `Hermione` |
| `personajes_masculinos.txt` | Nombres de personajes masculinos | `Sherlock` |
| `apellidos.txt` | Apellidos de personajes, **sin espacios** | `VanHelsing` |
| `adjetivos.txt` | `masculino / femenino`, o una sola palabra si no cambia | `explorador / exploradora` · `veloz` |

**Cómo editarlos:**

1. Abre el fichero con el **Bloc de notas** (u otro editor de texto sencillo; no uses Word).
2. Escribe **una palabra por línea**. Puedes añadir, borrar o cambiar las que quieras.
3. Las líneas que empiezan por `#` son comentarios y las vacías se ignoran: úsalas para organizarte.
4. Usa solo letras (las tildes y la ñ están permitidas). No pongas números ni símbolos.
5. Al guardar, si el editor pregunta por la codificación, elige **UTF-8**.
6. **Reinicia la app** para que se apliquen los cambios: en local, para el servidor (Ctrl+C) y
   vuelve a arrancarlo; en Render, sube los cambios a GitHub y espera a que se vuelva a desplegar.

Si una línea está mal escrita (por ejemplo `listo / lista / listísimo`), la app no se rompe:
la ignora y deja un aviso en el registro (*log*). Los nombres de personaje se combinan con la
forma femenina o masculina del adjetivo según el fichero en que estén. Para evitar el nombre
real de un personaje (`HarryPotter`), en `app/alias.py` hay una tabla `APELLIDO_PROPIO`: si
añades un personaje cuyo apellido también está en la lista, añade ahí la pareja.

Por defecto **solo se aceptan alias generados**, aunque alguien manipule el formulario. Para
permitir alias libres, define la variable de entorno `ALIAS_LIBRE=1`. Esto no afecta a la
cuenta del profesorado (`ADMIN_ALIAS`), que no se registra por el formulario.

---

## 3. Funcionalidades

**Alumnado**
- Registro con alias, grupo y contraseña (se guarda cifrada con *hash*).
- **Descubrir**: tarjetas de libros que se arrastran a la derecha (me gusta) o a la izquierda
  (no me gusta). También funcionan los botones y las flechas del teclado.
- **Mis libros**: lista de valoraciones, con opción de cambiar de opinión.
- **Matches lectores** (antes «Afinidades»): porcentaje de afinidad con cada compañero/a y libros en común.

**Profesorado (admin)**
- Decide qué libros forman la biblioteca: los añade a mano o los **importa desde Open Library**.
- Puede activar u ocultar libros, editarlos o borrarlos.
- Panel con estadísticas, ranking de libros y **todas las conexiones** para formar grupos.
- Gestión del alumnado.

---

## 4. El algoritmo de afinidad

Está en [app/matching.py](app/matching.py). Usa el **índice de Jaccard**:

```
afinidad(A, B) = |libros que gustan a A y a B| / |libros que gustan a A o a B|
```

Hay **conexión** cuando la afinidad ≥ 30 % **y** hay al menos 2 libros en común. Ambos valores
se cambian en `app/__init__.py` (`UMBRAL_AFINIDAD`, `MIN_LIBROS_COMUNES`).

---

## 5. Contenidos que se trabajan

| Contenido | Dónde verlo en el código |
|---|---|
| Arquitectura cliente-servidor y MVC | Separación `models.py` / `templates/` / rutas |
| Bases de datos relacionales, claves foráneas, relación N:M | `models.py` |
| Consultas con `JOIN` y `GROUP BY` | `admin.py` → `panel()` y `usuarios()` |
| API REST y JSON | `main.py` (`/api/...`) y `descubrir.js` (`fetch`) |
| Consumir una API externa | `openlibrary.py` |
| Teoría de conjuntos aplicada | `matching.py` (∩, ∪, Jaccard) |
| Seguridad: *hash* de contraseñas, CSRF, control de acceso, XSS | `models.py`, `seguridad.py`, `textContent` en `descubrir.js` |
| Validación en servidor | `auth.py` → `registro()` |
| Diseño *responsive*, variables CSS, modo oscuro | `style.css` |
| Eventos del DOM (ratón, táctil, teclado) | `descubrir.js` |

---

## 6. Propuestas de actividades

### Para la parte técnica (programación / TIC / DAW)
1. **Lectura de código guiada:** sigue el recorrido de un voto desde el clic hasta la fila en la BD.
2. **Mejora el algoritmo:** que también cuenten los «no me gusta» en común y que los desacuerdos
   resten afinidad. Compara los resultados con los de Jaccard.
3. **Nuevo campo:** añade el *género* a `Libro` y un filtro por género en «Descubrir».
4. **Consultas SQL:** abre `instance/bookcrush.db` con *DB Browser for SQLite* y escribe consultas:
   el libro más polémico (los votos más repartidos), el alumno que más ha votado…
5. **Seguridad:** explica por qué `textContent` evita XSS y qué pasaría con `innerHTML`.
   Busca qué ataque evita el token CSRF.
6. **Ampliaciones:** reseñas cortas, grupos automáticos de 3–4 personas por afinidad, exportar
   las conexiones a CSV, tests con `pytest`.

### Para el resto de materias (Lengua, tutoría, biblioteca)
1. **Clubes de lectura:** usa las conexiones del panel para formar grupos que lean un libro
   que *aún no* hayan leído ninguno de sus miembros.
2. **Parejas de debate:** junta a quienes tienen **baja** afinidad para que defiendan
   cada uno su libro favorito.
3. **Recomendación cruzada:** cada persona recomienda a su conexión un libro que le gustó y que
   el otro no ha valorado.
4. **Estadística:** analiza el ranking del panel. ¿Qué libros gustan más en cada grupo?
5. **Reflexión digital:** ¿qué datos guarda la app? ¿Por qué solo un alias? ¿Cómo funcionan
   los algoritmos de recomendación de las plataformas que usamos a diario?

---

## 7. Privacidad y uso en el centro

- Solo se guardan un alias, el grupo, la contraseña cifrada y los votos.
- Se recomienda **no usar nombres reales completos**.
- El alumnado solo ve el alias, el grupo y los libros en común de sus conexiones.
- La app está pensada para ejecutarse **en local o en la red del centro**. Si se publicara en
  Internet, habría que cambiar `SECRET_KEY`, usar HTTPS y revisar la normativa de protección
  de datos (RGPD/LOPDGDD), especialmente con menores de 14 años.
