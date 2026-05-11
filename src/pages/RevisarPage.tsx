/**
 * Página Revisar — M9 (revisión clínica).
 * Muestra el visor 3D y la tabla de parámetros editable.
 * RF-15, RF-16.
 */
import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useIPC } from "../hooks/useIPC";
import { Viewer3D } from "../components/Viewer3D";
import { TablaParametros } from "../components/TablaParametros";
import { CargandoIndicador } from "../components/BarraProgreso";
import type { DatosCaso, SolicitudAjusteManual } from "../types";

export const RevisarPage: React.FC = () => {
  const navigate = useNavigate();
  const { obtenerCaso, ajusteManual, estadoCaso } = useIPC();
  const [caso, setCaso] = useState<DatosCaso | null>(null);
  const [piezaSeleccionada, setPiezaSeleccionada] = useState<number | null>(null);

  const idCaso = sessionStorage.getItem("odip_id_caso") ?? "";

  useEffect(() => {
    if (!idCaso) return;
    obtenerCaso(idCaso)
      .then(setCaso)
      .catch(() => {});
  }, [idCaso, obtenerCaso]);

  const manejarAjuste = useCallback(
    async (solicitud: SolicitudAjusteManual): Promise<boolean> => {
      const ok = await ajusteManual(solicitud);
      if (ok && idCaso) {
        // Refrescar datos
        const actualizado = await obtenerCaso(idCaso);
        setCaso(actualizado);
      }
      return ok;
    },
    [ajusteManual, idCaso, obtenerCaso]
  );

  if (!idCaso) {
    return (
      <div className="max-w-2xl mx-auto text-center py-16">
        <div className="text-4xl mb-4">⚠️</div>
        <p className="text-slate-400">
          No hay caso procesado. Vaya a la pestaña Procesar primero.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col space-y-4">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Revisión clínica</h1>
          <p className="text-slate-400 text-sm">
            Verifique y ajuste los parámetros por pieza. Los ajustes quedan registrados en bitácora.
          </p>
        </div>
        {caso && (
          <div className="text-right">
            <p className="text-xs text-slate-500">Caso</p>
            <p className="text-sm font-mono text-blue-300">{caso.id_caso}</p>
            <p className="text-xs text-slate-400">
              Prescripción: <span className="text-slate-200">{caso.prescripcion ?? "—"}</span>
            </p>
          </div>
        )}
      </div>

      {estadoCaso.cargando && (
        <div className="py-8">
          <CargandoIndicador mensaje="Cargando datos del caso..." />
        </div>
      )}

      {estadoCaso.error && (
        <div className="bg-red-950 border border-red-700 rounded-lg p-4">
          <p className="text-red-300">{estadoCaso.error}</p>
        </div>
      )}

      {caso && caso.piezas.length > 0 && (
        <div className="flex-1 grid grid-cols-2 gap-4 min-h-0">
          {/* Visor 3D */}
          <div className="h-full min-h-96">
            <Viewer3D
              piezas={caso.piezas}
              piezaSeleccionada={piezaSeleccionada}
              onSeleccionarPieza={setPiezaSeleccionada}
              mostrarEjes
            />
          </div>

          {/* Panel derecho: info pieza + tabla */}
          <div className="flex flex-col gap-3 overflow-auto">
            {/* Info pieza seleccionada */}
            {piezaSeleccionada && (
              <div className="bg-slate-800 border border-slate-600 rounded-lg p-4 shrink-0">
                {(() => {
                  const pieza = caso.piezas.find((p) => p.fdi === piezaSeleccionada);
                  if (!pieza) return null;
                  return (
                    <div>
                      <p className="text-blue-300 font-bold text-lg mb-2">
                        Pieza FDI {pieza.fdi}
                      </p>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div className="bg-slate-700 rounded p-2 text-center">
                          <p className="text-slate-400">Torque actual</p>
                          <p className="text-slate-100 font-mono text-base">
                            {pieza.torque_deg.toFixed(1)}°
                          </p>
                        </div>
                        <div className="bg-slate-700 rounded p-2 text-center">
                          <p className="text-slate-400">Angulación actual</p>
                          <p className="text-slate-100 font-mono text-base">
                            {pieza.angulacion_deg.toFixed(1)}°
                          </p>
                        </div>
                        <div className="bg-slate-700 rounded p-2 text-center">
                          <p className="text-slate-400">Inclinación actual</p>
                          <p className="text-slate-100 font-mono text-base">
                            {pieza.inclinacion_deg.toFixed(1)}°
                          </p>
                        </div>
                      </div>
                      <div className="mt-2 text-xs text-slate-400">
                        Distancia cingular: {pieza.distancia_cingular_mm.toFixed(2)} mm |
                        Confianza segmentación: {(pieza.confianza_segmentacion * 100).toFixed(0)}%
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}

            {/* Tabla */}
            <div className="flex-1 bg-slate-800 border border-slate-700 rounded-lg overflow-auto">
              <TablaParametros
                piezas={caso.piezas}
                idCaso={idCaso}
                piezaSeleccionada={piezaSeleccionada}
                onSeleccionarPieza={setPiezaSeleccionada}
                onAjusteManual={manejarAjuste}
              />
            </div>
          </div>
        </div>
      )}

      {/* Pie de revisión */}
      {caso && caso.piezas.length > 0 && (
        <div className="shrink-0 flex justify-end">
          <button
            onClick={() => navigate("/exportar")}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors"
          >
            Aprobar y exportar →
          </button>
        </div>
      )}
    </div>
  );
};
