/**
 * Tipos compartidos del frontend LingualParam-CSM™
 * Espejo de los contratos Python/preload para el renderer.
 */

export type EstadoCaso = "importado" | "procesado" | "aprobado" | "exportado";

export type TipoPrescripcion = "STb" | "2D" | "WIN" | "personalizada";

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
  estado: EstadoCaso;
  prescripcion: string | null;
  piezas: PiezaDatos[];
  errores: string[];
}

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

export interface SolicitudAjusteManual {
  id_caso: string;
  fdi: number;
  campo: "torque_deg" | "angulacion_deg" | "inclinacion_deg";
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

export interface EventoBitacora {
  id_evento: number;
  tipo: string;
  autor: string;
  id_caso: string | null;
  marca_temporal: string;
  hash: string;
  descripcion?: string;
}

export interface ParametrosHistorico {
  id_caso?: string;
  tipo?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  limite?: number;
}

export interface ResultadoHistorico {
  total: number;
  eventos: EventoBitacora[];
}

/** Estado global de la aplicación */
export interface EstadoApp {
  idCaso: string | null;
  rutaArchivoTmp: string | null;
  caso: DatosCaso | null;
  piezaSeleccionada: number | null;  // FDI
  cargando: boolean;
  error: string | null;
}
