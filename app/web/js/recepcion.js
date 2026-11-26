// Pantalla de recepción GUI-01 (CU-01, CU-05) y su integración con el modal GUI-02.
// Todo texto que llega del servidor se inserta con textContent (nunca como HTML).
import { llamar } from "./api.js";
import { abrirModal, cerrarModal, conectarModal } from "./modal_cliente.js";
import { mostrarToast } from "./ui_addons.js";

const PATRON_DNI = /^[0-9]{8}$/;
const MENSAJE_GENERAL = "No se pudo completar la operación. Intente de nuevo.";
const SIN_TECNICOS = "No hay técnicos disponibles";

const estado = {
  cliente: null, // cliente cargado (CU-05)
  equipos: [], // equipos del cliente cargado
  dniBuscado: null, // último DNI consultado (lo usa el modal GUI-02)
  tecnicos: [], // técnicos disponibles (RN-03)
  sinTecnicos: false,
  idOp: null, // ID de operación de la recepción en curso (RN-10, RNF-04)
  enviando: false, // hay un envío en curso (FR-021)
};

let conectado = false;
const el = (id) => document.getElementById(id);

// ---- ID de operación (RNF-04; research D11) ------------------------------------------

function nuevoIdOp() {
  const bytes = new Uint8Array(6);
  crypto.getRandomValues(bytes);
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("").toUpperCase();
  return `OP-${hex}`;
}

/** Muestra el ID de operación vigente en el pie de recepción. */
function mostrarIdOp() {
  el("id-operacion").textContent =
    `Referencia ${estado.idOp} · envío protegido contra duplicados`;
}

// ---- Mensajes ------------------------------------------------------------------------

function mostrarError(texto) {
  const caja = el("alerta-error");
  caja.textContent = texto || "";
  caja.hidden = !texto;
}

/** Alerta E01 (CU-01 curso 5a; RN-02): el número de serie ya tiene una orden activa. */
function mostrarE01(ordenActiva) {
  const caja = el("alerta-e01");
  caja.textContent = ordenActiva
    ? `Este número de serie ya posee la Orden activa N.° ${ordenActiva} en laboratorio`
    : "";
  caja.hidden = !ordenActiva;
  if (ordenActiva) caja.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function mostrarConfirmacion(texto) {
  const caja = el("confirmacion-orden");
  caja.textContent = texto || "";
  caja.hidden = !texto;
  const btnImp = el("btn-imprimir-orden");
  if (btnImp) btnImp.hidden = !texto;
  if (texto) caja.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function marcar(campo, invalido) {
  if (invalido) campo.setAttribute("aria-invalid", "true");
  else campo.removeAttribute("aria-invalid");
}

// ---- Cliente (CU-05; RF-01; RN-01) ---------------------------------------------------

function mostrarDniError(visible) {
  el("dni-error").hidden = !visible;
  marcar(el("dni"), visible);
}

function mostrarResumen(...nodos) {
  el("cliente-resumen").replaceChildren(...nodos);
}

function texto(contenido, clase) {
  const nodo = document.createElement(clase ? "span" : "small");
  nodo.textContent = contenido;
  if (clase) nodo.className = clase;
  return nodo;
}

function limpiarCliente() {
  estado.cliente = null;
  estado.equipos = [];
  mostrarResumen();
  el("registrar-cliente-abrir").disabled = true;
  poblarEquipos();
}

/** Carga un cliente (resultado de CU-05, o de CU-06 en los cursos 2a y 2b) y sus equipos. */
export function cargarCliente(datos) {
  estado.cliente = datos.cliente;
  estado.equipos = datos.equipos || [];
  estado.dniBuscado = datos.cliente.dni;
  el("dni").value = datos.cliente.dni;
  mostrarDniError(false);

  const nombre = document.createElement("strong");
  nombre.textContent = `${datos.cliente.nombres} ${datos.cliente.apellidos}`;
  mostrarResumen(
    nombre,
    document.createTextNode(` · ${datos.cliente.telefono} · `),
    texto("Cliente encontrado", "texto-ok"),
    document.createTextNode(" "),
    texto("(el registro solo se habilita si el DNI no existe)"),
  );
  el("registrar-cliente-abrir").disabled = true;
  poblarEquipos();
}

async function buscarCliente() {
  const dni = el("dni").value.trim();
  if (!PATRON_DNI.test(dni)) {
    limpiarCliente();
    mostrarDniError(true);
    return;
  }
  mostrarDniError(false);
  const boton = el("buscar-cliente");
  const textoOriginal = boton.textContent;
  boton.textContent = "Buscando...";
  boton.disabled = true;
  try {
    const respuesta = await llamar("GET", `/clientes/${dni}`);
    if (respuesta.terminada) return;
    if (respuesta.estado === 200) {
      cargarCliente(respuesta.datos);
    } else if (respuesta.estado === 404 && respuesta.datos?.codigo === "CLIENTE_NO_ENCONTRADO") {
      limpiarCliente();
      estado.dniBuscado = dni;
      mostrarResumen(document.createTextNode("Cliente no encontrado"));
      el("registrar-cliente-abrir").disabled = false; // CU-01 curso 2a
    } else if (respuesta.estado === 422) {
      limpiarCliente();
      mostrarDniError(true);
    } else {
      limpiarCliente();
      mostrarResumen(document.createTextNode(MENSAJE_GENERAL));
    }
  } catch (_) {
    limpiarCliente(); // sin conexión o respuesta inesperada
    mostrarResumen(document.createTextNode(MENSAJE_GENERAL));
  } finally {
    boton.textContent = textoOriginal;
    boton.disabled = false;
  }
}

// ---- Equipo (CU-01 paso 3; RF-01; RF-02) ---------------------------------------------

const CAMPOS_EQUIPO = ["equipo-tipo", "equipo-marca", "equipo-modelo", "equipo-serie"];

function opcion(valor, etiqueta) {
  const nodo = document.createElement("option");
  nodo.value = valor;
  nodo.textContent = etiqueta;
  return nodo;
}

/** Rellena el selector con los equipos del cliente más «Ingresar equipo nuevo». */
function poblarEquipos() {
  const selector = el("equipo-selector");
  selector.replaceChildren(opcion("", "Ingresar equipo nuevo"));
  for (const equipo of estado.equipos) {
    selector.appendChild(
      opcion(String(equipo.id), `${equipo.marca} ${equipo.modelo} · ${equipo.numero_serie}`),
    );
  }
  if (estado.equipos.length > 0) selector.value = String(estado.equipos[0].id);
  aplicarSeleccionEquipo();
}

/** Equipo existente: sus datos se muestran y no se editan. Equipo nuevo: campos editables. */
function aplicarSeleccionEquipo() {
  const id = el("equipo-selector").value;
  const equipo = estado.equipos.find((e) => String(e.id) === id);
  const valores = equipo
    ? [equipo.tipo, equipo.marca, equipo.modelo, equipo.numero_serie]
    : ["", "", "", ""];
  CAMPOS_EQUIPO.forEach((campo, i) => {
    const nodo = el(campo);
    nodo.value = valores[i];
    nodo.readOnly = Boolean(equipo);
    marcar(nodo, false);
  });
}

function accesorios() {
  const marcados = [];
  if (el("acc-cargador").checked) marcados.push("Cargador original");
  if (el("acc-funda").checked) marcados.push("Funda / maletín");
  return marcados.length ? marcados.join(", ") : null;
}

// ---- Orden de servicio (CU-01 pasos 4 a 6; RF-02; RN-03) ----------------------------

async function cargarCosto() {
  try {
    const respuesta = await llamar("GET", "/ordenes/costo-revision-inicial");
    if (respuesta.terminada) return;
    if (respuesta.estado === 200) {
      const monto = Number(respuesta.datos.costo_revision);
      el("costo-revision").value = `S/ ${Number.isFinite(monto) ? monto.toFixed(2) : respuesta.datos.costo_revision}`;
    }
  } catch (_) { /* el costo se vuelve a pedir al iniciar la siguiente recepción */ }
}

function actualizarBotonGenerar() {
  el("generar-orden").disabled = estado.enviando || estado.sinTecnicos;
}

async function cargarTecnicos() {
  const selector = el("tecnico");
  try {
    const respuesta = await llamar("GET", "/tecnicos/disponibles");
    if (respuesta.terminada) return;
    if (respuesta.estado !== 200) return;
    estado.tecnicos = respuesta.datos;
  } catch (_) {
    return; // se conserva la lista anterior
  }
  const anterior = selector.value;
  estado.sinTecnicos = estado.tecnicos.length === 0;
  selector.replaceChildren(opcion("", estado.sinTecnicos ? SIN_TECNICOS : "Seleccione un técnico"));
  for (const t of estado.tecnicos) {
    selector.appendChild(opcion(String(t.id), `${t.nombres} ${t.apellidos} (${t.cola} en cola)`));
  }
  if (anterior && estado.tecnicos.some((t) => String(t.id) === anterior)) selector.value = anterior;
  if (estado.sinTecnicos) mostrarError(SIN_TECNICOS);
  actualizarBotonGenerar();
}

/** Valida los campos obligatorios y marca los que faltan (CU-01 paso 5). Devuelve el primero. */
function validar() {
  const faltantes = [];
  const exigir = (campo, valor) => {
    const vacio = !String(valor).trim();
    marcar(campo, vacio);
    if (vacio) faltantes.push(campo);
  };
  if (!estado.cliente) {
    marcar(el("dni"), true);
    faltantes.push(el("dni"));
  }
  if (el("equipo-selector").value === "") {
    CAMPOS_EQUIPO.forEach((id) => exigir(el(id), el(id).value));
  }
  exigir(el("estado-fisico"), el("estado-fisico").value);
  exigir(el("falla"), el("falla").value);
  exigir(el("tecnico"), el("tecnico").value);
  return faltantes[0] || null;
}

function cuerpoOrden() {
  const equipoId = el("equipo-selector").value;
  const cuerpo = {
    id_op: estado.idOp,
    dni: estado.cliente.dni,
    accesorios: accesorios(),
    estado_fisico: el("estado-fisico").value.trim(),
    falla_reportada: el("falla").value.trim(),
    tecnico_id: Number(el("tecnico").value),
  };
  if (equipoId) {
    cuerpo.equipo_id = Number(equipoId);
  } else {
    cuerpo.equipo = {
      tipo: el("equipo-tipo").value.trim(),
      marca: el("equipo-marca").value.trim(),
      modelo: el("equipo-modelo").value.trim(),
      numero_serie: el("equipo-serie").value.trim(),
    };
  }
  return cuerpo;
}

async function generarOrden() {
  if (estado.enviando) return; // doble clic o reenvío mientras hay un envío en curso (FR-021)
  mostrarError("");
  mostrarE01("");
  mostrarConfirmacion("");
  const primerFaltante = validar();
  if (primerFaltante) {
    mostrarError(
      estado.cliente ? "Complete los campos obligatorios marcados." : "Busque o registre al cliente (DNI) antes de generar la orden.",
    );
    primerFaltante.focus();
    return;
  }

  estado.enviando = true;
  const boton = el("generar-orden");
  const textoOriginal = boton.textContent;
  boton.textContent = "Generando...";
  actualizarBotonGenerar();
  try {
    const respuesta = await llamar("POST", "/ordenes", { cuerpo: cuerpoOrden() });
    if (respuesta.terminada) return;
    if (respuesta.estado === 201 || respuesta.estado === 200) {
      const codigo = respuesta.datos.orden.codigo;
      reiniciar();
      mostrarConfirmacion(`N.° ${codigo} listo para imprimir · el técnico recibe +1 en su cola`);
      mostrarToast("Orden generada", `${codigo} registrada en estado RECEPCIONADO.`, "ok");
      await cargarTecnicos(); // la cola del técnico ya subió
    } else if (respuesta.estado === 409 && respuesta.datos?.codigo === "E01") {
      mostrarE01(respuesta.datos.detalle?.orden_activa); // bloquea la generación; no se crea la orden
      mostrarToast("Alerta E01", "El equipo ya posee una orden activa en laboratorio.", "error");
    } else if (respuesta.estado === 422) {
      mostrarError("Revise los datos ingresados.");
    } else {
      mostrarError(respuesta.datos?.mensaje || MENSAJE_GENERAL);
    }
  } catch (_) {
    mostrarError(MENSAJE_GENERAL); // sin conexión: se conserva lo ingresado y el ID de operación
  } finally {
    estado.enviando = false;
    boton.textContent = textoOriginal;
    actualizarBotonGenerar();
  }
}

// ---- Reinicio y arranque -------------------------------------------------------------

/** Deja GUI-01 en su estado inicial con un ID de operación nuevo (nueva recepción). */
function reiniciar() {
  estado.dniBuscado = null;
  estado.idOp = nuevoIdOp(); // solo cambia al iniciar, confirmar o cancelar; un fallo lo conserva
  mostrarIdOp();
  el("dni").value = "";
  mostrarDniError(false);
  limpiarCliente(); // también vacía el selector y los campos de equipo
  cerrarModal();
  el("estado-fisico").value = "";
  el("falla").value = "";
  el("tecnico").value = "";
  for (const id of ["estado-fisico", "falla", "tecnico"]) marcar(el(id), false);
  el("acc-cargador").checked = false;
  el("acc-funda").checked = false;
  mostrarError("");
  mostrarE01("");
  mostrarConfirmacion("");
  if (estado.sinTecnicos) mostrarError(SIN_TECNICOS);
}

function cancelar() {
  reiniciar();
}

/** Limpia los datos de recepción en memoria y en el DOM al cerrar o expirar la sesión (RNF-02). */
export function limpiarRecepcion() {
  reiniciar();
}

/** Se invoca cada vez que se muestra GUI-01 (tras iniciar sesión como Recepcionista). */
export function iniciarRecepcion() {
  if (!conectado) {
    el("buscar-cliente").addEventListener("click", buscarCliente);
    el("dni").addEventListener("input", () => {
      const soloDigitos = el("dni").value.replace(/\D/g, "").slice(0, 8);
      if (el("dni").value !== soloDigitos) el("dni").value = soloDigitos;
      mostrarDniError(false);
    });
    el("dni").addEventListener("keydown", (evento) => {
      if (evento.key === "Enter") buscarCliente();
    });
    el("equipo-selector").addEventListener("change", aplicarSeleccionEquipo);
    // E01 desaparece al cambiar de equipo o de datos (FR-023).
    for (const id of ["dni", "equipo-selector", ...CAMPOS_EQUIPO, "estado-fisico", "falla", "tecnico"]) {
      for (const tipo of ["input", "change"]) el(id).addEventListener(tipo, () => mostrarE01(""));
    }
    el("generar-orden").addEventListener("click", generarOrden);
    el("btn-imprimir-orden")?.addEventListener("click", () => window.print());
    // GUI-02: abrir con el DNI buscado y cargar el cliente que devuelve (cursos 2a y 2b).
    conectarModal({
      alCargar: (datos) => {
        cargarCliente(datos);
        if (!datos.equipos?.length) el("equipo-tipo").focus();
      },
    });
    el("registrar-cliente-abrir").addEventListener("click", () => abrirModal(estado.dniBuscado));
    el("cancelar-orden").addEventListener("click", cancelar);
    for (const id of [...CAMPOS_EQUIPO, "estado-fisico", "falla", "tecnico"]) {
      for (const tipo of ["input", "change"]) {
        el(id).addEventListener(tipo, () => marcar(el(id), false));
      }
    }
    conectado = true;
  }
  reiniciar();
  cargarCosto();
  cargarTecnicos();
}
