// Arranque, navegación por rol y sesión (RNF-02). Una sola vista visible a la vez.
import { leerSesion, registrarAvisos } from "./api.js";
import { cerrarSesion, iniciarLogin } from "./login.js";
import { iniciarRecepcion, limpiarRecepcion } from "./recepcion.js";
import {
  cargarAlmacen,
  cargarClientes,
  cargarPanel,
  iniciarTaller,
  prepararCobro,
  prepararDecision,
  prepararDiagnostico,
  prepararFinalizar,
} from "./taller.js";
import { iniciarModalDetalle, iniciarTema } from "./ui_addons.js";

const VISTAS = {
  login: "vista-login",
  rechazo: "vista-rechazo-rol",
  panel: "vista-panel",
  recepcion: "vista-recepcion",
  clientes: "vista-clientes",
  diagnostico: "vista-diagnostico",
  decision: "vista-decision",
  finalizar: "vista-finalizar",
  cobro: "vista-cobro",
  almacen: "vista-almacen",
};

const TABS = {
  panel: "tab-panel",
  recepcion: "tab-recepcion",
  clientes: "tab-clientes",
  diagnostico: "tab-diagnostico",
  decision: "tab-decision",
  finalizar: "tab-finalizar",
  cobro: "tab-cobro",
  almacen: "tab-almacen",
};

const TABS_POR_ROL = {
  RECEPCIONISTA: ["panel", "recepcion", "clientes", "decision", "cobro", "almacen"],
  TECNICO: ["panel", "diagnostico", "finalizar", "almacen"],
};

let rolActivo = null;

export function mostrarVista(nombre, { mensajeLogin = "" } = {}) {
  for (const [clave, id] of Object.entries(VISTAS)) {
    document.getElementById(id).hidden = clave !== nombre;
  }
  const enLogin = nombre === "login";
  const sinMenu = enLogin || nombre === "rechazo";
  document.querySelector("header.encabezado").hidden = enLogin;
  document.getElementById("nav-principal").hidden = sinMenu;
  document.getElementById("sesion-etiqueta").hidden = sinMenu;
  document.getElementById("app-shell").classList.toggle("app-shell--login", sinMenu);

  for (const [clave, id] of Object.entries(TABS)) {
    document.getElementById(id).classList.toggle("nav-tab--activa", clave === nombre);
  }

  if (enLogin) {
    const error = document.getElementById("login-error");
    error.textContent = mensajeLogin;
    error.hidden = !mensajeLogin;
    document.getElementById("login-usuario").focus();
  }
}

function irAApartado(nombre) {
  mostrarVista(nombre);
  if (nombre === "panel") cargarPanel(1);
  if (nombre === "recepcion") iniciarRecepcion();
  if (nombre === "clientes") cargarClientes(1);
  if (nombre === "diagnostico") prepararDiagnostico();
  if (nombre === "decision") prepararDecision();
  if (nombre === "finalizar") prepararFinalizar();
  if (nombre === "cobro") prepararCobro();
  if (nombre === "almacen") cargarAlmacen(1);
}

function configurarNavegacionPorRol(rol) {
  const permitidas = new Set(TABS_POR_ROL[rol] || []);
  for (const [clave, id] of Object.entries(TABS)) {
    document.getElementById(id).hidden = !permitidas.has(clave);
  }
  document.getElementById("sesion-etiqueta").textContent =
    rol === "RECEPCIONISTA"
      ? "Recepcionista · sesión activa"
      : "Técnico de laboratorio · sesión activa";
}

function entrarSegunRol(rol) {
  rolActivo = rol;
  if (!TABS_POR_ROL[rol]) {
    mostrarVista("rechazo");
    return;
  }
  configurarNavegacionPorRol(rol);
  iniciarTaller({ rol, irA: irAApartado });
  irAApartado("panel");
}

function arrancar() {
  iniciarTema();
  iniciarModalDetalle();
  registrarAvisos({
    alExpirar: () => {
      rolActivo = null;
      limpiarRecepcion();
      mostrarVista("login", { mensajeLogin: "Su sesión expiró" });
    },
    alRechazarRol: () => {
      mostrarVista("rechazo");
    },
  });

  iniciarLogin({ alEntrar: entrarSegunRol });

  for (const [clave, id] of Object.entries(TABS)) {
    document.getElementById(id).addEventListener("click", () => {
      if (rolActivo && TABS_POR_ROL[rolActivo]?.includes(clave)) {
        irAApartado(clave);
      }
    });
  }

  document.getElementById("cerrar-sesion").addEventListener("click", () => {
    cerrarSesion(() => {
      rolActivo = null;
      limpiarRecepcion();
      mostrarVista("login");
    });
  });

  const { token, rol } = leerSesion();
  if (token && rol) entrarSegunRol(rol);
  else mostrarVista("login");
}

arrancar();
