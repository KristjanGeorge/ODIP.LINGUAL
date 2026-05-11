/**
 * Tabla de parámetros por pieza, editable.
 * Columnas: FDI, T actual, A actual, I actual, T objetivo, A objetivo, I objetivo,
 *           ΔT, ΔA, ΔI, Grosor base, Ángulo slot.
 * RF-15, RF-16.
 */
import React, { useState, useCallback } from "react";
import type { PiezaDatos, SolicitudAjusteManual } from "../types";

// ------------------------------------------------------------------
// Tipos
// ------------------------------------------------------------------

interface PropsTablaParametros {
  piezas: PiezaDatos[];
  idCaso: string;
  piezaSeleccionada: number | null;
  onSeleccionarPieza: (fdi: number) => void;
  onAjusteManual: (solicitud: SolicitudAjusteManual) => Promise<boolean>;
}

type CampoEditable = "torque_deg" | "angulacion_deg" | "inclinacion_deg";

interface EstadoEdicion {
  fdi: number;
  campo: CampoEditable;
  valorActual: string;
}

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------

const etiquetaFDI = (fdi: number): string => `${fdi}`;

const colorDelta = (delta: number): string => {
  const abs = Math.abs(delta);
  if (abs < 1) return "text-green-400";
  if (abs < 3) return "text-yellow-400";
  return "text-red-400";
};

const formatearAngulo = (val: number): string => val.toFixed(1) + "°";

// ------------------------------------------------------------------
// Celda editable
// ------------------------------------------------------------------

const CeldaEditable: React.FC<{
  valor: number;
  fdi: number;
  campo: CampoEditable;
  edicionActual: EstadoEdicion | null;
  onIniciarEdicion: (fdi: number, campo: CampoEditable, valorActual: number) => void;
  onConfirmarEdicion: (valorNuevo: number) => void;
  onCancelarEdicion: () => void;
  onChange: (valor: string) => void;
}> = ({
  valor,
  fdi,
  campo,
  edicionActual,
  onIniciarEdicion,
  onConfirmarEdicion,
  onCancelarEdicion,
  onChange,
}) => {
  const estaEditando =
    edicionActual?.fdi === fdi && edicionActual?.campo === campo;

  if (estaEditando) {
    return (
      <div className="flex items-center gap-1">
        <input
          type="number"
          step="0.1"
          value={edicionActual.valorActual}
          onChange={(e) => onChange(e.target.value)}
          className="w-20 bg-slate-700 border border-blue-500 rounded px-1 py-0.5 text-sm text-right"
          autoFocus
          onKeyDown={(e) => {
            if (e.key === "Enter")
              onConfirmarEdicion(parseFloat(edicionActual.valorActual));
            if (e.key === "Escape") onCancelarEdicion();
          }}
        />
        <button
          onClick={() => onConfirmarEdicion(parseFloat(edicionActual.valorActual))}
          className="text-green-400 hover:text-green-300 text-xs"
          title="Confirmar"
        >
          ✓
        </button>
        <button
          onClick={onCancelarEdicion}
          className="text-red-400 hover:text-red-300 text-xs"
          title="Cancelar"
        >
          ✗
        </button>
      </div>
    );
  }

  return (
    <button
      className="text-right w-full hover:text-blue-300 hover:underline cursor-pointer transition-colors"
      onClick={() => onIniciarEdicion(fdi, campo, valor)}
      title="Haga clic para editar"
    >
      {formatearAngulo(valor)}
    </button>
  );
};

// ------------------------------------------------------------------
// Modal de justificación
// ------------------------------------------------------------------

const ModalJustificacion: React.FC<{
  onConfirmar: (justificacion: string, autor: string) => void;
  onCancelar: () => void;
}> = ({ onConfirmar, onCancelar }) => {
  const [justificacion, setJustificacion] = useState("");
  const [autor, setAutor] = useState("");

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-slate-800 border border-slate-600 rounded-lg p-6 w-96 shadow-xl">
        <h3 className="text-lg font-semibold mb-4 text-slate-100">
          Justificación de ajuste manual
        </h3>
        <div className="mb-3">
          <label className="block text-sm text-slate-400 mb-1">
            Autor (Ortodoncista)
          </label>
          <input
            type="text"
            value={autor}
            onChange={(e) => setAutor(e.target.value)}
            className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm"
            placeholder="Dr./Dra. Apellido"
          />
        </div>
        <div className="mb-4">
          <label className="block text-sm text-slate-400 mb-1">
            Justificación clínica *
          </label>
          <textarea
            value={justificacion}
            onChange={(e) => setJustificacion(e.target.value)}
            className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm h-24 resize-none"
            placeholder="Describa la razón clínica del ajuste..."
          />
        </div>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancelar}
            className="px-4 py-2 text-sm text-slate-400 hover:text-slate-200"
          >
            Cancelar
          </button>
          <button
            onClick={() => onConfirmar(justificacion, autor)}
            disabled={!justificacion.trim() || !autor.trim()}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:text-slate-400 rounded font-medium"
          >
            Confirmar ajuste
          </button>
        </div>
      </div>
    </div>
  );
};

// ------------------------------------------------------------------
// Componente principal
// ------------------------------------------------------------------

export const TablaParametros: React.FC<PropsTablaParametros> = ({
  piezas,
  idCaso,
  piezaSeleccionada,
  onSeleccionarPieza,
  onAjusteManual,
}) => {
  const [edicion, setEdicion] = useState<EstadoEdicion | null>(null);
  const [pendiente, setPendiente] = useState<{
    fdi: number;
    campo: CampoEditable;
    valorNuevo: number;
  } | null>(null);

  const iniciarEdicion = useCallback(
    (fdi: number, campo: CampoEditable, valor: number) => {
      setEdicion({ fdi, campo, valorActual: valor.toFixed(1) });
    },
    []
  );

  const confirmarEdicion = useCallback(
    (valorNuevo: number) => {
      if (!edicion) return;
      setPendiente({ fdi: edicion.fdi, campo: edicion.campo, valorNuevo });
      setEdicion(null);
    },
    [edicion]
  );

  const cancelarEdicion = useCallback(() => setEdicion(null), []);

  const manejarJustificacion = useCallback(
    async (justificacion: string, autor: string) => {
      if (!pendiente) return;
      await onAjusteManual({
        id_caso: idCaso,
        fdi: pendiente.fdi,
        campo: pendiente.campo,
        valor_nuevo: pendiente.valorNuevo,
        autor,
        justificacion,
      });
      setPendiente(null);
    },
    [pendiente, idCaso, onAjusteManual]
  );

  const columnas = [
    "FDI",
    "T actual",
    "A actual",
    "I actual",
    "T objetivo",
    "A objetivo",
    "I objetivo",
    "ΔT",
    "ΔA",
    "ΔI",
    "Grosor base",
    "Ángulo slot",
    "Conf.",
    "Ajuste",
  ];

  return (
    <>
      {pendiente && (
        <ModalJustificacion
          onConfirmar={manejarJustificacion}
          onCancelar={() => setPendiente(null)}
        />
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-slate-800 border-b border-slate-600">
              {columnas.map((col) => (
                <th
                  key={col}
                  className="px-3 py-2 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {piezas.map((pieza) => {
              const seleccionada = piezaSeleccionada === pieza.fdi;
              const tObjetivo = pieza.torque_deg + pieza.delta_t;
              const aObjetivo = pieza.angulacion_deg + pieza.delta_a;
              const iObjetivo = pieza.inclinacion_deg + pieza.delta_i;

              return (
                <tr
                  key={pieza.fdi}
                  onClick={() => onSeleccionarPieza(pieza.fdi)}
                  className={[
                    "border-b border-slate-700 cursor-pointer transition-colors",
                    seleccionada
                      ? "bg-blue-950 border-blue-700"
                      : "hover:bg-slate-800",
                  ].join(" ")}
                >
                  <td className="px-3 py-2 font-mono font-bold text-blue-300">
                    {etiquetaFDI(pieza.fdi)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <CeldaEditable
                      valor={pieza.torque_deg}
                      fdi={pieza.fdi}
                      campo="torque_deg"
                      edicionActual={edicion}
                      onIniciarEdicion={iniciarEdicion}
                      onConfirmarEdicion={confirmarEdicion}
                      onCancelarEdicion={cancelarEdicion}
                      onChange={(v) =>
                        setEdicion((e) => e ? { ...e, valorActual: v } : null)
                      }
                    />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <CeldaEditable
                      valor={pieza.angulacion_deg}
                      fdi={pieza.fdi}
                      campo="angulacion_deg"
                      edicionActual={edicion}
                      onIniciarEdicion={iniciarEdicion}
                      onConfirmarEdicion={confirmarEdicion}
                      onCancelarEdicion={cancelarEdicion}
                      onChange={(v) =>
                        setEdicion((e) => e ? { ...e, valorActual: v } : null)
                      }
                    />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <CeldaEditable
                      valor={pieza.inclinacion_deg}
                      fdi={pieza.fdi}
                      campo="inclinacion_deg"
                      edicionActual={edicion}
                      onIniciarEdicion={iniciarEdicion}
                      onConfirmarEdicion={confirmarEdicion}
                      onCancelarEdicion={cancelarEdicion}
                      onChange={(v) =>
                        setEdicion((e) => e ? { ...e, valorActual: v } : null)
                      }
                    />
                  </td>
                  <td className="px-3 py-2 text-right text-slate-300">
                    {formatearAngulo(tObjetivo)}
                  </td>
                  <td className="px-3 py-2 text-right text-slate-300">
                    {formatearAngulo(aObjetivo)}
                  </td>
                  <td className="px-3 py-2 text-right text-slate-300">
                    {formatearAngulo(iObjetivo)}
                  </td>
                  <td className={`px-3 py-2 text-right font-mono ${colorDelta(pieza.delta_t)}`}>
                    {pieza.delta_t > 0 ? "+" : ""}{formatearAngulo(pieza.delta_t)}
                  </td>
                  <td className={`px-3 py-2 text-right font-mono ${colorDelta(pieza.delta_a)}`}>
                    {pieza.delta_a > 0 ? "+" : ""}{formatearAngulo(pieza.delta_a)}
                  </td>
                  <td className={`px-3 py-2 text-right font-mono ${colorDelta(pieza.delta_i)}`}>
                    {pieza.delta_i > 0 ? "+" : ""}{formatearAngulo(pieza.delta_i)}
                  </td>
                  <td className="px-3 py-2 text-right text-slate-300">
                    {pieza.grosor_base_mm.toFixed(2)} mm
                  </td>
                  <td className="px-3 py-2 text-right text-slate-300">
                    {formatearAngulo(pieza.angulo_slot_deg)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <span
                      className={
                        pieza.confianza_segmentacion >= 0.95
                          ? "text-green-400"
                          : pieza.confianza_segmentacion >= 0.80
                          ? "text-yellow-400"
                          : "text-red-400"
                      }
                    >
                      {(pieza.confianza_segmentacion * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-3 py-2 text-center">
                    {pieza.ajuste_manual ? (
                      <span
                        className="text-yellow-400 text-xs"
                        title={pieza.justificacion_ajuste}
                      >
                        ✏️
                      </span>
                    ) : (
                      <span className="text-slate-600 text-xs">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
};
