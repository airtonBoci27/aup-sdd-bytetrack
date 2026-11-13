// Modal GUI-02 «Registrar nuevo cliente» (CU-06; CU-01 cursos 2a y 2b; RF-01; RN-01).
// Todo texto que llega del servidor se inserta con textContent.
import { llamar } from "./api.js";

const PATRON_DNI = /^[0-9]{8}$/;
const MENSAJE_GENERAL = "No se pudo completar la operación. Intente de nuevo.";
const AVISO_DNI_REGISTRADO = "El DNI ya está registrado";

const el = (id) => document.getElementById(id);
const CAMPOS = ["cli-dni", "cli-nombres", "cli-apellidos", "cli-telefono", "cli-correo"];
const ETIQUETAS = { "cli-dni": "DNI", "cli-nombres": "Nombres", "cli-apellidos": "Apellidos", "cli-telefono": "Teléfono" };

let alCargarCliente = () => {};
let conectado = false;
let enviando = false;

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

export function cerrarModal() {
  el("modal-cliente").hidden = true;
}

/** Abre el modal con el DNI buscado precargado (FR-028). */
export function abrirModal(dni) {
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

/** Valida los obligatorios y el DNI de 8 dígitos; marca y lista cada campo a corregir (FR-029). */
function validar() {
  const incorrectos = [];
  const exigir = (id, valido) => {
    marcar(el(id), !valido);
    if (!valido) incorrectos.push(id);
  };
  exigir("cli-dni", PATRON_DNI.test(el("cli-dni").value.trim()));
  for (const id of ["cli-nombres", "cli-apellidos", "cli-telefono"]) exigir(id, el(id).value.trim() !== "");
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
  el("cli-guardar").disabled = true;
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
    el("cli-guardar").disabled = bloquearGuardar;
  }
}

/** Conecta los botones del modal una sola vez. `alCargar(datos)` carga el cliente en GUI-01. */
export function conectarModal({ alCargar }) {
  alCargarCliente = alCargar;
  if (conectado) return;
  el("cli-guardar").addEventListener("click", guardar);
  el("cli-cancelar").addEventListener("click", cerrarModal); // cierra sin registrar (FR-032)
  for (const id of CAMPOS) {
    el(id).addEventListener("input", () => marcar(el(id), false));
  }
  el("cli-dni").addEventListener("input", () => {
    mostrarAviso(""); // al editar el DNI se vuelve a permitir guardar
    el("cli-guardar").disabled = enviando;
  });
  conectado = true;
}
