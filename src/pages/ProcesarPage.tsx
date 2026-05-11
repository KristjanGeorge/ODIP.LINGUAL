/**
 * Página Procesar — M2-M7.
 * Selección de prescripción y ejecución del pipeline completo.
 * RF-03..RF-14.
 */
import React, { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useIPC } from "../hooks/useIPC";
import { BarraProgreso, CargandoIndicador } from "../components/BarraProgreso";
import type { TipoPrescripcion } from "../types";

const PRESCRIPCIONES: { valor: TipoPrescripcion; etiqueta: string; descripcion: string }[] = [
  {
    valor: "STb",
    etiqueta: "STb (Scuzzo-Takemoto)",
    descripcion: "Prescripción lingual estándar STb. Referencia: Scuzzo & Takemoto, 2003.",
  },
  {
    valor: "2D",
    etiqueta: "2D (Wiechmann)",
    descripcion: "Sistema 2D Wiechmann individualizado. Brackets Language de Ormco.",
  },
  {
    valor: "WIN",
    etiqueta: "WIN (Wild Smile)",
    descripcion: "Prescripción WIN Wild Smile 4th generation.",
  },
  {
    valor: "personalizada",
    etiqueta: "Prescripción personalizada",
    descripcion: "Cargue sus propios valores desde un archivo JSON.",
  },
];

export const ProcesarPage: React.FC = () => {
  const navigate = useNavigate();
  const { procesar, estadoProcesar } = useIPC();
  const [prescripcionSeleccionada, setPrescripcionSeleccionada] =
    useState<TipoPrescripcion>("STb");
  const [idCaso, setIdCaso] = useState<string>(
    `caso-${Date.now()}`
  );
  const [procesado, setProcesado] = useState(false);

  const rutaArchivo = sessionStorage.getItem("odip_ruta_tmp") ?? "";

  const manejarProcesar = useCallback(async () => {
    if (!rutaArchivo) return;
    try {
      const resultado = await procesar(
        rutaArchivo,
        idCaso,
        prescripcionSeleccionada
      );
      if (resultado.ok) {
        sessionStorage.setItem("odip_id_caso", idCaso);
        setProcesado(true);
      }
    } catch {
      // error ya capturado en estadoProcesar.error
    }
  }, [rutaArchivo, idCaso, prescripcionSeleccionada, procesar]);

  const manejarContinuar = useCallback(() => {
    navigate("/revisar");
  }, [navigate]);

  if (!rutaArchivo) {
    return (
      <div className="max-w-2xl mx-auto text-center py-16">
        <div className="text-4xl mb-4">⚠️</div>
        <p className="text-slate-400">
          No hay archivo importado. Vaya a la pestaña Importar primero.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-1">
          Procesamiento del caso
        </h1>
        <p className="text-slate-400 text-sm">
          Configure la prescripción y ejecute el pipeline de segmentación y
          cálculo de parámetros ortodónticos.
        </p>
      </div>

      {/* ID del caso */}
      <div className="bg-slate-800 border border-slate-600 rounded-lg p-4 space-y-2">
        <label className="block text-sm text-slate-400 font-medium">
          Identificador del caso
        </label>
        <input
          type="text"
          value={idCaso}
          onChange={(e) => setIdCaso(e.target.value)}
          className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm font-mono"
          placeholder="caso-XXXXXXXXX"
        />
        <p className="text-slate-500 text-xs">
          Se usa para agrupar resultados y bitácora. No contiene datos del paciente.
        </p>
      </div>

      {/* Selección de prescripción */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Prescripción ortodóntica
        </h2>
        {PRESCRIPCIONES.map((presc) => (
          <label
            key={presc.valor}
            className={[
              "flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-colors",
              prescripcionSeleccionada === presc.valor
                ? "border-blue-500 bg-blue-950"
                : "border-slate-600 bg-slate-800 hover:border-slate-500",
            ].join(" ")}
          >
            <input
              type="radio"
              name="prescripcion"
              value={presc.valor}
              checked={prescripcionSeleccionada === presc.valor}
              onChange={() => setPrescripcionSeleccionada(presc.valor)}
              className="mt-0.5"
            />
            <div>
              <p className="text-slate-200 font-medium">{presc.etiqueta}</p>
              <p className="text-slate-400 text-xs mt-0.5">{presc.descripcion}</p>
            </div>
          </label>
        ))}
      </div>

      {/* Módulos que se ejecutarán */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <p className="text-xs text-slate-400 mb-2 font-semibold uppercase tracking-wider">
          Pipeline a ejecutar
        </p>
        <div className="flex flex-wrap gap-2">
          {["M2 Pre-proceso", "M3 Segmentación", "M4 Geometría", "M5 Parámetros", "M6 Prescripción", "M7 Bracket"].map(
            (mod) => (
              <span
                key={mod}
                className="px-2 py-1 bg-slate-700 text-slate-300 text-xs rounded"
              >
                {mod}
              </span>
            )
          )}
        </div>
      </div>

      {/* Botón procesar */}
      {!estadoProcesar.cargando && !procesado && (
        <button
          onClick={manejarProcesar}
          disabled={!idCaso.trim()}
          className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:text-slate-400 text-white rounded-lg font-semibold transition-colors"
        >
          Ejecutar pipeline
        </button>
      )}

      {/* Cargando */}
      {estadoProcesar.cargando && (
        <div className="bg-slate-800 rounded-lg p-4 space-y-3">
          <CargandoIndicador mensaje="Ejecutando pipeline M2-M7..." />
          <BarraProgreso progreso={45} etiqueta="Segmentando piezas dentales" variante="azul" />
          <p className="text-slate-500 text-xs">
            Este proceso puede tomar 30–120 segundos dependiendo de la densidad de la malla.
          </p>
        </div>
      )}

      {/* Error */}
      {estadoProcesar.error && (
        <div className="bg-red-950 border border-red-700 rounded-lg p-4">
          <p className="text-red-300 font-medium">Error en el pipeline</p>
          <p className="text-red-400 text-sm mt-1">{estadoProcesar.error}</p>
        </div>
      )}

      {/* Resultado exitoso */}
      {procesado && estadoProcesar.datos && (
        <div className="bg-green-950 border border-green-700 rounded-lg p-4 space-y-3">
          <p className="text-green-300 font-semibold">Pipeline ejecutado correctamente</p>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
            <dt className="text-slate-400">ID Caso</dt>
            <dd className="text-slate-200 font-mono">{estadoProcesar.datos.id_caso}</dd>
            <dt className="text-slate-400">Piezas calculadas</dt>
            <dd className="text-slate-200">{estadoProcesar.datos.n_piezas}</dd>
            <dt className="text-slate-400">Estado</dt>
            <dd className="text-green-300 capitalize">{estadoProcesar.datos.estado}</dd>
          </dl>
          {estadoProcesar.datos.advertencias.length > 0 && (
            <div className="bg-yellow-950 border border-yellow-700 rounded p-2">
              <p className="text-yellow-300 text-xs font-medium mb-1">Advertencias:</p>
              {estadoProcesar.datos.advertencias.map((adv, i) => (
                <p key={i} className="text-yellow-400 text-xs">• {adv}</p>
              ))}
            </div>
          )}
          <button
            onClick={manejarContinuar}
            className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium"
          >
            Continuar a revisión →
          </button>
        </div>
      )}
    </div>
  );
};
