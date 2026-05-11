/**
 * Preload script — LingualParam-CSM™
 * Expone la API IPC al renderer mediante contextBridge.
 * No expone Node.js directamente al renderer.
 */
import { contextBridge, ipcRenderer } from "electron";

/** API expuesta al renderer bajo window.odip */
export interface OdipAPI {
  health: () => Promise<{ estado: string; version: string }>;
  abrirArchivo: () => Promise<string | null>;
  seleccionarCarpeta: () => Promise<string | null>;
  abrirCarpeta: (ruta: string) => Promise<void>;
  importar: (rutaArchivo: string) => Promise<ResultadoImportacion>;
  procesar: (
    rutaArchivo: string,
    idCaso: string,
    tipoPrescripcion: string,
    rutaModeloCNN?: string
  ) => Promise<ResultadoProcesamiento>;
  obtenerCaso: (idCaso: string) => Promise<DatosCaso>;
  ajusteManual: (datos: SolicitudAjusteManual) => Promise<{ ok: boolean }>;
  exportar: (datos: SolicitudExportacion) => Promise<ResultadoExportacion>;
  historico: (params: ParametrosHistorico) => Promise<ResultadoHistorico>;
}

// ------------------------------------------------------------------
// Tipos de la API IPC
// ------------------------------------------------------------------

export interface ResultadoImportacion {
  ok: boolean;
  ruta_tmp?: string;
  formato?: string;
  n_vertices?: number;
  n_caras?: number;
  arcada?: string;
  hash_origen?: string;
  detail?: string;
}

export interface ResultadoProcesamiento {
  ok: boolean;
  id_caso: string;
  estado: string;
  n_piezas: number;
  errores: string[];
  advertencias: string[];
}

export interface PiezaDatos {
  fdi: number;
  torque_deg: number;
  angulacion_deg: number;
  inclinacion_deg: number;
  distancia_cingular_mm: number;
  delta_t: number;
  delta_a: number;
  delta_i: number;
  grosor_base_mm: number;
  angulo_slot_deg: number;
  ajuste_manual: boolean;
  justificacion_ajuste: string;
  confianza_segmentacion: number;
  centroide_lingual: [number, number, number];
  eje_longitudinal: [number, number, number];
  vector_normal_lingual: [number, number, number];
}

export interface DatosCaso {
  id_caso: string;
  estado: string;
  prescripcion: string | null;
  piezas: PiezaDatos[];
  errores: string[];
}

export interface SolicitudAjusteManual {
  id_caso: string;
  fdi: number;
  campo: string;
  valor_nuevo: number;
  autor: string;
  justificacion: string;
}

export interface SolicitudExportacion {
  id_caso: string;
  nombre_paciente: string;
  fecha_nacimiento: string;
  rut_u_id: string;
  directorio_destino: string;
}

export interface ResultadoExportacion {
  ok: boolean;
  id_paciente_anonimizado: string;
  hashes: Record<string, string>;
}

export interface ParametrosHistorico {
  id_caso?: string;
  tipo?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  limite?: number;
}

export interface EventoBitacora {
  id_evento: number;
  tipo: string;
  autor: string;
  id_caso: string | null;
  marca_temporal: string;
  hash: string;
  descripcion?: string;
}

export interface ResultadoHistorico {
  total: number;
  eventos: EventoBitacora[];
}

// ------------------------------------------------------------------
// Exposición via contextBridge
// ------------------------------------------------------------------

contextBridge.exposeInMainWorld("odip", {
  health: () => ipcRenderer.invoke("odip:health"),
  abrirArchivo: () => ipcRenderer.invoke("odip:abrirArchivo"),
  seleccionarCarpeta: () => ipcRenderer.invoke("odip:seleccionarCarpeta"),
  abrirCarpeta: (ruta: string) => ipcRenderer.invoke("odip:abrirCarpeta", ruta),
  importar: (rutaArchivo: string) =>
    ipcRenderer.invoke("odip:importar", rutaArchivo),
  procesar: (
    rutaArchivo: string,
    idCaso: string,
    tipoPrescripcion: string,
    rutaModeloCNN?: string
  ) =>
    ipcRenderer.invoke(
      "odip:procesar",
      rutaArchivo,
      idCaso,
      tipoPrescripcion,
      rutaModeloCNN
    ),
  obtenerCaso: (idCaso: string) =>
    ipcRenderer.invoke("odip:obtenerCaso", idCaso),
  ajusteManual: (datos: SolicitudAjusteManual) =>
    ipcRenderer.invoke("odip:ajusteManual", datos),
  exportar: (datos: SolicitudExportacion) =>
    ipcRenderer.invoke("odip:exportar", datos),
  historico: (params: ParametrosHistorico) =>
    ipcRenderer.invoke("odip:historico", params),
} satisfies OdipAPI);
