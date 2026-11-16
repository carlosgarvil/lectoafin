/*
 * alias.js — botón 🎲 "Generar otro" del formulario de registro.
 *
 * Pide un alias nuevo al servidor (GET /api/alias-aleatorio -> {"alias": "..."})
 * y lo escribe en el campo, que es de solo lectura.
 * El servidor vuelve a comprobar el alias al registrarse: el navegador no es de fiar.
 */
const campoAlias = document.getElementById("alias");
const botonOtro = document.getElementById("otro-alias");
const dado = botonOtro.querySelector(".dado");

async function pedirAlias() {
  botonOtro.disabled = true;
  dado.classList.remove("girando");
  void dado.offsetWidth;            // reinicia la animación del dado
  dado.classList.add("girando");
  try {
    const respuesta = await fetch("/api/alias-aleatorio");
    const datos = await respuesta.json();
    if (!respuesta.ok || !datos.alias) throw new Error(datos.error || respuesta.status);
    campoAlias.value = datos.alias;
  } catch (err) {
    alert("No se pudo generar un alias nuevo. Inténtalo otra vez.");
  } finally {
    botonOtro.disabled = false;
  }
}

botonOtro.addEventListener("click", pedirAlias);

// Si por algún motivo la página llegó sin alias, pedimos uno al cargar
if (!campoAlias.value) pedirAlias();
