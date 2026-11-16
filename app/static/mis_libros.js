/*
 * mis_libros.js — animaciones al mover un libro entre "Mis crushes" y "Paso de ellos".
 *
 * El botón envía un formulario normal (POST) y la página se recarga. Para animarlo:
 *   1. Interceptamos el envío, animamos la tarjeta y DESPUÉS enviamos el formulario.
 *   2. Antes de enviar, guardamos el id del libro en sessionStorage. Al recargar,
 *      buscamos ese libro en su nueva lista y le hacemos una animación de "llegada".
 * Si JavaScript falla o no está, el formulario funciona igual (sin animación).
 */
const MENOS_MOVIMIENTO = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const CLAVE = "bookcrush-libro-movido";
const DURACION = 650;   // ms que dura la animación de salida

// Lanza unos emojis que salen volando desde un elemento
function lanzarEmojis(origen, emojis, cantidad, clase = "") {
  const caja = origen.getBoundingClientRect();
  for (let i = 0; i < cantidad; i++) {
    const e = document.createElement("span");
    e.className = "corazoncito " + clase;
    e.textContent = emojis[i % emojis.length];
    e.style.left = caja.left + caja.width / 2 - 12 + "px";
    e.style.top = caja.top + "px";
    e.style.setProperty("--dx", (Math.random() * 140 - 70) + "px");
    e.style.animationDelay = i * 50 + "ms";
    document.body.append(e);
    e.addEventListener("animationend", () => e.remove());
  }
}

document.querySelectorAll(".form-cambiar").forEach((form) => {
  form.addEventListener("submit", (evento) => {
    const tarjeta = form.closest(".mini");
    const boton = form.querySelector("button");
    try { sessionStorage.setItem(CLAVE, tarjeta.dataset.libro); } catch (e) {}
    if (MENOS_MOVIMIENTO) return;            // sin animación: se envía directamente

    evento.preventDefault();
    boton.disabled = true;                   // evita dobles clics
    if (form.dataset.efecto === "romper") {
      lanzarEmojis(boton, ["💔"], 1, "grande");
      tarjeta.classList.add("sale-roto");
    } else {
      lanzarEmojis(boton, ["💘", "💖", "✨"], 6);
      tarjeta.classList.add("sale-flechazo");
    }
    setTimeout(() => form.submit(), DURACION);   // form.submit() no vuelve a lanzar este evento
  });
});

// Al cargar: si venimos de mover un libro, lo resaltamos en su nueva lista
let movido = null;
try { movido = sessionStorage.getItem(CLAVE); sessionStorage.removeItem(CLAVE); } catch (e) {}
const llegada = movido && document.querySelector(`.mini[data-libro="${CSS.escape(movido)}"]`);
if (llegada) {
  llegada.scrollIntoView({ block: "center", behavior: MENOS_MOVIMIENTO ? "auto" : "smooth" });
  llegada.classList.add("llega");
  llegada.addEventListener("animationend", () => llegada.classList.remove("llega"), { once: true });
}
