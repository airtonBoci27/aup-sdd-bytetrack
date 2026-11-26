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
  const toggleClave = document.getElementById("login-ver-clave");
  const avisoMayus = document.getElementById("login-mayus");

  toggleClave.addEventListener("click", () => {
    const mostrar = clave.type === "password";
    clave.type = mostrar ? "text" : "password";
    toggleClave.textContent = mostrar ? "Ocultar" : "Mostrar";
    toggleClave.setAttribute("aria-pressed", String(mostrar));
    clave.focus();
  });

  const revisarMayus = (evento) => {
    if (typeof evento.getModifierState === "function") {
      avisoMayus.hidden = !evento.getModifierState("CapsLock");
    }
  };
  clave.addEventListener("keydown", revisarMayus);
  clave.addEventListener("keyup", revisarMayus);
  clave.addEventListener("blur", () => { avisoMayus.hidden = true; });

  for (const campo of [usuario, clave]) {
    campo.addEventListener("input", () => {
      campo.removeAttribute("aria-invalid");
      mostrarError("");
    });
  }

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
    const textoOriginal = boton.textContent;
    boton.textContent = "Iniciando sesión...";
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
      clave.type = "password";
      toggleClave.textContent = "Mostrar";
      toggleClave.setAttribute("aria-pressed", "false");
      avisoMayus.hidden = true;
      boton.textContent = textoOriginal;
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
