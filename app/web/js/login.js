// Inicio y cierre de sesión (RNF-02; precondición de CU-01).
import { guardarSesion, llamar, borrarSesion } from "./api.js";

const MENSAJE_GENERAL = "No se pudo completar la operación. Intente de nuevo.";

function mostrarError(texto) {
  const caja = document.getElementById("login-error");
  caja.textContent = texto;
  caja.hidden = !texto;
}

/** Conecta el formulario de inicio de sesión. `alEntrar(rol)` decide qué vista mostrar. */
export function iniciarLogin({ alEntrar }) {
  const formulario = document.querySelector("#vista-login form");
  const usuario = document.getElementById("login-usuario");
  const clave = document.getElementById("login-clave");
  const boton = document.getElementById("login-entrar");

  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    mostrarError("");
    const nombre = usuario.value.trim();
    usuario.removeAttribute("aria-invalid");
    clave.removeAttribute("aria-invalid");
    if (!nombre || !clave.value) {
      if (!nombre) usuario.setAttribute("aria-invalid", "true");
      if (!clave.value) clave.setAttribute("aria-invalid", "true");
      mostrarError("Ingrese su usuario y su contraseña");
      return;
    }
    boton.disabled = true;
    try {
      const { estado, datos } = await llamar("POST", "/auth/token", {
        formulario: { username: nombre, password: clave.value },
        sinAvisos: true,
      });
      if (estado === 200 && datos && datos.access_token) {
        guardarSesion(datos.access_token, datos.rol);
        usuario.value = "";
        alEntrar(datos.rol);
      } else if (estado === 401) {
        mostrarError((datos && datos.mensaje) || "Usuario o contraseña incorrectos");
      } else {
        mostrarError(MENSAJE_GENERAL);
      }
    } catch (_) {
      mostrarError(MENSAJE_GENERAL); // sin conexión o respuesta inesperada
    } finally {
      clave.value = "";
      boton.disabled = false;
    }
  });
}

/** Cierra la sesión: invalida el token en el servidor y vuelve al inicio aunque la llamada falle. */
export async function cerrarSesion(alTerminar) {
  try {
    await llamar("POST", "/auth/logout", { sinAvisos: true });
  } catch (_) { /* la interfaz vuelve al inicio de sesión de todos modos (D3) */ }
  borrarSesion();
  alTerminar();
}
