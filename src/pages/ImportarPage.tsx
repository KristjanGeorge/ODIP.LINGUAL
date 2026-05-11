/**
 * Página Importar — M1/M2.
 * Permite seleccionar un archivo 3D dental y validar su integridad.
 * RF-01, RF-02.
 */
import React, { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useIPC } from "../hooks/useIPC";
import { BarraProgreso, CargandoIndicador } from "../components/BarraProgreso";
import type { ResultadoImportacion } from "../types";

const EXTENSIONES_SOPORTADAS = [".stl", ".ply", ".obj", ".dcm"];

const FormatosBadge: React.FC = () => (
  <div className="flex gap-2 flex-wrap">
    {EXTENSIONES_SOPORTADAS.map((ext) => (
      <span
        key={ext}
        className="px-2 py-0.5 bg-slate-700 text-slate-300 text-xs rounded font-mono"
      >
        {ext.toUpperCase()}
      </span>
    ))}
  </div>
);

export const ImportarPage: React.FC = () => {
  const navigate = useNavigate();
  const { abrirArchivo, importar, estadoImportar } = useIPC();
  const [rutaSeleccionada, setRutaSeleccionada] = useState<string | null>(null);
  const [resultado, setResultado] = useState<ResultadoImportacion | null>(null);

  const manejarSeleccion = useCallback(async () => {
    const ruta = await abrirArchivo();
    if (!ruta) return;
    setRutaSeleccionada(ruta);
    setResultado(null);
  }, [abrirArchivo]);

  const manejarImportar = useCallback(async () => {
    if (!rutaSeleccionada) return;
    try {
      const res = await importar(rutaSeleccionada);
      setResultado(res);
      if (res.ok) {
        sessionStorage.setItem("odip_ruta_tmp", res.ruta_tmp ?? "");
        sessionStorage.setItem("odip_formato", res.formato ?? "");
      }
    } catch {
      // El error ya está en estadoImportar.error
    }
  }, [rutaSeleccionada, importar]);

  const manejarContinuar = useCallback(() => {
    navigate("/procesar");
  }, [navigate]);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-1">
          Importar archivo 3D
        </h1>
        <p className="text-slate-400 text-sm">
          Seleccione un archivo de escaneo dental. El sistema validará la
          integridad, unidades (mm) y completitud de la arcada.
        </p>
      </div>

      {/* Zona de selección */}
      <div className="bg-slate-800 border-2 border-dashed border-slate-600 rounded-xl p-8 text-center space-y-4">
        <div className="text-5xl">🦷</div>
        <div>
          <p className="text-slate-300 font-medium mb-2">
            Formatos soportados:
          </p>
          <FormatosBadge />
        </div>
        <button
          onClick={manejarSeleccion}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors"
        >
          Seleccionar archivo
        </button>
      </div>

      {/* Archivo seleccionado */}
      {rutaSeleccionada && (
        <div className="bg-slate-800 border border-slate-600 rounded-lg p-4 space-y-3">
          <div className="flex items-start gap-3">
            <span className="text-2xl">📄</span>
            <div className="flex-1 min-w-0">
              <p className="text-slate-200 font-medium truncate">
                {rutaSeleccionada.split(/[/\\]/).pop()}
              </p>
              <p className="text-slate-500 text-xs truncate">{rutaSeleccionada}</p>
            </div>
          </div>

          {!estadoImportar.cargando && !resultado && (
            <button
              onClick={manejarImportar}
              className="w-full py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg font-medium transition-colors"
            >
              Importar y validar
            </button>
          )}
        </div>
      )}

      {/* Cargando */}
      {estadoImportar.cargando && (
        <div className="bg-slate-800 rounded-lg p-4 space-y-3">
          <CargandoIndicador mensaje="Importando y validando archivo..." />
          <BarraProgreso progreso={60} etiqueta="Validando integridad" />
        </div>
      )}

      {/* Error */}
      {estadoImportar.error && (
        <div className="bg-red-950 border border-red-700 rounded-lg p-4">
          <p className="text-red-300 font-medium">Error de importación</p>
          <p className="text-red-400 text-sm mt-1">{estadoImportar.error}</p>
        </div>
      )}

      {/* Resultado exitoso */}
      {resultado?.ok && (
        <div className="bg-green-950 border border-green-700 rounded-lg p-4 space-y-3">
          <p className="text-green-300 font-semibold">Archivo validado correctamente</p>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
            <dt className="text-slate-400">Formato</dt>
            <dd className="text-slate-200 font-mono uppercase">{resultado.formato}</dd>
            <dt className="text-slate-400">Vértices</dt>
            <dd className="text-slate-200 font-mono">{resultado.n_vertices?.toLocaleString()}</dd>
            <dt className="text-slate-400">Caras</dt>
            <dd className="text-slate-200 font-mono">{resultado.n_caras?.toLocaleString()}</dd>
            <dt className="text-slate-400">Arcada</dt>
            <dd className="text-slate-200 capitalize">{resultado.arcada}</dd>
            <dt className="text-slate-400">Hash SHA-256</dt>
            <dd className="text-slate-400 font-mono text-xs truncate col-span-1">
              {resultado.hash_origen}
            </dd>
          </dl>
          <button
            onClick={manejarContinuar}
            className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors"
          >
            Continuar a procesamiento →
          </button>
        </div>
      )}
    </div>
  );
};
