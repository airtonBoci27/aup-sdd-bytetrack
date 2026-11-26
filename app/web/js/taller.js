// Apartados del ciclo completo del taller: Panel/KPIs (paginado), GUI-03 (CU-02/CU-07),
// GUI-04 (CU-03), GUI-05 (CU-08) y GUI-06 (CU-04). Todo texto se inserta con textContent / DOM.
import { llamar } from "./api.js";
import { cargarCliente } from "./recepcion.js";
import { abrirDetalleOrden, mostrarToast, renderGraficoDistribucion } from "./ui_addons.js";

const el = (id) => document.getElementById(id);
const MENSAJE_GENERAL = "No se pudo completar la operación. Intente de nuevo.";

let conectado = false;
let navegarA = () => {};
let rolActual = null;

const estadoPanel = { page: 1, totalPages: 1, ultimasOrdenes: [] };
const estadoClientes = { page: 1, totalPages: 1 };
const estadoAlmacen = { page: 1, totalPages: 1 };
const estadoDiag = {
  orden: null,
  repPage: 1,
  repTotalPages: 1,
  cotizacion: new Map(), // repuesto_id -> { repuesto, cantidad }
  idOp: null,
};
const estadoDec = { orden: null, idOp: null };
const estadoFin = { orden: null, idOp: null };
const estadoCob = { orden: null, idOp: null };

function nuevoIdOp(prefijo = "OP") {
  const bytes = new Uint8Array(6);
  crypto.getRandomValues(bytes);
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("").toUpperCase();
  return `${prefijo}-${hex}`;
}

function mostrarMsg(id, texto) {
  const caja = el(id);
  caja.textContent = texto || "";
  caja.hidden = !texto;
  if (texto) caja.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function badgeEstado(estado) {
  const span = document.createElement("span");
  span.className = `badge badge--${estado.toLowerCase()}`;
  span.textContent = estado;
  return span;
}

function celda(contenido) {
  const td = document.createElement("td");
  if (contenido instanceof Node) td.appendChild(contenido);
  else td.textContent = contenido;
  return td;
}

function montoOrden(orden) {
  if (orden.comprobante) return `S/ ${Number(orden.comprobante.monto_total).toFixed(2)}`;
  if (orden.diagnostico) return `S/ ${Number(orden.diagnostico.total_presupuesto).toFixed(2)}`;
  return `S/ ${Number(orden.costo_revision).toFixed(2)}`;
}

// ---- Panel Operativo y Tabla Paginada de Órdenes -------------------------------------

function actualizarBadge(id, cantidad) {
  const nodo = el(id);
  if (!nodo) return;
  const n = Number(cantidad) || 0;
  nodo.textContent = String(n);
  nodo.hidden = n <= 0;
}

function renderTecnicosCarga(tecnicos) {
  const grid = el("tecnicos-grid");
  if (!grid) return;
  grid.replaceChildren();
  const maxCola = Math.max(4, ...tecnicos.map((t) => t.cola || 0));
  for (const t of tecnicos) {
    const card = document.createElement("div");
    card.className = "tecnico-card";

    const top = document.createElement("div");
    top.className = "tecnico-card__top";
    const nombre = document.createElement("strong");
    nombre.textContent = `${t.nombres} ${t.apellidos}`;
    const estadoBadge = document.createElement("span");
    estadoBadge.className = t.disponible ? "badge badge--listo" : "badge badge--rechazado";
    estadoBadge.textContent = t.disponible ? "Disponible" : "No disponible";
    top.append(nombre, estadoBadge);

    const barra = document.createElement("div");
    barra.className = "tecnico-card__barra";
    const fill = document.createElement("div");
    fill.className = `tecnico-card__fill${t.disponible ? "" : " tecnico-card__fill--ocupado"}`;
    fill.style.width = `${Math.min(100, Math.round((t.cola / maxCola) * 100))}%`;
    barra.appendChild(fill);

    const nota = document.createElement("small");
    nota.className = "nota";
    nota.textContent = `${t.cola} orden(es) en cola`;

    card.append(top, barra, nota);
    grid.appendChild(card);
  }
}

export async function cargarPanel(pagina = estadoPanel.page) {
  estadoPanel.page = pagina;
  const q = el("filtro-ordenes-q").value.trim();
  const est = el("filtro-ordenes-estado").value;
  const params = new URLSearchParams({ page: String(pagina), limit: "6" });
  if (q) params.set("q", q);
  if (est) params.set("estado", est);

  try {
    const [resResumen, resLista, resTecnicos] = await Promise.all([
      llamar("GET", "/ordenes/resumen"),
      llamar("GET", `/ordenes?${params.toString()}`),
      llamar("GET", "/tecnicos/resumen"),
    ]);
    if (resResumen.terminada || resLista.terminada || resTecnicos.terminada) return;
    if (resResumen.estado === 200) {
      const p = resResumen.datos.por_estado;
      el("kpi-recepcionado").textContent = String(p.RECEPCIONADO ?? 0);
      el("kpi-presupuestado").textContent = String(p.PRESUPUESTADO ?? 0);
      el("kpi-aprobado").textContent = String(p.APROBADO ?? 0);
      el("kpi-listo").textContent = String(p.LISTO ?? 0);
      el("kpi-entregado").textContent = String(p.ENTREGADO ?? 0);
      el("kpi-stock-bajo").textContent = String(resResumen.datos.repuestos_stock_bajo ?? 0);
      renderGraficoDistribucion(p, resResumen.datos.total_ordenes);

      // Badges numéricos en tiempo real en la barra lateral
      actualizarBadge("badge-diagnostico", p.RECEPCIONADO ?? 0);
      actualizarBadge("badge-decision", p.PRESUPUESTADO ?? 0);
      actualizarBadge("badge-finalizar", p.APROBADO ?? 0);
      actualizarBadge("badge-cobro", (p.LISTO ?? 0) + (p.RECHAZADO ?? 0));
      actualizarBadge("badge-almacen", resResumen.datos.repuestos_stock_bajo ?? 0);
    }
    if (resLista.estado === 200) {
      estadoPanel.ultimasOrdenes = resLista.datos.items;
      renderTablaOrdenes(resLista.datos);
    }
    if (resTecnicos.estado === 200) {
      renderTecnicosCarga(resTecnicos.datos);
    }
  } catch (_) { /* sin conexión */ }
}

function botonAccionOrden(orden) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "boton boton--chico";

  if (rolActual === "RECEPCIONISTA" && orden.estado === "PRESUPUESTADO") {
    btn.textContent = "Registrar decisión";
    btn.addEventListener("click", () => {
      el("dec-orden-codigo").value = orden.codigo;
      navegarA("decision");
      cargarOrdenDecision();
    });
    return btn;
  }
  if (rolActual === "RECEPCIONISTA" && orden.estado === "LISTO") {
    btn.textContent = "Cobrar y entregar";
    btn.addEventListener("click", () => {
      el("cob-orden-codigo").value = orden.codigo;
      navegarA("cobro");
      cargarOrdenCobro();
    });
    return btn;
  }
  if (rolActual === "RECEPCIONISTA" && orden.estado === "RECHAZADO") {
    btn.textContent = "Devolver equipo";
    btn.addEventListener("click", () => {
      el("cob-orden-codigo").value = orden.codigo;
      navegarA("cobro");
      cargarOrdenCobro();
    });
    return btn;
  }
  if (rolActual === "TECNICO" && orden.estado === "RECEPCIONADO") {
    btn.textContent = "Diagnosticar";
    btn.addEventListener("click", () => {
      el("diag-orden-codigo").value = orden.codigo;
      navegarA("diagnostico");
      cargarOrdenDiagnostico();
    });
    return btn;
  }
  if (rolActual === "TECNICO" && orden.estado === "APROBADO") {
    btn.textContent = "Finalizar";
    btn.addEventListener("click", () => {
      el("fin-orden-codigo").value = orden.codigo;
      navegarA("finalizar");
      cargarOrdenFinalizar();
    });
    return btn;
  }
  const texto = document.createElement("small");
  texto.className = "nota";
  texto.textContent = orden.comprobante ? orden.comprobante.numero : "—";
  return texto;
}

function renderTablaOrdenes(pagina) {
  const tbody = el("tabla-ordenes-body");
  tbody.replaceChildren();
  estadoPanel.totalPages = pagina.total_pages;

  if (!pagina.items.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 7;
    td.className = "tabla__vacio";
    td.textContent = "No hay órdenes que coincidan con el filtro actual.";
    tr.appendChild(td);
    tbody.appendChild(tr);
  } else {
    for (const orden of pagina.items) {
      const tr = document.createElement("tr");
      const codBtn = document.createElement("button");
      codBtn.type = "button";
      codBtn.className = "boton-enlace";
      codBtn.textContent = orden.codigo;
      codBtn.title = "Ver detalle y línea de tiempo";
      codBtn.addEventListener("click", () => abrirDetalleOrden(orden));
      tr.append(
        celda(codBtn),
        celda(`${orden.cliente.nombres} ${orden.cliente.apellidos} (${orden.cliente.dni})`),
        celda(`${orden.equipo.marca} ${orden.equipo.modelo} · ${orden.equipo.numero_serie}`),
        celda(`${orden.tecnico.nombres} ${orden.tecnico.apellidos}`),
        celda(badgeEstado(orden.estado)),
        celda(montoOrden(orden)),
        celda(botonAccionOrden(orden)),
      );
      tbody.appendChild(tr);
    }
  }
  el("paginacion-ordenes-info").textContent =
    `Página ${pagina.page} de ${pagina.total_pages} · ${pagina.total} orden(es)`;
  el("ordenes-prev").disabled = pagina.page <= 1;
  el("ordenes-next").disabled = pagina.page >= pagina.total_pages;
}

// ---- GUI-03: Diagnóstico y Stock de Repuestos (CU-02, CU-07) -------------------------

export function prepararDiagnostico() {
  estadoDiag.idOp = nuevoIdOp("OP-DIAG");
  el("diag-id-op").textContent = `Referencia ${estadoDiag.idOp} · reserva de stock protegida`;
  cargarRepuestos(1);
}

async function cargarOrdenDiagnostico() {
  mostrarMsg("alerta-e02", "");
  mostrarMsg("diag-confirmacion", "");
  const codigo = el("diag-orden-codigo").value.trim().toUpperCase();
  if (!codigo) return;
  try {
    const r = await llamar("GET", `/ordenes/${encodeURIComponent(codigo)}`);
    if (r.terminada) return;
    if (r.estado !== 200) {
      estadoDiag.orden = null;
      el("diag-cabecera").textContent = "";
      mostrarMsg("alerta-e02", r.datos?.mensaje || MENSAJE_GENERAL);
      return;
    }
    estadoDiag.orden = r.datos;
    el("diag-cabecera").textContent =
      `${r.datos.codigo} · ${r.datos.equipo.marca} ${r.datos.equipo.modelo} (${r.datos.equipo.numero_serie}) · Falla: ${r.datos.falla_reportada} · Estado: ${r.datos.estado}`;
  } catch (_) {
    mostrarMsg("alerta-e02", MENSAJE_GENERAL);
  }
}

async function cargarRepuestos(pagina = estadoDiag.repPage) {
  estadoDiag.repPage = pagina;
  const q = el("rep-buscar-q").value.trim();
  const params = new URLSearchParams({ page: String(pagina), limit: "5" });
  if (q) params.set("q", q);
  try {
    const r = await llamar("GET", `/repuestos?${params.toString()}`);
    if (r.terminada || r.estado !== 200) return;
    const tbody = el("tabla-repuestos-body");
    tbody.replaceChildren();
    estadoDiag.repTotalPages = r.datos.total_pages;
    if (!r.datos.items.length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 5;
      td.className = "tabla__vacio";
      td.textContent = "Sin repuestos con stock libre para esa búsqueda.";
      tr.appendChild(td);
      tbody.appendChild(tr);
    } else {
      for (const rep of r.datos.items) {
        const tr = document.createElement("tr");
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "boton boton--chico";
        btn.textContent = "+ Añadir";
        btn.addEventListener("click", () => agregarRepuestoCotizacion(rep));
        tr.append(
          celda(rep.sku),
          celda(rep.nombre),
          celda(`${rep.stock_libre} libre(s)`),
          celda(`S/ ${Number(rep.precio_unitario).toFixed(2)}`),
          celda(btn),
        );
        tbody.appendChild(tr);
      }
    }
    el("paginacion-repuestos-info").textContent =
      `Página ${r.datos.page} de ${r.datos.total_pages} · ${r.datos.total} repuesto(s)`;
    el("rep-prev").disabled = r.datos.page <= 1;
    el("rep-next").disabled = r.datos.page >= r.datos.total_pages;
  } catch (_) { /* sin conexión */ }
}

function agregarRepuestoCotizacion(rep) {
  mostrarMsg("alerta-e02", "");
  const actual = estadoDiag.cotizacion.get(rep.id);
  const nuevaCantidad = actual ? actual.cantidad + 1 : 1;
  if (nuevaCantidad > rep.stock_libre) {
    mostrarMsg("alerta-e02", `Cantidad máxima libre para ${rep.sku}: ${rep.stock_libre} unidad(es).`);
    return;
  }
  estadoDiag.cotizacion.set(rep.id, { repuesto: rep, cantidad: nuevaCantidad });
  renderCotizacion();
}

function renderCotizacion() {
  const tbody = el("tabla-cotizacion-body");
  tbody.replaceChildren();
  let subtotalRep = 0;
  if (estadoDiag.cotizacion.size === 0) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 5;
    td.className = "tabla__vacio";
    td.textContent = "Sin repuestos añadidos (solo mano de obra).";
    tr.appendChild(td);
    tbody.appendChild(tr);
  } else {
    for (const [id, item] of estadoDiag.cotizacion.entries()) {
      const sub = Number(item.repuesto.precio_unitario) * item.cantidad;
      subtotalRep += sub;
      const tr = document.createElement("tr");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "boton boton--chico";
      btn.textContent = "Quitar";
      btn.addEventListener("click", () => {
        estadoDiag.cotizacion.delete(id);
        renderCotizacion();
      });
      tr.append(
        celda(item.repuesto.sku),
        celda(item.repuesto.nombre),
        celda(String(item.cantidad)),
        celda(`S/ ${sub.toFixed(2)}`),
        celda(btn),
      );
      tbody.appendChild(tr);
    }
  }
  const manoObra = Number(el("diag-mano-obra").value) || 0;
  el("diag-totales").textContent =
    `Repuestos: S/ ${subtotalRep.toFixed(2)} · Total presupuesto: S/ ${(manoObra + subtotalRep).toFixed(2)}`;
}

async function emitirDiagnostico() {
  mostrarMsg("alerta-e02", "");
  mostrarMsg("diag-confirmacion", "");
  const codigo = el("diag-orden-codigo").value.trim().toUpperCase();
  const informe = el("diag-informe").value.trim();
  const manoObra = el("diag-mano-obra").value.trim();
  if (!codigo || !informe || manoObra === "" || Number.isNaN(Number(manoObra))) {
    mostrarMsg("alerta-e02", "Complete el código de orden, el informe técnico y el costo de mano de obra.");
    return;
  }
  const btn = el("diag-emitir");
  const txt = btn.textContent;
  btn.textContent = "Emitiendo...";
  btn.disabled = true;
  try {
    const r = await llamar("POST", `/ordenes/${encodeURIComponent(codigo)}/diagnostico`, {
      cuerpo: {
        id_op: estadoDiag.idOp,
        informe_tecnico: informe,
        costo_mano_obra: manoObra,
        repuestos: Array.from(estadoDiag.cotizacion.values()).map((i) => ({
          repuesto_id: i.repuesto.id,
          cantidad: i.cantidad,
        })),
      },
    });
    if (r.terminada) return;
    if (r.estado === 201 || r.estado === 200) {
      const tot = Number(r.datos.orden.diagnostico.total_presupuesto).toFixed(2);
      mostrarMsg(
        "diag-confirmacion",
        `Diagnóstico emitido para ${r.datos.orden.codigo} · Estado: PRESUPUESTADO · Total: S/ ${tot}`,
      );
      mostrarToast("Diagnóstico emitido", `${r.datos.orden.codigo} pasó a PRESUPUESTADO (S/ ${tot}).`, "ok");
      estadoDiag.cotizacion.clear();
      el("diag-informe").value = "";
      renderCotizacion();
      prepararDiagnostico();
    } else {
      mostrarMsg("alerta-e02", r.datos?.mensaje || MENSAJE_GENERAL);
    }
  } catch (_) {
    mostrarMsg("alerta-e02", MENSAJE_GENERAL);
  } finally {
    btn.textContent = txt;
    btn.disabled = false;
  }
}

// ---- GUI-04: Decisión de Presupuesto (CU-03) -----------------------------------------

export function prepararDecision() {
  estadoDec.idOp = nuevoIdOp("OP-DEC");
  el("dec-id-op").textContent = `Referencia ${estadoDec.idOp} · envío protegido contra duplicados`;
}

async function cargarOrdenDecision() {
  mostrarMsg("dec-error", "");
  mostrarMsg("dec-confirmacion", "");
  const codigo = el("dec-orden-codigo").value.trim().toUpperCase();
  if (!codigo) return;
  try {
    const r = await llamar("GET", `/ordenes/${encodeURIComponent(codigo)}`);
    if (r.terminada) return;
    if (r.estado !== 200) {
      el("dec-resumen").textContent = "";
      mostrarMsg("dec-error", r.datos?.mensaje || MENSAJE_GENERAL);
      return;
    }
    estadoDec.orden = r.datos;
    const diag = r.datos.diagnostico;
    const resumenMonto = diag
      ? `Mano de obra: S/ ${Number(diag.costo_mano_obra).toFixed(2)} + Repuestos: S/ ${Number(diag.subtotal_repuestos).toFixed(2)} = Total: S/ ${Number(diag.total_presupuesto).toFixed(2)}`
      : "Sin presupuesto emitido aún";
    el("dec-resumen").textContent =
      `${r.datos.codigo} · ${r.datos.cliente.nombres} ${r.datos.cliente.apellidos} · Estado: ${r.datos.estado} · ${resumenMonto}`;
  } catch (_) {
    mostrarMsg("dec-error", MENSAJE_GENERAL);
  }
}

async function registrarDecision() {
  mostrarMsg("dec-error", "");
  mostrarMsg("dec-confirmacion", "");
  const codigo = el("dec-orden-codigo").value.trim().toUpperCase();
  const evidencia = el("dec-evidencia").value.trim();
  if (!codigo || !evidencia) {
    mostrarMsg("dec-error", "Ingrese el código de orden y la evidencia textual de la decisión (RN-05).");
    return;
  }
  const btn = el("dec-registrar");
  const txt = btn.textContent;
  btn.textContent = "Registrando...";
  btn.disabled = true;
  try {
    const r = await llamar("POST", `/ordenes/${encodeURIComponent(codigo)}/decision`, {
      cuerpo: {
        id_op: estadoDec.idOp,
        decision: el("dec-valor").value,
        canal: el("dec-canal").value,
        evidencia,
      },
    });
    if (r.terminada) return;
    if (r.estado === 200) {
      mostrarMsg(
        "dec-confirmacion",
        `Decisión registrada para ${r.datos.orden.codigo} · Nuevo estado: ${r.datos.orden.estado}`,
      );
      mostrarToast("Decisión registrada", `${r.datos.orden.codigo} ahora está en ${r.datos.orden.estado}.`, "ok");
      el("dec-evidencia").value = "";
      prepararDecision();
    } else {
      mostrarMsg("dec-error", r.datos?.mensaje || MENSAJE_GENERAL);
    }
  } catch (_) {
    mostrarMsg("dec-error", MENSAJE_GENERAL);
  } finally {
    btn.textContent = txt;
    btn.disabled = false;
  }
}

// ---- GUI-05: Finalizar Reparación (CU-08) --------------------------------------------

export function prepararFinalizar() {
  estadoFin.idOp = nuevoIdOp("OP-FIN");
  el("fin-id-op").textContent = `Referencia ${estadoFin.idOp} · consumo de repuestos protegido`;
  el("fin-confirmar").disabled = !el("fin-prueba-conforme").checked;
}

async function cargarOrdenFinalizar() {
  mostrarMsg("fin-error", "");
  mostrarMsg("fin-confirmacion", "");
  const codigo = el("fin-orden-codigo").value.trim().toUpperCase();
  if (!codigo) return;
  try {
    const r = await llamar("GET", `/ordenes/${encodeURIComponent(codigo)}`);
    if (r.terminada) return;
    if (r.estado !== 200) {
      el("fin-resumen").textContent = "";
      mostrarMsg("fin-error", r.datos?.mensaje || MENSAJE_GENERAL);
      return;
    }
    estadoFin.orden = r.datos;
    const nRep = r.datos.diagnostico ? r.datos.diagnostico.detalles.length : 0;
    el("fin-resumen").textContent =
      `${r.datos.codigo} · ${r.datos.equipo.marca} ${r.datos.equipo.modelo} · Estado: ${r.datos.estado} · ${nRep} ítem(s) reservados por consumir`;
  } catch (_) {
    mostrarMsg("fin-error", MENSAJE_GENERAL);
  }
}

async function confirmarFinalizacion() {
  mostrarMsg("fin-error", "");
  mostrarMsg("fin-confirmacion", "");
  const codigo = el("fin-orden-codigo").value.trim().toUpperCase();
  const trabajo = el("fin-trabajo").value.trim();
  const resultado = el("fin-resultado-prueba").value.trim();
  if (!codigo || !trabajo || !resultado || !el("fin-prueba-conforme").checked) {
    mostrarMsg("fin-error", "Complete trabajo realizado, resultado de prueba y marque «Prueba conforme» (RN-07).");
    return;
  }
  const btn = el("fin-confirmar");
  const txt = btn.textContent;
  btn.textContent = "Finalizando...";
  btn.disabled = true;
  try {
    const r = await llamar("POST", `/ordenes/${encodeURIComponent(codigo)}/finalizar`, {
      cuerpo: {
        id_op: estadoFin.idOp,
        trabajo_realizado: trabajo,
        prueba_conforme: true,
        resultado_prueba: resultado,
      },
    });
    if (r.terminada) return;
    if (r.estado === 200) {
      mostrarMsg(
        "fin-confirmacion",
        `Reparación finalizada para ${r.datos.orden.codigo} · Repuestos consumidos · Estado: LISTO`,
      );
      mostrarToast("Reparación finalizada", `${r.datos.orden.codigo} lista para cobro y entrega.`, "ok");
      el("fin-trabajo").value = "";
      el("fin-resultado-prueba").value = "";
      el("fin-prueba-conforme").checked = false;
      prepararFinalizar();
    } else {
      mostrarMsg("fin-error", r.datos?.mensaje || MENSAJE_GENERAL);
    }
  } catch (_) {
    mostrarMsg("fin-error", MENSAJE_GENERAL);
  } finally {
    btn.textContent = txt;
    btn.disabled = !el("fin-prueba-conforme").checked;
  }
}

// ---- GUI-06: Cobro Único y Entrega (CU-04) -------------------------------------------

export function prepararCobro() {
  estadoCob.idOp = nuevoIdOp("OP-COB");
  el("cob-id-op").textContent = `Referencia ${estadoCob.idOp} · cobro único protegido`;
}

async function cargarOrdenCobro() {
  mostrarMsg("cob-error", "");
  mostrarMsg("cob-confirmacion", "");
  const codigo = el("cob-orden-codigo").value.trim().toUpperCase();
  if (!codigo) return;
  try {
    const r = await llamar("GET", `/ordenes/${encodeURIComponent(codigo)}`);
    if (r.terminada) return;
    if (r.estado !== 200) {
      el("cob-resumen").textContent = "";
      mostrarMsg("cob-error", r.datos?.mensaje || MENSAJE_GENERAL);
      return;
    }
    estadoCob.orden = r.datos;
    const esRechazado = r.datos.estado === "RECHAZADO";
    const total = esRechazado
      ? Number(r.datos.costo_revision).toFixed(2)
      : r.datos.diagnostico
        ? Number(r.datos.diagnostico.total_presupuesto).toFixed(2)
        : Number(r.datos.costo_revision).toFixed(2);
    el("cob-monto").value = total;
    const concepto = esRechazado ? "Costo de revisión por devolución" : "Total a cobrar";
    el("cob-resumen").textContent =
      `${r.datos.codigo} · ${r.datos.cliente.nombres} ${r.datos.cliente.apellidos} · ${r.datos.equipo.marca} ${r.datos.equipo.modelo} · Accesorios: ${r.datos.accesorios || "Ninguno"} · Estado: ${r.datos.estado} · ${concepto}: S/ ${total}`;
  } catch (_) {
    mostrarMsg("cob-error", MENSAJE_GENERAL);
  }
}

async function liquidarOrden() {
  mostrarMsg("cob-error", "");
  mostrarMsg("cob-confirmacion", "");
  const codigo = el("cob-orden-codigo").value.trim().toUpperCase();
  const monto = el("cob-monto").value.trim();
  if (!codigo || !monto || !el("cob-conformidad").checked) {
    mostrarMsg("cob-error", "Ingrese el código de orden, el monto total y marque conformidad de entrega (RN-08).");
    return;
  }
  const btn = el("cob-liquidar");
  const txt = btn.textContent;
  btn.textContent = "Liquidando...";
  btn.disabled = true;
  try {
    const r = await llamar("POST", `/ordenes/${encodeURIComponent(codigo)}/liquidar`, {
      cuerpo: {
        id_op: estadoCob.idOp,
        metodo_pago: el("cob-metodo").value,
        monto_recibido: monto,
        conformidad_entrega: true,
      },
    });
    if (r.terminada) return;
    if (r.estado === 201 || r.estado === 200) {
      mostrarMsg(
        "cob-confirmacion",
        `Orden ${r.datos.orden.codigo} ENTREGADA · Comprobante interno ${r.datos.comprobante.numero} emitido (S/ ${Number(r.datos.comprobante.monto_total).toFixed(2)})`,
      );
      el("btn-imprimir-comprobante").hidden = false;
      mostrarToast("Entrega completada", `Comprobante ${r.datos.comprobante.numero} emitido.`, "ok");
      el("cob-conformidad").checked = false;
      prepararCobro();
    } else {
      mostrarMsg("cob-error", r.datos?.mensaje || MENSAJE_GENERAL);
    }
  } catch (_) {
    mostrarMsg("cob-error", MENSAJE_GENERAL);
  } finally {
    btn.textContent = txt;
    btn.disabled = false;
  }
}

// ---- Directorio de Clientes, Almacén y Exportación CSV -------------------------------

export async function cargarClientes(pagina = estadoClientes.page) {
  estadoClientes.page = pagina;
  const q = el("filtro-clientes-q").value.trim();
  const params = new URLSearchParams({ page: String(pagina), limit: "6" });
  if (q) params.set("q", q);
  try {
    const r = await llamar("GET", `/clientes?${params.toString()}`);
    if (r.terminada || r.estado !== 200) return;
    const tbody = el("tabla-clientes-body");
    tbody.replaceChildren();
    estadoClientes.totalPages = r.datos.total_pages;
    if (!r.datos.items.length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 5;
      td.className = "tabla__vacio";
      td.textContent = "No se encontraron clientes con ese criterio.";
      tr.appendChild(td);
      tbody.appendChild(tr);
    } else {
      for (const item of r.datos.items) {
        const c = item.cliente;
        const eqTexto = item.equipos.length
          ? item.equipos.map((e) => `${e.marca} ${e.modelo} (${e.numero_serie})`).join(" · ")
          : "Sin equipos registrados";
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "boton boton--chico";
        btn.textContent = "Nueva orden";
        btn.addEventListener("click", () => {
          navegarA("recepcion");
          cargarCliente(item);
        });
        const tr = document.createElement("tr");
        tr.append(
          celda(c.dni),
          celda(`${c.nombres} ${c.apellidos}`),
          celda(`${c.telefono}${c.correo ? ` · ${c.correo}` : ""}`),
          celda(eqTexto),
          celda(btn),
        );
        tbody.appendChild(tr);
      }
    }
    el("paginacion-clientes-info").textContent =
      `Página ${r.datos.page} de ${r.datos.total_pages} · ${r.datos.total} cliente(s)`;
    el("clientes-prev").disabled = r.datos.page <= 1;
    el("clientes-next").disabled = r.datos.page >= r.datos.total_pages;
  } catch (_) { /* sin conexión */ }
}

export async function cargarAlmacen(pagina = estadoAlmacen.page) {
  estadoAlmacen.page = pagina;
  const q = el("filtro-almacen-q").value.trim();
  const params = new URLSearchParams({ page: String(pagina), limit: "6", solo_con_stock: "false" });
  if (q) params.set("q", q);
  try {
    const r = await llamar("GET", `/repuestos?${params.toString()}`);
    if (r.terminada || r.estado !== 200) return;
    const tbody = el("tabla-almacen-body");
    tbody.replaceChildren();
    estadoAlmacen.totalPages = r.datos.total_pages;
    if (!r.datos.items.length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 7;
      td.className = "tabla__vacio";
      td.textContent = "No hay repuestos para esa búsqueda.";
      tr.appendChild(td);
      tbody.appendChild(tr);
    } else {
      for (const rep of r.datos.items) {
        const badge = document.createElement("span");
        if (rep.stock_libre <= 0) {
          badge.className = "badge badge--rechazado";
          badge.textContent = "Agotado";
        } else if (rep.stock_libre <= 2) {
          badge.className = "badge badge--presupuestado";
          badge.textContent = "Stock bajo";
        } else {
          badge.className = "badge badge--listo";
          badge.textContent = "Disponible";
        }
        const tr = document.createElement("tr");
        tr.append(
          celda(rep.sku),
          celda(rep.nombre),
          celda(String(rep.stock_disponible)),
          celda(String(rep.stock_reservado)),
          celda(String(rep.stock_libre)),
          celda(`S/ ${Number(rep.precio_unitario).toFixed(2)}`),
          celda(badge),
        );
        tbody.appendChild(tr);
      }
    }
    el("paginacion-almacen-info").textContent =
      `Página ${r.datos.page} de ${r.datos.total_pages} · ${r.datos.total} repuesto(s)`;
    el("almacen-prev").disabled = r.datos.page <= 1;
    el("almacen-next").disabled = r.datos.page >= r.datos.total_pages;
  } catch (_) { /* sin conexión */ }
}

function exportarOrdenesCsv() {
  if (!estadoPanel.ultimasOrdenes.length) {
    mostrarToast("Sin datos", "No hay órdenes en pantalla para exportar.", "aviso");
    return;
  }
  const escapar = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const encabezados = ["Código", "DNI", "Cliente", "Equipo", "Serie", "Técnico", "Estado", "Monto", "Comprobante"];
  const filas = estadoPanel.ultimasOrdenes.map((o) => [
    o.codigo,
    o.cliente.dni,
    `${o.cliente.nombres} ${o.cliente.apellidos}`,
    `${o.equipo.marca} ${o.equipo.modelo}`,
    o.equipo.numero_serie,
    `${o.tecnico.nombres} ${o.tecnico.apellidos}`,
    o.estado,
    montoOrden(o),
    o.comprobante ? o.comprobante.numero : "",
  ]);
  const csv = "\uFEFF" + [encabezados, ...filas].map((f) => f.map(escapar).join(",")).join("\r\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = "bytetrack-ordenes.csv";
  enlace.click();
  URL.revokeObjectURL(url);
  mostrarToast("Exportación lista", "Se descargó bytetrack-ordenes.csv.", "ok");
}

// ---- Conexión inicial ----------------------------------------------------------------

export function iniciarTaller({ rol, irA }) {
  rolActual = rol;
  navegarA = irA;
  if (!conectado) {
    el("btn-filtrar-ordenes").addEventListener("click", () => cargarPanel(1));
    el("btn-exportar-csv")?.addEventListener("click", exportarOrdenesCsv);
    el("btn-filtrar-clientes")?.addEventListener("click", () => cargarClientes(1));
    el("filtro-clientes-q")?.addEventListener("keydown", (e) => { if (e.key === "Enter") cargarClientes(1); });
    el("clientes-prev")?.addEventListener("click", () => cargarClientes(estadoClientes.page - 1));
    el("clientes-next")?.addEventListener("click", () => cargarClientes(estadoClientes.page + 1));
    el("btn-filtrar-almacen")?.addEventListener("click", () => cargarAlmacen(1));
    el("filtro-almacen-q")?.addEventListener("keydown", (e) => { if (e.key === "Enter") cargarAlmacen(1); });
    el("almacen-prev")?.addEventListener("click", () => cargarAlmacen(estadoAlmacen.page - 1));
    el("almacen-next")?.addEventListener("click", () => cargarAlmacen(estadoAlmacen.page + 1));
    el("filtro-ordenes-estado").addEventListener("change", () => cargarPanel(1));
    el("filtro-ordenes-q").addEventListener("keydown", (e) => {
      if (e.key === "Enter") cargarPanel(1);
    });
    el("ordenes-prev").addEventListener("click", () => cargarPanel(estadoPanel.page - 1));
    el("ordenes-next").addEventListener("click", () => cargarPanel(estadoPanel.page + 1));

    el("diag-cargar-orden").addEventListener("click", cargarOrdenDiagnostico);
    el("diag-mano-obra").addEventListener("input", renderCotizacion);
    el("rep-buscar-btn").addEventListener("click", () => cargarRepuestos(1));
    el("rep-buscar-q").addEventListener("keydown", (e) => {
      if (e.key === "Enter") cargarRepuestos(1);
    });
    el("rep-prev").addEventListener("click", () => cargarRepuestos(estadoDiag.repPage - 1));
    el("rep-next").addEventListener("click", () => cargarRepuestos(estadoDiag.repPage + 1));
    el("diag-emitir").addEventListener("click", emitirDiagnostico);

    el("dec-cargar-orden").addEventListener("click", cargarOrdenDecision);
    el("dec-registrar").addEventListener("click", registrarDecision);

    el("fin-cargar-orden").addEventListener("click", cargarOrdenFinalizar);
    el("fin-prueba-conforme").addEventListener("change", () => {
      el("fin-confirmar").disabled = !el("fin-prueba-conforme").checked;
    });
    el("fin-confirmar").addEventListener("click", confirmarFinalizacion);

    el("cob-cargar-orden").addEventListener("click", cargarOrdenCobro);
    el("cob-liquidar").addEventListener("click", liquidarOrden);
    el("btn-imprimir-comprobante")?.addEventListener("click", () => window.print());

    // KPIs interactivos: clic en una tarjeta filtra la tabla por ese estado.
    const botonesKpi = Array.from(document.querySelectorAll("#kpi-grid button[data-estado]"));
    const actualizarKpiActivo = (est) => {
      for (const b of botonesKpi) {
        b.classList.toggle("kpi-card--activo", est !== "" && b.dataset.estado === est);
      }
    };
    for (const btn of botonesKpi) {
      btn.addEventListener("click", () => {
        const actual = el("filtro-ordenes-estado").value;
        const destino = btn.dataset.estado === actual ? "" : btn.dataset.estado;
        el("filtro-ordenes-estado").value = destino;
        actualizarKpiActivo(destino);
        cargarPanel(1);
      });
    }
    el("filtro-ordenes-estado").addEventListener("change", () => {
      actualizarKpiActivo(el("filtro-ordenes-estado").value);
    });

    renderCotizacion();
    conectado = true;
  }
}
