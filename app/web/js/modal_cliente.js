// Modal GUI-02 «Registrar nuevo cliente» (CU-06; CU-01 cursos 2a y 2b; RF-01; RN-01).
// Todo texto que llega del servidor se inserta con textContent.
import { llamar } from "./api.js";

const PATRON_DNI = /^[0-9]{8}$/;
const PATRON_CORREO = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const MENSAJE_GENERAL = "No se pudo completar la operación. Intente de nuevo.";
const AVISO_DNI_REGISTRADO = "El DNI ya está registrado";

const el = (id) => document.getElementById(id);
const CAMPOS = ["cli-dni", "cli-nombres", "cli-apellidos", "cli-telefono", "cli-correo"];
const ETIQUETAS = {
  "cli-dni": "DNI",
  "cli-nombres": "Nombres",
  "cli-apellidos": "Apellidos",
  "cli-telefono": "Teléfono",
  "cli-correo": "Correo",
};

let alCargarCliente = () => {};
let conectado = false;
let enviando = false;
let elementoPrevio = null;

function marcar(campo, invalido) {
  if (invalido) campo.setAttribute("aria-invalid", "true");
  else campo.removeAttribute("aria-invalid");
}

function mostrarError(texto) {
  el("cli-error").textContent = texto || "";
  el("cli-error").hidden = !texto;
}

function mostrarAviso(texto) {
  el("cli-aviso").textContent = texto || "";
  el("cli-aviso").hidden = !texto;
}

export function cerrarModal({ restaurarFoco = false } = {}) {
  const modal = el("modal-cliente");
  if (modal.hidden) return;
  modal.hidden = true;
  if (restaurarFoco && elementoPrevio && !elementoPrevio.disabled) {
    elementoPrevio.focus();
  }
  elementoPrevio = null;
}

/** Abre el modal con el DNI buscado precargado (FR-028). */
export function abrirModal(dni) {
  elementoPrevio = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  for (const id of CAMPOS) {
    el(id).value = "";
    marcar(el(id), false);
  }
  el("cli-dni").value = dni || "";
  mostrarError("");
  mostrarAviso("");
  el("cli-guardar").disabled = false;
  el("modal-cliente").hidden = false;
  el("cli-nombres").focus();
}

/** Valida los obligatorios, el DNI de 8 dígitos y el correo opcional; marca y lista cada campo a corregir (FR-029). */
function validar() {
  const incorrectos = [];
  const exigir = (id, valido) => {
    marcar(el(id), !valido);
    if (!valido) incorrectos.push(id);
  };
  exigir("cli-dni", PATRON_DNI.test(el("cli-dni").value.trim()));
  for (const id of ["cli-nombres", "cli-apellidos", "cli-telefono"]) exigir(id, el(id).value.trim() !== "");
  const correo = el("cli-correo").value.trim();
  exigir("cli-correo", correo === "" || PATRON_CORREO.test(correo));
  return incorrectos;
}

async function guardar() {
  if (enviando) return;
  mostrarError("");
  mostrarAviso("");
  const incorrectos = validar();
  if (incorrectos.length) {
    mostrarError(`Corrija los campos marcados: ${incorrectos.map((id) => ETIQUETAS[id]).join(", ")}.`);
    el(incorrectos[0]).focus();
    return;
  }
  enviando = true;
  const boton = el("cli-guardar");
  const textoOriginal = boton.textContent;
  boton.textContent = "Guardando...";
  boton.disabled = true;
  let bloquearGuardar = false;
  try {
    const correo = el("cli-correo").value.trim();
    const respuesta = await llamar("POST", "/clientes", {
      cuerpo: {
        dni: el("cli-dni").value.trim(),
        nombres: el("cli-nombres").value.trim(),
        apellidos: el("cli-apellidos").value.trim(),
        telefono: el("cli-telefono").value.trim(),
        correo: correo || null,
      },
    });
    if (respuesta.terminada) return;
    if (respuesta.estado === 201) {
      cerrarModal(); // CU-01 curso 2a: vuelve a GUI-01 con el cliente cargado
      alCargarCliente(respuesta.datos);
    } else if (respuesta.estado === 200 && respuesta.datos?.ya_registrado) {
      // CU-01 curso 2b: se avisa, se carga el cliente existente y no se duplica.
      mostrarAviso(respuesta.datos.aviso || AVISO_DNI_REGISTRADO);
      alCargarCliente(respuesta.datos);
      bloquearGuardar = true; // hasta que se edite el DNI
    } else if (respuesta.estado === 422) {
      mostrarError("Revise los datos ingresados.");
    } else {
      mostrarError(MENSAJE_GENERAL);
    }
  } catch (_) {
    mostrarError(MENSAJE_GENERAL); // sin conexión: no se registra nada
  } finally {
    enviando = false;
    boton.textContent = textoOriginal;
    boton.disabled = bloquearGuardar;
  }
}

/** Conecta los botones del modal una sola vez. `alCargar(datos)` carga el cliente en GUI-01. */
export function conectarModal({ alCargar }) {
  alCargarCliente = alCargar;
  if (conectado) return;
  el("cli-guardar").addEventListener("click", guardar);
  el("cli-cancelar").addEventListener("click", () => cerrarModal({ restaurarFoco: true })); // cierra sin registrar (FR-032)
  el("modal-cliente").addEventListener("click", (evento) => {
    if (evento.target === el("modal-cliente")) cerrarModal({ restaurarFoco: true });
  });
  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && !el("modal-cliente").hidden) {
      cerrarModal({ restaurarFoco: true });
    }
  });
  for (const id of CAMPOS) {
    el(id).addEventListener("input", () => marcar(el(id), false));
    el(id).addEventListener("keydown", (evento) => {
      if (evento.key === "Enter") {
        evento.preventDefault();
        guardar();
      }
    });
  }
  el("cli-dni").addEventListener("input", () => {
    const soloDigitos = el("cli-dni").value.replace(/\D/g, "").slice(0, 8);
    if (el("cli-dni").value !== soloDigitos) el("cli-dni").value = soloDigitos;
    mostrarAviso(""); // al editar el DNI se vuelve a permitir guardar
    el("cli-guardar").disabled = enviando;
  });
  conectado = true;
}
