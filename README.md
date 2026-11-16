# 📚 Lectoafín

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
│ BASE DE DATOS: SQLite (instance/lectoafin.db) │
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
└── app/
    ├── __init__.py        ← crea la app y configura (umbral de afinidad, etc.)
    ├── models.py          ← tablas: Usuario, Libro, Voto
    ├── auth.py            ← registro / login / logout
    ├── main.py            ← páginas y API del alumnado
    ├── admin.py           ← panel del profesorado
    ├── matching.py        ← ⭐ algoritmo de afinidad (índice de Jaccard)
    ├── openlibrary.py     ← cliente de la API de Open Library
    ├── seguridad.py       ← protección CSRF y control de acceso
    ├── cli.py             ← comandos: crear-admin, datos-ejemplo
    ├── templates/         ← HTML (Jinja2)
    └── static/            ← style.css, descubrir.js
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
* Para empezar de cero, borra `instance/lectoafin.db`.
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

Limitaciones del plan gratuito: la web se «duerme» tras 15 minutos sin visitas (la primera
carga tarda en torno a un minuto) y la base de datos gratuita caduca a los 30 días.

---

## 3. Funcionalidades

**Alumnado**
- Registro con alias, grupo y contraseña (se guarda cifrada con *hash*).
- **Descubrir**: tarjetas de libros que se arrastran a la derecha (me gusta) o a la izquierda
  (no me gusta). También funcionan los botones y las flechas del teclado.
- **Mis libros**: lista de valoraciones, con opción de cambiar de opinión.
- **Afinidades**: porcentaje de afinidad con cada compañero/a y libros en común.

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
4. **Consultas SQL:** abre `instance/lectoafin.db` con *DB Browser for SQLite* y escribe consultas:
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
