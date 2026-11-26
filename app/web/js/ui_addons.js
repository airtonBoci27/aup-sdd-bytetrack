// Add-ons de interfaz: notificaciones Toast, tema claro/oscuro, gráfico de distribución
// y modal de detalle/línea de tiempo de órdenes. Solo DOM nativo (textContent / createElement).

const CLAVE_TEMA = "bytetrack.tema";
const FLUJO_ESTADOS = ["RECEPCIONADO", "PRESUPUESTADO", "APROBADO", "LISTO", "ENTREGADO"];
const COLORES_ESTADO = {
  RECEPCIONADO: "#0284c7",
  PRESUPUESTADO: "#ea580c",
  APROBADO: "#7c3aed",
  RECHAZADO: "#e11d48",
  LISTO: "#059669",
  ENTREGADO: "#0d9488",
};

const el = (id) => document.getElementById(id);

// ---- 1. Notificaciones Toast ---------------------------------------------------------

export function mostrarToast(titulo, mensaje, tipo = "ok") {
  const contenedor = el("toast-contenedor");
  if (!contenedor) return;

  const toast = document.createElement("div");
  toast.className = `toast toast--${tipo}`;
  toast.setAttribute("role", tipo === "error" ? "alert" : "status");

  const t = document.createElement("strong");
  t.textContent = titulo;
  const p = document.createElement("span");
  p.textContent = mensaje;

  toast.append(t, p);
  contenedor.appendChild(toast);

  window.setTimeout(() => {
    toast.classList.add("toast--salir");
    window.setTimeout(() => toast.remove(), 240);
  }, 4200);
}

// ---- 2. Tema Claro / Oscuro ----------------------------------------------------------

function aplicarTema(tema) {
  const oscuro = tema === "dark";
  document.documentElement.dataset.theme = oscuro ? "dark" : "light";
  const btn = el("btn-tema");
  if (btn) {
    btn.textContent = oscuro ? "Tema claro" : "Tema oscuro";
    btn.setAttribute("aria-pressed", String(oscuro));
  }
}

export function iniciarTema() {
  let guardado = "light";
  try {
    guardado = localStorage.getItem(CLAVE_TEMA) || "light";
  } catch (_) { /* modo privado */ }
  aplicarTema(guardado);

  const btn = el("btn-tema");
  if (btn) {
    btn.addEventListener("click", () => {
      const siguiente = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      aplicarTema(siguiente);
      try { localStorage.setItem(CLAVE_TEMA, siguiente); } catch (_) { /* noop */ }
    });
  }
}

// ---- 3. Gráfico de Distribución por Estado (sin librerías externas) ------------------

export function renderGraficoDistribucion(porEstado, totalOrdenes) {
  const barra = el("grafico-barra");
  const leyenda = el("grafico-leyenda");
  if (!barra || !leyenda) return;

  barra.replaceChildren();
  leyenda.replaceChildren();

  const total = totalOrdenes || 0;
  for (const [estado, cantidad] of Object.entries(porEstado)) {
    const pct = total > 0 ? Math.round((cantidad / total) * 100) : 0;
    if (cantidad > 0) {
      const seg = document.createElement("div");
      seg.className = "grafico-barra__seg";
      seg.style.width = `${pct}%`;
      seg.style.backgroundColor = COLORES_ESTADO[estado] || "#4f46e5";
      seg.title = `${estado}: ${cantidad} (${pct}%)`;
      barra.appendChild(seg);
    }

    const item = document.createElement("span");
    item.className = "grafico-leyenda__item";
    const punto = document.createElement("i");
    punto.className = "grafico-leyenda__punto";
    punto.style.backgroundColor = COLORES_ESTADO[estado] || "#4f46e5";
    item.append(punto, document.createTextNode(`${estado}: ${cantidad} (${pct}%)`));
    leyenda.appendChild(item);
  }
}

// ---- 4. Modal de Detalle y Línea de Tiempo de Orden ----------------------------------

function bloqueDetalle(titulo, filas) {
  const sec = document.createElement("div");
  sec.className = "detalle-bloque";
  const h = document.createElement("h3");
  h.textContent = titulo;
  sec.appendChild(h);

  for (const [clave, valor] of filas) {
    if (valor === null || valor === undefined || valor === "") continue;
    const fila = document.createElement("div");
    fila.className = "detalle-fila";
    const k = document.createElement("span");
    k.className = "detalle-fila__k";
    k.textContent = clave;
    const v = document.createElement("strong");
    v.className = "detalle-fila__v";
    v.textContent = String(valor);
    fila.append(k, v);
    sec.appendChild(fila);
  }
  return sec;
}

export function abrirDetalleOrden(orden) {
  const modal = el("modal-detalle-orden");
  const titulo = el("det-titulo");
  const timeline = el("det-timeline");
  const cuerpo = el("det-cuerpo");
  if (!modal || !titulo || !timeline || !cuerpo) return;

  titulo.textContent = `Orden ${orden.codigo} · ${orden.estado}`;

  // Línea de tiempo de estados
  timeline.replaceChildren();
  const idxActual = FLUJO_ESTADOS.indexOf(orden.estado);
  for (let i = 0; i < FLUJO_ESTADOS.length; i += 1) {
    const paso = document.createElement("span");
    const est = FLUJO_ESTADOS[i];
    let cls = "timeline__paso";
    if (orden.estado === "RECHAZADO" && i <= 1) cls += " timeline__paso--hecho";
    else if (idxActual >= 0 && i < idxActual) cls += " timeline__paso--hecho";
    else if (idxActual === i) cls += " timeline__paso--actual";
    paso.className = cls;
    paso.textContent = est;
    timeline.appendChild(paso);
  }
  if (orden.estado === "RECHAZADO") {
    const rech = document.createElement("span");
    rech.className = "timeline__paso timeline__paso--rechazado";
    rech.textContent = "RECHAZADO";
    timeline.appendChild(rech);
  }

  // Bloques de detalle
  cuerpo.replaceChildren();
  cuerpo.appendChild(
    bloqueDetalle("1. Recepción y Equipo", [
      ["Cliente", `${orden.cliente.nombres} ${orden.cliente.apellidos} (DNI ${orden.cliente.dni})`],
      ["Teléfono", orden.cliente.telefono],
      ["Equipo", `${orden.equipo.tipo} · ${orden.equipo.marca} ${orden.equipo.modelo}`],
      ["N.° de serie", orden.equipo.numero_serie],
      ["Accesorios", orden.accesorios || "Ninguno"],
      ["Estado físico", orden.estado_fisico],
      ["Falla reportada", orden.falla_reportada],
      ["Técnico asignado", `${orden.tecnico.nombres} ${orden.tecnico.apellidos}`],
    ]),
  );

  if (orden.diagnostico) {
    const filasDiag = [
      ["Informe técnico", orden.diagnostico.informe_tecnico],
      ["Mano de obra", `S/ ${Number(orden.diagnostico.costo_mano_obra).toFixed(2)}`],
      ["Subtotal repuestos", `S/ ${Number(orden.diagnostico.subtotal_repuestos).toFixed(2)}`],
      ["Total presupuesto", `S/ ${Number(orden.diagnostico.total_presupuesto).toFixed(2)}`],
    ];
    for (const d of orden.diagnostico.detalles) {
      filasDiag.push([
        `Repuesto (${d.sku})`,
        `${d.nombre} ×${d.cantidad} · S/ ${Number(d.subtotal).toFixed(2)} [${d.estado_reserva}]`,
      ]);
    }
    cuerpo.appendChild(bloqueDetalle("2. Diagnóstico y Presupuesto", filasDiag));
  }

  if (orden.decision_canal) {
    cuerpo.appendChild(
      bloqueDetalle("3. Decisión del Cliente", [
        ["Canal", orden.decision_canal],
        ["Fecha", orden.decision_fecha],
        ["Evidencia", orden.decision_evidencia],
      ]),
    );
  }

  if (orden.trabajo_realizado) {
    cuerpo.appendChild(
      bloqueDetalle("4. Cierre Técnico", [
        ["Trabajo realizado", orden.trabajo_realizado],
        ["Prueba conforme", orden.prueba_conforme ? "Sí (conforme)" : "No"],
        ["Resultado prueba", orden.resultado_prueba],
      ]),
    );
  }

  if (orden.comprobante) {
    cuerpo.appendChild(
      bloqueDetalle("5. Comprobante y Entrega", [
        ["Comprobante", orden.comprobante.numero],
        ["Método de pago", orden.comprobante.metodo_pago],
        ["Monto cobrado", `S/ ${Number(orden.comprobante.monto_total).toFixed(2)}`],
        ["Conformidad entrega", orden.comprobante.conformidad_entrega ? "Confirmada" : "Pendiente"],
      ]),
    );
  }

  modal.hidden = false;
  el("det-cerrar")?.focus();
}

export function iniciarModalDetalle() {
  const modal = el("modal-detalle-orden");
  const cerrar = () => { if (modal) modal.hidden = true; };
  el("det-cerrar")?.addEventListener("click", cerrar);
  el("det-imprimir")?.addEventListener("click", () => window.print());
  modal?.addEventListener("click", (e) => {
    if (e.target === modal) cerrar();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal && !modal.hidden) cerrar();
  });
}
