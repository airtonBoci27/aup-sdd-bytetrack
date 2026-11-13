// Arranque, vistas y sesión (RNF-02). Una sola vista visible a la vez.
import { leerSesion, registrarAvisos } from "./api.js";
import { cerrarSesion, iniciarLogin } from "./login.js";
import { iniciarRecepcion } from "./recepcion.js";

const VISTAS = {
  login: "vista-login",
  rechazo: "vista-rechazo-rol",
  recepcion: "vista-recepcion",
};
const ROL_RECEPCIONISTA = "RECEPCIONISTA";

export function mostrarVista(nombre, { mensajeLogin = "" } = {}) {
  for (const [clave, id] of Object.entries(VISTAS)) {
    document.getElementById(id).hidden = clave !== nombre;
  }
  document.querySelector("header.encabezado").hidden = nombre === "login";
  document.getElementById("sesion-etiqueta").hidden = nombre !== "recepcion";
  if (nombre === "login") {
    const error = document.getElementById("login-error");
    error.textContent = mensajeLogin;
    error.hidden = !mensajeLogin;
    document.getElementById("login-usuario").focus();
  }
}

function entrarSegunRol(rol) {
  if (rol === ROL_RECEPCIONISTA) {
    mostrarVista("recepcion");
    iniciarRecepcion();
  } else {
    mostrarVista("rechazo");
  }
}

function arrancar() {
  registrarAvisos({
    alExpirar: () => mostrarVista("login", { mensajeLogin: "Su sesión expiró" }),
    alRechazarRol: () => mostrarVista("rechazo"),
  });
  iniciarLogin({ alEntrar: entrarSegunRol });
  document.getElementById("cerrar-sesion").addEventListener("click", () => {
    cerrarSesion(() => mostrarVista("login"));
  });

  const { token, rol } = leerSesion();
  if (token && rol) entrarSegunRol(rol);
  else mostrarVista("login");
}

arrancar();
