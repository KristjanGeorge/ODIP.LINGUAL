/**
 * Hook para comunicación IPC con el proceso principal de Electron.
 * Abstrae window.odip y provee manejo de estado (cargando/error).
 */
import { useState, useCallback } from "react";
import type {
  DatosCaso,
  ParametrosHistorico,
  ResultadoExportacion,
  ResultadoHistorico,
  ResultadoImportacion,
  ResultadoProcesamiento,
  SolicitudAjusteManual,
  SolicitudExportacion,
} from "../types";

interface EstadoIPC<T> {
  datos: T | null;
  cargando: boolean;
  error: string | null;
}

function estadoInicial<T>(): EstadoIPC<T> {
  return { datos: null, cargando: false, error: null };
}

/** API IPC tipada expuesta por el preload */
declare global {
  interface Window {
    odip: {
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
    };
  }
}

/** Hook principal para llamadas IPC */
export function useIPC() {
  const [estadoImportar, setEstadoImportar] =
    useState<EstadoIPC<ResultadoImportacion>>(estadoInicial());
  const [estadoProcesar, setEstadoProcesar] =
    useState<EstadoIPC<ResultadoProcesamiento>>(estadoInicial());
  const [estadoCaso, setEstadoCaso] =
    useState<EstadoIPC<DatosCaso>>(estadoInicial());
  const [estadoExportar, setEstadoExportar] =
    useState<EstadoIPC<ResultadoExportacion>>(estadoInicial());

  const abrirArchivo = useCallback(async (): Promise<string | null> => {
    return window.odip.abrirArchivo();
  }, []);

  const seleccionarCarpeta = useCallback(async (): Promise<string | null> => {
    return window.odip.seleccionarCarpeta();
  }, []);

  const importar = useCallback(async (rutaArchivo: string) => {
    setEstadoImportar({ datos: null, cargando: true, error: null });
    try {
      const resultado = await window.odip.importar(rutaArchivo);
      if (!resultado.ok) throw new Error(resultado.detail ?? "Error al importar.");
      setEstadoImportar({ datos: resultado, cargando: false, error: null });
      return resultado;
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setEstadoImportar({ datos: null, cargando: false, error: msg });
      throw err;
    }
  }, []);

  const procesar = useCallback(
    async (
      rutaArchivo: string,
      idCaso: string,
      tipoPrescripcion: string,
      rutaModeloCNN?: string
    ) => {
      setEstadoProcesar({ datos: null, cargando: true, error: null });
      try {
        const resultado = await window.odip.procesar(
          rutaArchivo,
          idCaso,
          tipoPrescripcion,
          rutaModeloCNN
        );
        setEstadoProcesar({ datos: resultado, cargando: false, error: null });
        return resultado;
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        setEstadoProcesar({ datos: null, cargando: false, error: msg });
        throw err;
      }
    },
    []
  );

  const obtenerCaso = useCallback(async (idCaso: string) => {
    setEstadoCaso({ datos: null, cargando: true, error: null });
    try {
      const resultado = await window.odip.obtenerCaso(idCaso);
      setEstadoCaso({ datos: resultado, cargando: false, error: null });
      return resultado;
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setEstadoCaso({ datos: null, cargando: false, error: msg });
      throw err;
    }
  }, []);

  const ajusteManual = useCallback(
    async (datos: SolicitudAjusteManual): Promise<boolean> => {
      try {
        const resultado = await window.odip.ajusteManual(datos);
        return resultado.ok;
      } catch {
        return false;
      }
    },
    []
  );

  const exportar = useCallback(async (datos: SolicitudExportacion) => {
    setEstadoExportar({ datos: null, cargando: true, error: null });
    try {
      const resultado = await window.odip.exportar(datos);
      setEstadoExportar({ datos: resultado, cargando: false, error: null });
      return resultado;
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setEstadoExportar({ datos: null, cargando: false, error: msg });
      throw err;
    }
  }, []);

  const historico = useCallback(async (params: ParametrosHistorico) => {
    return window.odip.historico(params);
  }, []);

  const abrirCarpeta = useCallback(async (ruta: string) => {
    return window.odip.abrirCarpeta(ruta);
  }, []);

  return {
    // Estado
    estadoImportar,
    estadoProcesar,
    estadoCaso,
    estadoExportar,
    // Acciones
    abrirArchivo,
    seleccionarCarpeta,
    importar,
    procesar,
    obtenerCaso,
    ajusteManual,
    exportar,
    historico,
    abrirCarpeta,
  };
}
