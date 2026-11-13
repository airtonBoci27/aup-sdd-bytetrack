// Llamadas HTTP y sesión (RNF-02). Sin framework; el texto del servidor nunca se inserta como HTML.

const CLAVE_TOKEN = "bytetrack.token";
const CLAVE_ROL = "bytetrack.rol";

// Respaldo en memoria por si sessionStorage no está disponible (modo privado, datos bloqueados).
let enMemoria = { token: null, rol: null };

export class ErrorRed extends Error {}

export function guardarSesion(token, rol) {
  enMemoria = { token, rol };
  try {
    sessionStorage.setItem(CLAVE_TOKEN, token);
    sessionStorage.setItem(CLAVE_ROL, rol);
  } catch (_) { /* se usa la copia en memoria */ }
}

export function leerSesion() {
  try {
    const token = sessionStorage.getItem(CLAVE_TOKEN);
    const rol = sessionStorage.getItem(CLAVE_ROL);
    if (token && rol) return { token, rol };
  } catch (_) { /* se usa la copia en memoria */ }
  return { ...enMemoria };
}

export function borrarSesion() {
  enMemoria = { token: null, rol: null };
  try {
    sessionStorage.removeItem(CLAVE_TOKEN);
    sessionStorage.removeItem(CLAVE_ROL);
  } catch (_) { /* nada que borrar */ }
}

let avisos = { alExpirar: () => {}, alRechazarRol: () => {} };

/** app.js registra qué hacer cuando el servidor responde 401 (sesión expirada) o 403 (rol). */
export function registrarAvisos(nuevos) {
  avisos = { ...avisos, ...nuevos };
}

/**
 * Llama a la API con `Authorization: Bearer`.
 * Devuelve `{ estado, datos, terminada }`. Ante 401 (sesión) o 403 (rol) borra la sesión o avisa a
 * app.js y devuelve `terminada: true`: el llamador debe dejar de procesar la respuesta.
 * `sinAvisos` desactiva ese manejo (inicio y cierre de sesión).
 */
export async function llamar(metodo, ruta, { cuerpo, formulario, sinAvisos = false } = {}) {
  const cabeceras = { Accept: "application/json" };
  const { token } = leerSesion();
  if (token) cabeceras.Authorization = `Bearer ${token}`;

  let contenido;
  if (formulario) {
    cabeceras["Content-Type"] = "application/x-www-form-urlencoded";
    contenido = new URLSearchParams(formulario).toString();
  } else if (cuerpo !== undefined) {
    cabeceras["Content-Type"] = "application/json";
    contenido = JSON.stringify(cuerpo);
  }

  let respuesta;
  try {
    respuesta = await fetch(ruta, { method: metodo, headers: cabeceras, body: contenido });
  } catch (_) {
    throw new ErrorRed("Sin conexión con el servidor");
  }

  let datos = null;
  if (respuesta.status !== 204) {
    try { datos = await respuesta.json(); } catch (_) { datos = null; }
  }

  if (!sinAvisos && respuesta.status === 401) {
    borrarSesion();
    avisos.alExpirar();
    return { estado: 401, datos, terminada: true };
  }
  if (!sinAvisos && respuesta.status === 403) {
    avisos.alRechazarRol();
    return { estado: 403, datos, terminada: true };
  }
  return { estado: respuesta.status, datos, terminada: false };
}
