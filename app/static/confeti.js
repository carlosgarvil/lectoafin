/*
 * confeti.js — lluvia de confeti suave en la página de matches.
 *
 * Solo se lanza cuando hay MÁS matches que la última vez que el usuario abrió la página
 * (lo recordamos en localStorage, que vive en el navegador de cada persona).
 * Si el sistema pide "reducir movimiento", no se lanza.
 */
(function () {
  const lista = document.getElementById("matches");
  if (!lista) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const total = Number(lista.dataset.total) || 0;
  let anterior = 0;
  try { anterior = Number(localStorage.getItem("bookcrush-matches")) || 0; } catch (e) {}
  try { localStorage.setItem("bookcrush-matches", total); } catch (e) {}
  if (total <= anterior) return;

  const COLORES = ["#ff8fb8", "#b9a3ff", "#8ee6c0", "#ffc49b", "#ffe27a"];
  for (let i = 0; i < 70; i++) {
    const trozo = document.createElement("span");
    trozo.className = "confeti";
    trozo.style.left = Math.random() * 100 + "vw";
    trozo.style.background = COLORES[i % COLORES.length];
    trozo.style.setProperty("--dx", (Math.random() * 160 - 80) + "px");
    trozo.style.setProperty("--giro", (Math.random() * 720 - 360) + "deg");
    trozo.style.setProperty("--t", (1.8 + Math.random() * 1.6) + "s");
    trozo.style.animationDelay = Math.random() * 400 + "ms";
    document.body.append(trozo);
    trozo.addEventListener("animationend", () => trozo.remove());
  }
})();
