/*
 * descubrir.js — FRONT-END de la pantalla de valoración.
 *
 * Flujo:
 *   1. Pedimos al servidor el siguiente libro:   GET  /api/siguiente
 *   2. Lo pintamos como una tarjeta.
 *   3. Al votar enviamos el voto:                POST /api/votar  {libro_id, me_gusta}
 *      y el servidor nos responde con el siguiente libro.
 *
 * Así el navegador y el servidor solo se comunican con JSON (como una API REST).
 */

const mazo = document.getElementById("mazo");
const contador = document.getElementById("contador");
const botones = document.getElementById("botones");
const CSRF = document.querySelector('meta[name="csrf-token"]').content;

let libroActual = null;
let ocupado = false;   // evita votos dobles mientras esperamos al servidor

// ---------------------------------------------------------------- Comunicación con el back

async function pedirSiguiente() {
  const respuesta = await fetch("/api/siguiente");
  mostrar(await respuesta.json());
}

async function votar(meGusta) {
  if (!libroActual || ocupado) return;
  ocupado = true;
  const tarjeta = mazo.querySelector(".tarjeta-libro");
  tarjeta.classList.add(meGusta ? "sale-derecha" : "sale-izquierda");

  try {
    const respuesta = await fetch("/api/votar", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": CSRF },
      body: JSON.stringify({ libro_id: libroActual.id, me_gusta: meGusta }),
    });
    if (!respuesta.ok) throw new Error("Error " + respuesta.status);
    const datos = await respuesta.json();
    setTimeout(() => mostrar(datos), 250);   // esperamos a que acabe la animación
  } catch (err) {
    alert("No se pudo guardar el voto. Revisa la conexión.");
    tarjeta.classList.remove("sale-derecha", "sale-izquierda");
  } finally {
    ocupado = false;
  }
}

// ---------------------------------------------------------------- Pintar en pantalla

function crear(etiqueta, clase, texto) {
  const el = document.createElement(etiqueta);
  if (clase) el.className = clase;
  if (texto) el.textContent = texto;   // textContent (no innerHTML): evita inyección de HTML
  return el;
}

function mostrar({ libro, pendientes }) {
  libroActual = libro;
  mazo.replaceChildren();

  if (!libro) {
    contador.textContent = "¡Has valorado todos los libros!";
    botones.hidden = true;
    const fin = crear("div", "tarjeta fin");
    fin.append(crear("p", "", "📚 No quedan libros por valorar."));
    const enlace = crear("a", "boton", "Ver mis afinidades");
    enlace.href = "/afinidades";
    fin.append(enlace);
    mazo.append(fin);
    return;
  }

  botones.hidden = false;
  contador.textContent = `Quedan ${pendientes} libro${pendientes === 1 ? "" : "s"} por valorar`;

  const tarjeta = crear("article", "tarjeta-libro");
  if (libro.portada_url) {
    const img = crear("img", "portada");
    img.src = libro.portada_url;
    img.alt = "Portada de " + libro.titulo;
    img.draggable = false;
    tarjeta.append(img);
  } else {
    const lomo = crear("div", "portada sin-portada");
    lomo.style.setProperty("--tono", (libro.id * 47) % 360);
    lomo.append(crear("span", "", libro.titulo));
    tarjeta.append(lomo);
  }

  const info = crear("div", "info");
  info.append(crear("h2", "", libro.titulo));
  info.append(crear("p", "autor", libro.autor + (libro.anio ? ` · ${libro.anio}` : "")));
  if (libro.sinopsis) info.append(crear("p", "sinopsis", libro.sinopsis));
  tarjeta.append(info);

  tarjeta.append(crear("div", "sello sello-si", "ME GUSTA"));
  tarjeta.append(crear("div", "sello sello-no", "NO"));

  hacerArrastrable(tarjeta);
  mazo.append(tarjeta);
}

// ---------------------------------------------------------------- Arrastrar (ratón y táctil)

function hacerArrastrable(tarjeta) {
  let inicioX = null, dx = 0;
  const UMBRAL = 100; // píxeles necesarios para que cuente como voto

  tarjeta.addEventListener("pointerdown", (e) => {
    inicioX = e.clientX;
    tarjeta.setPointerCapture(e.pointerId);
    tarjeta.style.transition = "none";
  });

  tarjeta.addEventListener("pointermove", (e) => {
    if (inicioX === null) return;
    dx = e.clientX - inicioX;
    tarjeta.style.transform = `translateX(${dx}px) rotate(${dx / 15}deg)`;
    tarjeta.style.setProperty("--op-si", Math.max(0, dx / UMBRAL));
    tarjeta.style.setProperty("--op-no", Math.max(0, -dx / UMBRAL));
  });

  const soltar = () => {
    if (inicioX === null) return;
    inicioX = null;
    tarjeta.style.transition = "";
    tarjeta.style.transform = "";
    tarjeta.style.setProperty("--op-si", 0);
    tarjeta.style.setProperty("--op-no", 0);
    if (dx > UMBRAL) votar(true);
    else if (dx < -UMBRAL) votar(false);
    dx = 0;
  };
  tarjeta.addEventListener("pointerup", soltar);
  tarjeta.addEventListener("pointercancel", soltar);
}

// ---------------------------------------------------------------- Botones y teclado

document.getElementById("btn-si").addEventListener("click", () => votar(true));
document.getElementById("btn-no").addEventListener("click", () => votar(false));
document.addEventListener("keydown", (e) => {
  if (e.key === "ArrowRight") votar(true);
  if (e.key === "ArrowLeft") votar(false);
});

pedirSiguiente();
